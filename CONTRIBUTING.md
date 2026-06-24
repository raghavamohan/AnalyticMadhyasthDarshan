# Contributing studies

Thank you for helping expand rigorous analytic work on Madhyasth Darshan. This repository uses a **two-stage flow**: propose a study on GitHub, wait for maintainer approval, then submit a pull request. Continuous integration regenerates PDFs and keeps catalogs in sync — you only need to edit markdown.

Read [Studies/README.md](Studies/README.md) for study format, tone, and structure before you start. Agents and automation should follow **[AGENTS.md](AGENTS.md)** for Edited on, PDF pipeline, prose style, and Standpoint and scope.

---

## Overview

| Stage | What you do | What maintainers do |
|-------|-------------|---------------------|
| 1. Proposal | Open a [study proposal issue](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-proposal.yml) | Review scope and fit |
| 2. Approval | Wait for the `proposal-approved` label and follow-up comment | Label approved proposals |
| 3. Pull request | Fork, branch, submit PR with the right label | Review content and merge |

The public catalog at [analyticmadhyasthdarshan.org](https://analyticmadhyasthdarshan.org) links to this workflow from **How to contribute**.

---

## Step 1 — Propose a study

Open a [**Study proposal**](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-proposal.yml) issue. Include:

- **Proposed title** — becomes the study name; the file slug is derived from it (e.g. `The Ontology of Coexistence` → `The-Ontology-of-Coexistence`).
- **Category** — topical area (Ontology, Epistemology, Ethics, etc.) or formal focus.
- **One-line description** — catalog summary shown on the studies page.
- **Study summary** — the question, primary texts, and scope you plan to cover.

A good proposal states a clear analytic question, names the Madhyasth Darshan texts you will use, and explains why the topic fits the collection. Comparison with Advaita Vedanta, modern philosophy, or science is welcome when relevant.

Issues are labeled `study-proposal` automatically. Blank issues are disabled so every proposal uses the form.

---

## Step 2 — Wait for approval

Maintainers review proposals for overlap, scope, and alignment with [Studies/README.md](Studies/README.md). When approved, they add the **`proposal-approved`** label. A bot comment on the issue will include:

- Confirmation of approval
- A link to open a pull request with the **new-study** template
- Reminders to fork the repo and add `Studies/<Slug>/<Slug>.md`

If changes are needed, maintainers will comment on the issue before approving.

---

## Step 3 — Submit a pull request

Fork [AnalyticMadhyasthDarshan](https://github.com/raghavamohan/AnalyticMadhyasthDarshan), create a branch, and open a PR using one of the templates below. **Apply the matching label** so CI runs the correct checks.

### New study (`new-study`)

Use after your proposal is **`proposal-approved`**.

1. Create `Studies/<Slug>/<Slug>.md` following the author block and structure in existing studies.
2. Open a PR with the [**new-study** template](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/compare?expand=1&template=new-study.md).
3. Fill in:
   - `Proposal issue: #123` (your approved issue number)
   - `Slug: Your-Study-Slug` (must match the `.md` filename)
   - `Tags: MVD, SB, JV` (primary citation tags)
4. Apply the **`new-study`** label.

CI verifies the linked issue has `proposal-approved`, reads category and description from the issue, runs `_add_study.py`, and commits the PDF and catalog updates to your branch.

### Update an existing study (`study-update`)

1. Edit `Studies/<Slug>/<Slug>.md`.
2. Update **`**Edited on:**`** to the current time (IST). CI syncs the catalog date from this field.
3. Open a PR with the [**study-update** template](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/compare?expand=1&template=study-update.md).
4. Apply the **`study-update`** label.

CI regenerates the PDF and verifies timestamps match across `.md`, `index.html`, and `README.md`. It also runs `Scripts/_verify_studies_index.py` to confirm catalog JSON and the index landing-page shell stay in sync.

### Change draft ↔ released (`status-change`)

Do **not** hand-edit catalog status rows or watermarks.

1. Open a PR with the [**status-change** template](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/compare?expand=1&template=status-change.md).
2. Fill in study slug, target status (`draft` or `released`), and a brief reason.
3. Apply the **`status-change`** label.

CI runs `_set_study_status.py`, updates metadata and catalogs, and regenerates the PDF with or without the Draft watermark.

---

## Before your PR is merged

- Follow study format and intent in [Studies/README.md](Studies/README.md).
- Link references to files under `References/` where permitted; otherwise link externally — see [References/NOT-DOWNLOADED.md](References/NOT-DOWNLOADED.md). Do not upload restricted material.
- Update [References/MANIFEST.md](References/MANIFEST.md) for new citations (CI may prompt you if tags are missing).
- Run `python Scripts\_quote_tool.py verify --study <Slug>` locally if you quote local sources (optional but recommended).
- Describe the question, primary texts, and any new references in the PR description.

---

## Repository labels

Create these labels in **GitHub → Issues → Labels** (one-time setup):

| Label | Color (suggested) | Used on |
|-------|-------------------|---------|
| `study-proposal` | default | New proposal issues (auto-applied) |
| `proposal-approved` | green | Approved proposals |
| `new-study` | blue | PRs adding a study |
| `study-update` | yellow | PRs editing study content |
| `status-change` | purple | PRs changing draft/released |

---

## Maintainer duties

1. **Review proposals** — scope, overlap, fit with collection standards.
2. **Approve** — add `proposal-approved` when ready (bot posts PR instructions).
3. **Review PRs** — content quality, citations, quote accuracy.
4. **Merge** when the `study-pr` CI check passes.
5. **Release policy** — only merge `status-change` → `released` when the study is ready for public release without a Draft watermark.

Enable branch protection on `main` with the **`study-pr`** check required before merge (recommended).

---

## Local development (optional)

Contributors can preview PDFs locally without waiting for CI:

```powershell
pip install -r requirements.txt
cd Scripts
npm install
cd ..

python Scripts\_regenerate_pdf.py <Slug>
```

Study management scripts: see [README.md](README.md#for-contributors).

---

## License

Studies and original writing: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) — cite **AnalyticMadhyasthDarshan.org** and link to this repository.
