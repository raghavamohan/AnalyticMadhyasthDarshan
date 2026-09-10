# Public API improvement plan

This plan covers the public study HTTP API, MCP, Agent Skills, WebMCP, the
submission API, the discussion API, and their discovery documents. The guiding
rule is simple: discovery must describe deployed behavior exactly. A protocol
is not advertised until its runtime, authentication, conformance tests, and
operational ownership all exist.

## Current supported surface

| Surface | Role | Authentication |
|---|---|---|
| Study HTTP API and catalog JSON | Search, retrieve, navigate, cite | Public |
| MCP and MCP Server Card | Read-only study tools and resources | Public |
| Agent Skills and WebMCP | Reader workflows and browser tools | Public |
| Submission API | Proposals, revisions, submissions, status changes | Human GitHub sign-in, first-party cookie, Turnstile |
| Discussion API | Comments and moderation | Human email magic link, first-party cookie, Turnstile |
| Notification hook | CI-to-worker email events | Shared secret |

A2A task operations, agent OAuth access tokens, and native mobile store clients
are intentionally not part of the supported surface. The decision gates below
define when A2A or agent OAuth should be added. Native Android/iOS applications
are out of scope on the [website plan](website-improvement-plan.md); do not add
bearer write tokens or a second origin policy in order to support a store app.
Browser PWA install, JSON Feed/Atom, and discussion reply mail stay on the
existing first-party cookie and public-read contracts.

## Phase 1 — lock the contract (implemented)

Status: complete and deployed by the protected-branch workflows after the Phase
1 API-contract merge.

- Make OpenAPI the required review artifact for every route change.
- Validate all three OpenAPI files in CI with a standards-compliant parser and
  linter, in addition to the repository's runtime-route parity checks.
- Define one JSON error envelope with `code`, `message`, `requestId`, and
  optional `details`; migrate every JSON error without changing success bodies.
- Document shared `400`, `401`, `403`, `409`, `413`, `415`, `429`, and `503`
  responses as reusable OpenAPI components.
- Add contract tests for response bodies and headers, not only paths and status
  codes. Include cookie-only `401`, trusted-origin enforcement, JSON media-type
  enforcement, and private/no-store caching.
- Fail CI when API catalog, OpenAPI, Auth.md, homepage `Link` headers, sitemap,
  Worker bundles, or live canonical publications drift.

Exit criteria: every implemented operation is represented in OpenAPI; every
documented non-2xx response has a test; canonical discovery files and generated
Worker payloads compare byte-for-byte.

Implementation notes:

- `Scripts/_validate_openapi.py` validates all three documents with a standards
  parser and enforces the shared error schema, response components, examples,
  operation IDs, and summaries.
- Submission, discussion, and Studies HTTP errors return `success: false`,
  `code`, `message`, `requestId`, and optional `details`; MCP protocol errors
  retain their JSON-RPC envelope and carry the request ID in `error.data`.
- Runtime tests cover the common error statuses and the browser-facing cookie,
  origin, media-type, privacy, and no-store contracts. Publication tests compare
  deployed discovery and OpenAPI payloads with their canonical repository files.
- Both API workflows now run when a runtime, browser client, OpenAPI document,
  discovery test, or shared contract changes, so a route cannot bypass contract
  validation.

## Phase 2 — make writes resilient and predictable (implemented)

Status: complete in the repository; deployment follows the protected-branch
workflow after merge.

- Extend operation receipts and idempotency keys from propose/revise/submit to
  status changes and deletions.
- Return a stable operation resource with explicit `notStarted`, `inProgress`,
  `complete`, and `uncertain` states.
- Publish rate-limit headers and retry guidance for worker and edge limits.
- Add optimistic-concurrency fields to every update/delete operation and return
  `409` with the current source identifier when state is stale.
- Set explicit maximum sizes in OpenAPI request schemas and test the boundary
  values.
- Add pagination and bounded filters before any list endpoint can grow beyond a
  single predictable response.

Exit criteria: retrying a write with the same idempotency key cannot create a
duplicate GitHub issue or pull request; clients can recover an interrupted
operation without guessing.

Implementation notes:

- All five contribution writes use the account-scoped `ContributorOperations`
  Durable Object. Status and deletion requests now use client-persisted UUIDv4
  receipts and deterministic recovery branches, just like content submissions.
- `GET /api/operation` exposes one state vocabulary while retaining the previous
  booleans and top-level result fields for additive compatibility.
- The dashboard stores at most one status/deletion receipt per GitHub account in
  browser storage before sending. A reload can check an uncertain result or
  retry only a confirmed `notStarted` action with the same receipt and payload.
- Existing study, note, and presentation replacements, status changes, artifact
  deletions, discussion moderation, and notification-preference updates carry a
  source identifier. A stale request returns `409` and
  `details.currentSource`; the browser preserves the original operation payload
  instead of silently rebasing a write.
- Contribution attempts publish the 30-per-account hourly policy, remaining
  capacity, and reset delay. Discussion magic-link requests publish their
  five-per-email hourly policy. Every API response advertises the 40-per-IP,
  10-second edge policy; `429` responses include `Retry-After`, which clients
  must honor before any reset hint.
- JSON bodies are counted as UTF-8 bytes before parsing. The public schemas
  state the 18,000,000-byte contribution-upload envelope, 65,536-byte small
  submission envelope, 16,384-byte discussion envelope, 2 MiB Markdown limit,
  10 MiB presentation limit, and individual string bounds.
- Studies and glossary reads, MCP list/search tools, submission dashboards,
  editable-artifact discovery, discussion threads, and discussion statistics
  use `limit`/`offset`, default 50, with a maximum page size of 100. Filters have
  explicit enums or maximum lengths. Browser clients follow `nextOffset` while
  every individual response remains bounded.
- No new Durable Object migration or secret is required.

## Phase 3 — observability and service levels (implemented)

Status: complete in the repository; deployment and the first 30-day baseline
follow the protected-branch workflows after merge. The authenticated production
smoke remains an operator-run activity because it requires an agreed disposable
GitHub record and authorized mailbox; safe read-only synthetics run hourly.

- Generate a request ID at the edge and return it on every response.
- Record structured metrics by operation ID, status family, latency, dependency,
  and retry outcome without storing study drafts, tokens, email addresses, or
  session cookies.
- Define initial objectives: 99.9% monthly availability for public reads, 99%
  for authenticated writes excluding upstream GitHub/Resend outages, and p95
  latency targets per operation class.
- Add synthetic checks for catalog search, one study, citation behavior, MCP
  initialization/tool listing, write authentication, and discovery-file
  equality.
- Publish a small machine-readable status endpoint for each runtime and document
  dependency degradation separately from total outage.

Exit criteria: regressions can be localized to edge, Worker, storage, GitHub,
email, or publication drift from one request ID and dashboard.

Implementation notes:

- Every dynamic study, MCP, submission, and discussion response now carries an
  `X-Request-ID`, including successful, redirect, empty, and not-found
  responses. Structured Worker logs use the same ID.
- All three runtimes write the shared `amd_api_metrics` Analytics Engine schema
  by service, OpenAPI operation ID, method, status family, latency, dominant
  dependency, retry outcome, and Worker version. The schema intentionally has
  no URL, query, body, draft, token, email, cookie, IP, or session fields.
- `/api/studies/health`, submission `/api/health`, and
  `/api/discussions/health` distinguish runtime reachability from required
  dependency readiness without exposing secret values.
- `.github/workflows/api-synthetics.yml` independently checks production every
  hour and on demand. It verifies statuses, search, detail, citation, MCP
  initialization/tool listing, unauthenticated write rejection, request IDs,
  and canonical discovery equality. Failures open or update one incident issue;
  a successful recovery closes it.
- [Public API operations](api-operations.md) defines the initial availability
  and p95 objectives, Analytics Engine dashboard queries, alert thresholds,
  incident localization, and the redacted authenticated OAuth/magic-link/write
  smoke record. Automated checks never create proposals, PRs, comments, or
  magic links.

## Phase 4 — versioning and client usability (later)

Status: deferred. Start only once a real external client depends on the API. A
browser PWA, the catalog Recently updated UI, and ordinary feed readers using
`feed.json` / Atom do
**not** by themselves start this phase. Pull ETags forward earlier if SITE-02
caching needs them. Do not treat a hypothetical store app as the external
client that unlocks bearer writes.

- Adopt a compatibility policy: additive changes remain within a major version;
  removals or semantic changes require a versioned base path and deprecation
  window.
- Add `Sunset` and deprecation links before removing a supported operation.
- Generate typed examples or a small client from OpenAPI and run it against the
  synthetic environment in CI.
- Add conditional GET support (`ETag` and `If-None-Match`) for catalogs, study
  detail, glossary, start-here, and citation responses.
- Publish examples for the complete read journey and each human write workflow.

Exit criteria: an external client can discover, generate against, and upgrade
the API without reading Worker source.

## Optional protocol decision gates

### A2A

Status: deferred for later; no current implementation work is planned.

Implement A2A only when there is a real stateful agent task that cannot be
expressed as an MCP read tool or ordinary HTTP request. Before publishing an
Agent Card, require:

- at least one A2A protocol binding and the required message/task operations;
- task lifecycle storage, cancellation, error, and retention semantics;
- protocol conformance and live end-to-end tests;
- authentication and abuse controls appropriate to every advertised skill;
- an owner for compatibility, monitoring, and incident response.

### Agent OAuth

Status: deferred for later; no current implementation work is planned. This is
separate from the already-supported human GitHub OAuth browser session.

Implement an OAuth authorization server only when a non-browser client needs
delegated write access. A native store application is not that client. Before
publishing authorization-server or protected-resource metadata, require:

- a concrete client and scope model with least-privilege permissions;
- implemented authorization and token endpoints, revocation, expiration,
  rotation, and audit logging;
- PKCE and current OAuth security best practices;
- bearer-token validation on the protected APIs and complete challenge/error
  behavior;
- security review, conformance tests, key-rotation runbook, and incident owner.

Until those gates are met, Auth.md remains the authoritative statement that
reads are public and writes use interactive human sessions or the private
notification secret.

### Discussion watch / reply mail (website-first)

Add authenticated discussion preference and report routes only when
[website DIS-01](website-improvement-plan.md) is scheduled, after discussion
session revocation (OPS-01). Keep the existing magic-link cookie. Document any
new route in `openapi/discussions.json` before deploy. This is not agent OAuth
and not a mobile push platform.

### Catalog feed siblings (website-first)

An Atom (or RSS) sibling of `Studies/feed.json` is an additive catalog resource
for SITE-02. Generate it from the same catalog writer, add it to
`openapi/studies.json` and `_verify_studies_index.py`, and keep JSON Feed as the
canonical machine feed. No new Worker is required.

## Delivery order

1. Keep the deployed Phase 1 contract/error checks green.
2. Keep the completed Phase 2 receipt, concurrency, pagination, and retry
   contracts green.
3. Deploy Phase 3 telemetry/status, run the safe hourly synthetics, and collect
   the first 30-day service-level baseline. Perform the authenticated production
   smoke only with an agreed disposable record and authorized mailbox.
4. When SITE-02 ships, document Atom/feed discovery in OpenAPI and catalog
   verification. Add ETags for catalogs and feeds if caching needs them.
5. Later, add Phase 4 versioning and generated clients when a non-browser consumer
   other than today’s MCP/WebMCP readers depends on the API.
6. Later, revisit A2A or agent OAuth only in response to a validated use case and an
   identified operator. A native store app is not that use case.
