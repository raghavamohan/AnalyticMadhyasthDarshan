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

### Register your paper

If you have a finished PDF, one command copies it into `Studies/` and updates all catalog files:

```powershell
python Scripts\_add_study.py "path\to\Your-Study.pdf" `
  --title "Your Study Title" `
  --description "One-line summary for the catalog" `
  --tags "MVD, SB, JV"
```

Or on Windows:

```powershell
.\Scripts\_add_study.ps1 "path\to\Your-Study.pdf" -Title "Your Study Title"
```

Omit `--title`, `--description`, and `--tags` to be prompted interactively.

The script will:

1. Copy the PDF to `Studies/Your-Study-Title.pdf`
2. Create a stub `Studies/Your-Study-Title.md` (author block + placeholder References)
3. Update `Studies/index.html`, `Studies/README.md`, `References/README.md`, and `References/MANIFEST.md`

Use `--dry-run` to preview. Use `--force` to replace an existing study with the same slug.

### Finish before opening a pull request

1. **Expand the markdown source** — the `.md` file is the canonical source; flesh out sections and add a proper References section
2. **Link references** — point to files under `References/` where a local copy exists; otherwise link to the original publisher or author URL. **Do not upload restricted material** (copyrighted commercial books, publisher PDFs you are not allowed to redistribute, and similar) to `References/` — add an entry to [References/NOT-DOWNLOADED.md](References/NOT-DOWNLOADED.md) and link externally instead.
3. **Update citation records** — refine tag details in `References/MANIFEST.md` (change `TBD` to present/external as needed); add new source files to `References/` only when you have permission to store them
4. **Regenerate the PDF** from markdown when the source is ready:

```powershell
python Scripts\_convert_to_pdf.py "Studies\Your-Study-Title.md"
node Scripts\_html_to_pdf.js "Studies\Your-Study-Title.html"
```

Run `npm install` once inside `Scripts/` before using Puppeteer.

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
2. Remove the row from `Studies/index.html`, `Studies/README.md`, and `References/README.md`
3. Remove the paper block and update **Cited in** entries in `References/MANIFEST.md`

Use `--dry-run` to preview. Use `--yes` to skip the confirmation prompt.

After running:

1. **Check cross-links** — search other Studies for links to the removed paper and edit them
2. **Review `References/MANIFEST.md`** — update the summary table if tag counts changed
3. **Commit** the deletions and catalog updates

---

## License

Studies and original writing: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) — cite **AnalyticMadhyasthDarshan.org** and link to this repository.

Source files in `References/` include Madhyasth Darshan primary texts, Advaita Vedanta translations, comparative sources (AV, SV), and a few author-hosted open-access papers; commercial books and ATR link externally. See [References/NOT-DOWNLOADED.md](References/NOT-DOWNLOADED.md).
