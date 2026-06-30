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
4. **Authorization callback URL:** `https://amd-submissions.raghavamohan.workers.dev/api/auth/callback`  
   (use your deployed worker origin if the name changes)
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

OAuth scope requested: `read:user public_repo` (proposals are filed as issues on the contributor's account).

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

The worker URL is shown after deploy (currently `https://amd-submissions.raghavamohan.workers.dev`). The portal reads this URL from the `API_BASE` constant in [`Studies/submit.html`](../../Studies/submit.html) — update it if the worker name or account changes.

After deploy, confirm the OAuth app callback URL matches `{worker-origin}/api/auth/callback`.

## API

| Route | Auth | Purpose |
|-------|------|---------|
| `GET /api/auth/github?return_to=…` | — | Start GitHub OAuth; redirects back to `return_to` after sign-in |
| `GET /api/auth/callback` | — | OAuth callback; sets session cookie |
| `GET /api/auth/me` | cookie | `{ loggedIn, login }` |
| `POST /api/auth/logout` | cookie | Clear session |
| `GET /api/me/submissions` | cookie | Unified dashboard: proposals (pending/approved/declined), pre-catalog status, PRs, CI, row actions |
| `POST /api/propose` | cookie + Turnstile | Create a `study-proposal` issue **as the signed-in user** |
| `GET /api/proposal-status?issue=N` | optional | Approval/declined status, locked slug, `preCatalog`, `ownedByYou` when signed in |
| `POST /api/submit` | cookie + Turnstile | Branch, commit `Studies/<Slug>/<Slug>.md`, open PR; enforces locked slug and one open PR per slug |
| `POST /api/status-change` | cookie + Turnstile | Open a `status-change` PR (body: `Study slug:` / `Target status:` for CI) |

For new studies, `/api/submit` requires `proposalIssue`, verifies `proposal-approved`, and checks the signed-in user owns the proposal issue. PR bodies include `Portal-GitHub: @login` so submissions can be correlated in search.

### Dashboard performance

`GET /api/me/submissions` uses a batched fetch pipeline (no per-proposal GitHub searches):

1. Parallel: proposal search, PR search, catalog JSON (three files, cached 60 s via Workers Cache API).
2. In-memory join: link proposals to PRs by `Proposal issue: #N` in PR bodies.
3. Conditional enrich: check-runs for open PRs only (concurrency pool of 5).

Response includes `meta.timingMs`, `meta.githubRequests`, and optional `meta.truncated` when search results exceed 20 items.

## Local development

```powershell
npx wrangler dev
```

Set secrets for local runs with `wrangler secret put …` or a `.dev.vars` file (gitignored — do not commit tokens).

Open the portal with a matching `ALLOWED_ORIGINS` entry and use the local worker URL as `API_BASE` in `submit.html` while testing.
