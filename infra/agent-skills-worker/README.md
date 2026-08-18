# Agent Skills worker (`amd-agent-skills`)

Serves [Agent Skills Discovery](https://github.com/cloudflare/agent-skills-discovery-rfc)
v0.2.0 for `https://analyticmadhyasthdarshan.org/.well-known/agent-skills/*`.

Canonical files stay in [`.well-known/agent-skills/`](../../.well-known/agent-skills/).
The Worker embeds those files so the index and `SKILL.md` artifacts return HTTP 200
with `application/json` / `text/markdown`.

The zone API token can upload this Worker but cannot create a Workers Route, so
production currently 302-redirects `/.well-known/agent-skills/*` to
`https://amd-agent-skills.raghavamohan.workers.dev` (managed by
`python Scripts/_cloudflare_performance.py --apply-redirect`). When a token with
Workers Routes Edit is available, attach

`analyticmadhyasthdarshan.org/.well-known/agent-skills/*` → `amd-agent-skills`

and remove that redirect.

## Deploy

From the repository root:

```powershell
python Scripts/_build_agent_skills_index.py
python Scripts/_publish_agent_skills_snippet.py
python Scripts/_test_agent_skills.py --live
```

The publish script writes `src/index.js` (gitignored), uploads Worker
`amd-agent-skills`, enables the workers.dev host, and upserts the redirect.
