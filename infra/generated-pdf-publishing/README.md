# Generated PDF publishing migration

This document is the implementation plan and restart ledger for moving generated
study, presentation, presenter-notes, and technical-note PDFs out of Git and into
Cloudflare R2. Markdown, PPTX, figures, and companion source files remain in Git.

## Decisions

- Generate PDFs during verification/publishing, not during a web request.
- Publish through the existing Cloudflare R2 S3 credentials.
- Preserve the current public PDF paths by serving R2 objects through a
  same-origin Cloudflare Worker route.
- Use repository-relative object keys, for example
  `Studies/<Slug>/<Document>.pdf`, so existing links do not need a second naming
  system.
- Keep source artifacts and HTML in Git. Remove generated PDFs only after every
  public path has passed an R2/Worker cutover check.
- Harden the presentation pipeline before it becomes a CI publisher.
- Do not rewrite Git history as part of the functional migration. Consider a
  separately approved history rewrite only after the cutover is stable.

## Inventory at start

- Seven PPTX source decks under `Studies/`, containing 167 slides in total.
- Seven slides-only presentation PDFs.
- Three read-aloud notes PDFs.
- Study and companion-note PDFs are also generated artifacts and enter the same
  publishing system in a later milestone.
- Reference PDFs under `References/` are source material, not generated output;
  they remain in Git.

## Target flow

1. A source file or shared renderer input changes.
2. CI generates the affected PDF in a temporary output directory.
3. Structural, content, layout, and reproducibility checks pass.
4. The publisher uploads the artifact to its repository-relative R2 key with a
   SHA-256 checksum and explicit content/cache metadata.
5. A Cloudflare Worker serves the object at the existing website path.
6. The deployment verifies the public object before declaring success.

PDFs are never generated inside a website request. This keeps downloads fast and
prevents untrusted traffic from invoking PowerPoint, LibreOffice, Chromium, or
document-conversion code.

## Milestones and exit criteria

### M0 — access and baseline

- [x] Confirm Cloudflare account, zone, Worker script, Worker route, R2 storage,
  and cache-purge permissions.
- [x] Confirm the existing R2 S3 token can list, upload, read/head, and delete an
  object. The permission canary was removed after verification.
- [x] Create feature branch `codex/r2-generated-pdf-pipeline`.
- [x] Record the source-deck and generated-PDF baseline.

### M1 — harden presentation generation

- [x] Make checker and converter diagnostics UTF-8-safe on Windows and CI.
- [x] Replace implicit renderer fallback in production builds with an explicit
  renderer contract and recorded renderer version.
- [x] Generate slides and notes PDFs into a temporary directory before
  publication or replacement.
- [x] Add a canonical presentation manifest covering every PPTX and its expected
  slides/notes outputs.
- [x] Add automated verification for manifest coverage, slide/page count,
  dimensions/orientation, nonblank pages, speaker-note preservation, required
  fonts, and output provenance.
- [x] Add focused unit tests for the new contract and verifier.
- [x] Add a CI presentation job with source-aware path triggers.
- [x] Run the checker across all decks and fix every fatal source-deck layout
  finding on the feature branch.
- [ ] Render all seven decks with the selected CI renderer and compare against
  the PowerPoint baseline before accepting the renderer.
- [ ] Prove two consecutive builds from identical inputs have the required
  stable hashes (byte hashes where supported; normalized/raster/text hashes
  where renderer metadata is nondeterministic).

### M2 — R2 artifact publisher

- [ ] Add a publisher that reads credentials from `.env` locally and GitHub
  Actions secrets in CI without logging them.
- [ ] Support the current `CLOUDFLARE_R2_*`, documented `R2_*`, and conventional
  `AWS_*` variable names.
- [ ] Refuse upload when verification or manifest coverage fails.
- [ ] Upload only changed checksums and attach content type, cache policy,
  checksum, source hash, and renderer provenance.
- [ ] Provide dry-run, single-artifact, changed-artifacts, and full-sync modes.
- [ ] Verify each uploaded object by HEAD/checksum and make stale-object deletion
  an explicit, separate operation.
- [ ] Add mocked unit tests; keep live R2 tests opt-in.

### M3 — same-origin R2 delivery

- [ ] Add a narrowly scoped Cloudflare Worker/R2 binding for generated PDF paths.
- [ ] Preserve `Content-Type`, download filenames, range requests, HEAD, ETag,
  and cache behavior.
- [ ] Return a controlled 404 for an unpublished artifact; do not fall back to
  request-time generation.
- [ ] Deploy a canary path, then verify representative study, slide, notes, and
  technical-note downloads through the public domain.
- [ ] Document rollback to repository-hosted PDFs until cutover is accepted.

### M4 — CI publication and repository cutover

- [ ] Configure GitHub Actions secrets for the existing S3 token and repository
  variables for account, bucket, endpoint, and zone identifiers.
- [ ] Build, verify, and publish affected artifacts on protected-branch updates;
  pull requests build and verify without publishing.
- [ ] Upload the complete current generated-PDF set to R2 and verify public paths.
- [ ] Remove generated study, presentation, notes, and technical-note PDFs from
  Git; add precise ignore rules that do not hide `References/**/*.pdf`.
- [ ] Update catalog/cache-buster and reference checks so absence from Git is
  expected while public availability remains verified.
- [ ] Run the full local and CI suites, then perform a post-cutover live audit.

### M5 — optional historical storage reduction

- [ ] Measure repository and GitHub storage after ordinary PDF removal.
- [ ] If the remaining historical cost justifies it, prepare a separately
  approved `git filter-repo` migration and collaborator coordination plan.

## Restart procedure

From the repository root:

```powershell
git switch codex/r2-generated-pdf-pipeline
git status --short
Get-Content infra/generated-pdf-publishing/README.md
python Scripts/_check_deck_layout.py --all
```

Continue from the first unchecked item in the active milestone. Before changing
anything under `Studies/` or `Applications/`, confirm the feature branch is still
checked out. Never expose `.env` values in logs.

## Progress log

### 2026-09-03 — started

- Cloudflare API permissions and the existing R2 S3 object permissions were
  verified without leaving test resources behind.
- The repository was clean at commit `9424e26` before the feature branch was
  created.
- Baseline review found that the presentation pipeline is manual-only in CI,
  renderer selection is host-dependent, notes-PDF fonts silently fall back, and
  the all-deck layout checker can fail to print Unicode diagnostics on a default
  Windows console.
- Active work: M1, beginning with UTF-8-safe diagnostics, renderer/provenance
  contracts, manifest coverage, and automated verification.

### 2026-09-03 — M1 hardening slice

- Added `Scripts/presentation-pipeline.json` with explicit mappings for all seven
  decks. The mapping prevents same-basename decks from colliding with canonical
  study PDFs and declares PowerPoint baseline and LibreOffice CI-candidate
  renderer versions.
- Added atomic, staged presentation builds and structural verification for page
  counts, page geometry, blank pages, text preservation, speaker-note coverage,
  and required font families.
- Removed host-dependent renderer fallback. PowerPoint `16.0.20228.20188` is the
  accepted local baseline; LibreOffice `26.2.3.2` is still a CI candidate pending
  deck-by-deck comparison.
- Replaced presentation conversion's broken Python-COM dependency with the
  native PowerShell COM bridge. A 12-slide smoke render completed with the
  expected page count and aspect ratio.
- Made the notes composer atomic and deterministic. Two consecutive 12-slide
  notes builds now have identical SHA-256 hashes.
- Manifest/unit tests pass. Full artifact verification intentionally still
  reports four missing notes PDFs and one deck rendered with substitute fonts;
  those are baseline gaps to close, not suppressed exceptions.
- The all-deck checker now completes with Unicode diagnostics. One fatal finding
  remains: the title/subtitle collision on slide 1 of
  `Coexistence-in-Comparison-MD-vs-Advaita-Philosophy-Science.pptx`.
- Active work: repair that inherited slide-1 geometry with artifact-tool, rerun
  all-deck layout checks, then add the Windows LibreOffice candidate CI job.

### 2026-09-03 — M1 deck repair and CI candidate gate

- Repaired the title/subtitle collision on slide 1 of the ontology comparison
  deck by moving only the inherited subtitle frame. Template fidelity, speaker
  notes, theme parts, slide count, overflow checks, and the full 18-slide visual
  review all pass.
- Rebuilt that deck's slides and read-aloud notes PDFs with the pinned
  PowerPoint `16.0.20228.20188` profile. Structural verification passed and
  visual inspection of page 1 in both PDFs confirmed the repaired spacing. The
  regenerated PDFs were deliberately not added to Git history; only the PPTX
  source and pipeline changes are retained while R2 publication is being built.
- The all-deck layout checker now exits successfully across all seven decks;
  its remaining findings are informational review notes, not fatal geometry.
- Added a Windows CI smoke workflow that downloads the manifest-pinned
  LibreOffice `26.2.3.2` MSI, verifies its SHA-256, requires the deck fonts,
  builds every deck twice, verifies both trees, compares rendered/text content,
  and uploads the first candidate build for deck-by-deck review.
- Added a reproducibility comparator that reports raw byte equality while
  gating on page geometry, extracted text, and rendered-page hashes so volatile
  PDF metadata cannot hide or invent a visual difference.
- A second local PowerPoint build confirmed stable rendered/text hashes for both
  artifacts. The slides PDF was not byte-identical because PowerPoint writes
  volatile PDF internals; the notes PDF was byte-identical.
- Active work: run the LibreOffice candidate workflow, compare its artifact
  against the PowerPoint baseline, and decide whether to promote the candidate
  renderer before enabling R2 publication.

### 2026-09-03 — first LibreOffice CI run

- PR #368 started all three expected checks. The first presentation smoke run
  verified the MSI download and installation, then failed before rendering
  because a PowerShell `-notmatch` expression did not leave a reusable
  `$Matches` array. The installer now stores the regex match object explicitly;
  no version check or digest check was relaxed.
- The retry reached the same post-install assertion and showed that
  `soffice.exe`, LibreOffice's Windows GUI launcher, emits no capturable version
  text. Version detection and headless conversion now prefer the sibling
  `soffice.com` console launcher; the exact-version assertion is unchanged.
