---
name: update-reference-translation
description: >-
  Update an ongoing primary-text translation PDF (such as JVD, AVD, SB, AA, or
  KD) from a Google Doc or local PDF, map shifted page numbers across Studies/,
  Applications/, Primer/, and .pptx decks using
  Scripts/_sync_reference_translation.py, publish the updated reference to
  Cloudflare R2, and finalize all affected studies and companion artifacts.
---

# Update a reference translation

When an ongoing primary-text translation (such as `JVD`, `AVD`, `SB`, `AA`, or
`KD`) advances through peer review or revision, its pagination and English
wording often shift as multi-version candidate translations are consolidated into
a single rendering.

Use this skill to export or ingest the updated PDF, map every cited page number
across Markdown and PowerPoint files, inspect side-by-side wording diffs, publish
the updated reference to Cloudflare R2, and synchronize all affected studies.

Works with **Cursor**, **OpenCode**, and **ZCode** (skills live in
`.agents/skills/`; OpenCode reads them via `.opencode/skills/` junction).

## When to use

- User provides a Google Docs link or updated PDF for an ongoing translation (`JVD`, `AVD`, `SB`, `AA`, `KD`, `MVD`, `JV`)
- A peer-reviewed translation snapshot replaces an earlier work-in-progress PDF under `References/Madhyasth-Darshan/`
- You need to audit and update page numbers, blockquotes, and terminology across studies, technical notes, presentations, and `Primer/` after a reference edition change

## End-to-end workflow

### 1. Run the citation scanner and shingle page-mapper

Before overwriting the file under `References/`, run
`Scripts/_sync_reference_translation.py` from the repository root. It resolves
or hydrates the previous PDF via `Scripts/_reference_store.py`, downloads the
new PDF (if a Google Doc URL or ID is given), scans all `.md` and `.pptx` files
for citations to the sigil, maps old pages to new pages using 5-word shingle
overlap (over both Hindi and English tokens), and writes a de-wrapped
side-by-side comparison report:

```powershell
# From a Google Docs sharing URL or document ID:
python Scripts/_sync_reference_translation.py --sigil JVD --google-doc "https://docs.google.com/document/d/<DOC_ID>/edit?usp=sharing"

# Or from a local updated PDF:
python Scripts/_sync_reference_translation.py --sigil JVD --new-pdf tmp/JVD-updated.pdf
```

Supported built-in presets (`--sigil`): `JVD`, `AVD`, `SB`, `MVD`, `JV`, `AA`,
`KD` (or pass `--reference-path References/...` for any other PDF).

Inspect the generated report at `tmp/<sigil>-translation-diff.md`:

1. **Section 1 (Page 1 status diff):** Check the updated review date and peer-review boundary page.
2. **Section 2 (Old -> New Page Mapping Summary):** Identify which cited pages are `UNCHANGED` vs. `SHIFTED (old -> new)`.
3. **Section 3 (Repository Citation Inventory):** Review every `.md` line and `.pptx` slide/notes XML entry that cites the text.
4. **Section 4 (Side-by-Side Cited Page Text):** Compare `[OLD p. X]` against `[NEW p. Y]` for every cited page to check whether any direct blockquotes or key technical terms were refined during peer review.

### 2. Replace the reference PDF and publish to Cloudflare R2

Copy the verified PDF into its canonical path under `References/` (for example,
`References/Madhyasth-Darshan/JVD-Janvad.pdf`), then update
`References/r2-artifacts.json` and upload the new object to Cloudflare R2:

```powershell
Copy-Item -LiteralPath tmp/JVD-updated.pdf -Destination References/Madhyasth-Darshan/JVD-Janvad.pdf -Force
python Scripts/_publish_reference_artifacts.py --sync-manifest --upload --verify
python Scripts/_verify_reference_delivery.py
```

If `References/MANIFEST.md` records the total page count or review status of the
file, update that entry as well.

### 3. Update citations and quotes across Markdown and PowerPoint files

Work on a feature branch (`study-update/...` when any file under `Studies/` or
`Applications/` is modified; see [AGENTS.md](../../../AGENTS.md) §7):

1. **Markdown files (`Studies/`, `Applications/`, `Primer/`, `docs/`):**
   - Update shifted page numbers (`p. X` -> `p. Y`, `pp. X–Y` -> `pp. A–B`) in body citations, `## Editorial Notes` tables, and `## References` entries.
   - Where a study quotes the translation verbatim in a blockquote and the peer-reviewed English wording changed, update the blockquote to match the finalized translation (and verify that surrounding analytical prose remains consistent).
2. **PowerPoint decks (`Studies/*/*.pptx`, `Applications/*/*.pptx`):**
   - If the citation inventory in `tmp/<sigil>-translation-diff.md` listed `.pptx` matches (`ppt/slides/*.xml` or `ppt/notesSlides/*.xml`), update the page numbers in those XML entries inside the `.pptx` archive and rebuild the deck PDFs:
     ```powershell
     python Scripts/_pptx_to_pdf.py Studies/<Slug>/<Deck>.pptx
     python Scripts/_build_deck_notes_pdf.py Studies/<Slug>/<Deck>.pptx
     ```

### 4. Finalize affected studies and run reference checks

For every modified study under `Studies/` or `Applications/`, run the shared
finalizer so `**Edited on:**`, catalog timestamps (`Studies/README.md`,
`Studies/index.html`, `Studies/catalog-*.json`), `sitemap.xml`, `llms-full.txt`,
`Studies/search-data/`, and HTML/PDF readers stay in sync:

```powershell
python Scripts/_finalize_study_artifacts.py --study <Slug1> --study <Slug2>
```

If a companion technical note was also edited, regenerate its HTML/PDF:

```powershell
python Scripts/_regenerate_pdf.py Studies/<Slug>/Technical-Note-<Name>.md
```

Then run the full reference and catalog verification suite:

```powershell
python Scripts/_check_references.py
python Scripts/_verify_studies_index.py
```

Finally, remove any locally generated `.pdf` files under `Studies/` and
`Applications/` before committing (generated study/deck PDFs are gitignored and
built/published in CI).

## Files

| File | Role |
|------|------|
| `Scripts/_sync_reference_translation.py` | Google Doc exporter, `.md`/`.pptx` citation scanner, 5-word shingle page mapper, and side-by-side diff generator |
| `Scripts/_publish_reference_artifacts.py` | Updates `References/r2-artifacts.json` (`bytes`, `sha256`), uploads to R2, and verifies remote storage |
| `Scripts/_verify_reference_delivery.py` | Verifies R2 reference manifest and public delivery |
| `Scripts/_finalize_study_artifacts.py` | Refreshes `**Edited on:**`, catalogs, search data, and study HTML/PDFs |
| `Scripts/_check_references.py` | Full reference integrity checks across `Studies/` |

## Completion checklist

- [ ] `python Scripts/_sync_reference_translation.py --sigil <SIGIL> ...` run and `tmp/<sigil>-translation-diff.md` reviewed
- [ ] Updated PDF published to R2 and `References/r2-artifacts.json` (plus `References/MANIFEST.md` if applicable) updated
- [ ] All shifted page numbers and updated blockquotes synced across `Studies/`, `Applications/`, `Primer/`, `docs/`, and `.pptx` decks
- [ ] Affected studies finalized (`_finalize_study_artifacts.py`) and companion notes/decks rebuilt and verified
- [ ] `python Scripts/_check_references.py`, `python Scripts/_verify_reference_delivery.py`, and `python Scripts/_verify_studies_index.py` exit 0
- [ ] Temporary files in `tmp/` and locally generated PDFs under `Studies/` / `Applications/` cleaned up before commit

## Related

- Reference integrity checks: [check-references](../check-references/SKILL.md)
- Downloading new mirrors: [download-references](../download-references/SKILL.md)
- Study lifecycle: [manage-studies](../manage-studies/SKILL.md)
- Agent rules: [AGENTS.md](../../../AGENTS.md) §1, §3, §6, §7
