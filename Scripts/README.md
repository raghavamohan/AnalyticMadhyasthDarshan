# Scripts

Tools for managing studies, generating PDFs, and verifying quotes. Run all commands from the **repository root**.

## One-time setup

```powershell
pip install -r requirements.txt
cd Scripts
npm install
cd ..
```

## Contributor commands

| Task | Command |
|------|---------|
| Add / register a study | `python Scripts/_add_study.py Studies/<Slug>.md --category "..." --description "..." --tags "MVD, SB" --status draft` |
| Remove a study | `python Scripts/_remove_study.py <Slug> --yes` |
| Draft ↔ Released | `python Scripts/_set_study_status.py <Slug> --status released` |
| Regenerate PDF | `python Scripts/_regenerate_pdf.py <Slug>` |
| Verify blockquotes | `python Scripts/_quote_tool.py verify [--study <Slug>]` |
| Sync PDF text cache | `python Scripts/_quote_tool.py cache sync [--study <Slug>] [--tags MVD,SB] [--force]` |
| Search a reference PDF | `python Scripts/_quote_tool.py search <tag-or-path> "<regex>"` |
| Read one PDF page (cleaned) | `python Scripts/_quote_tool.py page <tag-or-path> <n> [--keyword kw]` |
| Locate phrase in tagged source | `python Scripts/_quote_tool.py snippet <tag> "<phrase>"` |
| Download / audit references | `python Scripts/_audit_references.py` then `python Scripts/_download_references.py` |

Windows wrappers: `.\Scripts\_add_study.ps1`, `.\Scripts\_remove_study.ps1`, `.\Scripts\_set_study_status.ps1`, `.\Scripts\_download_references.ps1`.

## Internal modules (do not invoke directly)

| Module | Role |
|--------|------|
| `_common.py` | Paths, PDF text extraction, phrase matching, reference registry |
| `_study_catalog.py` | Catalog CRUD, IST timestamps, `regenerate_pdf` |
| `_quote_verify.py` | Blockquote extraction and verification logic |
| `_convert_to_pdf.py` | MD → HTML (called by `regenerate_pdf`) |
| `_html_to_pdf.js` | HTML → PDF via Puppeteer (called by `regenerate_pdf`) |
| `_download_references.py` | Download manifest entries into `References/` (called by `.ps1`) |
| `_reference_downloads.py` | Manifest of mirrorable reference files |
| `_audit_references.py` | Audit Studies/ bibliography links vs local files |
| `_ci_study_pr.py` | GitHub Actions study PR pipeline |

PDF reference text is cached under `Scripts/_pdf_cache/` (gitignored, format `v2`). The cache rebuilds automatically when a PDF is newer than its cache file; empty extractions (e.g. scanned PDFs) are not cached. Run `cache sync` after downloading references or adding new PDFs under `References/`.

## CI

Labeled study PRs run [`_ci_study_pr.py`](_ci_study_pr.py) via [`.github/workflows/study-pr.yml`](../.github/workflows/study-pr.yml).
