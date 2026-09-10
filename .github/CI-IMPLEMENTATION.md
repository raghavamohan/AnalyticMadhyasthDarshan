# CI findings F1–F15

Implementation of the September 2026 review of #440–#456. See [CI.md](CI.md) for the operating contract and dependency graph.

| Finding | Implementation |
|---|---|
| F1 Content reverts | Immutable content manifests exclude source/runtime provenance; deployment receipts are separate. |
| F2 Runtime audits | The fast path requires the same content and complete runtime/binding fingerprint. Audits verify the new marker, including its build receipt. |
| F3 Live dashboard navigation | Live links carry the verified publication revision and an explicit navigation exemption. |
| F4 Active baseline | Plans compare current consumed inputs with the active deployment's protected build receipt and R2 checksums, never the last push. |
| F5 Public API state | MCP/Studies API reads the active publication and its catalog/Markdown, with no Git HEAD fallback. |
| F6 Generator ownership | One Markdown PDF owner; declared companion source chain and freshness gate; deterministic DOCX/no-op notes; per-card seals; approved reference source and byte hashes. |
| F7 Preparation readiness | Source-only portal drafts report Preparing; complete verification follows accepted preparation; readiness follows successful verification. |
| F8 Duplicate verification | Exact head/base/intent identities, idempotent dispatch, and live identity rechecks before acceptance and success. |
| F9 Dependency selectors | One consumed-input graph for Markdown, recursive embedded resources, used link metadata, deck pairs and references. |
| F10 Output cache inputs | Ignored PDFs never enter input fingerprints; link decisions use source/catalog/HTML availability. |
| F11 Jobs/transfers | Plan before renderers, skip empty families, transfer selected files, reuse unchanged R2 records without body downloads. |
| F12 Packaging churn | Stable asset hashes and dependency URLs; canonical HTML redirects to a release URL; shared navigation carries revision without embedding it in every file. |
| F13 Repeated builds | Verified same-repo preparation/review PDFs can feed later phases; parallel checks/renderers; one master validation owner. |
| F14 Generator fan-out | Disposable HTML for PDF verification; batch search/offline finalization for preparation. |
| F15 Worker selection | Compare each executable/configuration fingerprint with its active Cloudflare version; one serialized shared edge-policy owner. |

The companion gate found one existing stale ontology speaker note on slide 10. It was synchronized from the existing companion source, and both PDFs were rebuilt and verified with LibreOffice 26.2.3.2. Canonical study text and Edited-on timestamps are unchanged. Social cards received initial input/output seals; unchanged runs skip rendering.

Regression coverage includes `_test_artifact_graph.py`, `_test_publication_proofs.py`, `_test_site_release.py`, `_test_mcp_api_errors.mjs`, generated-PDF/cache tests, and the existing required lifecycle/security/reader suites.

Local validation passed all 45 enforced Python suites, Worker and navigation tests, actionlint, generated-output freshness and agent-mirror checks. Real Draft and Released PDFs were byte-identical across two runs with pinned Chrome. The unified companion PDF passed verification, and a browser check confirmed that an older dashboard opens the newer Live revision.

The first deployment needs a cold generated-PDF build or matching reviewed artifacts because the old deployment has no build receipt. Approved references already present with matching R2 metadata are reused. Subsequent publication uses the newly active receipt. No production object deletion is part of this migration.
