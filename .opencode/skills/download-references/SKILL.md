---
name: download-references
description: >-
  Audit Studies/ bibliographies and download redistributable references into
  References/ using Scripts/_audit_references.py and _download_references.py.
  Use when reviewing study citations, mirroring open-access papers, refreshing
  local reference files, or updating NOT-DOWNLOADED.md and study reference links.
---

# Download references

Audit what Studies cite, download only works you may redistribute, then sync
catalogs and study links.

Works with **Cursor**, **OpenCode**, and **ZCode** (skills live in
`.agents/skills/`; OpenCode reads them via `.opencode/skills/` junction).

## When to use

- User asks to review Studies references or download sources locally
- A new study cites external URLs that might be open access or public domain
- Refresh corrupted or stale PDFs under `References/`
- After adding an entry to the download manifest

## What we store vs link externally

| Store locally | Link externally only |
|---------------|----------------------|
| Madhyasth Darshan, Advaita, open-access papers, author preprints, public-domain texts, existing SEP/HTML snapshots used for quote verification | Commercial books, paywalled journals, IEP articles (no reposting), unclear translation rights |

**Never** upload restricted publisher PDFs. Document external-only works in
[References/NOT-DOWNLOADED.md](../../References/NOT-DOWNLOADED.md).

## Workflow

### 1. Audit current citations

From repo root:

```powershell
python Scripts/_audit_references.py
python Scripts/_audit_references.py --study Nature-Of-Time
```

Reports local vs external links and flags broken `../References/` paths.

### 2. Check redistribution rights

Before mirroring an external URL:

- **OK:** public domain, CC license, arXiv/author preprint, publisher open access, Wikisource
- **Not OK:** commercial books, JSTOR/paywall without OA, IEP (link only), publisher PDF with restrictive terms

When in doubt, keep the external URL and add or keep a row in `NOT-DOWNLOADED.md`.

### 3. Add to download manifest (if newly mirrorable)

Edit [Scripts/_reference_downloads.py](../../Scripts/_reference_downloads.py):

```python
DownloadEntry(
    dest="Modern-Philosophy/Author-2024-Title.pdf",
    urls=("https://author-hosted-or-open-access-url",),
    tag="Author 2024",
    notes="CC BY / author preprint / public domain — one line why it is safe to mirror.",
),
```

Prefer author or archive URLs over publisher landing pages when bot checks block downloads.

### 4. Download

```powershell
python Scripts/_download_references.py --dry-run
python Scripts/_download_references.py --tag "Author 2024"
python Scripts/_download_references.py
```

Windows wrapper:

```powershell
.\Scripts\_download_references.ps1 -Tag "McTaggart 1908"
```

Flags: `--dry-run`, `--force`, `--skip-cache-sync`, repeatable `--tag`.

### 5. Update documentation and study links

After a successful local mirror:

1. **References/README.md** — add row under the correct subsection table (`**TAG** | [file](path) | notes`)
2. **References/MANIFEST.md** — move tag from external to present; refresh summary counts
3. **References/NOT-DOWNLOADED.md** — remove tag if it was external-only; keep publisher URL in study as `Also at …` when helpful
4. **Study `.md` References section** — primary link `../References/...`; external URL optional
5. Refresh `**Edited on:**` + catalogs if study References changed ([AGENTS.md](../../AGENTS.md) §1)
6. Regenerate affected PDFs: `python Scripts/_regenerate_pdf.py <Slug>`

### 6. Verify quotes and cache

```powershell
python Scripts/_quote_tool.py verify
python Scripts/_quote_tool.py cache sync
```

External-only tags are skipped during verify. HTML snapshots are not PDF-cached.

## Example (from June 2026 review)

| Tag | Action | Source |
|-----|--------|--------|
| McTaggart 1908 | Downloaded Wikisource HTML | Public domain |
| Hashemi 2025 | Downloaded author preprint | PhilSci-Archive |
| Kuhn 2024 | Left external | CC BY-NC-ND but ScienceDirect blocked automated fetch |
| Gettier 1963, IEP Enactivism | Left external | Copyright / IEP repost policy |

## Files

| File | Role |
|------|------|
| `Scripts/_reference_downloads.py` | Manifest of mirrorable files (edit to add entries) |
| `Scripts/_download_references.py` | Downloader (Python; cross-platform) |
| `Scripts/_download_references.ps1` | PowerShell wrapper |
| `Scripts/_audit_references.py` | Studies bibliography audit |
| `References/README.md` | Local file registry for quote tool |
| `References/MANIFEST.md` | Citation audit by study |
| `References/NOT-DOWNLOADED.md` | External-only works + URLs |

## Completion checklist

- [ ] Audit run; no broken `../References/` links
- [ ] New mirrors have clear redistribution basis documented in README notes
- [ ] `NOT-DOWNLOADED.md`, `MANIFEST.md`, and `README.md` agree on local vs external
- [ ] Study References use `../References/...` for local files (no `NOT-DOWNLOADED.md` pointers in study body)
- [ ] `quote_tool verify` and `cache sync` run after PDF additions
- [ ] Study PDFs regenerated when References sections changed

## Related

- Quote verification: `python Scripts/_quote_tool.py verify`
- Study lifecycle: [manage-studies](../manage-studies/SKILL.md)
- Agent rules: [AGENTS.md](../../AGENTS.md); contributor overview [References/README.md](../../References/README.md)
