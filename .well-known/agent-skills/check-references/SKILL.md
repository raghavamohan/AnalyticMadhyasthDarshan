---
name: check-references
description: >-
  Run full reference integrity checks on Studies/ bibliographies, local
  ../References/ links, References/ mirror files, and study PDF links using
  Scripts/_check_references.py. Use when adding or editing study references,
  after downloading references, before committing bibliography changes, or when
  a user asks to verify reference links work. Includes direct companion-note
  checks outside the canonical-study suite's coverage.
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
- Required CI infers affected studies/references from committed changes; labels do not control whether validation can be bypassed (see [AGENTS.md](../../../AGENTS.md) §6–§7).

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
| **PDF links** | Locally generated study PDFs must not contain `file://` links; stable site links must target usable sources |

A file is **unusable** when it is empty, too small, or a PDF whose content starts
with `<!DOCTYPE` (publisher bot-wall HTML saved as `.pdf`).

## Companion-note coverage

`_check_references.py` and `_audit_references.py` enumerate canonical
`<Slug>/<Slug>.md` studies, not their technical/research notes. The `--study`
filter and automatic PDF-link checks have that same scope. Run the applicable
suite, but do not report its success as verification of a note's bibliography.

For a changed note, additionally inspect its own bibliography and body links,
resolve relative paths from the note's directory, and inspect its generated PDF
link annotations for `file://` URLs or incorrect public targets. Use
`Scripts/_reference_store.py` / `Scripts/_hydrate_references.py` to resolve or
hydrate manifest-backed references: an absent local PDF alone is not a broken
reference. Check external-only citations against their canonical source URLs.
Update applicable usage entries in `References/README.md` and
`References/MANIFEST.md` when adding a note that cites those sources.

There is no companion-path CLI option on these two reference-check commands;
do not invent one. Report direct note checks separately from canonical-suite
results.

## What a passing check does not establish

Link integrity and quotation matching do not verify the meaning of a paraphrase,
translation, or synthesis. For a substantive source review, use
[review-study](../review-study/SKILL.md) and AGENTS.md §§4–5. Inspect the source
page when OCR returns a partial or failed match; do not infer conceptual error
from an extraction failure.

## If checks fail

1. **Empty or corrupt local file** — re-download via [download-references](../download-references/SKILL.md), or remove the local path and link the external DOI/URL only; document in [References/NOT-DOWNLOADED.md](../../../References/NOT-DOWNLOADED.md).
2. **Missing file** — resolve manifest-backed storage first. For a genuinely missing mirror, add to `Scripts/_reference_downloads.py` and download, or switch the study entry to an external link.
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
- [ ] Changed companion-note links checked directly, including generated PDF targets
- [ ] Broken locals fixed or switched to external-only links + `NOT-DOWNLOADED.md`
- [ ] `References/README.md` and `MANIFEST.md` updated when local vs external status changes
- [ ] Affected study PDFs regenerated when bibliography links changed
- [ ] Generated study PDFs were not added to Git; public R2 delivery is audited by the publishing workflow
- [ ] `**Edited on:**` and catalogs updated if study `.md` references changed ([AGENTS.md](../../../AGENTS.md) §1)

## Related

- Download workflow: [download-references](../download-references/SKILL.md)
- Agent rules: [AGENTS.md](../../../AGENTS.md) §6
- Scripts overview: [Scripts/README.md](../../../Scripts/README.md)
