# Contributing studies

Thank you for helping expand rigorous analytic work on Madhyasth Darshan. This repository uses a **two-stage flow** managed through **[My Submissions](Studies/submit.html)** on the Web Submission Portal: propose a study, wait for maintainer approval, then submit your draft. **GitHub sign-in** is required to propose, submit, update, or change release status. Reading studies on the site does not require an account.

Read [Studies/README.md](Studies/README.md) for study format, tone, and structure before you start. Agents and automation should follow **[AGENTS.md](AGENTS.md)** for Edited on, PDF pipeline, prose style, study-specific scope, and (§7) the branch/PR-label/template workflow described below.

**Quick start:** Open [My Submissions](Studies/submit.html) → sign in with GitHub → propose or update a study → track approval, CI, and pull requests on the same page.

---

## Overview

| Stage | What you do | What maintainers do |
|-------|-------------|---------------------|
| 1. Proposal | Propose via **[My Submissions](Studies/submit.html)** | Review scope and fit |
| 2. Approval | Wait for **Preparing workspace** to become **Ready for draft** | Label approved proposals; CI registers and verifies **pre-catalog** metadata, then lists it on the index as **Planned** |
| 3. Submit draft | Paste full markdown; slug is **locked** from the proposal | Review the pull request; request changes or merge |
| 4. Catalog (Draft) | Track CI on **My Submissions** | Merge when required `verify` passes; publication makes the complete Draft live |
| 5. Release (optional) | Request **Released** when ready | Merge `status-change` PR when content is final |

Approved proposals get workspace metadata and a **Planned** catalog row, with no public reader, PDF or discussion page. Portal submissions stay in a GitHub draft PR during generation, then become ready for review with generated files and downloadable PDF artifacts. Required CI verifies that exact commit without rewriting it.

The public catalog at [analyticmadhyasthdarshan.org](https://analyticmadhyasthdarshan.org) links to this workflow from **Contribute** (hero buttons and footer on the studies page).

### Ways to contribute (ranked)

1. **Web Submission Portal (recommended)** — [Studies/submit.html](Studies/submit.html). Sign in with GitHub to propose, submit drafts, and track status under **My Submissions**. No local clone required.
2. **Study feedback issue** — [Suggest a correction](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-feedback.yml) for typos, terminology, or factual notes on an existing study. Also linked from each study page toolbar. No approval gate.
3. **GitHub issue template** — [Study proposal](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-proposal.yml) if you prefer filing directly on GitHub. Still wait for `proposal-approved`, then sign in on the portal to submit your draft.
4. **Fork and pull request (advanced)** — for contributors comfortable with Git. See the collapsible **Advanced** section in the maintainer approval comment, or [README.md](README.md#for-maintainers).

   From a fork you must **regenerate artifacts yourself and commit them**. On a branch in this repository CI regenerates the PDF, catalog, and index for you and pushes the result back; it cannot do that on a fork, because GitHub gives a pull request from a fork a read-only token. Run the [local development setup](#local-development-optional) once, then before pushing:

   ```bash
   python Scripts/_regenerate_pdf.py <Slug>
   python Scripts/_verify_studies_index.py
   ```

   If you skip this, the **Study PR** check fails and tells you the same thing. The Web Submission Portal avoids the whole step, which is why it is ranked first.


---

## Step 1 — Propose a study

Open the [**Web Submission Portal**](Studies/submit.html), **sign in with GitHub**, and fill out the **Propose a Study** form. Include:

- **Proposed title** — becomes the study name; the file slug is derived from it (e.g. `The Ontology of Coexistence` → `The-Ontology-of-Coexistence`). Keep titles short enough for a slug of **60 characters or fewer** (roughly eight words); the portal rejects longer slugs so paths work on Windows and in CI.
- **Category** — topical area (Ontology, Epistemology, Ethics, etc.) or formal focus.
- **One-line description** — catalog summary shown on the studies page.
- **Study summary** — the question, primary texts, and scope you plan to cover.

A good proposal states a clear analytic question, names the Madhyasth Darshan texts you will use, and explains why the topic fits the collection. Comparison with Advaita Vedanta, modern philosophy, or science is welcome when relevant.

---

## Step 2 — Wait for approval

Maintainers review proposals for overlap, scope, and alignment with [Studies/README.md](Studies/README.md). You will be notified once it is approved — GitHub notifies you on the issue, and you can opt in to email updates from the notification bar on **My Submissions**. If a proposal is not accepted, maintainers add `proposal-declined` and comment on the issue. The proposal issue stays **open** so later draft PRs can link to `Proposal issue: #N`.

When approved, My Submissions first shows **Preparing workspace**. Automation registers `.proposal-meta.json` and a Planned catalog row through a verified PR, then unlocks **Ready for draft**. The authenticated portal creates a starter from approved metadata on demand. Topical and Formal proposals expose no reader, PDF or discussion page until their first draft is published.

Closing an unpublished proposal issue makes its My Submissions card **Retired**
and locks first-draft submission for as long as the issue remains closed.
Closing the issue does not itself delete a Planned workspace from the
repository: if one exists, retire it through the normal `study-update` removal
pull request so its directory, catalog row, and proposal metadata are removed
together. A closed historical proposal for a study that is still Draft or
Released continues to resolve to that live study.

---

## Step 3 — Submit a draft

Once the card says **Ready for draft**, return to [**My Submissions**](Studies/submit.html) and click **Submit draft** on your proposal row. Approval alone does not unlock submission while the verified workspace is still being prepared.

1. Enter your author name — the name published on the study, which can differ from your GitHub handle (slug is pre-filled and locked from the approved proposal).
2. Enter the approved **proposal issue number** (pre-filled when opened from your row).
3. Click **Insert house-style template** for a section skeleton, then paste or write your full markdown content. A quick check warns if the draft is missing **References**.
4. Submit the form.

The portal opens one **new-study** pull request at a time per slug. If review requests changes, use **Revise draft** on the same card: the portal updates that pull request's existing branch and reruns CI instead of opening a competing PR.

### Minor corrections vs full revisions

- **Typos or citations on a published study** — [study feedback issue](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/issues/new?template=study-feedback.yml) (no approval gate).
- **Author revision** — expand **Files and updates** on the study's My Submissions card (`study-update` PR).
- **Maintainer edit** — direct PR on the default branch (portal optional).

### Update an existing study or change status

From **My Submissions**, each of your studies has one card for its proposal, review status, release status, category, and editable files. Use the **State** and **Category** filters to narrow a long list; multi-category studies appear under each of their categories. Expand **Manage files** on that card to edit the study document, replace a mapped technical/research note or presentation, add a new companion file, or request deletion of a file. The server checks that the signed-in account owns the study before accepting an update, deletion, or release-status request. Deleting the complete study requires typing its slug; every deletion opens a `study-update` pull request and takes effect only after maintainer approval and merge. The mapped file list is independent of historical proposal issues or pull requests.

- **Study Markdown (`.md`)** — choose a UTF-8 file, click **Load current content**, or work directly in the editor.
- **Technical or research note (`.md`)** — select an existing mapped note to load and edit it, or add a file named `Technical-Note-Topic.md` or `Research-Note-Topic.md`.
- **Study presentation (`.pptx`)** — select the mapped deck to replace and upload the PowerPoint file directly (up to 10 MB), or add a new one. New deck filenames are registered in the presentation build pipeline automatically; every slide should include speaker notes so its CI checks can pass.

Enter the study slug so the portal places the file in the matching `Studies/<Slug>/` or `Applications/<Slug>/` directory. Companion-file uploads use a `study-update` pull request and do not change the canonical study's `**Edited on:**` timestamp.

The durable inventory lives in `Studies/companion-artifacts.json`. It is generated from the catalog and repository files; after adding, removing, or renaming a note or presentation locally, run `python Scripts/_companion_artifacts.py`. Study PR CI performs the same synchronization before committing generated artifacts.

To change **Draft** ↔ **Released**, use **Change release status** on the same page, or click **Release study** / **Revert to draft** on a merged row. The portal opens a `status-change` pull request; preparation runs `_set_study_status.py` before review. Repeated same-status requests leave timestamps unchanged.

### Rename a study slug or title

The slug is **locked** when a proposal is approved. If the derived slug is too long for Windows paths or you need a shorter catalog name, rename **before or right after** the first draft merge using a maintainer-reviewed **`study-update`** pull request:

For local proposal-issue synchronization, set `GITHUB_TOKEN` and
`GITHUB_REPOSITORY` before the non-dry-run command. If GitHub authentication is
unavailable, pass `--skip-issue` and let post-merge reconciliation complete the
issue synchronization on the pull-request branch.

1. Run `python Scripts/_rename_study.py --from <Old-Slug> --to <New-Slug> --title "New display title" --skip-issue` on a feature branch. The script moves the directory and the canonical `<Slug>.md` / `.html` / `.pdf` files while preserving companion filenames, then syncs the catalog in place, proposal registry and metadata, and `References/` links. Publication reconciles the GitHub proposal issue after merge.
2. Update any Start here entry in `Scripts/_build_studies_index.py` and every Markdown link or `§` section reference that targets the old slug. Include all affected studies in the same pull request; CI validates both inbound and outbound cross-study references.
3. Set `Study slug: <New-Slug>` in the PR body and apply the **`study-update`** label. Required CI verifies the committed rename metadata and links without rewriting the branch.

Do **not** rename only the directory without updating the proposal issue and registry; **My Submissions** keys studies by slug and will show duplicate rows if metadata drifts.

---

## Study pull requests (labels, templates, and CI)

Every change under `Studies/` or `Applications/` lands through a labeled pull request.
Preparation reads source paths and **body fields**. Labels organize reviews; required `verify` runs on every PR and cannot be skipped by omitting a label.

### Choose the right template and label

Open the matching template from [.github/pull_request_template.md](.github/pull_request_template.md)
(do **not** leave the chooser text as the PR body):

| Change | Template | Label | Required body field(s) |
|--------|----------|-------|-------------------------|
| First draft after `proposal-approved` | [new-study](.github/PULL_REQUEST_TEMPLATE/new-study.md) | `new-study` | `Proposal issue: #N` and `Slug: <Slug>` |
| Edit, rename, or remove one or more studies; or edit companion files (`.pptx`, research notes, figures) | [study-update](.github/PULL_REQUEST_TEMPLATE/study-update.md) | `study-update` | `Study slug: <primary Slug>` |
| Draft ↔ Released | [status-change](.github/PULL_REQUEST_TEMPLATE/status-change.md) | `status-change` | `Study slug: <Slug>` and `Target status: draft` or `released` |

Apply **exactly one** of those three labels. Changes that only touch `Scripts/`, `AGENTS.md`,
`infra/`, etc. are ordinary PRs — **no** study label and **no** `Study slug:` field.
`new-study` and `status-change` PRs are single-purpose. Use `study-update` when one
change intentionally touches multiple existing studies, such as repairing inbound
links after a slug or section-heading rename.

### Fill required fields correctly

Put each required field on its **own line**. The slug must be the **bare catalog directory name**
(the folder under `Studies/` or `Applications/`), with nothing else on that line:

```text
Study slug: The-Ontology-of-Coexistence
```

**Incorrect** (CI cannot look this up in the catalog):

```text
Study slug: The-Ontology-of-Coexistence (companion presentation deck, not the study markdown)
```

Put explanations under **Summary of changes**, not on the `Study slug:` / `Slug:` /
`Target status:` lines. Companion-only PRs still use `study-update` and a bare
`Study slug:`; mark Edited-on checklist items N/A when the study `.md` was not changed.

The Web Submission Portal writes these fields for you. Hand-authored or agent PRs must follow
the templates above. Full agent checklist: [AGENTS.md](AGENTS.md) §7.

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
2. **Approve** — add `proposal-approved` when ready (bot registers pre-catalog metadata and posts portal instructions).
3. **Decline** — add `proposal-declined` with a comment when scope does not fit.
4. **Review PRs** — content quality, citations, quote accuracy; use **Request changes** on GitHub when needed.
5. **Merge** when required `verify` passes. Confirm public deployment separately in My Submissions or the Publish site run.
6. **Release policy** — only merge `status-change` → `released` when the study is ready for public release without a Draft watermark.

**One aggregate check is required.** The `verify` context includes catalog/reader consistency, lifecycle timestamps, reference integrity, all enforced tests and applicable PDF/presentation builds. A failed applicable study check blocks merging. Fork and local contributors prepare generated files before requesting review.

GitHub-token preparation uses an explicit exact-SHA status bridge. Bootstrap still uses merge commits while its artifact action carries a CI-skip token; retain merge-only settings during migration. Public deployment follows the staged procedure in [.github/CI.md](.github/CI.md).

The full pipeline reference — every workflow, what it may write, what it does not check,
and how to reproduce each check locally — is **[.github/CI.md](.github/CI.md)**.

### Shared glossary (`Studies/glossary.json`)

Hindi and darshan-specific terms that recur across studies are registered in [Studies/glossary.json](Studies/glossary.json). The HTML reader shows inline tooltips from this file. When you introduce a term that will appear in multiple studies, add or update an entry there (run `python Scripts/_verify_glossary.py` locally). Study-local **Quick Glossary** tables remain for terms specific to one paper.

Before writing or changing a shared definition, check [MD-Mapping.xlsx](References/Madhyasth-Darshan/MD-Mapping.xlsx). When the term has a corresponding row, retain its established English mapping and derive the compact definition from that row's English definition, notes, and cited local source. When no row exists, use the primary or comparative works already stored under `References/`. Label tradition-specific meanings explicitly instead of silently applying one tradition's sense to another. Definitions must be plain text because the tooltip displays them literally rather than rendering Markdown.

---

## Local development (optional)

Contributors who clone the repository can preview PDFs locally without waiting for CI.
This is **required** if you contribute from a fork, where CI cannot regenerate
artifacts for you (see [Ways to contribute](#ways-to-contribute-ranked)):

```powershell
pip install -r requirements.txt
cd Scripts
npm ci
npx puppeteer browsers install chrome
cd ..

python Scripts\_regenerate_pdf.py <Slug>
```

Study management scripts are for **maintainers and local development** — see [README.md](README.md#for-maintainers) and [Scripts/README.md](Scripts/README.md). To submit a study without a clone, use the [Web Submission Portal](Studies/submit.html).

### When a contributor only has a PDF

The portal accepts **markdown only**. If someone sends a PDF (email, issue attachment, or direct handoff), maintainers convert it locally before opening a study PR:

```powershell
python Scripts/_add_study.py path/to/submission.pdf `
  --convert --slug <Slug> --title "Study title" `
  --category "..." --description "..." --tags "MVD, SB" --status draft
```

Or convert without registering in the catalog:

```powershell
python Scripts/_pdf_to_study_md.py path/to/submission.pdf --slug <Slug> --title "Study title"
```

Review the generated `Studies/<Slug>/<Slug>.md` — fix headings, tables, citations, study-specific assumptions and limits, and `## References` to house style (AGENTS.md §4–§5) — then regenerate the PDF and open a labeled pull request as usual. The shared comparative method lives in Our approach on the landing page. Conversion works best on text-native PDFs; scanned documents fail with a clear error. Run `python Scripts/_test_pdf_to_md.py` after changing the import scripts.

---

## License

Studies and original writing: [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) — cite **AnalyticMadhyasthDarshan.org** and link to this repository.
