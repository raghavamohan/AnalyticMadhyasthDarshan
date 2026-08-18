# Auth.md worker (`amd-auth-md`)

Serves [`/auth.md`](../../auth.md) plus OAuth discovery at
`/.well-known/oauth-protected-resource` and
`/.well-known/oauth-authorization-server`. Stub `501` responses on
`/agent/auth`, `/agent/auth/claim`, and `/oauth2/token`.

The publish script embeds those files and writes gitignored `src/index.js`.
Production attaches zone Workers Routes for those paths. A leftover Snippet
`amd_auth_md` still runs before Workers; until it can be unbound, a Redirect
Rule 302s the same paths to `amd-auth-md.raghavamohan.workers.dev`.

## Deploy

From the repository root:

```powershell
python Scripts/_publish_auth_md_snippet.py
python Scripts/_test_auth_md.py --live
```
