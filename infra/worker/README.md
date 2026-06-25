# Submissions worker (`amd-submissions`)

Cloudflare Worker that backs the [Web Submission Portal](../../Studies/submit.html). It creates GitHub study-proposal issues and opens labeled pull requests for new or updated study markdown.

## Setup

From this directory:

```powershell
npm install
```

Create a fine-grained GitHub personal access token (or classic PAT) with **Issues**, **Contents**, and **Pull requests** write access on `raghavamohan/AnalyticMadhyasthDarshan` only.

Store it as a Worker secret (never commit the token):

```powershell
npx wrangler secret put GITHUB_TOKEN
```

Optional: override the default branch if the repository default changes:

```powershell
npx wrangler secret put DEFAULT_BRANCH
```

When prompted, enter `master` (the repository default today).

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

## API

| Route | Purpose |
|-------|---------|
| `POST /api/propose` | Create a `study-proposal` GitHub issue (requires valid Turnstile token) |
| `POST /api/submit` | Create branch, commit `Studies/<Slug>/<Slug>.md`, open PR with `new-study` or `study-update` label (requires valid Turnstile token) |

For new studies, `/api/submit` requires `proposalIssue` and verifies the issue has the `proposal-approved` label before opening a PR. The PR body includes `Proposal issue: #N` and `Slug:` so [`Scripts/_ci_study_pr.py`](../../Scripts/_ci_study_pr.py) can run `_add_study.py`.

## Local development

```powershell
npx wrangler dev
```

Set secrets for local runs with `wrangler secret put GITHUB_TOKEN` or a `.dev.vars` file (gitignored by Wrangler defaults — do not commit tokens).
