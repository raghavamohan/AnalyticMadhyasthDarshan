# Submissions worker (`amd-submissions`)

Cloudflare Worker that backs the [Web Submission Portal](../../Studies/submit.html). Contributors **sign in with GitHub** to propose studies and submit drafts; the worker creates GitHub issues and pull requests and exposes a **My Submissions** dashboard.

Reading studies on the public site does **not** require GitHub.

## Setup

From this directory:

```powershell
npm install
```

### GitHub token (maintainer PAT)

Fine-grained or classic PAT with **Issues**, **Contents**, and **Pull requests** write access on `raghavamohan/AnalyticMadhyasthDarshan` only. Used to open submission branches and pull requests.

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

Both portal forms require Cloudflare Turnstile. The public site key is in [`wrangler.toml`](wrangler.toml) (`TURNSTILE_SITE_KEY`) and [`Studies/submit.html`](../../Studies/submit.html).

Store the widget secret on the Worker:

```powershell
python _fetch_turnstile_secret.py
Get-Content .turnstile-secret.tmp -Raw | npx wrangler secret put TURNSTILE_SECRET_KEY
Remove-Item .turnstile-secret.tmp
```

The worker verifies `turnstileToken` on every `/api/propose` and `/api/submit` request before calling GitHub. To add hostnames (for example `localhost`), update the widget domains in the Cloudflare dashboard or run `_update_turnstile_domains.py` when the API token has `Account.Turnstile:Edit`.

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
| `GET /api/me/submissions` | cookie | List contributor's study proposals (`study-proposal` or `proposal-approved` label) and linked PRs |
| `POST /api/propose` | cookie + Turnstile | Create a `study-proposal` issue **as the signed-in user** |
| `GET /api/proposal-status?issue=N` | optional | Approval status, slug, `ownedByYou` when signed in |
| `POST /api/submit` | cookie + Turnstile | Branch, commit `Studies/<Slug>/<Slug>.md`, open PR (`Portal-GitHub: @user` in body) |

For new studies, `/api/submit` requires `proposalIssue`, verifies `proposal-approved`, and checks the signed-in user owns the proposal issue. PR bodies include `Portal-GitHub: @login` so submissions can be correlated in search.

## Local development

```powershell
npx wrangler dev
```

Set secrets for local runs with `wrangler secret put …` or a `.dev.vars` file (gitignored — do not commit tokens).

Open the portal with a matching `ALLOWED_ORIGINS` entry and use the local worker URL as `API_BASE` in `submit.html` while testing.
