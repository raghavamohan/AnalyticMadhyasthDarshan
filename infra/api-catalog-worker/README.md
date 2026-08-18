# API catalog worker (`amd-api-catalog`)

Canonical [RFC 9727](https://www.rfc-editor.org/rfc/rfc9727) linkset for
`https://analyticmadhyasthdarshan.org/.well-known/api-catalog`. Keep
[`src/api-catalog.json`](src/api-catalog.json) identical to
[`.well-known/api-catalog`](../../.well-known/api-catalog).
`python Scripts/_test_api_catalog.py` checks that they match.

**Production does not run this Worker.** GitHub Pages can host the JSON but
cannot set `Content-Type: application/linkset+json` on the extensionless path,
so live serving uses a Snippet plus a Transform Rule (see **Live serving**
below). Deploy this Worker only when replacing that Snippet.

## Deploy

From this directory (requires a Cloudflare token with Workers deploy permission):

```powershell
npx wrangler deploy
```

Route: `https://analyticmadhyasthdarshan.org/.well-known/api-catalog`

## Live serving

GitHub Pages cannot set `Content-Type: application/linkset+json` on this
extensionless path. Production currently serves the catalog with:

1. A Cloudflare Snippet (`amd_api_catalog`) that returns the linkset with HTTP 200
2. A Transform Rule that sets the RFC 9727 Content-Type and `Link` header
3. A homepage Transform Rule that advertises `api-catalog`, `service-desc`,
   `service-doc`, and `describedby` on `/` and `/Studies/index.html`
   ([RFC 8288](https://www.rfc-editor.org/rfc/rfc8288),
   [RFC 9727 §3](https://www.rfc-editor.org/rfc/rfc9727#section-3)), including
   the A2A Agent Card at `/.well-known/agent-card.json` and the Agent Skills
   Discovery index at `/.well-known/agent-skills/index.json`

After changing `.well-known/api-catalog`, `.well-known/agent-card.json`, or
`.well-known/agent-skills/`, re-publish the snippets and confirm the header
rules:

```powershell
python Scripts/_publish_api_catalog_snippet.py
python Scripts/_publish_agent_card_snippet.py
python Scripts/_publish_agent_skills_snippet.py
python Scripts/_publish_auth_md_snippet.py
python Scripts/_cloudflare_performance.py --apply-security-headers
python Scripts/_test_api_catalog.py --live
python Scripts/_test_agent_card.py --live
python Scripts/_test_agent_skills.py --live
python Scripts/_test_auth_md.py --live
```

When a Cloudflare token with **Workers Scripts Edit** is available, you can
`npx wrangler deploy` this worker instead. Remove the snippet rule first so the
two do not both handle the same path.

Human documentation: [api-docs.html](../../api-docs.html).
