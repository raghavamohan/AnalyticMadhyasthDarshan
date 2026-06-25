# Contributing studies

Thank you for helping expand rigorous analytic work on Madhyasth Darshan. This repository uses a **two-stage flow** managed through our **[Web Submission Portal](Studies/submit.html)**: propose a study, wait for maintainer approval, then submit your draft. The web portal automatically handles all GitHub issues and pull requests behind the scenes.

Read [Studies/README.md](Studies/README.md) for study format, tone, and structure before you start. Agents and automation should follow **[AGENTS.md](AGENTS.md)** for Edited on, PDF pipeline, prose style, and Standpoint and scope.

---

## Overview

| Stage | What you do | What maintainers do |
|-------|-------------|---------------------|
| 1. Proposal | Propose a study via the **[Web Submission Portal](Studies/submit.html)** | Review scope and fit |
| 2. Approval | Wait for a GitHub issue comment from maintainers | Label approved proposals |
| 3. Submit | Paste your markdown draft into the Web Portal | Review content and merge |

The public catalog at [analyticmadhyasthdarshan.org](https://analyticmadhyasthdarshan.org) links to this workflow from **How to contribute**.


---

## Step 1 — Propose a study

Open the [**Web Submission Portal**](Studies/submit.html) and fill out the **Propose a Study** form. Include:

- **Proposed title** — becomes the study name; the file slug is derived from it (e.g. `The Ontology of Coexistence` → `The-Ontology-of-Coexistence`).
- **Category** — topical area (Ontology, Epistemology, Ethics, etc.) or formal focus.
- **One-line description** — catalog summary shown on the studies page.
- **Study summary** — the question, primary texts, and scope you plan to cover.

A good proposal states a clear analytic question, names the Madhyasth Darshan texts you will use, and explains why the topic fits the collection. Comparison with Advaita Vedanta, modern philosophy, or science is welcome when relevant.

---

## Step 2 — Wait for approval

Maintainers review proposals for overlap, scope, and alignment with [Studies/README.md](Studies/README.md). You will be notified once it is approved. If changes are needed, maintainers will reach out.

---

## Step 3 — Submit a draft

Once approved, return to the [**Web Submission Portal**](Studies/submit.html) and use the **Submit a Draft** form.

1. Enter your study slug and author name.
2. Enter the approved **proposal issue number** from GitHub.
3. Check the "new study" box.
4. Paste your full markdown content.
5. Submit the form.

The portal will automatically create a Pull Request on your behalf. CI verifies the format, runs `_add_study.py`, and commits the PDF and catalog updates.

### Update an existing study or change status

To update an existing study, use the same **Submit a Draft** form on the portal but uncheck the "new study" box. The portal will automatically open a pull request updating your existing file.

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

Study management scripts: see [README.md](README.md#for-maintainers) and [Scripts/README.md](Scripts/README.md).

---

## License

Studies and original writing: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) — cite **AnalyticMadhyasthDarshan.org** and link to this repository.
