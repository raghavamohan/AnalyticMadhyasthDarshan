# Auth.md worker (`amd-auth-md`)

Serves the canonical [`/auth.md`](../../auth.md) identity policy.

The publish script embeds that file and writes gitignored `src/index.js`.
Production attaches a zone Workers Route for `/auth.md*`. Deployment also
removes retired OAuth-discovery and agent-registration routes. A leftover
Snippet `amd_auth_md` still runs before Workers; until it can be
unbound, a Redirect Rule sends `/auth.md` to the workers.dev host.

## Deploy

From the repository root:

```powershell
python Scripts/_publish_auth_md_snippet.py
python Scripts/_test_auth_md.py --live
```
