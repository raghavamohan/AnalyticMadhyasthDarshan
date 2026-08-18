# Submissions worker (`amd-submissions`)

Cloudflare Worker that backs the [Web Submission Portal](../../Studies/submit.html). Contributors **sign in with GitHub** to propose studies, submit drafts, update content, and change Draft/Released status. The default portal view is **My Submissions** — a unified dashboard of proposals, pull requests, catalog status, and CI checks.

Reading studies on the public site does **not** require GitHub.

## Setup

From this directory:

```powershell
npm install
```

### GitHub token (maintainer PAT)

Fine-grained or classic PAT with **Issues**, **Contents**, and **Pull requests** write access on `raghavamohan/AnalyticMadhyasthDarshan` only. Used to open submission branches and pull requests, fetch catalog JSON, and read CI check runs.

```powershell
npx wrangler secret put GITHUB_TOKEN
```

Optional: override the default branch if the repository default changes:

```powershell
npx wrangler secret put DEFAULT_BRANCH
```

When prompted, enter `master` (the repository default today).

### GitHub OAuth App (contributor sign-in)

1. **GitHub → Settings → Developer settings → OAuth Apps → New OAuth App**
2. **Application name:** `Analytic Madhyasth Darshan Portal` (or similar)
3. **Homepage URL:** `https://analyticmadhyasthdarshan.org`
4. **Authorization callback URL:** `https://api.analyticmadhyasthdarshan.org/api/auth/callback`  
   (the same-site custom domain configured in `wrangler.toml`; use your deployed worker origin if it differs)
5. Copy the **Client ID** into `wrangler.toml` as `GITHUB_CLIENT_ID`, or set:

   ```powershell
   npx wrangler secret put GITHUB_CLIENT_ID
   ```

6. Store the **Client secret**:

   ```powershell
   npx wrangler secret put GITHUB_CLIENT_SECRET
   ```

7. Generate a random session signing key (32+ bytes):

   ```powershell
   npx wrangler secret put SESSION_SECRET
   ```

OAuth scope requested: `read:user user:email public_repo` (proposals are filed as issues on the contributor's account; `user:email` lets the portal offer optional email notifications).

For local `wrangler dev`, add a second callback URL on the OAuth app, e.g. `http://localhost:8787/api/auth/callback`, and set:

```powershell
npx wrangler secret put ALLOWED_ORIGINS
```

Enter: `http://localhost:8787,http://127.0.0.1:8787`

## Turnstile (bot protection)

Portal forms require Cloudflare Turnstile. The public site key is in [`wrangler.toml`](wrangler.toml) (`TURNSTILE_SITE_KEY`) and [`Studies/submit.html`](../../Studies/submit.html).

Store the widget secret on the Worker:

```powershell
python _fetch_turnstile_secret.py
Get-Content .turnstile-secret.tmp -Raw | npx wrangler secret put TURNSTILE_SECRET_KEY
Remove-Item .turnstile-secret.tmp
```

The worker verifies `turnstileToken` on every write request before calling GitHub. To add hostnames (for example `localhost`), update the widget domains in the Cloudflare dashboard or run `_update_turnstile_domains.py` when the API token has `Account.Turnstile:Edit`.

## Deploy

```powershell
npx wrangler deploy
```

The worker is served from the same-site custom domain `https://api.analyticmadhyasthdarshan.org` (configured via `routes` in [`wrangler.toml`](wrangler.toml)). Serving the API on a subdomain of the site keeps the session cookie **first-party**, so it is not blocked by Safari ITP or Firefox Total Cookie Protection. The cookie uses `SameSite=Lax` (`COOKIE_SAMESITE` in `wrangler.toml`).

The portal reads this URL from the `API_BASE` constant in [`Studies/submit.html`](../../Studies/submit.html) — update it if the domain changes. For cross-site (`*.workers.dev`) deployments, set `COOKIE_SAMESITE = "None"` instead, but note third-party-cookie blocking will break sign-in in some browsers.

After deploy, confirm the OAuth app callback URL matches `https://api.analyticmadhyasthdarshan.org/api/auth/callback` (or your worker origin).

## API

| Route | Auth | Purpose |
|-------|------|---------|
| `GET /api/health` | — | Liveness `{ status: "ok" }` |
| `GET /api/auth/github?return_to=…` | — | Start GitHub OAuth; redirects back to `return_to` after sign-in |
| `GET /api/auth/callback` | — | OAuth callback; sets session cookie |
| `GET /api/auth/me` | cookie | `{ loggedIn, login }` |
| `POST /api/auth/logout` | cookie | Clear session |
| `GET /api/me/submissions` | cookie | Unified dashboard: proposals (pending/approved/declined), pre-catalog status, PRs, CI, row actions |
| `GET /api/me/notifications` | cookie | `{ configured, email, enabled }` notification preferences |
| `POST /api/me/notifications` | cookie | Update notification `email` / `enabled` |
| `POST /api/propose` | cookie + Turnstile | Create a `study-proposal` issue **as the signed-in user** |
| `GET /api/proposal-status?issue=N` | optional | Approval/declined status, locked slug, `preCatalog`, `ownedByYou` when signed in |
| `GET /api/study-source?slug=Slug` | — | Current published markdown for a study (used by **Update a study**) |
| `POST /api/submit` | cookie + Turnstile | Branch, commit `Studies/<Slug>/<Slug>.md`, open PR; enforces locked slug and one open PR per slug |
| `POST /api/status-change` | cookie + Turnstile | Open a `status-change` PR (body: `Study slug:` / `Target status:` for CI) |
| `POST /api/notify` | `X-Notify-Secret` | Called by the `portal-notify.yml` workflow to email a contributor on approval/decline/merge |

For new studies, `/api/submit` requires `proposalIssue`, verifies `proposal-approved`, and checks the signed-in user owns the proposal issue. PR bodies include `Portal-GitHub: @login` so submissions can be correlated in search.

## Email notifications (optional)

Contributors can opt in to email when a proposal is approved/declined or a study PR is merged, instead of relying on GitHub notifications. The feature is **off** unless configured.

1. OAuth requests the `user:email` scope; on sign-in the worker stores the contributor's verified primary email as their notification address (only if none is set — the portal toggle wins afterwards). Preferences live in the `SESSIONS` KV namespace under `notify:<login>`.
2. Set the Resend secret and a shared notify secret:

   ```powershell
   npx wrangler secret put RESEND_API_KEY
   npx wrangler secret put NOTIFY_SECRET
   ```

   Optionally override the `From` address with an `EMAIL_FROM` var.
3. In GitHub, add a repository secret `PORTAL_NOTIFY_SECRET` (same value as `NOTIFY_SECRET`) and optionally a variable `PORTAL_API_BASE` (defaults to `https://api.analyticmadhyasthdarshan.org`). The [`portal-notify.yml`](../../.github/workflows/portal-notify.yml) workflow calls `POST /api/notify` on the `proposal-approved` / `proposal-declined` labels and on merged portal PRs.

Contributors manage their address and opt-out from the notification bar on **My Submissions**. `POST /api/notify` is a no-op when the contributor has not opted in.

> **GitHub Actions must reach `/api/notify`.** The runner uses a datacenter IP; without the WAF skip below, Super Bot Fight Mode returns `403 "Just a moment…"` and email is never sent (the workflow may still show `success`, with `Notify request failed (403)` in the logs).
>
> **Pro (current):** Super Bot Fight Mode is on; WAF skip rule `amd_skip_sbfm_portal_notify` exempts only `/api/notify`. Verify with `python Scripts/_cloudflare_performance.py --check-edge-security` (notify reachability check). Re-apply with `--apply-portal-edge-security` if the skip rule was removed.
>
> **Free plan fallback:** turn Bot Fight Mode off (Security → Bots) — the worker still enforces `X-Notify-Secret`, Turnstile on writes, and signed sessions.
>
> Functional test: toggle `proposal-approved` or `proposal-declined` on a test issue; `portal-notify` should log `Notify response: {"success":true,...}`.

### Dashboard performance

`GET /api/me/submissions` uses a batched fetch pipeline (no per-proposal GitHub searches):

1. Parallel: the user's proposals via the REST issues list (`creator` + `study-proposal` label — immediately consistent, so a just-submitted proposal shows up at once), PR search, catalog JSON (three files, cached 60 s via Workers Cache API).
2. In-memory join: link proposals to PRs by `Proposal issue: #N` in PR bodies.
3. Conditional enrich: check-runs for open PRs only (concurrency pool of 5).

Response includes `meta.timingMs`, `meta.githubRequests`, and optional `meta.truncated`.

## Cloudflare edge configuration (not in this repo)

- **Custom domain:** submissions worker at `api.analyticmadhyasthdarshan.org` via [`wrangler.toml`](wrangler.toml) (`SameSite=Lax` cookie with the portal).
- **API catalog:** [RFC 9727](https://www.rfc-editor.org/rfc/rfc9727) discovery at `/.well-known/api-catalog` is served by [`infra/api-catalog-worker`](../api-catalog-worker/README.md). The homepage advertises that catalog plus OpenAPI and docs via RFC 8288 `Link` headers. Identity discovery: [`/auth.md`](../../auth.md) and [RFC 9728](https://www.rfc-editor.org/rfc/rfc9728) Protected Resource Metadata. Human docs: [`api-docs.html`](../../api-docs.html).

Zone settings live on `analyticmadhyasthdarshan.org` in Cloudflare, not in git. Scripts in [`Scripts/_cloudflare_performance.py`](../../Scripts/_cloudflare_performance.py) apply and verify the stack; [`infra/discussions-worker/README.md`](../discussions-worker/README.md) notes discussion-specific limits and CSP/Turnstile interaction.

**Verify anytime:** `python Scripts/_cloudflare_performance.py --check-edge-security`

### Applied on Pro (live)

| Control | Rule / setting | Script ref |
|---------|----------------|------------|
| Super Bot Fight Mode | `managed_challenge` on definitely automated; AI bots blocked | `--apply-portal-edge-security` |
| Notify SBFM skip | `amd_skip_sbfm_portal_notify` → `http_request_sbfm` skip for `/api/notify` only | `--apply-portal-edge-security` |
| Probe-path block | `amd_block_common_probes` (`/wp-*`, `/.env`, `/.git`, …) | `--apply-edge-security` |
| API rate limit | `amd_rl_edge_api` — 40 req / 10 s per IP (portal `api.*` + apex discussion routes); plus leaked-credential rule (Pro max **2** rate-limit rules) | `--apply-discussions-rate-limits` |
| TLS / transport | min TLS 1.2, HSTS 1y + includeSubDomains (preload **off**), HTTPS rewrites on, `browser_check` off, SSL **full** (GitHub Pages) | `--apply-security-baseline` |
| Response headers | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, **CSP report-only** on static pages (not `/api/*`); RFC 8288 `Link` on `/` and `/Studies/index.html`; `text/markdown` on `/auth.md`; `application/json` on OAuth well-known URIs; RFC 9727 `application/linkset+json` on `/.well-known/api-catalog` | `--apply-security-headers` |

**Re-apply full stack after drift or zone changes:** `python Scripts/_cloudflare_performance.py --apply-edge-security`

### Operator next steps (not done yet)

1. **CSP enforce** — CSP is **report-only** today. Browse `Studies/index.html`, `Studies/submit.html`, and a discussion page; confirm the browser console shows no unexpected violations for 1–2 weeks. Then change `security_headers_rule_body()` in `_cloudflare_performance.py` to set `Content-Security-Policy` (enforcing) instead of `Content-Security-Policy-Report-Only`, run `--apply-security-headers`, and re-check pages.
2. **HSTS preload** — only after ~30 days of stable HSTS with no HTTPS regressions. Set `preload: true` in `security_header_hsts_spec()`, re-run `--apply-security-baseline`, then submit the domain to the [HSTS preload list](https://hstspreload.org/) if desired. Preload is hard to undo.
3. **Manual smoke tests** — portal GitHub OAuth sign-in + submit flow; discussion magic-link request + email verify link; optional [SSL Labs](https://www.ssllabs.com/ssltest/) check (TLS 1.2+ only, HSTS present).
4. **Optional: `content_bots_protection`** — can enable in Super Bot Fight Mode after confirming Google/Bing indexing in Search Console (verified bots remain allowed). Not enabled by default.
5. **Rate-limit tuning** — if users behind a shared office IP hit `amd_rl_edge_api`, raise `requests_per_period` in `edge_api_rate_limit_rules_spec()` (e.g. 50–60) and re-run `--apply-discussions-rate-limits`.

Items **not** planned: SSL Full (Strict) on GitHub Pages origin; separate per-route rate limits beyond Pro’s two-rule cap (worker-side limits cover magic-link abuse).

## Local development

```powershell
npx wrangler dev
```

Set secrets for local runs with `wrangler secret put …` or a `.dev.vars` file (gitignored — do not commit tokens).

Open the portal with a matching `ALLOWED_ORIGINS` entry and use the local worker URL as `API_BASE` in `submit.html` while testing.
