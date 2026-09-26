# CI implementation and acceptance evidence

CI **R1–R8 is complete**, verified on 26–27 September 2026.
[#517](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/517) delivered the core implementation;
the authenticated public exercise exposed seven additional lifecycle fixes, all merged with required checks.
The [core receipt](ci-acceptance/2026-09-26.json) and
[public lifecycle receipt](ci-acceptance/public-2026-09-27.json) record separate deployed scopes.
See [CI.md](CI.md) for the operating contract and [STUDY-LIFECYCLE.md](STUDY-LIFECYCLE.md) for repeatable acceptance.
Older September deployment records below remain historical evidence attributed to their original PRs.

## R1–R8 implementation in #517

The four discovery Workers now pass an automated audit on disposable same-zone
routes before production deployment is permitted. The receipt binds the exact
executable, metadata, account and audit time; failed audit or cleanup produces no
passing receipt. A live pre-merge execution passed all 16 checks and removed all
four candidate Workers and their routes.

Slides and notes now require identical PDF bytes across repeat builds. The
normalizer preserves visible pages, text, tagged structure and navigation while
canonicalizing source-derived metadata and PDF object traversal. The hosted
[eight-deck repeat render](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/36256046447)
passed for all 16 outputs. A separate local repeat also passed; the old #457
result below is historical evidence of the defect, not the current contract.
The adjacent default-output diagnostic defect, `PPTX-DIAG-01`, is repaired.

Runtime patches, runner families and complete font inventories are now explicit
and enforced before rendering. The Ubuntu inventory contains 101 font/config
files. Windows is observed after installing the exact production LibreOffice,
because its installation adds fonts. The
[hosted font audit](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/36256046461)
confirmed both checked-in inventories. Rolling image labels are recorded as
host evidence; matching consumed runtime/font bytes establish the rendering
contract. Local diagnostic environments do not acquire publication authority.

Every site publication now retains one PDF/R2/Worker summary, including failure
and skipped job results. Selected builds are distinguished from observed staging
and deployment. The inactive Pages retry workflow has been deleted; regressions
reject any return of its publication authority. The existing coherent-site
publisher remains the owner.

The [retention/withdrawal policy](../docs/publication-retention.md) retains all
published revisions and shared assets, separates hard withdrawal from retirement,
and requires an independently verified backup before planning aged unreachable
objects. The planner has no deletion operation. A live scan against the downloaded,
verified Google Drive backup covered 3,322 objects and found **zero candidates**.
No production objects were deleted. A checked-in empty hard-withdrawal policy is
enforced before historical reads; retained-version rollback is blocked when a
hard withdrawal is registered.

Historical review recovery now searches at most 100 recently closed PRs. Only
same-repository PRs merged into master and ancestral to the intended source can
qualify, with exact consumed inputs, successful allowlisted producers, verified
output hashes, safe archive paths and complete deck pairs. Normal active-receipt
reuse remains the first choice.

The 59 enforced Python suites, workflow lint, required PR checks and six local portal browser cases pass.
Four pre-existing held suites are not counted as passing enforced suites. All 11 isolated deployed
recovery/offline checks passed on clean source `438cd9d2`, with test resources cleaned up.
Their [receipt](ci-acceptance/2026-09-26.json) binds exact inputs, versions and revisions.

[#517 production publication](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/36258110582)
passed at merge source `1725280e8cc055a62a32d3e4ca4b6b879490ae8c`, as did both Worker deployment workflows.
Its bounded origin-propagation retry repaired the #516 audit failure while retaining exact-byte requirements.

## Public lifecycle acceptance 26-27 September

Approved disposable [proposal #518](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/518)
used the shipped authenticated portal for proposal, first draft, canonical revision and release.
Each reviewed source merged through required checks and the ordinary protected publisher.

| Phase | PR | Protected publication | Catalog/API/reader/PDF result | Revision |
|---|---|---|---|---|
| Planned | [#519](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/519) | [Passed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/36259772359) | Ongoing; canonical HTML/PDF 404 | `d33bd040ff34` |
| Draft | [#522](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/522) | [Passed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/36264084604) | Draft; every page watermarked | `991100793b99` |
| Revision | [#528](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/528) | [Passed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/36264856716) | Draft; distinct source and PDF hashes | `f402afcc937b` |
| Released | [#529](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/529) | [Passed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/36265509902) | Released; no Draft watermark | `4097f8276cf1` |
| Retired | [#530](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/530) | [Passed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/36266366971) | Absent; canonical HTML/PDF 404 | `0c74ad64ff14` |

Every public phase matched the active source, build receipt, catalog/API status and timestamps.
Complete reader/PDF bytes matched their release-manifest SHA-256 and length. A full-object R2 HTTP 206
was accepted only when its Content-Range covered every expected byte. Draft watermarks were checked
on every page; Released PDFs contained none.

The dashboard retained its Planned navigation revision `d33bd040ff34` across both draft publications.
Clicking its refreshed Live link opened revision `f402afcc937b` and the visible `PUBLIC-LIFECYCLE-REVISION-2`
paragraph. The Released dashboard reported Released/Live as Released. Retirement used the standard
maintainer remove-study CLI because IAB did not expose the typed deletion prompt; no live portal-delete
success is claimed. After public removal, issue #518 was closed and the dashboard reported Retired/Removed
from public site with no Live link. All six retained Draft/revision/Released reader/PDF reads still matched
their original checksums. No production R2 objects were deleted. The [retired dashboard screenshot](ci-acceptance/public-retired-2026-09-27.png)
shows the completed fixture; its SHA-256 is recorded in the public receipt.

The public exercise found and repaired these failures:

- [#520](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/520): Register and retire neutral visual assignments with catalog lifecycle.
- [#521](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/521): Supply bot identity when resuming divergent Planned bootstrap branches.
- [#523](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/523): Keep trusted ownership inspection free of PDF runtime imports.
- [#524](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/524): Wait for API visibility of the pushed prepared head.
- [#525](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/525): Enforce the renderer contract only when restored preparation PDFs need rendering.
- [#526](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/526): Grant trusted readiness consumer the required repository write permission.
- [#527](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/527): Complete readiness from the trusted writer after exact successful verification.

Each repair includes regression coverage and passed its required exact-head verifier. The
[public receipt](ci-acceptance/public-2026-09-27.json) includes PR heads/merges, successful CI/publication runs,
all phase bytes/hashes, dashboard navigation and retained-history results. Controlled rollback, failed/superseded
promotion and disconnection remain explicitly scoped to the real isolated deployed drill, not production rollback.

## Lifecycle completion after #462

- Shared preparation/finalization and selective companion deletion are merged.
- Implemented Applied proposal/registration/first-draft routing, including revisions.
- Added presenter submissions, SVG/raster bundles, bulk companion removal and
  corresponding version checks, receipts, ownership declarations and API schema.
- Added companion rename/move and restoration from merged history, with scripts,
  skills and parent/ownership protection. Empty global deck inventories are valid.
- Corrected same-status no-op instructions and synchronized skill mirrors.
- Added required, scoped browser acceptance. Six local browser scenarios pass,
  including recovery that previously overwrote a saved companion draft. Local
  lifecycle tests also cover Applied registration, final-deck removal, relocation,
  restoration and exact-source binary permissions.

At the time of #463, the deployed lifecycle, offline and recovery matrix and R1/R3–R8
were still open. Both Worker workflows passed, but #463 site publication failed during
artifact collection before staging or promotion. Subsequent collector repairs and #517
resolved those failures; the current completion evidence is recorded above.

The F1–F15 implementation is merged and running in production. Both the site and Agent-facing Workers deployments passed at the recorded migration revisions. The initial migration/build-receipt bootstrap is complete. #517 completes strict slide-PDF byte reproducibility and the implemented follow-ups described above. A green deployment does not establish that every lifecycle, offline, recovery, or renderer scenario has been exercised.

## Completed implementation

“Implemented” records merged code and its regression coverage. Remaining operational exercises are tracked in [PENDING.md](../PENDING.md#ci).

| Finding | Status | Delivered behavior |
|---|---|---|
| F1 Content reverts | Implemented | Immutable content manifests exclude source/runtime provenance; deployment receipts are separate. A → B → A is covered by regression tests; controlled deployed rollback/forward recovery passed on isolated resources in #517. |
| F2 Runtime audits | Implemented | The fast path requires the same content and complete runtime/binding fingerprint. Audits verify the new marker, including its build receipt. |
| F3 Live dashboard navigation | Implemented | Live links carry the verified publication revision and an explicit navigation exemption. An older-dashboard → newer-Live browser check passed. |
| F4 Active baseline | Implemented; production reuse verified | Plans compare consumed inputs with the active deployment's protected build receipt and R2 checksums, never the last push. #458 established the receipt; #459 reused it. |
| F5 Public API state | Implemented; live checks passed | MCP/Studies API reads the active publication and its catalog/Markdown, with no Git HEAD fallback. #458/#459 corrected Cloudflare cache/routing configuration and the live audit. |
| F6 Generator ownership and determinism | Implemented; strict slide/notes bytes verified in #517 | One Markdown PDF owner; declared companion source chain and freshness gate; deterministic DOCX/no-op notes; per-card seals; approved reference source and byte hashes. Strict slide-PDF byte determinism is now enforced. |
| F7 Preparation readiness | Implemented | Source-only portal drafts report Preparing; complete verification follows accepted preparation; readiness follows successful verification. The public proposal/draft/revision/release/retirement exercise passed on 26–27 September 2026. |
| F8 Duplicate verification | Implemented | Exact head/base/intent identities, idempotent dispatch, and live identity rechecks before acceptance and success. |
| F9 Dependency selectors | Implemented | One consumed-input graph for Markdown, recursive embedded resources, used link metadata, deck pairs and references. Static files retain a complete release inventory. |
| F10 Output cache inputs | Implemented | Ignored PDFs never enter input fingerprints; link decisions use source/catalog/HTML availability. |
| F11 Jobs/transfers | Implemented; production skips verified | Plan before renderers, skip empty families, transfer selected files, reuse unchanged R2 records without PDF body downloads. |
| F12 Packaging churn | Implemented; unchanged-content path verified | Stable asset hashes and dependency URLs; canonical HTML redirects to a release URL; shared navigation carries revision without embedding it in every file. |
| F13 Repeated builds | Implemented within current proof scope | Verified same-repo preparation/review PDFs can feed later phases; parallel checks/renderers; one master validation owner. Bounded trusted historical lookup is delivered in #517. |
| F14 Generator fan-out | Implemented | Disposable HTML for PDF verification; batch search/offline finalization for preparation. |
| F15 Worker selection | Implemented; production skips verified | Compare each executable/configuration fingerprint with its active Cloudflare version; one serialized shared edge-policy owner. Only MCP changed among the four Agent-facing Workers in #459. |

The companion gate also found and repaired an existing stale ontology speaker note on slide 10, using the existing companion source. Both deck PDFs were verified with LibreOffice 26.2.3.2. Canonical study text and Edited-on timestamps were unchanged. Social cards received input/output seals so unchanged runs skip rendering.

## Deployment fixes and production evidence

| PR | Work completed | Outcome |
|---|---|---|
| [#457](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/457) | Main F1–F15 implementation, dependency planner, build proofs, publication protocol, preparation gates, generator ownership and Worker selection. | PR checks passed. Production exposed a reusable-workflow permission error and an unsupported MCP cache option. Submission/discussion Workers and shared edge policy deployed successfully. |
| [#458](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/458) | Granted the publication caller `actions: read`; made the MCP API uploader use Wrangler's runtime configuration; enabled `cache_option_enabled`; added configuration regressions. | [Site publication passed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/34424746547) and established the durable build receipt. MCP still read the old origin and failed with publication-marker 404/API 502. |
| [#459](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/459) | Enabled `global_fetch_strictly_public` so same-zone reads reach the site Worker; retained a required routing guard; stopped requiring API quota headers on static marker/catalog/reading-path reads while retaining API/MCP and challenge checks. | [Agent-facing Workers passed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/34426704381); [site publication passed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/34426704500). |
| [#463](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/463) | Completed lifecycle, Applied-study and companion operations, skills and scoped acceptance coverage. | PR checks and both Worker workflows passed. [Site publication failed](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/34438946641) while collecting the single reused PDF bundle; staging and promotion did not run. |

The #463 publication reused all 47 selected PDFs (31 Markdown and 16 deck outputs),
so both renderer jobs skipped and only `generated-reviewed-pdfs` was downloaded.
`download-artifact@v7` extracts a single match directly into its destination, even
with `merge-multiple: false`. The collector assumed every download had an artifact
directory around it and treated `Studies/` as that directory, dropping the public
path prefix. The repair recognizes flat and per-artifact layouts while retaining
inventory, conflict and provenance checks. Regression coverage exercises single
and multiple bundles, all three collection roots, deck proofs and rejected paths.
The actual failed-run bundle now collects successfully locally: all 47 PDF hashes
match the protected plan and pass the publisher's artifact verification. This is
local repair evidence; successful production promotion still needs confirmation
after the repair merges.

Confirmed for #459:

- Site run: **2m54s**, from creation at 01:44:59 UTC to final update at 01:47:53 UTC. This is one configuration-only run, not a benchmark for content changes.
- Planner: **0 builds, 81 reused artifacts**: 31 Markdown PDFs, 16 presentation PDFs and 34 approved reference artifacts. Both renderer jobs skipped; no PDF ZIP transfer or PDF upload was selected.
- Public content revision remained `206e6515fe0abe4fe5febeadda46bed25b7806afa9e27eed32aa79353ff91d47`. The source pointer advanced to the #459 merge. Canary and production reported **0 static asset upload batches**. Site Worker versions and provenance still advance on this path; “no content upload” does not mean no deployment work.
- The active build receipt is `site/builds/d10b853ba1564bd2e22768cdc3a988defab2ec2ab1964999fdd17ef4910cac4e.json`.
- MCP deployed its changed configuration. Agent Skills, Auth.md and API catalog skipped unchanged executable deployments.
- Live checks passed for all **27 catalog entries**, study outline, glossary, reading path, citations, citation errors, MCP initialization/tool discovery, Agent Skills, Auth.md and API catalog. A direct read after completion confirmed the #459 source marker and HTTP 200 from the Studies API.

## Validation completed and its limits

All 45 enforced Python suites and eight MCP JavaScript tests passed for the repair; all applicable PR checks passed. The main implementation also passed actionlint, freshness/agent-mirror checks, Worker/navigation tests, and real byte-identical Draft and Released Markdown-PDF rerenders with pinned Chrome. Four pre-existing held Python suites remain documented in `_run_test_suites.py`; they are not counted as passing enforced suites.

A temporary Worker on a unique same-zone Cloudflare route reproduced #458's exact failure using its old configuration. The repaired configuration then passed the complete live API audit plus nine additional MCP tool/resource reads. The temporary route and Worker were removed. This was a manual pre-merge canary; #517 now automates that gate before production deployment.

The [#457 presentation smoke run](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/34422569722) rendered all eight deck pairs twice. All rendered/text comparisons passed. **All eight slides PDFs reported `byte-identical=no`; all eight notes PDFs reported `byte-identical=yes`.** This established the R3 defect; #517 fixes it and now fails the smoke on any differing PDF bytes.

## CI backlog

The sole CI backlog is [PENDING.md](../PENDING.md#ci), which now has no pending CI items.
Keep completion evidence and how-to in this file; do not add a second remaining-work table here.

## Historical disposition after #459

This table describes the historical #459 state. The completed R1–R8 evidence above supersedes it.

| Earlier item | Historical status after #459 |
|---|---|
| Merge #440 | Complete; subsequent implementation and repairs #457–#459 are also merged. |
| Verify automatic publication | Complete for current deployment: both #459 production workflows and live checks passed. |
| Operational acceptance | Partial. Earlier lifecycle exercises and the older-dashboard navigation check exist; finish the post-migration matrix in R2. |
| Slide-PDF byte reproducibility | Still open, explicitly confirmed by the #457 smoke output; R3. |
| Transitional CI cleanup | Partial. Single validation/edge-policy owners and new publication paths are active; disabled Pages retry remains. Finish R6 after acceptance. |
| Retention/withdrawal | Still open; R7. No production objects have been deleted as part of this migration. |
| Toolchain consistency | Partial. Explicit family contracts, pinned renderers and stronger cache fingerprints are delivered; finish R4. |

The earlier recommendation to start with R1 is superseded by #517's implementation.
Current remaining work lives only in [PENDING.md](../PENDING.md#ci). No re-enable
action, migration bootstrap, blanket PDF rebuild, or rerun of the failed #457/#458
deployments is needed.
