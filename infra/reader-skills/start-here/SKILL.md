---
name: start-here
description: >-
  Orient a reader or agent to Analytic Madhyasth Darshan: public catalogs,
  the recommended reading path, standpoint and scope, and where write APIs
  stay human-only. Use when an agent first lands on the site or asks how
  to begin reading the studies.
---

# Start here

This site publishes analytic studies of **Madhyasth Darshan** (Co-existentialism). Catalog reads are public. Write APIs are for humans; see [auth.md](https://analyticmadhyasthdarshan.org/auth.md).

## Catalogs

| Resource | URL |
|----------|-----|
| Human catalog | https://analyticmadhyasthdarshan.org/Studies/index.html |
| Unified JSON | https://analyticmadhyasthdarshan.org/Studies/catalog-all.json |
| Search | https://analyticmadhyasthdarshan.org/api/studies?q= |
| One study + outline | https://analyticmadhyasthdarshan.org/api/studies/The-Ontology-of-Coexistence |
| Glossary search | https://analyticmadhyasthdarshan.org/api/glossary?q=jeevan |
| Start here path | https://analyticmadhyasthdarshan.org/api/start-here |
| Citation | https://analyticmadhyasthdarshan.org/api/cite/The-Ontology-of-Coexistence |
| Glossary blob | https://analyticmadhyasthdarshan.org/Studies/glossary.json |
| Change feed | https://analyticmadhyasthdarshan.org/Studies/feed.json |
| `llms.txt` | https://analyticmadhyasthdarshan.org/llms.txt |

Each published row has `html`, `pdf`, and `md`. **Markdown is the source of truth.** HTML and PDF are generated.

## Reading path

On the studies landing page, follow **Start here**. The usual order is human, existence, knowledge, value, then lived participation. Formal and applied studies are a parallel track, not a substitute for the topical papers.

Every topical study includes **Standpoint and scope**: the author writes as a scientist/technologist; matter-first science is the honest starting point; the method is to state the darshan and compare it with physics and natural sciences, Advaita Vedanta, and modern Western philosophy. The aim is comparative understanding, not persuasion.

## Tools

- MCP Streamable HTTP: `POST https://analyticmadhyasthdarshan.org/mcp` (`search_studies`, `list_studies`, `get_study`, `get_study_outline`, `get_glossary`, `get_start_here`, `get_cite`)
- Study markdown resource: `studies://study/{slug}`
- WebMCP in the browser: https://analyticmadhyasthdarshan.org/webmcp.js
- OpenAPI: https://analyticmadhyasthdarshan.org/openapi/studies.json
- Public skills: https://analyticmadhyasthdarshan.org/.well-known/agent-skills/index.json
- Maintainer skills (git clone): https://analyticmadhyasthdarshan.org/.well-known/agent-skills/index-maintainer.json

Do not call discussion magic-link or GitHub OAuth routes from a passive scan.
