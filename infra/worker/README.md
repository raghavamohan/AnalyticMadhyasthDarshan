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

`CLOUDFLARE_API_TOKEN` must include **Account → Workers Scripts → Edit**. A zone-only token can apply Transform Rules and Snippets but `wrangler deploy` fails with API error 10000.

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
> **Pro (current):** Super Bot Fight Mode is on; WAF skip `amd_skip_sbfm_portal_notify` exempts `/api/notify`, and `amd_skip_sbfm_webmcp` exempts the studies catalog and `/webmcp.js` so in-browser agent scans can register tools. Verify with `python Scripts/_cloudflare_performance.py --check-edge-security`. Re-apply with `--apply-portal-edge-security` if a skip rule was removed.
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
- **API catalog:** [RFC 9727](https://www.rfc-editor.org/rfc/rfc9727) discovery at `/.well-known/api-catalog` is served by Worker `amd-api-catalog` on a zone route ([`infra/api-catalog-worker`](../api-catalog-worker/README.md)). The A2A Agent Card at `/.well-known/agent-card.json` is served by Worker `amd-agent-card` on a zone route ([`infra/agent-card-worker`](../agent-card-worker/README.md)). Agent Skills Discovery at `/.well-known/agent-skills/` is served by Worker `amd-agent-skills` on a zone route ([`infra/agent-skills-worker`](../agent-skills-worker/README.md)). The MCP Server Card at `/.well-known/mcp/server-card.json` and `/mcp` plus `GET /api/studies` are served by Worker `amd-mcp` on zone routes ([`infra/mcp-worker`](../mcp-worker/README.md)). Web Bot Auth at `/.well-known/http-message-signatures-directory` is served by Worker `amd-web-bot-auth` on a zone route ([`infra/web-bot-auth-worker`](../web-bot-auth-worker/README.md)). In-browser catalog tools are registered by [`/webmcp.js`](../../webmcp.js) on the studies landing page. DNS-AID ServiceMode HTTPS records at `_index._agents` and `_a2a._agents` are published with [`Scripts/_publish_dns_aid.py`](../../Scripts/_publish_dns_aid.py) and signed with DNSSEC. The homepage advertises the catalog, Agent Card, Agent Skills index, MCP Server Card, Web Bot Auth directory, WebMCP script, Auth.md, OAuth metadata, catalog JSON, OpenAPI, and docs via RFC 8288 `Link` headers. Identity discovery: [`/auth.md`](../../auth.md) and [RFC 9728](https://www.rfc-editor.org/rfc/rfc9728) Protected Resource Metadata. Human docs: [`api-docs.html`](../../api-docs.html). Unauthenticated JSON `401` responses include `WWW-Authenticate` pointing at the apex Protected Resource Metadata.

Zone settings live on `analyticmadhyasthdarshan.org` in Cloudflare, not in git. Scripts in [`Scripts/_cloudflare_performance.py`](../../Scripts/_cloudflare_performance.py) apply and verify the stack; [`infra/discussions-worker/README.md`](../discussions-worker/README.md) notes discussion-specific limits and CSP/Turnstile interaction.

**Verify anytime:** `python Scripts/_cloudflare_performance.py --check-edge-security`

### Applied on Pro (live)

| Control | Rule / setting | Script ref |
|---------|----------------|------------|
| Super Bot Fight Mode | `managed_challenge` on definitely automated; AI bots blocked; WAF skip on catalog/`webmcp.js`/`/mcp`/`/api/studies` so agent scanners can run | `--apply-portal-edge-security` |
| Notify SBFM skip | `amd_skip_sbfm_portal_notify` → `http_request_sbfm` skip for `/api/notify` only | `--apply-portal-edge-security` |
| Probe-path block | `amd_block_common_probes` (`/wp-*`, `/.env`, `/.git`, …) | `--apply-edge-security` |
| API rate limit | `amd_rl_edge_api` — 40 req / 10 s per IP (portal `api.*` + apex discussion routes); plus leaked-credential rule (Pro max **2** rate-limit rules) | `--apply-discussions-rate-limits` |
| TLS / transport | min TLS 1.2, HSTS 1y + includeSubDomains + **preload**, HTTPS rewrites on, `browser_check` off, SSL **full** (GitHub Pages) | `--apply-security-baseline` |
| Response headers | `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, **enforcing CSP** on static pages (not `/api/*`); RFC 8288 `Link` on `/` and `/Studies/index.html`; `text/markdown` on `/auth.md` and Agent Skills `SKILL.md`; `application/json` on OAuth well-known URIs, `/.well-known/agent-skills/index.json`, and `/.well-known/mcp/server-card.json`; `application/http-message-signatures-directory+json` on `/.well-known/http-message-signatures-directory`; `application/a2a+json` on `/.well-known/agent-card.json`; RFC 9727 `application/linkset+json` on `/.well-known/api-catalog` | `--apply-security-headers` |
| DNS-AID | ServiceMode HTTPS at `_index._agents` and `_a2a._agents`; zone DNSSEC signing on; parent DS via Cloudflare Registrar CDS/CDNSKEY scan (1–2 days) | `python Scripts/_publish_dns_aid.py` |

**Re-apply full stack after drift or zone changes:** `python Scripts/_cloudflare_performance.py --apply-edge-security`

### Operator next steps (not done yet)

1. **HSTS preload list** — the HSTS header now includes `preload` (stable since July 2026). Submitting `analyticmadhyasthdarshan.org` to the [HSTS preload list](https://hstspreload.org/) is still optional and hard to undo. Do that only if you want Chrome/Firefox/Safari to hard-code HTTPS for this domain and every subdomain.
2. **Manual smoke tests** — automated checks cover TLS/HSTS, portal page load, GitHub OAuth start (`302` to GitHub), and discussion page load. Still do a signed-in pass: portal GitHub OAuth through submit, and a discussion magic-link request plus email verify. Optional [SSL Labs](https://www.ssllabs.com/ssltest/) check (TLS 1.2+ only, HSTS present).
3. **Optional: `content_bots_protection`** — can enable in Super Bot Fight Mode after confirming Google/Bing indexing in Search Console (verified bots remain allowed). Not enabled by default. `crawler_protection` is already on.
4. **Rate-limit tuning** — if users behind a shared office IP hit `amd_rl_edge_api`, raise `requests_per_period` in `edge_api_rate_limit_rules_spec()` (e.g. 50–60) and re-run `--apply-discussions-rate-limits`.

Items **not** planned: SSL Full (Strict) on GitHub Pages origin; separate per-route rate limits beyond Pro’s two-rule cap (worker-side limits cover magic-link abuse).

## Local development

```powershell
npx wrangler dev
```

Set secrets for local runs with `wrangler secret put …` or a `.dev.vars` file (gitignored — do not commit tokens).

Open the portal with a matching `ALLOWED_ORIGINS` entry and use the local worker URL as `API_BASE` in `submit.html` while testing.
