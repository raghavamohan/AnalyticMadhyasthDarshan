# Scripts

Tools for managing studies, generating PDFs, and verifying quotes. Run all commands from the **repository root**.

## One-time setup

```powershell
pip install -r requirements.txt
cd Scripts
npm install
cd ..
```

## Maintainer / local development

To submit a study without cloning this repository, use **[My Submissions](../Studies/submit.html)** on the Web Submission Portal.

Any `Studies/` change made from a local clone (by a human or an agent) still goes through a
feature branch and a `new-study` / `study-update` / `status-change` labeled pull request — see
[AGENTS.md](../AGENTS.md) §7 and [CONTRIBUTING.md](../CONTRIBUTING.md). The commands below are
what to run **on that branch** before opening the PR.

| Task | Command |
|------|---------|
| Add / register a study | `python Scripts/_add_study.py Studies/<Slug>/<Slug>.md --category "..." --description "..." --tags "MVD, SB" --status draft` |
| Remove a study | `python Scripts/_remove_study.py <Slug> --yes` |
| Draft ↔ Released | `python Scripts/_set_study_status.py <Slug> --status released` |
| Regenerate PDF | `python Scripts/_regenerate_pdf.py <Slug>` |
| Pin PDF dates and node IDs (reproducible bytes) | `python Scripts/_pdf_metadata.py Studies/<Slug>/<Slug>.md` (called automatically by `regenerate_pdf`) |
| Test the study-PR CI router | `python Scripts/_test_ci_study_pr.py` |
| Test the PDF reproducibility patches | `python Scripts/_test_pdf_metadata.py` |
| Companion PPTX → slides PDF | `python Scripts/_pptx_to_pdf.py path/to/deck.pptx` (PowerPoint COM, else LibreOffice) |
| Deck → read-aloud notes PDF | `python Scripts/_build_deck_notes_pdf.py path/to/deck.pptx` → `<Deck>-notes.pdf` (slide + speaker script per page; run after the slides PDF) |
| PDF → study markdown (maintainer) | `python Scripts/_pdf_to_study_md.py path/to/paper.pdf --slug <Slug> --title "..."` |
| PDF import with catalog register | `python Scripts/_add_study.py path/to/paper.pdf --convert --slug <Slug> --title "..." --category "..." --description "..." --tags "MVD, SB" --status draft` |
| Test PDF conversion | `python Scripts/_test_pdf_to_md.py` |
| Verify Mermaid in PDF | `python Scripts/_verify_pdf_diagrams.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf` |
| Verify fenced code in PDF | `python Scripts/_verify_pdf_fenced_code.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf` |
| Verify PDF sidebar bookmarks | `python Scripts/_verify_pdf_outline.py Studies/<Slug>/<Slug>.md Studies/<Slug>/<Slug>.pdf` |
| Verify blockquotes | `python Scripts/_quote_tool.py verify [--study <Slug>]` |
| Sync PDF text cache | `python Scripts/_quote_tool.py cache sync [--study <Slug>] [--tags MVD,SB] [--force]` |
| Search a reference PDF | `python Scripts/_quote_tool.py search <tag-or-path> "<regex>"` |
| Read one PDF page (cleaned) | `python Scripts/_quote_tool.py page <tag-or-path> <n> [--keyword kw]` |
| Locate phrase in tagged source | `python Scripts/_quote_tool.py snippet <tag> "<phrase>"` |
| Download / audit references | `python Scripts/_check_references.py` (full); `_audit_references.py` (bibliography only); `_download_references.py` (mirrors) |
| Extract & audit KD Hindi root terms | `python Scripts/_extract_kd_hindi_terms.py` |
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

Windows wrappers: `.\Scripts\_add_study.ps1`, `.\Scripts\_remove_study.ps1`, `.\Scripts\_set_study_status.ps1`, `.\Scripts\_download_references.ps1`.

## Internal modules (do not invoke directly)

| Module | Role |
|--------|------|
| `_common.py` | Paths, PDF text extraction, phrase matching, reference registry |
| `_study_catalog.py` | Catalog CRUD, IST timestamps, `regenerate_pdf`, catalog sync checks |
| `_build_studies_index.py` | `INDEX_TEMPLATE` for `Studies/index.html`; writes `Studies/catalog-*.json`; rebuild shell |
| `_verify_studies_index.py` | Verify catalog JSON ↔ README and index shell ↔ template |
| `_quote_verify.py` | Blockquote extraction and verification logic |
| `_convert_to_pdf.py` | MD → HTML; Mermaid fences → `<div class="mermaid">`; `pre-wrap` on fenced code (called by `regenerate_pdf`) |
| `_html_to_pdf.js` | Render Mermaid, then HTML → PDF via Puppeteer (called by `regenerate_pdf`) |
| `_verify_pdf_diagrams.py` | Fail if Mermaid source leaked into PDF text (called by `regenerate_pdf`) |
| `_verify_pdf_fenced_code.py` | Fail if fenced code/spec content clipped in PDF (called by `regenerate_pdf`) |
| `_verify_pdf_outline.py` | Fail if PDF document outline missing when study has multiple sections (called by `regenerate_pdf`) |
| `_download_references.py` | Download manifest entries into `References/` (called by `.ps1`) |
| `_reference_downloads.py` | Manifest of mirrorable reference files |
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

Labeled study PRs run [`_ci_study_pr.py`](_ci_study_pr.py) via [`.github/workflows/study-pr.yml`](../.github/workflows/study-pr.yml).

Pull requests that touch the studies catalog or index build also run
[`_verify_studies_index.py`](_verify_studies_index.py) via
[`.github/workflows/studies-index-check.yml`](../.github/workflows/studies-index-check.yml).
