# Discussions worker (`amd-discussions`)

Cloudflare Worker that backs **per-study discussion boards** on the public site. Readers sign in with an **email magic link** (any identity — no GitHub required) to post comments. Structured corrections still use [GitHub Issues](../../.github/ISSUE_TEMPLATE/study-feedback.yml).

## Setup

From this directory:

```powershell
npm ci
```

### D1 database

Create the database and bind it in `wrangler.toml`:

```powershell
npx wrangler d1 create amd-discussions
```

Copy the `database_id` into `wrangler.toml` under `[[d1_databases]]`, then apply migrations:

```powershell
npx wrangler d1 migrations apply amd-discussions --remote
npx wrangler d1 migrations apply amd-discussions --local
```

### Secrets

```powershell
npx wrangler secret put SESSION_SECRET
npx wrangler secret put TURNSTILE_SECRET_KEY
npx wrangler secret put RESEND_API_KEY
npx wrangler secret put ADMIN_EMAILS
```

Optional:

```powershell
npx wrangler secret put EMAIL_FROM
npx wrangler secret put ALLOWED_ORIGINS
```

| Secret | Purpose |
|--------|---------|
| `SESSION_SECRET` | HMAC signing key for `amd_discuss_session` cookie (32+ random bytes) |
| `TURNSTILE_SECRET_KEY` | Same Turnstile widget secret as the submissions worker |
| `RESEND_API_KEY` | [Resend](https://resend.com) API key for magic-link email |
| `EMAIL_FROM` | Sender address (default: `Discussions <discussions@analyticmadhyasthdarshan.org>`) |
| `ADMIN_EMAILS` | Comma-separated admin emails allowed to hide comments |
| `ALLOWED_ORIGINS` | Extra CORS origins for local preview |

For local dev without email, copy [`.dev.vars.example`](.dev.vars.example) to `.dev.vars` and set your values:

```powershell
Copy-Item .dev.vars.example .dev.vars
```

Example `.dev.vars`:

```
DEV_EXPOSE_MAGIC_LINK=true
```

Magic-link responses then include `verifyUrl` in JSON (never enable in production).

## Deploy

The `submission-worker-deploy.yml` matrix bundle-checks and tests both API
Workers on PRs and deploys them after merge to `master`. The commands below
remain available for an intentional manual deployment. The protected deployment
applies ordered D1 migrations before updating the discussion Worker. Migration
`0003_magic_return.sql` binds each new token to its allowed return destination.
Tokens store SHA-256 digests and use a conditional `UPDATE ... RETURNING`.
Outstanding links issued before this migration require requesting a new link.
Existing comments, identities and sessions are preserved.

POST requests require a trusted Origin and JSON content type. Add local preview
origins explicitly with `ALLOWED_ORIGINS`. Responses are private/no-store,
including comment lists whose permissions depend on the signed-in reader.
Existing discussion sessions are signed JWTs bound to a D1 `sessions` row.
Logout deletes that row so the cookie cannot be reused. Remaining discussion
controls include opt-in direct-reply mail and private signed-in reporting
(`DIS-01`). Authors can delete their own comments; moderators can hide comments
and review/resolve reports separately.

### Reply emails and reports

Reply email is off by default for every existing and new discussion account.
Enable it in any discussion using **Email me when someone replies to my comments**.
The account setting covers direct replies to your comments across studies. It
excludes your own replies and top-level comments. Email contains a link, not the
comment text. A maximum of ten notification jobs per recipient per hour bounds
reply-mail volume; extra replies remain published without additional email.

Migration `0004_notifications_reports.sql` adds preferences, a durable mail
outbox and private reports. A reply and its eligible notification job are one D1
transaction. The Worker cron runs every five minutes and handles at most ten jobs
per invocation. Atomic leases prevent concurrent sends. Retries use an unchanged
provider payload and Resend idempotency key; after 23 hours from the first attempt,
unconfirmed jobs become `uncertain` and are not resent. Never manually replay an
uncertain job without checking the provider. Provider acceptance is recorded as
`sent` with its provider message ID for delivery investigation; it does not
guarantee inbox delivery. Mail failures do not undo comments.

Unsubscribe links carry purpose-bound signed tokens in the fragment. GET only
opens a confirmation page; explicit same-origin POST disables the corresponding
opt-in enrollment without signing in. A link from an older enrollment cannot
disable a newer opt-in. Preferences can also be disabled while signed in.
Workers retain sent/cancelled outbox metadata for 30 days, uncertain jobs for
90 days, and resolved reports for 90 days. Provider payloads are cleared after
terminal outcomes. Open reports remain until moderators resolve them.

Reports require discussion sign-in, a reason of 1–1000 characters, and a visible
comment belonging to another account in the indicated discussion. Each account
can create at most ten reports per hour. Repeated reports of the same comment
return success without creating another report or changing its reason. Reports
never hide comments automatically and are not public. Accounts in `ADMIN_EMAILS`
can load the private report list on any discussion, resolve a report while
leaving the comment visible, or explicitly hide the comment and resolve it.
Hide retains the existing version-conflict protection.

Run `python Scripts/_test_discussion_features.py` for real SQLite outbox,
preference, unsubscribe and moderation regressions. The existing browser suite
also exercises preferences, reporting, moderator resolution and unsubscribe on
desktop and narrow layouts (optional local WebKit/touch coverage is documented
in [contributor reliability](../../docs/contributor-reliability.md)).

```powershell
npx wrangler deploy
```

`CLOUDFLARE_API_TOKEN` must include **Account → Workers Scripts → Edit**. A zone-only token can attach routes (`--apply-discussions-api`) but `wrangler deploy` fails with API error 10000.

The remote migration step additionally requires **Account → D1 → Edit** on the
account containing `amd-discussions`. D1 Read can list pending migrations but
cannot apply them; Cloudflare returns error `7500` when the query is denied.
Prefer a separate GitHub Actions secret `CLOUDFLARE_D1_API_TOKEN` scoped to that
account with D1 Edit. Only the migration step uses it. If that secret is absent,
the step uses `CLOUDFLARE_API_TOKEN`, which must then also have D1 Edit.
The Worker deployment continues to use the existing Worker token.

To recover a permission-only failed deployment, correct the appropriate token
permission or secret and rerun the failed job. Migrations are tracked in D1;
already-applied migrations are skipped. Do not bypass the migration gate or
deploy the new Worker against a schema missing `return_to`.

Default worker URL: `https://amd-discussions.<account>.workers.dev`

Discussion pages use same-origin `/api/...` when Worker routes are configured on `analyticmadhyasthdarshan.org`; otherwise they fall back to the workers.dev URL.

### Route on custom domain

After deploy, attach routes so the API is same-origin:

```powershell
# Run from the repository root, not infra/discussions-worker
python Scripts/_cloudflare_performance.py --apply-discussions-api
```

Or manually in Cloudflare dashboard → Workers Routes:

- `analyticmadhyasthdarshan.org/api/discussions/*` → `amd-discussions`
- `analyticmadhyasthdarshan.org/api/discuss-auth/*` → `amd-discussions`

## API

JSON errors use the public [`ErrorResponse`](../../openapi/discussions.json)
contract: `success: false`, stable `code`, human-readable `message`,
`requestId`, and optional `details`. The same value is returned in the
`X-Request-ID` header. Successful response bodies are unchanged.

| Route | Auth | Purpose |
|-------|------|---------|
| `GET /api/discussions/health` | — | Liveness and dependency readiness (`ok` or `degraded`; `health` is not a study slug) |
| `GET /api/discussions/stats` | — | Paginated comment counts and latest activity per study slug (`stats` is reserved) |
| `GET /api/discussions/:slug` | — | Paginated visible comments plus an email-free viewer/session summary for a study |
| `POST /api/discussions/:slug/comments` | cookie | Post a comment (session required; Turnstile not repeated per post) |
| `POST /api/discussions/:slug/comments/:id/hide` | admin cookie | Soft-hide another user's comment |
| `POST /api/discussions/:slug/comments/:id/delete` | author cookie | Soft-hide your own comment |
| `POST /api/discuss-auth/magic-link` | Turnstile | Send email sign-in link |
| `GET /api/discuss-auth/verify#token=…` | — | Read-only confirmation page; no session creation or token consumption |
| `POST /api/discuss-auth/confirm` | token + trusted Origin | Confirm JSON `{token}`; set session cookie and return the stored destination |
| `GET /api/discuss-auth/me` | cookie | `{ loggedIn, userId, email, displayName, isAdmin }` |
| `POST /api/discuss-auth/logout` | cookie | Revoke the stored session and clear the cookie |

Auth routes use the **`/api/discuss-auth/`** prefix so they do not clash with the submissions worker (`/api/auth/github`, etc.). `health` and `stats` are reserved slugs so `GET /api/discussions/:slug` cannot swallow the liveness or stats routes. Unauthenticated writes return JSON `401` responses and rely on the documented first-party session-cookie flow; they do not advertise bearer authentication.

List routes accept validated `limit` and `offset` query parameters (`limit` defaults
to 50 and is capped at 100; `offset` is capped at 10,000). Responses include a
`meta` object with `total`, `limit`, `offset`, `hasMore`, and `nextOffset`.
Every returned comment includes `updatedAt`; hide and delete requests must send that
value as `sourceUpdatedAt`. A concurrent change returns `409` with
`details.currentSource` and `details.providedSource`, allowing the client to reload
instead of silently overwriting newer state.

## Cloudflare edge limits (apex domain)

Discussion routes run on `analyticmadhyasthdarshan.org/api/...` (not the `api.` subdomain). **Pro plan allows only two WAF rate-limit rules** in the zone; the repo uses one for leaked-credential checks and one combined rule (`amd_rl_edge_api`: **40 req / 10 s per IP** on portal `/api/*`, all apex `/api/*`, and `/mcp*` paths). Worker-side magic-link limit remains 5/hour per email. Apply or verify via [`infra/worker/README.md`](../worker/README.md) (`--apply-discussions-rate-limits` / `--check-edge-security`).

Static discussion pages receive **enforcing CSP** and other security headers from zone Transform Rules. Turnstile needs `https://challenges.cloudflare.com` in `script-src`, `connect-src`, and `frame-src`; study Mermaid loads from `https://cdn.jsdelivr.net`; Cloudflare Web Analytics uses `static.cloudflareinsights.com` — all included in the repo CSP spec.

`GET /api/discuss-auth/verify` is covered by the shared edge rule, along with
other apex API routes. Honor `Retry-After` if an email-link retry is throttled.

## Moderation

- Comments are plain text (HTML stripped server-side).
- Max body length: 8192 characters.
- JSON request bodies are limited to 16 KiB; oversized payloads return `413`.
- Turnstile required on magic-link requests only (signed-in session covers repeat comment posts).
- Rate limit: 5 magic-link emails per address per hour (worker); edge WAF limits — see **Cloudflare edge limits** above.
- API responses advertise the edge policy in `RateLimit-Policy`. Magic-link responses also include the email-specific `RateLimit` state, and a `429` includes `Retry-After`.
- Admins (`ADMIN_EMAILS`) see a **Hide** button on others' comments.
- Authors see **Delete** on their own comments (same soft-hide in D1).
- Hidden comments are excluded from `GET /api/discussions/:slug`.

## Local development

```powershell
npx wrangler dev --port 8788
```

Set `ALLOWED_ORIGINS` to include your local preview origin. Point discussion page `API_BASE` at `http://localhost:8788` while testing, or use `wrangler dev` with the site open from the same origin if proxied.

## Privacy

Discussion sign-in stores email and display name in D1. Add a short notice on discussion pages (generated by `Scripts/_build_discussion_pages.py`) linking to site policies when auth is enabled.

## Email DNS (Resend)

Magic-link email is sent through [Resend](https://resend.com) from
`discussions@analyticmadhyasthdarshan.org` (override with `EMAIL_FROM`). The following
DNS records must exist in Cloudflare for the apex domain:

| Type | Name | Purpose |
|------|------|---------|
| TXT | `resend._domainkey` | DKIM public key (selector `resend`) |
| TXT | `send` | SPF — `v=spf1 include:amazonses.com ~all` |
| MX | `send` | Bounce/feedback — `feedback-smtp.us-east-1.amazonses.com` |
| TXT | `_dmarc` | DMARC policy (monitoring) |

Resend places SPF and MX on the **`send` subdomain**, not the apex. That is intentional.

### Verify DNS locally

From the repo root:

```powershell
python Scripts/_verify_resend_dns.py
```

This checks the Resend records above. [dns.email](https://dns.email/?domain=analyticmadhyasthdarshan.org)
(Resend's checker) should report all sending records as verified when DNS is correct.

### Cloudflare DMARC dashboard false positive

Cloudflare's DMARC dashboard probes only **common** DKIM selectors (`default`, `google`,
`selector1`, …). Resend uses **`resend`**, so the dashboard may show **DKIM Fail** even
when mail is signed correctly. Ignore that warning if `python Scripts/_verify_resend_dns.py`
passes and the Resend Domains page shows the domain as verified.

### Live send test (optional)

With `RESEND_API_KEY` exported (same key as the worker secret), or present in
`infra/discussions-worker/.dev.vars` for local runs:

```powershell
$env:RESEND_API_KEY = "re_..."
python Scripts/_verify_resend_dns.py --mail-tester
```

This sends a test message to [mail-tester.com](https://www.mail-tester.com/) and polls for
`dkim=pass`. You can also request a magic link on any discussion page and inspect the
received message headers for `s=resend; d=analyticmadhyasthdarshan.org` and
`dkim=pass` in `Authentication-Results`.
