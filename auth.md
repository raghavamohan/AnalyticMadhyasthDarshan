# auth.md

This document tells agents how Analytic Madhyasth Darshan handles identity and
which public interfaces require credentials.

The public API catalog is at
https://analyticmadhyasthdarshan.org/.well-known/api-catalog
([RFC 9727](https://www.rfc-editor.org/rfc/rfc9727)).

Repo agent skills are listed at
https://analyticmadhyasthdarshan.org/.well-known/agent-skills/index.json
([Agent Skills Discovery](https://github.com/cloudflare/agent-skills-discovery-rfc)).
That index is **reader skills only**. Maintainer skills that need a git clone
are at
https://analyticmadhyasthdarshan.org/.well-known/agent-skills/index-maintainer.json

The MCP Server Card is at
https://analyticmadhyasthdarshan.org/.well-known/mcp/server-card.json
([SEP-1649](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649)).
It advertises Streamable HTTP at `/mcp`. `POST /mcp` exposes read-only catalog
tools (`search_studies`, `list_studies`, `get_study`, `get_study_outline`,
`get_glossary`, `get_start_here`, `get_cite`) and resources
(`studies://catalog-all`, `studies://glossary`, `studies://feed`,
`studies://start-here`, `studies://study/{slug}`). There are
no write tools.

The shared glossary is at
https://analyticmadhyasthdarshan.org/Studies/glossary.json
(`GET https://analyticmadhyasthdarshan.org/api/glossary?q=` searches it).
The unified catalog is at
https://analyticmadhyasthdarshan.org/Studies/catalog-all.json
Catalog search is `GET https://analyticmadhyasthdarshan.org/api/studies`
(query parameters `q`, `collection`, `status`, `slug`, `limit`, `offset`).
One published study plus its heading outline is
`GET https://analyticmadhyasthdarshan.org/api/studies/{slug}`.
The recommended reading path is
`GET https://analyticmadhyasthdarshan.org/api/start-here`.
A suggested citation line is
`GET https://analyticmadhyasthdarshan.org/api/cite/{slug}`.
Study and glossary list responses default to 50 rows and allow at most 100 per
request. Their response includes `total`, `limit`, `offset`, `hasMore`, and
`nextOffset`. MCP `search_studies`, `list_studies`, and `get_glossary` use the
same bounds.

The Web Bot Auth directory is at
https://analyticmadhyasthdarshan.org/.well-known/http-message-signatures-directory
([IETF WebBotAuth](https://datatracker.ietf.org/wg/webbotauth/about/)).
It is a JWKS of Ed25519 public keys. Outbound signed requests use
`Signature-Agent` and `Signature-Input`. This site does not crawl other
origins as a verified bot.

Browser agents can call catalog tools through
[WebMCP](https://webmachinelearning.github.io/webmcp/). The page script is
https://analyticmadhyasthdarshan.org/webmcp.js
and registers tools with `navigator.modelContext.registerTool` on load.

DNS for AI Discovery ([DNS-AID](https://datatracker.ietf.org/doc/html/draft-mozleywilliams-dnsop-dnsaid))
publishes ServiceMode HTTPS records under the `_agents` namespace. The zone is
DNSSEC-signed; Cloudflare Registrar publishes the parent DS from CDS/CDNSKEY.
Query `_index._agents.analyticmadhyasthdarshan.org` for the site index.

## Audience

**Readers and agents fetching studies do not register.** The studies catalog
JSON, HTML, Markdown, and PDFs are public. Start at
[Studies/index.html](Studies/index.html),
[Studies/catalog-all.json](Studies/catalog-all.json), or
[Studies/catalog-topical.json](Studies/catalog-topical.json).

**Write APIs are for humans.** The public site does not expose an OAuth
authorization server, bearer-token flow, agent registration flow, or A2A task
runtime. Agents should treat submission and discussion writes as interactive
browser workflows unless a future API version explicitly documents otherwise.

## Human provisioning

### Submission portal — GitHub OAuth

Contributors who propose or edit studies sign in with GitHub in a browser.

- Start: `GET https://api.analyticmadhyasthdarshan.org/api/auth/github`
- Callback: `GET https://api.analyticmadhyasthdarshan.org/api/auth/callback`
- Session: first-party cookie; write routes also require a Cloudflare Turnstile
  token
- Docs: [api-docs.html](api-docs.html), OpenAPI at
  [openapi/submissions.json](/openapi/submissions.json)

### Discussions — verified email

Readers who comment on a study request a magic link to their email.

- Request: `POST https://analyticmadhyasthdarshan.org/api/discuss-auth/magic-link`
  (Turnstile required)
- Verify: `GET https://analyticmadhyasthdarshan.org/api/discuss-auth/verify`
- Session: first-party cookie
- Docs: [api-docs.html](api-docs.html), OpenAPI at
  [openapi/discussions.json](/openapi/discussions.json)

Do not call those discussion routes from a passive agent scan. A magic-link
request sends email.

## Credential use

Published studies need no credential. Portal and discussion writes use the
session cookie from the flows above, not `Authorization: Bearer`. Server-to-server
`POST /api/notify` uses a shared secret and is not a public client.

Browser POST requests must include a trusted `Origin` and
`Content-Type: application/json`, including bodyless actions such as logout.
The production browser origin is `https://analyticmadhyasthdarshan.org`; local
preview origins must be explicitly configured. API responses are private and
must not be cached. OAuth callbacks validate signed, expiring state and use
S256 PKCE; session cookies contain an opaque identifier rather than a GitHub
access token. Email sign-in links are single-use and expire after 15 minutes.

Existing-content updates and deletions require the source identifier returned
by the relevant read operation. Stale writes return `409` with the current
identifier in `details.currentSource`; clients must reload and reconcile rather
than overwrite it. Responses advertise rate policy in `RateLimit-Policy`.
Contribution writes also return account quota in `RateLimit`; magic-link
requests return their email quota. On `429`, honor `Retry-After` before retrying.
OpenAPI documents the byte and field-size limits for every JSON write.
