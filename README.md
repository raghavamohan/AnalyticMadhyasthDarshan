# Analytic Madhyasth Darshan

A collaborative repository for **rigorous studies** of **Madhyasth Darshan** (Co-existentialism), founded by **Shri A. Nagraj**.

We take defined philosophical questions from the darshan, ground claims in the **primary texts**, and compare critically with other traditions and modern thought where relevant. The aim is to present Shri Nagraj's philosophy **as he gave it to us** — with clear separation between what the texts say, what is interpretation or comparison, and what remains open.

Maintained by **[AnalyticMadhyasthDarshan.org](https://github.com/raghavamohan/AnalyticMadhyasthDarshan)**.

**Browse published studies:** [Studies/index.html](Studies/index.html)

---

## Adding a study

### What a study should be

- A **defined question** from or about Madhyasth Darshan
- **Grounded in primary texts** (and other sources where comparison requires them)
- **Critical and explicit** about interpretation vs. what follows from the darshan
- Written with the standard author block and a **`## References`** section (see an [existing study](Studies/) for format)

Read the [Studies intent statement](Studies/README.md) and browse [existing papers](Studies/index.html) for tone and depth.

### Register your study

**Recommended:** pass the markdown source (`.md`). The script sets `**Edited on:**`, updates all catalog files with matching timestamps, and regenerates the PDF. Draft studies get a **Draft** watermark automatically.

```powershell
python Scripts\_add_study.py "Studies\Your-Study-Title.md" `
  --category "Ontology" `
  --description "One-line summary for the catalog" `
  --tags "MVD, SB, JV" `
  --status draft
```

Or on Windows:

```powershell
.\Scripts\_add_study.ps1 "Studies\Your-Study-Title.md" `
  -Category "Ontology" `
  -Description "One-line summary for the catalog"
```

**Alternative:** import an external PDF (creates a stub `.md` and catalogs the study as draft). The imported PDF is kept as-is — expand the markdown and re-run on the `.md` file to apply the Draft watermark.

```powershell
python Scripts\_add_study.py "path\to\Your-Study.pdf" --title "Your Study Title"
```

**Ongoing placeholder** (no PDF yet, italic title in the catalog):

```powershell
python Scripts\_add_study.py "Studies\Future-Study.md" --status ongoing --category "Epistemology"
```

**Formal study** (separate Formal Studies table):

```powershell
python Scripts\_add_study.py "Studies\Your-Formal-Study.md" --formal --category "Category theory"
```

Omit `--category`, `--description`, and `--tags` to be prompted interactively.

The script will:

1. Ensure `Studies/Your-Study-Title.md` has the standard author block and current `**Edited on:**` timestamp
2. Regenerate `Studies/Your-Study-Title.pdf` from markdown (Draft watermark when `--status draft`; omit watermark when `--status released`)
3. Update `Studies/index.html`, `Studies/README.md`, `References/README.md`, and `References/MANIFEST.md` with synced status timestamps

Use `--dry-run` to preview. Use `--force` to refresh an existing study. Use `--skip-pdf` to update catalogs only. Use `--no-check-timestamps` to skip the post-add sync check.

### Finish before opening a pull request

1. **Expand the markdown source** — the `.md` file is the canonical source; flesh out sections and add a proper References section
2. **Link references** — point to files under `References/` where a local copy exists; otherwise link to the original publisher or author URL. **Do not upload restricted material** (copyrighted commercial books, publisher PDFs you are not allowed to redistribute, and similar) to `References/` — add an entry to [References/NOT-DOWNLOADED.md](References/NOT-DOWNLOADED.md) and link externally instead.
3. **Update citation records** — refine tag details in `References/MANIFEST.md` (change `TBD` to present/external as needed); add new source files to `References/` only when you have permission to store them
4. **Regenerate the PDF** from markdown when the source changes (or let `_add_study.py` do this when registering):

```powershell
python Scripts\_convert_to_pdf.py "Studies\Your-Study-Title.md" --watermark Draft
node Scripts\_html_to_pdf.js "Studies\Your-Study-Title.html"
Remove-Item "Studies\Your-Study-Title.html"
```

Omit `--watermark Draft` only for **Released** studies. Run `npm install` once inside `Scripts/` before using Puppeteer.

5. **Verify quotations** (recommended) — checks that blockquotes in your study appear in the local copy under `References/`:

```powershell
pip install pypdf
python Scripts\_verify_quotes.py
```

The script scans every `Studies/*.md` file for blockquotes with a source tag (for example `MVD`, `SB`, `JV`, `Chalmers 1995`). For each quote it loads the matching file from `References/` — any PDF, HTML, or markdown stored there — and reports whether the text was found (with page number when possible), only partially matched, attributed to the wrong source, or missing. Illustrative blockquotes without a source tag, and citations to works not stored locally, are skipped.

To check one study or tag set:

```powershell
python Scripts\_verify_quotes.py --study Why-Humans-Are-Not-Just-Material
python Scripts\_verify_quotes.py --tags MVD,SB,JV
```

Extracted PDF text is cached in `Scripts/_pdf_cache/` on first run.

6. **Open a pull request** — describe the question, primary texts used, and any new references added

---

## Removing a study

To retire a paper from the collection, one command deletes its files and updates all catalog entries:

```powershell
python Scripts\_remove_study.py Study-Slug
```

Or on Windows:

```powershell
.\Scripts\_remove_study.ps1 Study-Slug
```

Use the filename slug without worrying about the extension — for example `Why-Humans-Are-Not-Just-Material` or `Why-Humans-Are-Not-Just-Material.pdf`.

The script will:

1. Delete `Studies/Study-Slug.md`, `.pdf`, and local `.html` (if present)
2. Remove the row from the correct table in `Studies/index.html` and `Studies/README.md` (Topical or Formal; Ongoing placeholders supported)
3. Remove the paper from `References/README.md` and `References/MANIFEST.md` when the study was published (not Ongoing)

Use `--dry-run` to preview. Use `--yes` to skip the confirmation prompt.

After running:

1. **Check cross-links** — search other Studies for links to the removed paper and edit them
2. **Review `References/MANIFEST.md`** — update the summary table if tag counts changed
3. **Commit** the deletions and catalog updates

---

## License

Studies and original writing: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) — cite **AnalyticMadhyasthDarshan.org** and link to this repository.

Source files in `References/` include Madhyasth Darshan primary texts, Advaita Vedanta translations, comparative sources (AV, SV), and a few author-hosted open-access papers; commercial books and ATR link externally. See [References/NOT-DOWNLOADED.md](References/NOT-DOWNLOADED.md).
