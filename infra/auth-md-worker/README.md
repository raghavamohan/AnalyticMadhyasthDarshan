# Auth.md worker (`amd-auth-md`)

Serves the canonical [`/auth.md`](../../auth.md) identity policy.

The publish script embeds that file and writes gitignored `src/index.js`.
Production attaches a zone Workers Route for `/auth.md*`. Deployment also
removes retired OAuth-discovery and agent-registration routes. A leftover
Snippet `amd_auth_md` still runs before Workers; until it can be
unbound, a Redirect Rule sends `/auth.md` to the workers.dev host.

## Deploy

`agent-publications.yml` generates and validates the bundle on pull requests,
then deploys merged changes and checks the live policy against `auth.md`.
For local validation without credentials or deployment, run from the repository root:

```powershell
python Scripts/_publish_auth_md_snippet.py --generate-only
python Scripts/_test_auth_md.py
```

For an intentional manual deployment:

```powershell
python Scripts/_publish_auth_md_snippet.py
python Scripts/_test_auth_md.py --live
```
