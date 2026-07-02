---
name: add-study
description: >-
  Register a new study in Studies/ using Scripts/_add_study.py or
  _add_study.ps1 — sets metadata, updates catalogs, and generates PDF. Use when
  adding a study, registering a paper, creating an Ongoing placeholder, importing
  a PDF, or adding a Formal study.
---

# Add a study

## Before you start

1. Read [Studies/README.md](../../Studies/README.md) for study format and intent.
2. Follow [AGENTS.md](../../AGENTS.md) §4 (prose style) and §5 (Standpoint and scope).
   Reference implementations: `Studies/The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.md` (ontology, open problems);
   `Studies/Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material.md` (comparative anthropology, critique closings).
3. Write `Studies/<Slug>/<Slug>.md` with author block, or prepare an external PDF for maintainer conversion (`--convert`).
4. Choose catalog table: **topical** (default) or **formal** (`--formal`).

## Recommended: register from markdown

From repo root:

```powershell
python Scripts/_add_study.py "Studies/<Slug>/<Slug>.md" `
  --category "Ontology" `
  --description "One-line catalog summary" `
  --tags "MVD, SB, JV" `
  --status draft
```

Windows wrapper:

```powershell
.\Scripts\_add_study.ps1 "Studies\<Slug>.md" `
  -Category "Ontology" `
  -Description "One-line catalog summary"
```

Omit `--category`, `--description`, `--tags` in an interactive terminal to be prompted.

## What the script does

1. Sets `**Author:**`, `**Edited on:**`, `**Status:**` in the `.md`
2. Regenerates `Studies/<Slug>.pdf` (Draft watermark when `--status draft`)
3. Upserts catalog entry in `Studies/index.html` (JSON) and `Studies/README.md` (markdown table)
4. Updates `References/README.md` and `References/MANIFEST.md` (skipped for Ongoing)

## Registration modes

| Mode | Command |
|------|---------|
| Draft study (default) | `--status draft` |
| Released study | `--status released` |
| Ongoing placeholder (no PDF) | `--status ongoing --category "..."` |
| Formal Studies table | `--formal --category "Category theory"` |
| Import external PDF (stub only) | `python Scripts/_add_study.py "path/to/paper.pdf" --title "Title"` |
| Import external PDF (convert to markdown) | `python Scripts/_add_study.py "path/to/paper.pdf" --convert --slug <Slug> --title "Title" --category "..." --description "..."` |
| Convert PDF without catalog register | `python Scripts/_pdf_to_study_md.py "path/to/paper.pdf" --slug <Slug> --title "Title"` |

## Flags

| Flag | Purpose |
|------|---------|
| `--dry-run` | Preview without writing |
| `--force` | Overwrite existing slug |
| `--skip-pdf` | Update catalogs/metadata only |
| `--no-check-timestamps` | Skip post-run sync verification |
| `--slug` | Override filename-derived slug |
| `--convert` | For PDF input: extract markdown body instead of a stub |
| `--no-keep-pdf` | With `--convert`: skip copying source PDF into `Studies/<Slug>/` |

## PDF import

**Stub import (default):** copies the PDF and writes a placeholder `.md` for manual expansion.

**Converted import (`--convert`):** runs layout-aware extraction (`_pdf_to_md.py`) into a real
draft `.md`. Maintainer must review before regenerating PDF:

1. Fix headings, tables, blockquotes, and bibliography to house style (AGENTS.md §4)
2. Add or correct `## Standpoint and scope` if missing (§5)
3. Re-run `_add_study.py` on the `.md` or `_regenerate_pdf.py <Slug>` for Draft watermark

Diagrams, KaTeX math, and glossary tooltips are **not** recovered from PDF. Scanned PDFs fail
with a clear error. Test changes with `python Scripts/_test_pdf_to_md.py`.

## Manual edit after register

If you edit body text later:

1. Refresh `**Edited on:**` per `AGENTS.md` §1
2. Regenerate PDF: [regenerate-study-pdf](../regenerate-study-pdf/SKILL.md) (`python Scripts/_regenerate_pdf.py <Slug>`)

Or use `_set_study_status.py` / `_add_study.py --force --skip-pdf` only for metadata sync — not for body edits without timestamp update.

## Completion checklist

- [ ] Study appears in correct catalog (topical or formal)
- [ ] `verify_timestamp_sync` passes (default after add)
- [ ] `References/MANIFEST.md` TBD rows refined if needed
- [ ] Prose passes [AGENTS.md](../../AGENTS.md) §4 checklist (no scaffold tags, Verdict labels, or honesty qualifiers)
- [ ] `## Standpoint and scope` present per [AGENTS.md](../../AGENTS.md) §5
- [ ] PR describes question, primary texts, new references

## Related

- Overview: [manage-studies](../manage-studies/SKILL.md)
- Remove: [remove-study](../remove-study/SKILL.md)
- Release: [set-study-status](../set-study-status/SKILL.md)
