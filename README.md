# Analytic Madhyasth Darshan

A collaborative, open project for **rigorous analytic work** on **Madhyasth Darshan** (Co-existentialism), the philosophy founded by **Shri A. Nagraj**.

We examine defined questions from the darshan, ground claims in the **primary texts**, and compare them critically with other traditions and modern thought where relevant. The aim is to present Shri Nagraj's philosophy **as he gave it to us** — with a clear line between what the texts say, what is interpretation or comparison, and what remains open.

Maintained by **[AnalyticMadhyasthDarshan.org](https://github.com/raghavamohan/AnalyticMadhyasthDarshan)**. All original writing is under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

---

## For readers

| Resource | What you will find |
|----------|-------------------|
| **[Studies catalog](Studies/index.html)** | Published papers (PDF), topical and formal studies, and topics in progress |
| **[About the studies](Studies/README.md)** | Our approach, objectives, and how to read the collection |
| **[Official source materials](https://www.madhyasth.org/)** | Primary texts and institutional resources from **Divya Path Sansthan** — the authoritative source for Madhyasth Darshan |
| **[References](References/README.md)** | Source texts and papers cited across the studies |

Draft papers carry a **Draft** watermark on each page; released papers do not.

---

## What is in this repository

```
Studies/          Papers (.md source, .pdf output) and the public catalog (index.html)
References/       Local copies of cited sources; citation audit (MANIFEST.md)
Scripts/          Tools to add, remove, convert, and verify studies
```

The **markdown** file for each paper is the source of truth. PDFs and catalog pages are generated from it and should not be edited by hand.

---

## For contributors

Read **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full proposal → approval → pull request workflow, and **[Studies/README.md](Studies/README.md)** for what a study should cover, tone, and structure before you start writing.

### One-time setup

From the repository root in PowerShell:

```powershell
pip install -r requirements.txt
cd Scripts
npm install
cd ..
```

### Study lifecycle

| State | In the catalog | PDF |
|-------|----------------|-----|
| **Ongoing** | Italic title, no link | None — topic registered, not yet written |
| **Draft** | Linked title, “Draft” status | **Draft** watermark on every page |
| **Released** | Linked title, “Released” status | No watermark |

Published studies carry `**Edited on:**` and `**Status:**` in the `.md` file. The catalog **Last updated on** date must match `**Edited on:**`. The status line is for repository management only — it is omitted from the PDF (draft is shown by the watermark).

### Scripts

Run from the repository root. Append `--dry-run` to any command to preview without writing files.

| Task | Command |
|------|---------|
| Add or register a study | `python Scripts\_add_study.py Studies\<Slug>.md --category "..." --description "..." --tags "MVD, SB, JV" --status draft` |
| Remove a study | `python Scripts\_remove_study.py <Slug> --yes` |
| Draft ↔ Released | `python Scripts\_set_study_status.py <Slug> --status released` |
| Regenerate PDF after editing `.md` | `python Scripts\_regenerate_pdf.py <Slug>` |
| Verify blockquotes (optional) | `python Scripts\_quote_tool.py verify --study <Slug>` |

Windows wrappers: `.\Scripts\_add_study.ps1`, `.\Scripts\_remove_study.ps1`, `.\Scripts\_set_study_status.ps1`.

### Managing studies

**Add** — write `Studies/<Slug>.md`, then register:

```powershell
python Scripts\_add_study.py "Studies\<Slug>.md" `
  --category "Ontology" `
  --description "One-line catalog summary" `
  --tags "MVD, SB, JV" `
  --status draft
```

The script sets metadata, updates `Studies/index.html`, `Studies/README.md`, `References/README.md`, and `References/MANIFEST.md`, and regenerates the PDF.

Other modes: `--status ongoing` (catalog placeholder, no PDF), `--formal` (Formal Studies table), or pass an external `.pdf` to create a stub `.md` (re-run on the `.md` after expanding content to apply the watermark).

Flags: `--force` (refresh existing), `--skip-pdf` (catalog only), `--no-check-timestamps`.

**Edit** — change `Studies/<Slug>.md`, refresh `**Edited on:**` (and the catalog date to match), then regenerate the PDF.

**Release or revert to draft:**

```powershell
python Scripts\_set_study_status.py <Slug> --status released
python Scripts\_set_study_status.py <Slug> --status draft
```

Omit `--status` to toggle. The script syncs metadata, catalogs, and the PDF watermark.

**Remove:**

```powershell
python Scripts\_remove_study.py <Slug>
```

Confirm when prompted, or pass `--yes`. Then check other papers for cross-links and commit.

### PDF regeneration

```powershell
python Scripts\_regenerate_pdf.py <Slug>
```

This reads **Status:** from the markdown and applies the Draft watermark when appropriate. Manual steps if needed:

```powershell
python Scripts\_convert_to_pdf.py "Studies\<Slug>.md" --watermark Draft
node Scripts\_html_to_pdf.js "Studies\<Slug>.html"
Remove-Item "Studies\<Slug>.html"
```

### Before opening a pull request

1. Follow the study format and intent in [Studies/README.md](Studies/README.md).
2. Link references to files under `References/` where permitted; otherwise link externally — see [References/NOT-DOWNLOADED.md](References/NOT-DOWNLOADED.md). Do not upload restricted material.
3. Update [References/MANIFEST.md](References/MANIFEST.md) for new citations.
4. Run `python Scripts\_quote_tool.py verify --study <Slug>` on your study if it quotes local sources.
5. Describe the question, primary texts, and any new references in the PR.

---

## License

Studies and original writing: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) — cite **AnalyticMadhyasthDarshan.org** and link to this repository.

Source files in `References/` are described in [References/README.md](References/README.md). Works we do not store locally are listed in [References/NOT-DOWNLOADED.md](References/NOT-DOWNLOADED.md).
