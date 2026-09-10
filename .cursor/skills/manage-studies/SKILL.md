---
name: manage-studies
description: >-
  Manage study registration, content updates, Draft/Released transitions,
  rename and retirement, and route new or updated decks and technical notes.
  Use for study lifecycle work under Studies/ or Applications/ and for finalizing
  tracked artifacts with the same producers and checks as CI preparation.
---

# Manage studies

Use the focused skill for authoring, then complete the shared finish below.
[AGENTS.md](../../../AGENTS.md) governs timestamps, prose, references and PRs;
[CI.md](../../../.github/CI.md) describes verification and publication.

| Task | Skill / shared entry point |
|------|----------------------------|
| Register a study or first draft | [add-study](../add-study/SKILL.md), `_add_study.py` |
| Edit canonical study content | [regenerate-study-pdf](../regenerate-study-pdf/SKILL.md), `_regenerate_pdf.py <Slug>` |
| Draft ↔ Released | [set-study-status](../set-study-status/SKILL.md), `_set_study_status.py` |
| Remove selected notes/decks | [remove-study-companions](../remove-study-companions/SKILL.md), `_remove_study_companions.py` |
| Retire a study / planned placeholder | [remove-study](../remove-study/SKILL.md), `_remove_study.py` |
| Rename a study and its containing paths | [rename-study](../rename-study/SKILL.md), `_rename_study.py --skip-issue` |
| Rename/move an individual companion | [relocate-study-companion](../relocate-study-companion/SKILL.md), `_relocate_study_companion.py` |
| Restore a retired study or companion | [restore-study](../restore-study/SKILL.md), `_restore_study.py` |
| Add a presentation deck | [add-study-presentation](../add-study-presentation/SKILL.md) |
| Edit slides, notes, or slide order | [update-study-presentation](../update-study-presentation/SKILL.md), `_build_presentations.py` |
| Add a technical/research note and figures | [add-technical-note](../add-technical-note/SKILL.md) |
| Update a Presenter's Companion | [update-presenters-companion](../update-presenters-companion/SKILL.md) |
| Edit landing page/catalog copy | [refine-studies-index](../refine-studies-index/SKILL.md) |
| Audit citations / mirrors | [check-references](../check-references/SKILL.md), [download-references](../download-references/SKILL.md) |

## Sources and states

Canonical study sources are `Studies/<Slug>/<Slug>.md` (topical/formal) or
`Applications/<Slug>/<Slug>.md` (applied). Tracked HTML readers are generated
from those sources. Generated study/application PDFs are ignored by Git and
served through the coherent site's R2 release. Missing local PDFs are expected.

| State | Public catalog / artifacts |
|-------|----------------------------|
| Ongoing / Planned | No public read/download links or PDF; approved proposals may have internal MD/HTML stubs |
| Draft | Reader and PDF with Draft watermark |
| Released | Reader and PDF without watermark |

PPTX is the visible-slide source. `presentation-pipeline.json` declares every
deck's slides/notes PDF pair. `companion-pipeline.json` declares each Presenter's
Companion MD → DOCX/notes JSON → PPTX notes chain. Ordinary technical/research
notes use the Markdown pipeline and automatic inventory, without a presenter
mapping. Neither companions nor figures acquire catalog rows of their own.

## Prepare the affected outputs

Work from the repository root on a feature branch. Install repository Python
requirements and the pinned Node/Chrome dependencies when rendering Markdown;
deck rendering also needs the manifest's exact production renderer and fonts.
Use the lifecycle scripts' `--dry-run` when useful; inspect `--help` for each
command instead of assuming flags are interchangeable.

Refresh the canonical study's `Edited on` using real IST time when its Markdown
changes, including Status, citations or links. The add/status scripts set it;
manual edits follow AGENTS §1. Companion-only changes leave the parent's date
alone. Choose an explicit requested Draft/Released state; do not toggle to
discover the current state.

| Changed input | Required rendering |
|---------------|--------------------|
| Canonical MD, status or an embedded figure/resource | Regenerate each consuming study with `_regenerate_pdf.py <Slug>` |
| Technical/research-note MD or its embedded resources | Regenerate that note by Markdown path |
| PPTX, including notes-only or order-only edits | `_build_presentations.py --deck <ID> --in-place` builds and verifies both PDFs atomically |
| Presenter's Companion MD | `_build_presenters_companion.py <md> --pdf --pptx <deck>`; rebuild the deck pair if PPTX notes changed |
| Shared glossary | `_sync_glossary_html.py --write`, then `_build_reader_offline.py`; no PDF render |
| Catalog/landing-page copy, unused image, skill or web-only change | Finalize affected tracked web artifacts; no PDF render unless a consumed print input also changed |

The shared `_artifact_graph.py` follows embedded resources, including an image
referenced inside an SVG. An unused file beside a study does not invalidate its
PDF. A linked document's body change does not change the referring PDF's printed
URL. Changing an external SVG used to author a slide requires updating the image
inside the PPTX; the deck renderer consumes the PPTX, not that loose source image.

## Shared finish before review

1. After the targeted renders, finalize tracked artifacts:

   ```powershell
   python Scripts/_finalize_study_artifacts.py --study <Slug>
   ```

   Pass `--study` for each canonical Markdown whose metadata/catalog needs sync,
   including a registered first draft; repeat it for multiple studies. Omit it
   for companion-only changes, retirement, or catalog/shell-only changes:

   ```powershell
   python Scripts/_finalize_study_artifacts.py
   ```

   This reuses CI preparation's catalog synchronization, index, companion
   inventory, generated-PDF keys, social cards, search and offline builders. It
   checks index/inventory freshness and declared companion DOCX/JSON/PPTX
   consistency. It does not render PDFs, invent source timestamps or publish.
   A repeat on unchanged inputs must leave no diff.

2. Run applicable reference and quote checks from AGENTS §6–§7. Review source,
   HTML, catalog, registry, manifests and generated discovery diffs. Commit them
   together, including companion DOCX/notes JSON/PPTX when applicable; never add
   generated study/application PDFs. Run `git diff --check` before committing.

3. Write the PR body using the matching template, then validate the **committed
   HEAD** against the current base with that same body:

   ```powershell
   python Scripts/_validate_study_change.py --base-ref origin/master --body-file <PR-body-file>
   python Scripts/_verify_studies_index.py
   python Scripts/_verify_companion_outputs.py
   ```

   The first command compares commits, not uncommitted edits. First drafts also
   need `GITHUB_REPOSITORY` and an authenticated `GITHUB_TOKEN` for the read-only
   approval check against the linked open `proposal-approved` issue. Never print
   credentials. Fix failures, recommit, and repeat the affected checks.

   To inspect CI's affected PDF families after committing:
   `python Scripts/_pdf_build_cache.py --keys --changed-since origin/master`.
   CI uses the same graph for targeted Markdown and presentation builds; missing
   ignored PDFs alone do not request regeneration.

4. Open a ready-for-review PR with the appropriate `new-study`, `study-update`
   or `status-change` label and bare slug/status fields from AGENTS §7. A new
   technical note or deck uses `study-update`. Companion-only timestamp items
   are N/A. Labels organize the PR; required `verify` infers scope from the
   committed changes and intent, so a missing label does not bypass validation.

My Submissions can submit presenter Markdown for an existing deck, attach its
presenter Markdown to a PPTX upload, include local SVG/raster files with a Markdown
submission, and request deletion of multiple companions. Ownership declarations
are source changes; the trusted preparer reads only data from the exact submitted
commit when authorizing generated DOCX/JSON/PPTX outputs.

Local contributors prepare outputs before review. Portal source submissions use
the separate Draft-PR preparation/acceptance workflow; its preparation calls
this same finalizer, and its required verifier checks the accepted commit
without repair writes. Study Draft status does not mean a GitHub draft PR.

After merge, `publish-site.yml` compares the merged dependency graph with the
active publication receipt, reuses matching artifacts, builds/uploads changed
ones, checks the staged revision and promotes a coherent release. Normal skill
work ends with this protected workflow; do not run the standalone R2 publisher
or patch public pointers to publish a study independently.
