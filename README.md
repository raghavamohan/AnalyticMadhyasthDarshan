# Analytic Madhyasth Darshan

A collaborative, open project for **rigorous analytic work** on **Madhyasth Darshan** (Co-existentialism), the philosophy founded by **Shri A. Nagraj**.

We examine defined questions from the darshan, ground claims in the **primary texts**, and compare them critically with other traditions and modern thought where relevant. The aim is to present Shri Nagraj's philosophy **as he gave it to us** — with a clear line between what the texts say, what is interpretation or comparison, and what remains open. A further goal is **formal representation** of the darshan's structure — definitions, relations, and arguments stated with enough precision to compare traditions rigorously and to support the Formal Studies in this collection.

Maintained by **[AnalyticMadhyasthDarshan.org](https://github.com/raghavamohan/AnalyticMadhyasthDarshan)**. Original writing is under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/); the code (`Scripts/`, `infra/`) is under the [MIT License](LICENSE-CODE) — see [License](#license).

---

## For readers

| Resource | What you will find |
|----------|-------------------|
| **[Studies catalog](Studies/index.html)** | Published papers (PDF): topical, formal, and applied studies, plus topics in progress |
| **[My Submissions](Studies/submit.html)** | Web Submission Portal — sign in with GitHub to propose, submit, update, and track studies (reading the catalog needs no account) |
| **[About the studies](Studies/README.md)** | Our approach, objectives, and how to read the collection |
| **[Official source materials](https://www.madhyasth.org/)** | Primary texts and institutional resources from **Divya Path Sansthan** — the authoritative source for Madhyasth Darshan |
| **[References](References/README.md)** | Source texts and papers cited across the studies |

Each study page links to a **Discuss** board (email sign-in) for open conversation; structured corrections use **Suggest a correction** in the study toolbar or a [study feedback issue](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-feedback.yml).

Draft papers carry a **Draft** watermark on each page; released papers do not.

---

## What is in this repository

```
Studies/          Papers (.md source; companion .html and .pdf output; discussion.html),
                  catalog pages (index.html, submit.html), catalog JSON
                  (catalog-topical.json, catalog-formal.json, catalog-applied.json),
                  shared glossary (glossary.json), reader assets (assets/)
Applications/     Applied studies — concrete instantiations of formal templates
References/       Local copies of cited sources; citation audit (MANIFEST.md)
Scripts/          Tools to add, remove, convert, verify, and publish studies
infra/            Cloudflare Workers (submissions portal, per-study discussions),
                  performance baselines (cloudflare-rum-baseline.json), audit notes
AGENTS.md         Standing rules for agents and local maintainers (§1–§8)
.github/          CI workflows and study pull request templates
```

The **markdown** file for each paper is the source of truth. Companion HTML, PDFs, the studies landing page, and catalog JSON are generated from it and should not be edited by hand. The catalog page loads study metadata from `Studies/catalog-*.json`; `Studies/README.md` tables stay in sync via the study lifecycle scripts.

For the full script list, see **[Scripts/README.md](Scripts/README.md)**.

---

## For contributors

Two paths — pick the one that matches what you want to do.

**Corrections on a published study** — [Suggest a correction](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-feedback.yml) or use the toolbar link while reading a study. No approval gate; a GitHub account is required to file the issue.

**New study or full revision** — the Web Submission Portal:

1. **Read** [Studies/README.md](Studies/README.md) for what a study should cover and how we write.
2. Open **[My Submissions](Studies/submit.html)** and **sign in** with GitHub (required to propose or submit).
3. **Propose** a title, category, and summary from that page.
4. **Wait** for maintainer approval; the study appears on the index as **Planned** until your first draft merges.
5. When approved, click **Submit draft** on your row to open a pull request automatically.

The portal handles GitHub issues and pull requests for you. Agents and local git contributors follow the same branch, label, and checklist rules in [AGENTS.md](AGENTS.md) §7. Full details: [CONTRIBUTING.md](CONTRIBUTING.md).

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

Site operators: copy [`.env.example`](.env.example) to `.env` at the repo root (gitignored). Set `CLOUDFLARE_API_TOKEN` for `python Scripts/_cloudflare_performance.py`; set `R2_*` (or `AWS_*` aliases) for S3-compatible R2 access; set `GITHUB_TOKEN` for local proposal-bootstrap helpers. Worker runtime secrets (OAuth, Turnstile) live in Wrangler — see [infra/worker/README.md](infra/worker/README.md) and [infra/discussions-worker/README.md](infra/discussions-worker/README.md). Baseline metrics live in `infra/cloudflare-rum-baseline.json`.

### Study lifecycle

| State | On the studies index | In `Studies/README.md` | PDF / HTML |
|-------|----------------------|-------------------------|------------|
| **Planned** | “Planned” badge; read links when a proposal stub exists | `Ongoing` — topic registered or approved proposal awaiting first draft | Proposal stub after approval; none for catalog-only placeholders |
| **Draft** | “Draft” badge, linked title | `Draft` + **Last updated on** | **Draft** watermark on every PDF page; companion `.html` for reading |
| **Released** | “Released” badge, linked title | `Released` + **Last updated on** | No watermark |

Published studies carry `**Edited on:**` and `**Status:**` in the `.md` file. Refresh `**Edited on:**` with the current IST time whenever study content changes (`Get-Date -Format "MMMM d, yyyy, h:mm tt"` in PowerShell, then append ` IST`), and update the matching catalog **Last updated on** date in both `Studies/README.md` and `Studies/index.html` — see [AGENTS.md](AGENTS.md) §1. The `**Status:**` line is for repository management only; it is omitted from the PDF body (draft is shown by the watermark).

Recurring Hindi and darshan terms across studies belong in [Studies/glossary.json](Studies/glossary.json) (`python Scripts/_verify_glossary.py` after edits).

Every change under `Studies/` — by a human contributor or an agent — goes through a feature branch and a pull request labeled `new-study`, `study-update`, or `status-change`, never a direct commit to `master`. Use the matching template in [`.github/PULL_REQUEST_TEMPLATE/`](.github/PULL_REQUEST_TEMPLATE/) and include the required PR body field (`Study slug:`, `Proposal issue: #N`, or `Target status:`). See [CONTRIBUTING.md](CONTRIBUTING.md) for the contributor-facing flow and [AGENTS.md](AGENTS.md) §7 for the full local checklist before pushing.

### Scripts

Run from the repository root. Append `--dry-run` to any command to preview without writing files.

| Task | Command |
|------|---------|
| Add or register a study | `python Scripts\_add_study.py Studies\<Slug>\<Slug>.md --category "..." --description "..." --tags "MVD, SB, JV" --status draft` |
| Remove a study | `python Scripts\_remove_study.py <Slug> --yes` |
| Draft ↔ Released | `python Scripts\_set_study_status.py <Slug> --status released` |
| Regenerate PDF/HTML after editing `.md` | `python Scripts\_regenerate_pdf.py <Slug>` |
| Verify references / links | `python Scripts\_check_references.py` (or `--study <Slug>`) |
| Verify studies catalog sync | `python Scripts\_verify_studies_index.py` |
| Rebuild studies landing page shell | `python Scripts\_build_studies_index.py` |
| Rebuild per-study discussion pages | `python Scripts\_build_discussion_pages.py` |
| Sync agent rules and skills | `python Scripts\_sync_agent_rules.py` then `python Scripts\_sync_agent_rules.py --check` |
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

**Edit** — change `Studies/<Slug>/<Slug>.md`, refresh `**Edited on:**` (and the catalog date to match), then run `python Scripts\_regenerate_pdf.py <Slug>` (updates companion HTML and PDF).

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
python Scripts\_verify_study_svgs.py "Studies\<Slug>\<Slug>.md"
python Scripts\_convert_to_pdf.py "Studies\<Slug>\<Slug>.md"
node Scripts\_html_to_pdf.js "Studies\<Slug>\<Slug>.html" Draft
python Scripts\_verify_pdf_diagrams.py "Studies\<Slug>\<Slug>.md" "Studies\<Slug>\<Slug>.pdf"
python Scripts\_verify_pdf_fenced_code.py "Studies\<Slug>\<Slug>.md" "Studies\<Slug>\<Slug>.pdf"
python Scripts\_verify_pdf_outline.py "Studies\<Slug>\<Slug>.md" "Studies\<Slug>\<Slug>.pdf"
```

Pass `Draft` to `_html_to_pdf.js` for draft studies; omit it for released studies. Keep the companion `.html` beside each `.pdf` — the catalog **Read** links open HTML; do not delete it after regeneration.

### Before opening a pull request

1. Work on a **feature branch**, not `master`.
2. Follow the study format and intent in [Studies/README.md](Studies/README.md) and writing rules in [AGENTS.md](AGENTS.md) §4–§5.
3. Refresh `**Edited on:**` and the catalog **Last updated on** dates when study content changed ([AGENTS.md](AGENTS.md) §1).
4. Link references to files under `References/` where permitted; otherwise link externally — see [References/NOT-DOWNLOADED.md](References/NOT-DOWNLOADED.md). Do not upload restricted material.
5. Update [References/MANIFEST.md](References/MANIFEST.md) for new citations.
6. Run `python Scripts\_regenerate_pdf.py <Slug>` after editing a study `.md`.
7. Run `python Scripts\_check_references.py --study <Slug>` when bibliography or `../References/` links change.
8. Run `python Scripts\_quote_tool.py verify --study <Slug>` if the study quotes local sources.
9. Run `python Scripts\_verify_studies_index.py` if catalog data or the index shell changed.
10. Apply exactly one PR label (`new-study`, `study-update`, or `status-change`) and fill the matching template field in the PR body.
11. Describe the question, primary texts, and any new references in the PR.

---

## License

This repository is dual-licensed:

- **Content** — studies and original writing under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) (see [LICENSE](LICENSE)). Cite **AnalyticMadhyasthDarshan.org** and link to this repository.
- **Code** — the tooling in `Scripts/` and the backend services in `infra/` under the [MIT License](LICENSE-CODE).

Copyright © 2026 AnalyticMadhyasthDarshan.org.

Source files in `References/` are described in [References/README.md](References/README.md). Works we do not store locally are listed in [References/NOT-DOWNLOADED.md](References/NOT-DOWNLOADED.md).
