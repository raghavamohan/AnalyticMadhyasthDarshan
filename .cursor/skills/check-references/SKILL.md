---
name: check-references
description: >-
  Run full reference integrity checks on Studies/ bibliographies, local
  ../References/ links, References/ mirror files, and study PDF links using
  Scripts/_check_references.py. Use when adding or editing study references,
  after downloading references, before committing bibliography changes, or when
  a user asks to verify reference links work.
---

# Check references

Run the repository reference check suite before finishing any edit that adds or
changes study citations or files under `References/`.

Works with **Cursor**, **OpenCode**, and **ZCode** (skills live in
`.agents/skills/`; OpenCode reads them via `.opencode/skills/` junction).

## When to use

- User asks to verify references, audit links, or fix broken downloads
- After editing `## References` or any `../References/...` link in a study
- After `download-references` or manual adds under `References/`
- Before committing bibliography or reference-file changes
- CI runs this automatically on labeled study PRs (see [AGENTS.md](../../AGENTS.md) §6)

## Quick command

From repo root:

```powershell
python Scripts/_check_references.py
```

Windows wrapper:

```powershell
.\Scripts\_check_references.ps1
```

One study only (faster while drafting):

```powershell
python Scripts/_check_references.py --study Nature-Of-Time
```

Skip PDF link checks when PDFs are not regenerated yet:

```powershell
python Scripts/_check_references.py --study The-Ontology-of-Coexistence --skip-pdf
```

## What it checks

| Check | What fails |
|-------|------------|
| **Bibliography** | `## References` entries pointing at missing or unusable `../References/` files |
| **Markdown links** | Any `../References/...` link in the study body (not only the bibliography) |
| **Mirror files** | Every `.pdf` / `.html` under `References/` is non-empty and valid (full repo run only) |
| **PDF links** | Study PDFs must not contain `file://` links; site links must target usable local files |

A file is **unusable** when it is empty, too small, or a PDF whose content starts
with `<!DOCTYPE` (publisher bot-wall HTML saved as `.pdf`).

## If checks fail

1. **Empty or corrupt local file** — re-download via [download-references](../download-references/SKILL.md), or remove the local path and link the external DOI/URL only; document in [References/NOT-DOWNLOADED.md](../../References/NOT-DOWNLOADED.md).
2. **Missing file** — add to `Scripts/_reference_downloads.py` and download, or switch the study entry to an external link.
3. **PDF link mismatch** — regenerate the study PDF after fixing markdown or mirror files: [regenerate-study-pdf](../regenerate-study-pdf/SKILL.md).

## Related commands

| Task | Command |
|------|---------|
| Bibliography-only audit | `python Scripts/_audit_references.py` |
| Download mirrors | `python Scripts/_download_references.py` |
| Verify blockquotes | `python Scripts/_quote_tool.py verify [--study <Slug>]` |
| Sync PDF text cache | `python Scripts/_quote_tool.py cache sync` |

## Completion checklist

- [ ] `python Scripts/_check_references.py` exits 0 (or `--study <Slug>` for a single-study edit)
- [ ] Broken locals fixed or switched to external-only links + `NOT-DOWNLOADED.md`
- [ ] `References/README.md` and `MANIFEST.md` updated when local vs external status changes
- [ ] Affected study PDFs regenerated when bibliography links changed
- [ ] `**Edited on:**` and catalogs updated if study `.md` references changed ([AGENTS.md](../../AGENTS.md) §1)

## Related

- Download workflow: [download-references](../download-references/SKILL.md)
- Agent rules: [AGENTS.md](../../AGENTS.md) §6
- Scripts overview: [Scripts/README.md](../../Scripts/README.md)
