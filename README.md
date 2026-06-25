# Analytic Madhyasth Darshan

A collaborative, open project for **rigorous analytic work** on **Madhyasth Darshan** (Co-existentialism), the philosophy founded by **Shri A. Nagraj**.

We examine defined questions from the darshan, ground claims in the **primary texts**, and compare them critically with other traditions and modern thought where relevant. The aim is to present Shri Nagraj's philosophy **as he gave it to us** — with a clear line between what the texts say, what is interpretation or comparison, and what remains open. A further goal is **formal representation** of the darshan's structure — definitions, relations, and arguments stated with enough precision to compare traditions rigorously and to support the Formal Studies in this collection.

Maintained by **[AnalyticMadhyasthDarshan.org](https://github.com/raghavamohan/AnalyticMadhyasthDarshan)**. All original writing is under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

---

## For readers

| Resource | What you will find |
|----------|-------------------|
| **[Studies catalog](Studies/index.html)** | Published papers (PDF): topical, formal, and applied studies, plus topics in progress |
| **[About the studies](Studies/README.md)** | Our approach, objectives, and how to read the collection |
| **[Official source materials](https://www.madhyasth.org/)** | Primary texts and institutional resources from **Divya Path Sansthan** — the authoritative source for Madhyasth Darshan |
| **[References](References/README.md)** | Source texts and papers cited across the studies |

Draft papers carry a **Draft** watermark on each page; released papers do not.

---

## What is in this repository

```
Studies/          Papers (.md source, .pdf output), catalog page (index.html),
                  and catalog data (catalog-topical.json, catalog-formal.json,
                  catalog-applied.json)
Applications/     Applied studies — concrete instantiations of formal templates
References/       Local copies of cited sources; citation audit (MANIFEST.md)
Scripts/          Tools to add, remove, convert, verify, and publish studies
infra/            Site performance baselines (Cloudflare RUM), submissions worker, audit notes
```

The **markdown** file for each paper is the source of truth. PDFs, the studies landing page, and catalog JSON are generated from it and should not be edited by hand. The catalog page loads study metadata from `Studies/catalog-*.json`; `Studies/README.md` tables stay in sync via the study lifecycle scripts.

For the full script list, see **[Scripts/README.md](Scripts/README.md)**.

---

## For contributors

Read **[Studies/README.md](Studies/README.md)** for what a study should cover, and use the **[Web Submission Portal](Studies/submit.html)** to propose and submit your studies directly from your browser. The web portal handles all backend GitHub automation for you.

## For maintainers

### Clone and one-time setup

Clone the repository, then install Python and Node dependencies from the repo root in PowerShell:

```powershell
git clone https://github.com/raghavamohan/AnalyticMadhyasthDarshan.git
cd AnalyticMadhyasthDarshan
pip install -r requirements.txt
cd Scripts
npm install
cd ..
```

**Agent rules and skills.** A fresh clone already includes [AGENTS.md](AGENTS.md), [`.agents/skills/`](.agents/skills/), [`.cursor/rules/`](.cursor/rules/), and [`.cursor/skills/`](.cursor/skills/) — enough for **Cursor** with no extra steps. Nothing is generated automatically on clone; mirrors are refreshed only when you run `python Scripts/_sync_agent_rules.py` after editing `AGENTS.md` or a skill under `.agents/skills/`.

If you use **OpenCode** or **ZCode**, skills are read from [`.opencode/skills/`](.opencode/skills/), which should be a **junction** (Windows) or symlink to `.agents/skills/`. Git cannot store that link, so create it once after clone if `.opencode/skills` is a normal folder or missing the latest skills:

```powershell
# From repo root — skip if .opencode\skills already junctions to .agents\skills
Remove-Item -Recurse -Force .opencode\skills
cmd /c mklink /J ".opencode\skills" ".agents\skills"
```

Optional verify:

```powershell
python Scripts/_sync_agent_rules.py --check
python Scripts/_check_references.py
python Scripts/_verify_studies_index.py
```

Site operators: store `CLOUDFLARE_API_TOKEN` in a repo-root `.env` file (gitignored) to run `python Scripts/_cloudflare_performance.py` for redirect setup and checks. Baseline metrics live in `infra/cloudflare-rum-baseline.json`.

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
| Verify references / links | `python Scripts\_check_references.py` (or `--study <Slug>`) |
| Verify studies catalog sync | `python Scripts\_verify_studies_index.py` |
| Rebuild studies landing page shell | `python Scripts\_build_studies_index.py` |
| Cloudflare redirect / performance | `python Scripts\_cloudflare_performance.py` (`--apply-redirect`, `--verify-only`) |
| Verify blockquotes (optional) | `python Scripts\_quote_tool.py verify --study <Slug>` |

Windows wrappers: `.\Scripts\_add_study.ps1`, `.\Scripts\_remove_study.ps1`, `.\Scripts\_set_study_status.ps1`.

### Managing studies

**Add** — write `Studies/<Slug>/<Slug>.md`, then register:

```powershell
python Scripts\_add_study.py "Studies\<Slug>\<Slug>.md" `
  --category "Ontology" `
  --description "One-line catalog summary" `
  --tags "MVD, SB, JV" `
  --status draft
```

The script sets metadata, updates `Studies/catalog-*.json`, `Studies/README.md`, `References/README.md`, and `References/MANIFEST.md`, and regenerates the PDF.

Other modes: `--status ongoing` (catalog placeholder, no PDF), `--formal` (Formal Studies table), applied papers under `Applications/` (Applied Studies catalog), or pass an external `.pdf` to create a stub `.md` (re-run on the `.md` after expanding content to apply the watermark).

Flags: `--force` (refresh existing), `--skip-pdf` (catalog only), `--no-check-timestamps`.

**Edit** — change `Studies/<Slug>/<Slug>.md`, refresh `**Edited on:**` (and the catalog date to match), then regenerate the PDF.

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

Prefer the internal pipeline (reads **Status:** from the markdown and runs diagram/code checks):

```powershell
python Scripts\_regenerate_pdf.py <Slug>
```

Manual steps only if debugging:

```powershell
python Scripts\_convert_to_pdf.py "Studies\<Slug>\<Slug>.md"
node Scripts\_html_to_pdf.js "Studies\<Slug>\<Slug>.html" Draft
python Scripts\_verify_pdf_diagrams.py "Studies\<Slug>\<Slug>.md" "Studies\<Slug>\<Slug>.pdf"
python Scripts\_verify_pdf_fenced_code.py "Studies\<Slug>\<Slug>.md" "Studies\<Slug>\<Slug>.pdf"
Remove-Item "Studies\<Slug>\<Slug>.html"
```

Pass `Draft` to `_html_to_pdf.js` for draft studies; omit it for released studies.

### Before opening a pull request

1. Follow the study format and intent in [Studies/README.md](Studies/README.md).
2. Link references to files under `References/` where permitted; otherwise link externally — see [References/NOT-DOWNLOADED.md](References/NOT-DOWNLOADED.md). Do not upload restricted material.
3. Update [References/MANIFEST.md](References/MANIFEST.md) for new citations.
4. Run `python Scripts\_check_references.py --study <Slug>` when bibliography or `../References/` links change.
5. Run `python Scripts\_quote_tool.py verify --study <Slug>` if the study quotes local sources.
6. If you changed the studies landing page shell, run `python Scripts\_verify_studies_index.py`.
7. Describe the question, primary texts, and any new references in the PR.

---

## License

Studies and original writing: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) — cite **AnalyticMadhyasthDarshan.org** and link to this repository.

Source files in `References/` are described in [References/README.md](References/README.md). Works we do not store locally are listed in [References/NOT-DOWNLOADED.md](References/NOT-DOWNLOADED.md).
