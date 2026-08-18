# API catalog worker (`amd-api-catalog`)

Canonical [RFC 9727](https://www.rfc-editor.org/rfc/rfc9727) linkset for
`https://analyticmadhyasthdarshan.org/.well-known/api-catalog`. Keep
[`src/api-catalog.json`](src/api-catalog.json) identical to
[`.well-known/api-catalog`](../../.well-known/api-catalog).
`python Scripts/_test_api_catalog.py` checks that they match.

GitHub Pages can host the JSON but cannot set
`Content-Type: application/linkset+json` on the extensionless path. Production
attaches the zone Workers Route
`analyticmadhyasthdarshan.org/.well-known/api-catalog*` → `amd-api-catalog`.

## Deploy

From the repository root:

```powershell
python Scripts/_publish_api_catalog_snippet.py
python Scripts/_test_api_catalog.py --live
```

The publish script uploads Worker `amd-api-catalog` from a self-contained
module generated in memory (it does not overwrite committed `src/index.js`),
enables the workers.dev host, and binds the zone route.

## Homepage Link headers

A Transform Rule advertises `api-catalog`, `service-desc`, `service-doc`, and
`describedby` on `/` and `/Studies/index.html`
([RFC 8288](https://www.rfc-editor.org/rfc/rfc8288),
[RFC 9727 §3](https://www.rfc-editor.org/rfc/rfc9727#section-3)). After changing
`.well-known/api-catalog` or related discovery documents:

```powershell
python Scripts/_publish_api_catalog_snippet.py
python Scripts/_publish_agent_card_snippet.py
python Scripts/_publish_agent_skills_snippet.py
python Scripts/_publish_mcp_server_card.py
python Scripts/_publish_web_bot_auth.py
python Scripts/_publish_auth_md_snippet.py
python Scripts/_cloudflare_performance.py --apply-security-headers
python Scripts/_test_api_catalog.py --live
python Scripts/_test_agent_card.py --live
python Scripts/_test_agent_skills.py --live
python Scripts/_test_mcp_server_card.py --live
python Scripts/_test_web_bot_auth.py --live
python Scripts/_test_auth_md.py --live
```

Human documentation: [api-docs.html](../../api-docs.html).
