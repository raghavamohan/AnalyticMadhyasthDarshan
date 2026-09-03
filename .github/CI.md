# Continuous integration — maintainer reference

How CI works in this repository: what runs, when it runs, what it is allowed to
write, what it does **not** check, and how to reproduce every check locally.

Study-authoring rules live in [AGENTS.md](../AGENTS.md) §1–§9. Contributor-facing
flow lives in [CONTRIBUTING.md](../CONTRIBUTING.md). **This file is the reference
for the pipeline itself.**

---

## 1. What runs, and when

| Workflow | Fires on | Job | Writes to the repo? |
|----------|----------|-----|---------------------|
| [Study PR](workflows/study-pr.yml) | `pull_request`: `synchronize`, `reopened`, `labeled` — **and only** with one of `new-study` / `study-update` / `status-change` | `study-pr` | **Yes** — pushes regenerated artifacts to the PR branch |
| [Studies index](workflows/studies-index-check.yml) | **every** `pull_request`; `push` to `master`/`main` | `verify` | No |
| [PDF pipeline smoke](workflows/pdf-pipeline-smoke.yml) | `pull_request` path-filtered on the PDF pipeline; `workflow_dispatch` | `reproducible` | No |
| [Presentation pipeline smoke](workflows/presentation-pipeline-smoke.yml) | `pull_request` path-filtered on presentation sources/tooling; `workflow_dispatch` | `libreoffice-production` | No |
| [Generated PDF publish](workflows/generated-pdf-publish.yml) | path-filtered `pull_request`; relevant `push` to `master`; `workflow_dispatch` | `markdown`, `presentations`, `publish-and-deploy` | No Git writes; protected-branch runs publish to R2 and deploy/audit the delivery Worker |
| [Proposal approved](workflows/proposal-approved.yml) | `issues: labeled` with `proposal-approved`; `workflow_dispatch` | `comment`, `bootstrap` | **Yes** — `bootstrap` opens and merges its own PR to `master` |
| [Portal notifications](workflows/portal-notify.yml) | `issues: labeled`; `pull_request_target: closed` | `notify` | No |
| [Pages deploy retry](workflows/pages-deploy-retry.yml) | `workflow_run` on *pages build and deployment* completing | `retry` | No (re-runs a run) |

Four jobs are gated by more than their trigger, which is the most common source of
"why didn't CI run?":

- **Study PR** is skipped unless the PR carries a study label. A `skipped`
  conclusion on this workflow is normal for non-study PRs.
- **PDF pipeline smoke** is path-filtered. A PR touching none of its paths
  produces *no run at all* — see
  [§5 Required checks](#5-required-checks-and-branch-protection) for why that
  matters for required checks.
- **Presentation pipeline smoke** is also path-filtered. It runs only when a
  PPTX source, presentation renderer/checker, dependency pin, or the workflow
  itself changes.
- **Generated PDF publish** builds affected Markdown PDFs on pull requests but
  receives no Cloudflare credentials there. Only a `master` push or manual run
  on `master` can start its presentation and R2 publication jobs.

**Studies index is the only workflow that reports on every pull request**, and is
therefore the only one that can serve as a required status check.

---

## 2. Workflow reference

### 2.1 Study PR — `study-pr.yml`

The main pipeline. Checks out the PR head, runs the router
[`Scripts/_ci_study_pr.py`](../Scripts/_ci_study_pr.py), and pushes whatever the
router regenerated back onto the branch.

**Trigger design is deliberate. Do not "fix" it without reading this:**

- `opened` is omitted. Creating a PR with its label already applied fires both
  `opened` and `labeled`; with `cancel-in-progress` one run is cancelled, and a
  required check keyed on the cancelled run strands the PR — the successful run
  has already pushed a `[skip ci]` commit, so no `synchronize` ever re-runs it.
- `edited` is omitted so body/checklist edits do not re-run Puppeteer. The router
  compensates by re-reading the **live** PR body from the API
  (`resolve_pr_body`), so a corrected `Study slug:` line takes effect on the next
  run without a new commit.

**The router dispatches on the single study label:**

| Label | Handler | Required PR body field |
|-------|---------|------------------------|
| `new-study` | `handle_new_study` | `Proposal issue: #N` (+ `Slug:`) |
| `study-update` | `handle_study_update` | `Study slug: <Slug>` |
| `status-change` | `handle_status_change` | `Study slug:` + `Target status:` |

Two or more study labels is a hard error (`active_pr_label`). The slug must be
**bare** — trailing parentheticals break catalog lookup; `normalize_pr_slug`
strips common ones as a backstop only.

`handle_study_update` also covers **renames** (one or more canonical
`<Slug>/<Slug>.md` renames → `_rename_study.py --metadata-only`) and
**removals** (every changed path under each deleted slug is a deletion, the
directory is gone, `proposal-registry.json` no longer lists it, and no Markdown
link still targets it). Moving a figure/companion file between directories is
not a rename. Rename CI passes the catalog display title to the metadata script
and has `issues: write`, so both the proposal issue body and title stay aligned.

`new-study` and `status-change` are single-purpose handlers: if their diff also
touches another study directory, the router rejects the PR and directs the
author to use `study-update`. A `study-update` may change, rename, or remove
multiple studies; all changed/deleted slugs are derived from the diff even when
only one primary slug is named in the PR body.

For every changed canonical markdown source, `_study_links.py` validates
cross-study section references in both directions. A heading renumber therefore
requires all inbound `§` references to be repaired in the same multi-study PR.
Rename/removal verification also rejects links to the retired slug, and the
index verifier rejects Start here entries whose slug no longer exists.

**PDF regeneration is conditional.** `pdf_regeneration_reason()` rebuilds only
when the study markdown changed, a figure inside that study's directory changed,
the PDF pipeline or its shared inputs (requirements, glossary, KaTeX assets,
Chrome launcher, CNAME) changed. Generated PDFs are absent from Git by design,
so a missing sibling PDF is not itself a rebuild reason. Companion-only edits
(decks, unrelated research notes) skip the catalog study render.

Every run ends in `verify_studies_index()`, which calls the *same*
`collect_index_errors()` the master-push check uses. Calling a hand-picked subset
here is what previously let a stale `Studies/index.html` pass a PR and turn
`master` red after the merge.

**Composite actions are referenced as `raghavamohan/AnalyticMadhyasthDarshan/...@master`,
not `./`.** The checkout deliberately targets the PR head, which for a fork is the
fork's tree; a relative `uses:` would fail with *"Can't find 'action.yml'"* on any
fork branch predating the action. Resolving from `master` also stops a study PR
from altering the toolchain its own required check runs on.

### 2.2 Studies index — `studies-index-check.yml`

The cheap, always-run guard. Runs with `node: 'false'` — no Node, no Chrome, no
PDF rendering — in about a minute with a warm pip cache:

| Step | Script | Guards |
|------|--------|--------|
| Verify catalog JSON and index shell | `_verify_studies_index.py` | `index.html` ↔ `README.md` ↔ `catalog-*.json` sync |
| Run the enforced test suites | `_run_test_suites.py` | Every discovered non-held `_test_*.py` suite (see §4) |
| Check agent rules and skills mirrors | `_sync_agent_rules.py --check` | `AGENTS.md` ↔ `.cursor/rules/*.mdc` ↔ skill mirrors |

`_run_test_suites.py` **discovers by denylist**: it runs every `Scripts/_test_*.py`
except the few named in its `HELD` map, each with a written reason, and prints
what it held on every run. That inversion is the point — only four of twenty-one
suites used to be listed here by name, and the other seventeen were enforced by
nothing, because adding a test file to `Scripts/` did not add it to CI. A new
suite is now enforced the moment it lands.

Among what it covers: `_test_commit_artifacts` exercises the only part of CI that
writes to a branch — both workflows using that action need a label to fire, and
`study-pr.yml` resolves it `@master`, so without this job it could reach `master`
having never run. `_test_generated_file_writes` reads the source rather than
writing files, because this Linux runner cannot reproduce the Windows CRLF bug it
guards.

It runs on **both** `pull_request` and `push` to the default branch, **unfiltered
on purpose**. It previously carried two verbatim copies of a fifteen-entry
`paths:` list — easy to half-edit, and already outgrown: the suites it now runs
read `infra/`, `.agents/skills/`, `.well-known/`, `AGENTS.md` and
`Studies/glossary.json`, none of which any filter listed. Running unconditionally
also makes this the one workflow that reports on every PR, which is what a
required status check needs.

### 2.3 PDF pipeline smoke — `pdf-pipeline-smoke.yml`

Covers the Node/npm/Chrome path that `studies-index-check.yml` deliberately skips
and `study-pr.yml` only reaches on a labelled study PR. Regenerates one Released
and one Draft study twice each and compares SHA-256 digests — the two statuses
pin dates by different mechanisms (in-place patch vs. pdf-lib rewrite), so
covering one of each is what makes the test meaningful.

Unlike `study-pr.yml`, this uses the **local** `./.github/actions/...` path on
purpose: it never checks out a fork, so a PR changing the action is tested
against its own version.

`workflow_dispatch` inputs reach the shell as environment variables, never spliced
into `run:` — a dispatch value interpolated directly into a run line is executed
as shell.

### 2.4 Presentation pipeline smoke — `presentation-pipeline-smoke.yml`

Runs on `windows-2025` because the production renderer and the decks' required
Calibri/Cambria fonts are Windows-specific. The workflow reads the exact
LibreOffice version, installer URL, and SHA-256 from
`Scripts/presentation-pipeline.json`; the installer script verifies the digest
before a silent MSI install and the build refuses a renderer-version mismatch.

Every manifested deck is built twice into separate temporary trees. Each build
must pass source layout checks, page count and geometry, blank-page detection,
PPTX text recall, speaker-note coverage, notes headers, and required-font checks.
`_verify_presentation_reproducible.py` then compares page geometry, extracted
text, and rendered-page hashes between the two builds while reporting raw PDF
byte equality separately. The first verified tree is retained as a 14-day
artifact. LibreOffice `26.2.3.2` was accepted after a 167-page comparison with a
fresh PowerPoint baseline preserved every page's text and showed no clipping or
reflow defect in the worst-ranked pages. This workflow never publishes to R2
and never modifies the checkout.

### 2.5 Generated PDF publish — `generated-pdf-publish.yml`

This is the protected-branch publication path for all generated PDFs under
`Studies/` and `Applications/`. Pull requests run only the `markdown` job: it
selects affected Markdown sources, regenerates them through the pinned pipeline,
and uploads a short-lived Actions artifact for inspection. Pull-request jobs do
not receive R2 or Cloudflare credentials and cannot publish.

On a relevant `master` push (or a manual dispatch on `master`), CI builds all 46
Markdown-derived PDFs on Linux and all 14 slides/notes PDFs with the pinned
LibreOffice production renderer on Windows. `publish-and-deploy` does not start
until both complete successfully. It merges the two verified artifact trees,
publishes all 60 repository-relative object keys to R2, checks complete R2
coverage, deploys the generated allowlist Worker, attaches the two guarded
prefix routes, purges the generated URLs, and audits every public PDF including
a range request and checksum comparison. Worker code first deploys to the
isolated `amd-generated-pdfs-canary` workers.dev host and must pass the complete
60-object audit before the production script is updated.

Publication is checksum-driven and idempotent: matching R2 objects are skipped.
The workflow never commits PDFs. The `.gitignore` rules cover only generated
PDFs immediately below `Studies/<Slug>/` and `Applications/<Slug>/`; PDFs under
`References/` remain Git-tracked source material.

### 2.6 Proposal approved — `proposal-approved.yml`

Two independent jobs on the `proposal-approved` label:

- `comment` — re-applies labels and posts the portal instructions. Talks only to
  the issues API, so it is unaffected by anything below.
- `bootstrap` — runs `_bootstrap_proposal_study.py`, commits the pre-catalog study
  directory to a `ci/bootstrap-proposal-<N>` branch, waits out any in-flight Pages
  deploy, then **opens a pull request and merges it.**

**It lands through a pull request, not a direct push, and that is forced.** The
default-branch ruleset requires a pull request and has no bypass actors; a bypass
for the GitHub Actions app is an *organization* feature, and this is a user-owned
repository, so the option does not exist. A direct push here is refused, not merely
discouraged. (It last pushed successfully on 2026-07-03, six days before that
ruleset was created.)

Two details are load-bearing:

- The merge uses `--merge`, **never `--squash`** — a squash would carry the regen
  commit's `[skip ci]` onto `master` and suppress the post-merge index check.
- A pull request opened with `GITHUB_TOKEN` does not trigger workflows, so no
  checks run on it. That is the same coverage the direct push had, and it is why
  the required `verify` check does not block this merge.

The Pages wait sits before the *merge*, not the branch push, because the merge is
what lands on `master` and starts a deploy. It exists because this site is ~300 MB
and stacked deploys fail during `syncing_files`.

`workflow_dispatch` takes an issue number, so the whole path can be exercised
without burning a real proposal. The `comment` job stays keyed on the label, so a
dispatch runs the bootstrap only.

**What a failure here does and does not cost.** The `comment` job is independent
and still posts the approval instructions, and `_bootstrap_proposal_study.py`
writes the resolved slug into the issue body via the API *before* it touches any
file — so the slug lock survives even a failed run. The portal falls back to
`parseSlugFromIssueBody()` when the registry has no row, and `handle_new_study`
verifies approval from the issue's **labels**, not the registry. Contributors can
still submit. What is lost is the pre-catalog stub, the registry row, and the row
reading *Ready for draft* rather than *Approved* on My Submissions.

### 2.7 Portal notifications — `portal-notify.yml`

Best-effort email to submission-portal contributors via the submissions worker.
No-ops cleanly when `PORTAL_NOTIFY_SECRET` is unset, when the PR is not a portal
PR, or when no `Portal-GitHub: @login` line is present. A failed notify is logged
as a **warning**, never a failure — notifications must not block a merge.

It uses `pull_request_target`, which runs in a privileged context with access to
secrets. It is safe here **only because it never checks out PR code** and only
reads the payload as data. Do not add a checkout step to this workflow.

### 2.8 Pages deploy retry — `pages-deploy-retry.yml`

Re-runs failed `pages-build-deployment` jobs once, on `master`, on attempt 1 only.
Guards against the site's intermittent `syncing_files` failure, which has no
actionable build error. It has never had to fire.

---

## 3. Shared composite actions

### `setup-study-env`

Python (+ optionally Node, npm deps and Puppeteer Chrome), with pip, npm and
Chrome all cached. Chrome is ~150 MB and is keyed on `Scripts/package-lock.json`,
so a Puppeteer bump invalidates it naturally.

Pass `node: 'false'` for verification-only jobs.

### `commit-artifacts`

Stages the given paths as `github-actions[bot]`, commits with `[skip ci]`
appended, and pushes. Exits cleanly when nothing changed.

That `[skip ci]` is why the default branch accepts **merge commits only** — see
§5. Squash and rebase both carry the token onto `master` and suppress the
post-merge check.

Set the optional **`branch`** input to commit onto a new branch and push that
instead of the checked-out branch — for a protected target that must be reached
through a pull request. The **`pushed`** output is `'true'` only when a commit
actually went out; gate any follow-up step on it rather than probing the remote
for the branch. `proposal-approved.yml` uses both.

**Fork behaviour is intentional and must not be softened.** GitHub gives a fork PR
a read-only `GITHUB_TOKEN` regardless of the workflow's `permissions:` block, so
the push cannot succeed. The action detects the fork, prints the exact commands to
run locally, and **fails**. It only reaches that point when CI actually
regenerated something — a fork PR whose artifacts are already correct produces no
staged diff and exits earlier. Passing it would let stale artifacts merge and turn
the default branch red.

---

## 4. What CI does and does not enforce

**Enforced on every labelled study PR:** catalog timestamp sync from
`**Edited on:**`, catalog/index/README sync, conditional PDF generation and its embedded
verifiers (SVG, diagrams, fenced code, outline, math — all invoked through
`_study_catalog.regenerate_pdf`), reference link checks when the bibliography
changed, rename and removal metadata, and the router's own unit tests.

**Enforced by `studies-index-check.yml` on every PR:** every non-held `_test_*.py`
suite discovered by `_run_test_suites.py`, plus `_verify_studies_index.py` and the
`_sync_agent_rules.py --check` mirror sync that CLAUDE.md makes mandatory.

**Enforced when presentation sources/tooling change:** manifest coverage for all
PPTX sources, source-deck fatal layout checks, exact production renderer and font
availability, complete slides/notes artifact verification, and two-build
rendered/text reproducibility. Candidate PDFs are uploaded for review but are
not published.

**Enforced before protected-branch PDF publication:** a complete 60-key inventory,
successful Markdown and presentation builds, per-artifact structural/provenance
verification, R2 checksum and metadata verification, Worker allowlist/route
deployment, cache purge, and a full same-origin public download audit. A failure
before publication leaves the previous R2 objects and Worker routes serving the
last successful build.

**Held back from CI on purpose** — these pass, but failing them would not mean
the same thing as failing the others, so the call belongs to a maintainer. Each is
named in `_run_test_suites.py`'s `HELD` map with its reason, and printed on every
run. Run them with `--all`.

| Held suite | Why |
|------------|-----|
| `_test_study_html_layout.py` | Pins the reader's exact CSS and toolbar structure (`max-width: 46rem;`, two toolbar rows, specific aria-labels). A deliberate restyle fails it, so enforcing means every design change updates an assertion in the same commit. |
| `_test_analyze_jeevan_pass_three.py` | Asserts frozen results — exactly 122 members, 16 tokens each, residual 34 — parsed from a tracked research note in `The-Epistemology-of-Coexistence`. Editing that study's note would fail CI repo-wide. Also ~18s, more than the whole enforced set. |
| `_test_analyze_jeevan_pass_four.py` | Chained onto pass three's committed CSVs and its 122-record invariant. |
| `_test_validate_jeevan_pass_five.py` | Chained onto pass four's coverage register. |

**Genuinely not covered anywhere:**

| Gap | Consequence |
|-----|-------------|
| Non-PDF `--live` endpoint checks | Other site/infra suites keep production checks behind explicit `--live` flags. Generated PDF delivery is the exception: every protected-branch publication audits all 60 public URLs. |
| Other `infra/` Cloudflare Workers | Generated-PDF Worker contract tests and production deployment are covered; other Workers still lack a shared build/lint/type-check/deploy gate. |
| Any lint / formatter | No ruff, flake8, mypy, eslint or markdownlint |

**Pinned toolchain.** `requirements.txt` pins every package exactly, direct and
transitive, to the set CI resolved in a run where `_verify_pdf_reproducible.py`
passed; `Scripts/package.json` pins Puppeteer and the exact Chrome build.
`requirements.txt` is in `pdf-pipeline-smoke.yml`'s path filter, so a version
change runs the reproducibility check. Bump a version and regenerate the affected
PDFs **in the same pull request** — never in separate commits.

---

## 5. Required checks and branch protection

`master` is protected by the repository ruleset **"Protect default branch"**:

- `pull_request` required (0 approving reviews); `allowed_merge_methods` is
  **`["merge"]` — merge commits only**, with squash and rebase also switched off
  at the repository level so neither button is offered
- no force-push, no deletion
- **`required_status_checks`: `verify`**, pinned to the GitHub Actions app
  (integration `15368`), non-strict
- **no bypass actors**

**The required context is `verify` — the bare job name.** `Studies index / verify`
is the string GitHub renders in the UI; the check-run name that branch rules match
is whatever the job reports, which for a job with no explicit `name:` is its id.
Confirm with the API rather than reading it off the page, because a context that
never matches leaves every pull request pending forever:

```bash
gh api repos/OWNER/REPO/commits/SHA/check-runs -q '.check_runs[].name'
```

`strict_required_status_checks_policy` is **false** on purpose: true would force
every PR to re-sync with `master` whenever it moves, which on a repository this
active is constant churn for no safety gain.

**Merge commits only, and this one is load-bearing — do not relax it.**
`commit-artifacts` appends `[skip ci]` to the artifacts CI regenerates on a
branch. Under a merge commit that is harmless: the merge commit's own message is
what lands on `master`, so the post-merge `Studies index` run still fires. Both
other methods carry the token onto `master` instead —

- **squash** concatenates the branch's commit messages into the single commit that
  lands;
- **rebase** replays the branch's commits individually, and the regen commit is
  normally the last one CI pushes, so it becomes `master`'s tip.

Either way GitHub sees `[skip ci]` in the head commit message and skips the very
check that exists to catch post-merge drift. Both are disallowed in the ruleset
*and* switched off at the repository level, so the buttons are not offered rather
than failing late.

> **The token is matched anywhere in a commit message, including the body, and
> including when you are only talking about it.** The commit that introduced this
> section quoted `[skip ci]` in its own message to explain the hazard — and GitHub
> skipped every workflow on the push, so the required `verify` check never
> reported and the pull request sat `BLOCKED` with zero checks. Write *"the
> CI-skip token"* in commit messages; keep the literal string in files, where it
> is inert. This is also the direct evidence that the mechanism works on the head
> commit's full message, which is what makes the squash and rebase cases above
> real rather than theoretical.

The other way to close this would be to stop appending `[skip ci]` at all. It is
arguably already redundant — a push made with `GITHUB_TOKEN` does not trigger
workflows, and that, rather than the token, is what actually stops the regen push
from re-running `study-pr.yml`. It becomes load-bearing again the moment anyone
swaps to a PAT or App token, which is why it is still there and why the merge
method is constrained instead.

**Why `verify` and not the study pipeline.** `studies-index-check.yml` is
unfiltered and reports on every pull request, so requiring it is safe.
`study-pr.yml` **must not** be required: it omits the `opened` trigger by design
(§2.1), so a PR opened without a study label produces *no run at all*, and a
required check would sit pending forever. This document's own pull request
demonstrated exactly that, sitting with zero checks reported.

`study-pr` therefore remains advisory. Merging a study PR with it red is possible
and is a maintainer's judgement, not a gate — which is why the local verification
in AGENTS.md §7 step 3 is the real check on study work.

---

## 6. Known gaps and hazards

Ordered by how likely they are to bite. None of these are fixed by this document.

**1 — Fork PRs diff against the fork's base branch.**
`study-pr.yml` checks out the fork, so `origin` is the fork; `git fetch origin
<base>` then fetches the *fork's* copy. When a contributor's fork is out of sync,
`origin/master...HEAD` can resolve a different merge base than upstream would, and
the router sees a wider changed-path set than the PR really contains. Harmless
when the fork is current. Fix by fetching the base from the upstream URL
explicitly.

**2 — `github-script` upgrades are not validated by CI.**
Actions used by `studies-index-check.yml` are exercised on every PR, and
`setup-study-env`'s Node/Chrome path by `pdf-pipeline-smoke.yml`. But
`github-script` appears only in `portal-notify.yml` and `proposal-approved.yml`,
neither of which runs on a pull request — so a version bump or script edit there
reaches `master` untested and first executes against a real proposal or a real
merge. Read the release notes and re-read the scripts by hand; `workflow_dispatch`
on `proposal-approved.yml` can exercise its two.

**3 — Nothing pins the Python interpreter's patch level.**
`setup-study-env` asks for `python-version: '3.12'`, which resolves to whatever
3.12 patch GitHub currently ships. Every *package* is
now pinned exactly (§4), so this is the last floating input to a pipeline built
around byte-reproducible output. Low risk — a CPython patch release changing
rendered PDF bytes would be surprising — but it is the remaining one, and pinning
it costs a two-character edit against slower access to security patches.

---

## 7. Reproducing CI locally

One-time setup:

```bash
pip install -r requirements.txt
cd Scripts
npm ci
npx puppeteer browsers install chrome
cd ..
```

Everything `Studies index` runs — fast, no Node, no Chrome, under ten seconds:

```bash
python Scripts/_verify_studies_index.py
```

```bash
python Scripts/_run_test_suites.py
```

```bash
python Scripts/_sync_agent_rules.py --check
```

To see what is enforced and what is held, without running anything:

```bash
python Scripts/_run_test_suites.py --list
```

Everything `PDF pipeline smoke` runs (rewrites the selected studies' ignored
`.pdf` files and tracked `.html` readers in place; use a clean worktree and
inspect any HTML diff after a diagnostic run):

```bash
python Scripts/_verify_pdf_reproducible.py --runs 2
```

Build the complete Markdown PDF inventory into a temporary artifact tree:

```bash
python Scripts/_build_markdown_pdfs.py --all --output-root tmp/generated-markdown-pdfs
```

The presentation smoke workflow uses its manifest-pinned LibreOffice production renderer.
On Windows, install/verify that renderer and build two complete output trees:

```powershell
Scripts/_install_presentation_renderer.ps1 -Profile libreoffice-production
python Scripts/_build_presentations.py --all --profile libreoffice-production --output-root tmp/presentation-first
python Scripts/_build_presentations.py --all --profile libreoffice-production --output-root tmp/presentation-second
python Scripts/_verify_presentation_reproducible.py --all --left-root tmp/presentation-first --right-root tmp/presentation-second
```

With R2/Cloudflare environment variables configured, reproduce the final
publication gates without changing Git:

```powershell
python Scripts/_publish_generated_pdfs.py --artifact-root tmp/generated-pdfs --all --dry-run
python Scripts/_publish_generated_pdf_worker.py --check
python Scripts/_publish_generated_pdf_worker.py --check-r2-coverage
python Scripts/_verify_generated_pdf_delivery.py --public --all --artifact-root tmp/generated-pdfs
```

For candidate acceptance, compare the verified candidate tree against a fresh
PowerPoint baseline and inspect the ranked page panels (reference, candidate,
enhanced difference):

```powershell
python Scripts/_compare_presentation_renderers.py --reference-root <powerpoint-build> --candidate-root <libreoffice-build> --output-dir tmp/renderer-review
```

The study-PR pipeline's own steps, per changed study — see [AGENTS.md](../AGENTS.md) §7:

```bash
python Scripts/_regenerate_pdf.py <Slug>
python Scripts/_check_references.py --study <Slug>
python Scripts/_quote_tool.py verify --study <Slug>
```

Every suite including the held ones (adds ~18s, mostly Jeevan pass three):

```bash
python Scripts/_run_test_suites.py --all
```

`_ci_study_pr.py` itself is not directly runnable outside Actions — it requires
`GITHUB_EVENT_PATH`, `GITHUB_TOKEN` and `GITHUB_REPOSITORY`. Test it through
`_test_ci_study_pr.py`, which fakes the event payload.

---

## 8. Changing CI

- **A new test suite** needs nothing wired up: name it `Scripts/_test_*.py` and
  `_run_test_suites.py` picks it up on the next run. To hold one back, add it to
  that script's `HELD` map **with a reason** — the reason is printed on every run,
  so a held suite stays visible rather than quietly absent.
- **A new non-test check** belongs in `studies-index-check.yml` if it is fast and
  needs no Node; otherwise weigh it against the Puppeteer cost in `study-pr.yml`.
  Neither trigger is path-filtered any more, so there is no filter list to update.
- **A new study PR type** needs one entry in `HANDLERS` in `_ci_study_pr.py`, one
  entry in `PR_LABELS`, a body template under `.github/PULL_REQUEST_TEMPLATE/`,
  and rows in the tables in AGENTS.md §7 and CONTRIBUTING.md. The `assert
  set(HANDLERS) == set(PR_LABELS)` catches a half-done job.
- **Changing a composite action** is exercised by `pdf-pipeline-smoke.yml` (local
  path) but *not* by `study-pr.yml` (pinned `@master`) — so an action change is
  live on `master` the moment it merges, having never run in the study pipeline.
  Cover it with a test in `_test_commit_artifacts.py` before merging.
- **Never** commit a `Studies/` change straight to the default branch; see
  AGENTS.md §7.
