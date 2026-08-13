## Study update

<!--
REQUIRED — bare catalog slug only, on its own line.
Copy the Studies/<Slug>/ directory name exactly (e.g. The-Ontology-of-Coexistence).
Do NOT append notes, parentheticals, or em dashes on this line — CI looks up the
entire remainder of the line in the catalog and will fail (see PR #146).
Put context in "Summary of changes" below instead.

PR READINESS — open this as a ready-for-review GitHub pull request by default.
A study's Draft status is not GitHub's draft-PR state. Use a GitHub draft PR only
when explicitly requested for incomplete PR work.
-->
Study slug: <!-- e.g. The-Ontology-of-Coexistence -->

### Summary of changes

<!-- What you changed and why. Companion-only edits (pptx, research notes, SVGs)
     still use this template and the study-update label; say so here. -->

### Checklist

- [ ] `Study slug:` is the **bare** catalog slug only (no notes on that line)
- [ ] Handled study status separately from PR readiness (ready for review by default)
- [ ] Applied label **`study-update`** to this pull request (exactly one study label)
- [ ] Updated `**Edited on:**` in `Studies/<Slug>/<Slug>.md` to the current time (IST) — **required when the study `.md` changed**; N/A for companion-only files (pptx, research notes, figures) that do not edit the study markdown
- [ ] Updated [References/MANIFEST.md](../../References/MANIFEST.md) for any new citations — N/A if citations unchanged
- [ ] Ran `python Scripts/_quote_tool.py verify --study <Slug>` if quoting local sources (recommended)
