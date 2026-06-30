# Contributing studies

Thank you for helping expand rigorous analytic work on Madhyasth Darshan. This repository uses a **two-stage flow** managed through **[My Submissions](Studies/submit.html)** on the Web Submission Portal: propose a study, wait for maintainer approval, then submit your draft. **GitHub sign-in** is required to propose, submit, update, or change release status. Reading studies on the site does not require an account.

Read [Studies/README.md](Studies/README.md) for study format, tone, and structure before you start. Agents and automation should follow **[AGENTS.md](AGENTS.md)** for Edited on, PDF pipeline, prose style, and Standpoint and scope.

**Quick start:** Open [My Submissions](Studies/submit.html) → sign in with GitHub → propose or update a study → track approval, CI, and pull requests on the same page.

---

## Overview

| Stage | What you do | What maintainers do |
|-------|-------------|---------------------|
| 1. Proposal | Propose via **[My Submissions](Studies/submit.html)** | Review scope and fit |
| 2. Approval | Wait for `proposal-approved` on your issue | Label approved proposals; CI bootstraps a **pre-catalog** stub and lists it on the index as **Planned** |
| 3. Submit draft | Paste full markdown; slug is **locked** from the proposal | Review the pull request; request changes or merge |
| 4. Catalog (Draft) | Track CI on **My Submissions** | Merge when `study-pr` passes — study appears on the index as **Draft** |
| 5. Release (optional) | Request **Released** when ready | Merge `status-change` PR when content is final |

Approved proposals get a proposal stub (`.md`, `.html`, `.pdf`) in the repository and appear on the public studies index as **Planned** until the first draft PR is merged. Pull requests (not issue attachments) carry the review artifacts; CI regenerates PDFs and updates catalogs.

The public catalog at [analyticmadhyasthdarshan.org](https://analyticmadhyasthdarshan.org) links to this workflow from **Contribute** (hero buttons and footer on the studies page).

### Ways to contribute (ranked)

1. **Web Submission Portal (recommended)** — [Studies/submit.html](Studies/submit.html). Sign in with GitHub to propose, submit drafts, and track status under **My Submissions**. No local clone required.
2. **Study feedback issue** — [Suggest a correction](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-feedback.yml) for typos, terminology, or factual notes on an existing study. Also linked from each study page toolbar. No approval gate.
3. **GitHub issue template** — [Study proposal](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-proposal.yml) if you prefer filing directly on GitHub. Still wait for `proposal-approved`, then sign in on the portal to submit your draft.
4. **Fork and pull request (advanced)** — for contributors comfortable with Git. See the collapsible **Advanced** section in the maintainer approval comment, or [README.md](README.md#for-maintainers).


---

## Step 1 — Propose a study

Open the [**Web Submission Portal**](Studies/submit.html), **sign in with GitHub**, and fill out the **Propose a Study** form. Include:

- **Proposed title** — becomes the study name; the file slug is derived from it (e.g. `The Ontology of Coexistence` → `The-Ontology-of-Coexistence`).
- **Category** — topical area (Ontology, Epistemology, Ethics, etc.) or formal focus.
- **One-line description** — catalog summary shown on the studies page.
- **Study summary** — the question, primary texts, and scope you plan to cover.

A good proposal states a clear analytic question, names the Madhyasth Darshan texts you will use, and explains why the topic fits the collection. Comparison with Advaita Vedanta, modern philosophy, or science is welcome when relevant.

---

## Step 2 — Wait for approval

Maintainers review proposals for overlap, scope, and alignment with [Studies/README.md](Studies/README.md). You will be notified once it is approved. If a proposal is not accepted, maintainers add `proposal-declined` and comment on the issue. The proposal issue stays **open** so later draft PRs can link to `Proposal issue: #N`.

When approved, automation creates `Studies/<Slug>/<Slug>.md` (proposal stub), `.proposal-meta.json`, HTML, and PDF on the default branch. The study slug is written to the issue as `### Slug` and locked for draft submission.

---

## Step 3 — Submit a draft

Once approved, return to [**My Submissions**](Studies/submit.html) and click **Submit draft** on your proposal row (or use the pre-filled link from the approval comment).

1. Enter your author name (slug is pre-filled and locked from the approved proposal).
2. Enter the approved **proposal issue number** (pre-filled when opened from your row).
3. Paste your full markdown content.
4. Submit the form.

The portal opens one **new-study** pull request at a time per slug. If a draft PR is already open, wait for review before submitting again.

### Minor corrections vs full revisions

- **Typos or citations on a published study** — [study feedback issue](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-feedback.yml) (no approval gate).
- **Author revision** — **Update a study** on My Submissions (`study-update` PR).
- **Maintainer edit** — direct PR on the default branch (portal optional).

### Update an existing study or change status

From **My Submissions**, use **Update a study** to open a study-update pull request (paste revised markdown for an existing slug).

To change **Draft** ↔ **Released**, use **Change release status** on the same page, or click **Release study** / **Revert to draft** on a merged row. The portal opens a `status-change` pull request; CI runs `_set_study_status.py` on the branch.

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
| `proposal-approved` | green | Approved proposals (issue stays open) |
| `proposal-declined` | red | Declined proposals |
| `new-study` | blue | PRs adding a study |
| `study-update` | yellow | PRs editing study content |
| `status-change` | purple | PRs changing draft/released |

---

## Maintainer duties

1. **Review proposals** — scope, overlap, fit with collection standards.
2. **Approve** — add `proposal-approved` when ready (bot bootstraps pre-catalog stub and posts portal instructions).
3. **Decline** — add `proposal-declined` with a comment when scope does not fit.
4. **Review PRs** — content quality, citations, quote accuracy; use **Request changes** on GitHub when needed.
5. **Merge** when the `study-pr` CI check passes.
6. **Release policy** — only merge `status-change` → `released` when the study is ready for public release without a Draft watermark.

Enable branch protection on `main` with the **`study-pr`** check required before merge (recommended).

### Shared glossary (`Studies/glossary.json`)

Hindi and darshan-specific terms that recur across studies are registered in [Studies/glossary.json](Studies/glossary.json). The HTML reader shows inline tooltips from this file. When you introduce a term that will appear in multiple studies, add or update an entry there (run `python Scripts/_verify_glossary.py` locally). Study-local **Quick Glossary** tables remain for terms specific to one paper.

---

## Local development (optional)

Contributors who clone the repository can preview PDFs locally without waiting for CI:

```powershell
pip install -r requirements.txt
cd Scripts
npm install
cd ..

python Scripts\_regenerate_pdf.py <Slug>
```

Study management scripts are for **maintainers and local development** — see [README.md](README.md#for-maintainers) and [Scripts/README.md](Scripts/README.md). To submit a study without a clone, use the [Web Submission Portal](Studies/submit.html).

---

## License

Studies and original writing: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) — cite **AnalyticMadhyasthDarshan.org** and link to this repository.
