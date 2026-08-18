# API catalog worker (`amd-api-catalog`)

Serves [RFC 9727](https://www.rfc-editor.org/rfc/rfc9727) discovery at
`https://analyticmadhyasthdarshan.org/.well-known/api-catalog` with
`Content-Type: application/linkset+json`. GitHub Pages can host the same JSON
at [`.well-known/api-catalog`](../../.well-known/api-catalog) but cannot set
that media type on an extensionless path.

Keep [`src/api-catalog.json`](src/api-catalog.json) identical to the repo-root
`.well-known/api-catalog` file. `python Scripts/_test_api_catalog.py` checks
that they match.

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

After changing `.well-known/api-catalog`, re-publish the snippet and confirm the
header rule:

```powershell
python Scripts/_publish_api_catalog_snippet.py
python Scripts/_cloudflare_performance.py --apply-security-headers
python Scripts/_test_api_catalog.py --live
```

When a Cloudflare token with **Workers Scripts Edit** is available, you can
`npx wrangler deploy` this worker instead. Remove the snippet rule first so the
two do not both handle the same path.

Human documentation: [api-docs.html](../../api-docs.html).
