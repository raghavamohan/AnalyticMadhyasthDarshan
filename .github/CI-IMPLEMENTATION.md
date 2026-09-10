# CI implementation and remaining plan

Updated 10 September 2026 after production deployment of [#459](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/459), source `63e68a03c536e94ed6559172581d7f635afbf77f`. This is the current status of the September review of #440–#456 and the earlier seven remaining steps. See [CI.md](CI.md) for the operating contract and dependency graph.

The F1–F15 implementation is merged and running in production. Both the site and Agent-facing Workers deployments passed. The initial migration/build-receipt bootstrap is complete. Strict slide-PDF byte reproducibility remains unfinished within F6; broader operational acceptance and the follow-ups below are also still open. A green deployment does not establish that every lifecycle, offline, recovery, or renderer scenario has been exercised.

## Completed implementation

“Implemented” records merged code and its regression coverage. Remaining operational exercises are listed separately below.

| Finding | Status | Delivered behavior |
|---|---|---|
| F1 Content reverts | Implemented | Immutable content manifests exclude source/runtime provenance; deployment receipts are separate. A → B → A is covered by regression tests; a controlled live rollback exercise remains. |
| F2 Runtime audits | Implemented | The fast path requires the same content and complete runtime/binding fingerprint. Audits verify the new marker, including its build receipt. |
| F3 Live dashboard navigation | Implemented | Live links carry the verified publication revision and an explicit navigation exemption. An older-dashboard → newer-Live browser check passed. |
| F4 Active baseline | Implemented; production reuse verified | Plans compare consumed inputs with the active deployment's protected build receipt and R2 checksums, never the last push. #458 established the receipt; #459 reused it. |
| F5 Public API state | Implemented; live checks passed | MCP/Studies API reads the active publication and its catalog/Markdown, with no Git HEAD fallback. #458/#459 corrected Cloudflare cache/routing configuration and the live audit. |
| F6 Generator ownership and determinism | Ownership implemented; slide bytes still open | One Markdown PDF owner; declared companion source chain and freshness gate; deterministic DOCX/no-op notes; per-card seals; approved reference source and byte hashes. Strict slide-PDF byte determinism remains R3. |
| F7 Preparation readiness | Implemented | Source-only portal drafts report Preparing; complete verification follows accepted preparation; readiness follows successful verification. Repeat the full portal lifecycle under the new pipeline in R2. |
| F8 Duplicate verification | Implemented | Exact head/base/intent identities, idempotent dispatch, and live identity rechecks before acceptance and success. |
| F9 Dependency selectors | Implemented | One consumed-input graph for Markdown, recursive embedded resources, used link metadata, deck pairs and references. Static files retain a complete release inventory. |
| F10 Output cache inputs | Implemented | Ignored PDFs never enter input fingerprints; link decisions use source/catalog/HTML availability. |
| F11 Jobs/transfers | Implemented; production skips verified | Plan before renderers, skip empty families, transfer selected files, reuse unchanged R2 records without PDF body downloads. |
| F12 Packaging churn | Implemented; unchanged-content path verified | Stable asset hashes and dependency URLs; canonical HTML redirects to a release URL; shared navigation carries revision without embedding it in every file. |
| F13 Repeated builds | Implemented within current proof scope | Verified same-repo preparation/review PDFs can feed later phases; parallel checks/renderers; one master validation owner. Broader recovery lookup is optional R8. |
| F14 Generator fan-out | Implemented | Disposable HTML for PDF verification; batch search/offline finalization for preparation. |
| F15 Worker selection | Implemented; production skips verified | Compare each executable/configuration fingerprint with its active Cloudflare version; one serialized shared edge-policy owner. Only MCP changed among the four Agent-facing Workers in #459. |

The companion gate also found and repaired an existing stale ontology speaker note on slide 10, using the existing companion source. Both deck PDFs were verified with LibreOffice 26.2.3.2. Canonical study text and Edited-on timestamps were unchanged. Social cards received input/output seals so unchanged runs skip rendering.

## Deployment fixes and production evidence

| PR | Work completed | Outcome |
|---|---|---|
| [#457](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/457) | Main F1–F15 implementation, dependency planner, build proofs, publication protocol, preparation gates, generator ownership and Worker selection. | PR checks passed. Production exposed a reusable-workflow permission error and an unsupported MCP cache option. Submission/discussion Workers and shared edge policy deployed successfully. |
| [#458](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/458) | Granted the publication caller `actions: read`; made the MCP API uploader use Wrangler's runtime configuration; enabled `cache_option_enabled`; added configuration regressions. | [Site publication passed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/34424746547) and established the durable build receipt. MCP still read the old origin and failed with publication-marker 404/API 502. |
| [#459](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/459) | Enabled `global_fetch_strictly_public` so same-zone reads reach the site Worker; retained a required routing guard; stopped requiring API quota headers on static marker/catalog/reading-path reads while retaining API/MCP and challenge checks. | [Agent-facing Workers passed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/34426704381); [site publication passed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/34426704500). |

Confirmed for #459:

- Site run: **2m54s**, from creation at 01:44:59 UTC to final update at 01:47:53 UTC. This is one configuration-only run, not a benchmark for content changes.
- Planner: **0 builds, 81 reused artifacts**: 31 Markdown PDFs, 16 presentation PDFs and 34 approved reference artifacts. Both renderer jobs skipped; no PDF ZIP transfer or PDF upload was selected.
- Public content revision remained `206e6515fe0abe4fe5febeadda46bed25b7806afa9e27eed32aa79353ff91d47`. The source pointer advanced to the #459 merge. Canary and production reported **0 static asset upload batches**. Site Worker versions and provenance still advance on this path; “no content upload” does not mean no deployment work.
- The active build receipt is `site/builds/d10b853ba1564bd2e22768cdc3a988defab2ec2ab1964999fdd17ef4910cac4e.json`.
- MCP deployed its changed configuration. Agent Skills, Auth.md and API catalog skipped unchanged executable deployments.
- Live checks passed for all **27 catalog entries**, study outline, glossary, reading path, citations, citation errors, MCP initialization/tool discovery, Agent Skills, Auth.md and API catalog. A direct read after completion confirmed the #459 source marker and HTTP 200 from the Studies API.

## Validation completed and its limits

All 45 enforced Python suites and eight MCP JavaScript tests passed for the repair; all applicable PR checks passed. The main implementation also passed actionlint, freshness/agent-mirror checks, Worker/navigation tests, and real byte-identical Draft and Released Markdown-PDF rerenders with pinned Chrome. Four pre-existing held Python suites remain documented in `_run_test_suites.py`; they are not counted as passing enforced suites.

A temporary Worker on a unique same-zone Cloudflare route reproduced #458's exact failure using its old configuration. The repaired configuration then passed the complete live API audit plus nine additional MCP tool/resource reads. The temporary route and Worker were removed. This was a manual pre-merge canary; `agent-publications.yml` still deploys before running its automated live audit, which is why R1 remains.

The [#457 presentation smoke run](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/34422569722) rendered all eight deck pairs twice. All rendered/text comparisons passed. **All eight slides PDFs reported `byte-identical=no`; all eight notes PDFs reported `byte-identical=yes`.** `_verify_presentation_reproducible.py` currently accepts rendered/text equivalence. This is not proof of strict slide-byte determinism.

## Remaining work, in priority order

These are follow-ups, not failed or pending deployments. Planning them does not authorize production rollback, deletion, or new lifecycle submissions.

| Order | Priority | Remaining step | Completion evidence |
|---|---|---|---|
| R1 | P1 | **Automate pre-promotion API/Worker canaries.** Turn the manual same-zone test into a repeatable protected deployment gate for changed Workers. Validate the exact candidate bundle/configuration against the active publication before promotion, clean up temporary resources, and restore the prior version if the production audit fails. Keep secrets out of untrusted PR execution. | Cache/routing misconfiguration fails before the active API changes; catalog, Markdown, glossary, reading path and MCP calls pass through actual Cloudflare routing. Unchanged Workers still skip deployments. |
| R2 | P1 | **Finish operational acceptance under the new pipeline.** Record proposal → first draft → update → release → rename → retire, an already-open My Submissions page, saved/offline readers after changes and disconnection, failed/superseded publication recovery, and controlled rollback followed by forward re-promotion. Use approved disposable fixtures; closed/declined issue #420 is not a fixture. | A recorded matrix links each scenario to its revision, run/browser evidence and result. Public catalog, API, HTML, PDF and dashboard agree; stale preparation cannot write or mark ready; retained pages and offline resources follow the documented policy. Test isolated/canary recovery before any separately scheduled production drill. |
| R3 | P2 | **Finish strict slide-PDF byte reproducibility (F6).** Identify and canonicalize remaining nondeterministic LibreOffice PDF fields/structure, then require byte equality as well as visual/text/font/page fidelity for repeated renders. | All eight slide PDFs and eight notes PDFs have identical SHA-256 values across repeated clean builds under the pinned contract. Same-input repair/force rebuild does not introduce unexplained new blobs. |
| R4 | P2 | **Complete build/runtime/font contracts.** `render-contract.json`, renderer/package pins and Markdown host/font cache fingerprints are in place. Finish the Python/Node patch, runner-image/font version and migration policy for each artifact family; API jobs may keep a separate contract. | A renderer/font/runtime change is recorded and invalidates only its consumers; clean independent runners either reproduce the expected bytes or explicitly identify a contract change. |
| R5 | P2 | **Consolidate observability and measure change classes.** The JSON plan and logs already explain selections; add one run summary for rendered/reused PDFs, artifact-transfer bytes, R2 request/PUT bytes, changed Worker fingerprints, audit durations, and promotion/recovery results. Replay narrow edits such as #441/#452/#453 against the planner and record before/after selection counts. | Frontend-only, one-study, one-note, one-deck, catalog/proposal and retry runs have comparable evidence. Confirm zero unrelated renders/transfers and collect enough runs to set latency targets; do not generalize from #459 alone. |
| R6 | P3; after R2 | **Remove transitional CI paths.** Audit and retire disabled Pages retry and obsolete publication branches/comments once operational acceptance is recorded. Preserve shared builders, explicit bot verification dispatch and actual rollback support. | Each active surface has one documented owner; no disabled legacy workflow can accidentally resume publishing or request unnecessary write permissions. |
| R7 | P3; policy decision first | **Define retention, withdrawal and safe garbage collection.** Separate ordinary catalog retirement from immediate withdrawal; define retained-revision access, Worker-version retention, rollback horizon and reference rights obligations. Begin with a report of objects reachable from retained manifests/receipts. | An agreed policy and dry-run report protect all live/retained dependencies. Object deletion remains a separate reviewed operation and is never part of routine publication. |
| R8 | P3; optional optimization | **Broaden reviewed-artifact recovery lookup.** Current reuse searches the PR associated with the candidate merge and its validated preparation parent. If that merge only repairs CI while an earlier content merge never established a receipt, matching artifacts in the earlier PR are not discovered automatically. Add bounded history lookup only if worthwhile. | An isolated failed-content-publication → CI-repair scenario reuses earlier trusted artifacts with the same exact input/toolchain/provenance checks. Normal #459-style reuse already works through the active receipt. |

## Earlier seven steps: current disposition

| Earlier item | Status after #459 |
|---|---|
| Merge #440 | Complete; subsequent implementation and repairs #457–#459 are also merged. |
| Verify automatic publication | Complete for current deployment: both #459 production workflows and live checks passed. |
| Operational acceptance | Partial. Earlier lifecycle exercises and the older-dashboard navigation check exist; finish the post-migration matrix in R2. |
| Slide-PDF byte reproducibility | Still open, explicitly confirmed by the #457 smoke output; R3. |
| Transitional CI cleanup | Partial. Single validation/edge-policy owners and new publication paths are active; disabled Pages retry remains. Finish R6 after acceptance. |
| Retention/withdrawal | Still open; R7. No production objects have been deleted as part of this migration. |
| Toolchain consistency | Partial. Explicit family contracts, pinned renderers and stronger cache fingerprints are delivered; finish R4. |

The next recommended implementation is **R1**, followed by **R2**. No re-enable action, migration bootstrap, blanket PDF rebuild, or rerun of the failed #457/#458 deployments is needed for the current live site.
