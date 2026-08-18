# auth.md

This document tells agents how Analytic Madhyasth Darshan handles identity.
Machine-readable OAuth discovery is at

- https://analyticmadhyasthdarshan.org/.well-known/oauth-protected-resource
  ([RFC 9728](https://www.rfc-editor.org/rfc/rfc9728))
- https://analyticmadhyasthdarshan.org/.well-known/oauth-authorization-server
  ([RFC 8414](https://www.rfc-editor.org/rfc/rfc8414))

The public API catalog is at
https://analyticmadhyasthdarshan.org/.well-known/api-catalog
([RFC 9727](https://www.rfc-editor.org/rfc/rfc9727)).

The A2A Agent Card is at
https://analyticmadhyasthdarshan.org/.well-known/agent-card.json
([A2A Protocol](https://a2a-protocol.org/latest/specification/)).
It describes public catalog reads over HTTP+JSON. This site does not run an
A2A JSON-RPC Worker and does not accept `message/send` tasks.

Repo agent skills are listed at
https://analyticmadhyasthdarshan.org/.well-known/agent-skills/index.json
([Agent Skills Discovery](https://github.com/cloudflare/agent-skills-discovery-rfc)).

The MCP Server Card is at
https://analyticmadhyasthdarshan.org/.well-known/mcp/server-card.json
([SEP-1649](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1649)).
It advertises Streamable HTTP at `/mcp`. This site publishes the discovery
card; it does not yet run an MCP session runtime.

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
Query `_index._agents.analyticmadhyasthdarshan.org` for the site index
and `_a2a._agents.analyticmadhyasthdarshan.org` for the Agent Card endpoint.

## Audience

**Readers and agents fetching studies do not register.** The studies catalog
JSON, HTML, and PDFs are public. Start at
[Studies/index.html](Studies/index.html) or
[Studies/catalog-topical.json](Studies/catalog-topical.json).

**Write APIs are for humans.** This site does not mint OAuth access tokens for
agents, does not accept ID-JAG assertions, and does not run an Auth.md
credential ceremony. `POST` to `register_uri` or `claim_uri` returns
`501` and does not create an account, send email, or issue a credential.

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

Authorization Server metadata still advertises `bearer_methods_supported: ["header"]`
and a verified-email registration method so agents can discover this policy
through the Auth.md / RFC 9728 path. The advertised `register_uri` and
`claim_uri` are discovery stubs; they do not issue tokens.
