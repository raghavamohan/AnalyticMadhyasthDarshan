# Agent Skills worker (`amd-agent-skills`)

Serves [Agent Skills Discovery](https://github.com/cloudflare/agent-skills-discovery-rfc)
v0.2.0 for `https://analyticmadhyasthdarshan.org/.well-known/agent-skills/*`.

Canonical files stay in [`.well-known/agent-skills/`](../../.well-known/agent-skills/).
The Worker embeds those files so the public index, the maintainer index, and
`SKILL.md` artifacts return HTTP 200 with `application/json` / `text/markdown`.
Crawlers should load `index.json` (reader skills only). Clone-based agents can
load `index-maintainer.json` for repo lifecycle skills.

Production attaches the zone Workers Route
`analyticmadhyasthdarshan.org/.well-known/agent-skills/*` → `amd-agent-skills`.
`--apply-redirect` binds that route and does not 302 to workers.dev.

## Deploy

Changes to the canonical indexes, reader or maintainer skills, publisher, or
Worker are generated and checked on pull requests, then deployed automatically
after merge to `master` by `agent-publications.yml`. The post-deploy job compares
both live indexes and every advertised skill artifact with the canonical files.

For an intentional manual deployment from the repository root:

```powershell
python Scripts/_build_agent_skills_index.py
python Scripts/_publish_agent_skills_snippet.py
python Scripts/_test_agent_skills.py --live
```

The publish script writes `src/index.js` (gitignored), uploads Worker
`amd-agent-skills`, enables the workers.dev host, and upserts the redirect.
Pass `--generate-only` to write and syntax-check the bundle without Cloudflare
credentials or a deployment.
