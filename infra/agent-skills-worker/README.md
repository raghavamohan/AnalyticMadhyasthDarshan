# Agent Skills worker (`amd-agent-skills`)

Serves [Agent Skills Discovery](https://github.com/cloudflare/agent-skills-discovery-rfc)
v0.2.0 for `https://analyticmadhyasthdarshan.org/.well-known/agent-skills/*`.

Canonical files stay in [`.well-known/agent-skills/`](../../.well-known/agent-skills/).
The Worker embeds those files so the index and `SKILL.md` artifacts return HTTP 200
with `application/json` / `text/markdown`.

Production attaches the zone Workers Route
`analyticmadhyasthdarshan.org/.well-known/agent-skills/*` → `amd-agent-skills`.
`--apply-redirect` binds that route and does not 302 to workers.dev.

## Deploy

From the repository root:

```powershell
python Scripts/_build_agent_skills_index.py
python Scripts/_publish_agent_skills_snippet.py
python Scripts/_test_agent_skills.py --live
```

The publish script writes `src/index.js` (gitignored), uploads Worker
`amd-agent-skills`, enables the workers.dev host, and upserts the redirect.
