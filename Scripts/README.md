# Scripts

Maintainer entry points and pipeline components for studies, references, generated
documents, CI, and site infrastructure. Run commands from the **repository root**.

## One-time setup

```powershell
pip install -r requirements.txt
cd Scripts
npm ci
npx puppeteer browsers install chrome
cd ..
```

`npm ci` installs the versions pinned by `package-lock.json`. The PDF renderer also
checks the Chrome build recorded in `package.json`; do not use an unpinned system
Chrome for committed PDFs.

## Maintainer / local development

To submit a study without cloning this repository, use **[My Submissions](../Studies/submit.html)** on the Web Submission Portal.

Any `Studies/` or `Applications/` change made from a local clone (by a human or an agent) still goes through a
feature branch and a `new-study` / `study-update` / `status-change` labeled pull request — see
[AGENTS.md](../AGENTS.md) §7 and [CONTRIBUTING.md](../CONTRIBUTING.md). The commands below are
what to run **on that branch** before opening the PR.

| Task | Command |
|------|---------|
| Add / register a study | `python Scripts/_add_study.py Studies/<Slug>/<Slug>.md --category "..." --description "..." --tags "MVD, SB" --status draft` |
| Remove a study | `python Scripts/_remove_study.py <Slug> --yes` |
| Rename a study slug/title | `python Scripts/_rename_study.py --from <Old-Slug> --to <New-Slug> --title "New title"` |
| Draft ↔ Released | `python Scripts/_set_study_status.py <Slug> --status released` |
| Regenerate a study PDF/HTML | `python Scripts/_regenerate_pdf.py <Slug>` |
| Regenerate a companion note PDF/HTML | `python Scripts/_regenerate_pdf.py Studies/<Slug>/Research-Note.md` (unwatermarked; same verifiers) |
| Pin PDF dates and node IDs (reproducible bytes) | `python Scripts/_pdf_metadata.py Studies/<Slug>/<Slug>.md` (called automatically by `_regenerate_pdf.py`) |
| Test the study-PR CI router | `python Scripts/_test_ci_study_pr.py` |
| Test add/remove/rename lifecycle edge cases | `python Scripts/_test_study_lifecycle.py` |
| Test the PDF reproducibility patches | `python Scripts/_test_pdf_metadata.py` |
| Build + verify one companion deck's slides/notes PDFs | `python Scripts/_build_presentations.py --deck <Presentation-ID> --in-place` (ID/output paths and exact renderer are pinned in `presentation-pipeline.json`) |
| Build all companion presentations into a separate tree | `python Scripts/_build_presentations.py --all --profile libreoffice-production --output-root tmp/presentation-build` |
| Compare two presentation builds | `python Scripts/_verify_presentation_reproducible.py --all --left-root <first> --right-root <second>` |
| Review a candidate renderer against a baseline | `python Scripts/_compare_presentation_renderers.py --reference-root <baseline> --candidate-root <candidate> --output-dir <review>` |
| Diagnose PPTX → slides PDF only | `python Scripts/_pptx_to_pdf.py path/to/deck.pptx --profile powerpoint-baseline` |
| Diagnose deck → read-aloud notes PDF only | `python Scripts/_build_deck_notes_pdf.py path/to/deck.pptx` (run after the slides PDF) |
| PDF → study markdown (maintainer) | `python Scripts/_pdf_to_study_md.py path/to/paper.pdf --slug <Slug> --title "..."` |
| PDF import with catalog register | `python Scripts/_add_study.py path/to/paper.pdf --convert --slug <Slug> --title "..." --category "..." --description "..." --tags "MVD, SB" --status draft` |
| Test PDF conversion | `python Scripts/_test_pdf_to_md.py` |
| Verify Mermaid in PDF | `python Scripts/_verify_pdf_diagrams.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf` |
| Verify fenced code in PDF | `python Scripts/_verify_pdf_fenced_code.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf` |
| Verify KaTeX fonts in PDF | `python Scripts/_verify_pdf_math.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf` |
| Verify PDF sidebar bookmarks | `python Scripts/_verify_pdf_outline.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf` |
| Verify blockquotes | `python Scripts/_quote_tool.py verify [--study <Slug>]` |
| Sync PDF text cache | `python Scripts/_quote_tool.py cache sync [--study <Slug>] [--tags MVD,SB] [--force]` |
| Search a reference PDF | `python Scripts/_quote_tool.py search <tag-or-path> "<regex>"` |
| Read one PDF page (cleaned) | `python Scripts/_quote_tool.py page <tag-or-path> <n> [--keyword kw]` |
| Locate phrase in tagged source | `python Scripts/_quote_tool.py snippet <tag> "<phrase>"` |
| Download / audit references | `python Scripts/_check_references.py` (full); `python Scripts/_audit_references.py` (bibliography only); `python Scripts/_download_references.py` (mirrors) |
| Render / verify MSM translation source images | `python Scripts/_msm_render_page_images.py`; add `--check` to validate the source hash and all 268 PNGs |
| Review Rakesh Gupta translation alignment | `python Scripts/_review_rakesh_translations.py` |
| Verify studies index | `python Scripts/_verify_studies_index.py` |
| Rebuild index.html shell | `python Scripts/_build_studies_index.py` |
| Cloudflare performance setup | `python Scripts/_cloudflare_performance.py` (`--apply-redirect`, `--apply-api`, `--apply-edge-security`, `--check-edge-security`; token in `.env`) |
| Auth.md / OAuth discovery | `python Scripts/_test_auth_md.py` (`--live`); `python Scripts/_publish_auth_md_snippet.py` (Worker `amd-auth-md`) |
| RFC 9727 api-catalog | `python Scripts/_test_api_catalog.py` (`--live`); `python Scripts/_publish_api_catalog_snippet.py` |
| A2A Agent Card | `python Scripts/_test_agent_card.py` (`--live`); `python Scripts/_publish_agent_card_snippet.py` |
| Agent Skills Discovery | `python Scripts/_build_agent_skills_index.py` (`--check`); `python Scripts/_test_agent_skills.py` (`--live`); `python Scripts/_publish_agent_skills_snippet.py` |
| MCP runtime / Server Card | `python Scripts/_test_mcp_server_card.py` (`--live`); `python Scripts/_test_studies_api.py` (`--live`); `python Scripts/_publish_mcp_server_card.py` |
| Web Bot Auth | `python Scripts/_test_web_bot_auth.py` (`--live`); `python Scripts/_publish_web_bot_auth.py` |
| WebMCP | `python Scripts/_test_webmcp.py` (`--live`) |
| DNS-AID | `python Scripts/_test_dns_aid.py` (`--live`); `python Scripts/_publish_dns_aid.py` (`--check`) |
| Sync agent rules and skills | `python Scripts/_sync_agent_rules.py` then `python Scripts/_sync_agent_rules.py --check` |

Before a non-dry-run rename that resolves a proposal issue, set
`GITHUB_TOKEN` and `GITHUB_REPOSITORY`; otherwise pass `--skip-issue` and let
labeled CI complete proposal-issue synchronization on the PR branch.

Windows wrappers: `.\Scripts\_add_study.ps1`, `.\Scripts\_remove_study.ps1`,
`.\Scripts\_rename_study.ps1`, `.\Scripts\_set_study_status.ps1`,
`.\Scripts\_download_references.ps1`, and `.\Scripts\_check_references.ps1`.

## Pipeline components and specialized CLIs

Use the entry points above for normal workflows. The components below are invoked
by those entry points or run directly only for diagnostics and specialized work.

| Module | Role |
|--------|------|
| `_common.py` | Paths, PDF text extraction, phrase matching, reference registry |
| `_study_catalog.py` | Catalog CRUD, IST timestamps, `regenerate_pdf`, catalog sync checks |
| `_study_links.py` | Cross-study link discovery plus inbound/outbound `§` validation for every changed canonical study; retired-slug checks for rename/removal CI |
| `_build_studies_index.py` | `INDEX_TEMPLATE` for `Studies/index.html`; writes `Studies/catalog-*.json`; rebuild shell |
| `_verify_studies_index.py` | Verify catalog JSON ↔ README and index shell ↔ template |
| `_quote_verify.py` | Blockquote extraction and verification logic |
| `_verify_study_svgs.py` | Validate referenced study SVG files before conversion (called by `_regenerate_pdf.py`) |
| `_convert_to_pdf.py` | MD → HTML; Mermaid fences → `<div class="mermaid">`; `pre-wrap` on fenced code (called by `_regenerate_pdf.py`) |
| `_html_to_pdf.js` | Render Mermaid, then HTML → PDF via Puppeteer (called by `_regenerate_pdf.py`) |
| `_verify_pdf_diagrams.py` | Fail if Mermaid source leaked into PDF text (called by `_regenerate_pdf.py`) |
| `_verify_pdf_fenced_code.py` | Fail if fenced code/spec content clipped in PDF (called by `_regenerate_pdf.py`) |
| `_verify_pdf_math.py` | Fail if rendered KaTeX output has no embedded KaTeX font (called by `_regenerate_pdf.py`) |
| `_verify_pdf_outline.py` | Fail if PDF document outline missing when study has multiple sections (called by `_regenerate_pdf.py`) |
| `_pdf_metadata.py` | Pin PDF dates and tagged-structure node IDs for reproducible bytes (called by `_regenerate_pdf.py`) |
| `_download_references.py` | Download manifest entries into `References/` (called by `.ps1`) |
| `_reference_downloads.py` | Manifest of mirrorable reference files |
| `_msm_render_page_images.py` | Render the pinned MSM Hindi source to page-aligned PNGs and verify the complete image set |
| `_audit_references.py` | Bibliography-only audit of Studies/ `## References` links |
| `_check_references.py` | Full reference check suite (bibliography, markdown links, mirror files, PDF links) |
| `_pdf_to_md.py` | Layout-aware PDF → markdown body extraction (PyMuPDF + pdfplumber) |
| `_pdf_to_study_md.py` | Maintainer CLI: PDF → `Studies/<Slug>/<Slug>.md` with metadata |
| `_test_pdf_to_md.py` | Round-trip and failure tests for PDF import |
| `_ci_study_pr.py` | GitHub Actions study PR pipeline |
| `_sync_agent_rules.py` | Sync AGENTS.md → `.cursor/rules/*.mdc`; `.agents/skills/` → `.cursor/skills/` and `.well-known/agent-skills/` |
| `_build_agent_skills_index.py` | Publish Agent Skills Discovery index and SKILL.md copies under `.well-known/agent-skills/` |
| `_transcribe_fetch.py` | Fetch audio for a transcription manifest (yt-dlp, audio-only, resumable) |
| `_transcribe_batch.py` | Transcribe a manifest **without VAD** — GPU (whisper.cpp+Vulkan) or CPU fallback |

PDF reference text is cached under `Scripts/_pdf_cache/` (gitignored, format `v2`). The cache rebuilds automatically when a PDF is newer than its cache file; empty extractions (e.g. scanned PDFs) are not cached. Run `cache sync` after downloading references or adding new PDFs under `References/`.

## CI

Full pipeline reference: **[.github/CI.md](../.github/CI.md)**.

Which scripts CI actually executes:

| Workflow | Runs |
|----------|------|
| [`study-pr.yml`](../.github/workflows/study-pr.yml) — labeled study PRs only | [`_test_ci_study_pr.py`](_test_ci_study_pr.py), then [`_ci_study_pr.py`](_ci_study_pr.py) (which reaches `_add_study.py`, `_rename_study.py`, `_set_study_status.py`, `_study_catalog.regenerate_pdf` and its verifiers, `_study_links.py`, `_check_references.py`, `_verify_studies_index.py`) |
| [`studies-index-check.yml`](../.github/workflows/studies-index-check.yml) — **every** PR, and push to `master` | [`_verify_studies_index.py`](_verify_studies_index.py), every non-held suite discovered by [`_run_test_suites.py`](_run_test_suites.py), and [`_sync_agent_rules.py --check`](_sync_agent_rules.py) |
| [`pdf-pipeline-smoke.yml`](../.github/workflows/pdf-pipeline-smoke.yml) — PDF pipeline paths, or on demand | [`_verify_pdf_reproducible.py`](_verify_pdf_reproducible.py) |
| [`proposal-approved.yml`](../.github/workflows/proposal-approved.yml) — `proposal-approved` label | [`_bootstrap_proposal_study.py`](_bootstrap_proposal_study.py) |

Test suites are discovered by **denylist**: [`_run_test_suites.py`](_run_test_suites.py)
runs every `_test_*.py` except those named in its `HELD` map, so a new suite is
enforced as soon as it lands. Four are held — one pins the reader's CSS, three are
chained to one study's frozen research data — and the reason for each is printed on
every run. See [.github/CI.md](../.github/CI.md) §4.

```powershell
python Scripts/_run_test_suites.py --list   # what is enforced, what is held and why
python Scripts/_run_test_suites.py --all    # including the held suites
```

The site and infra suites each carry a `check_live()` behind an explicit `--live`
flag that hits production. CI runs the offline form only.
