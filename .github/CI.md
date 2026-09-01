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
| [Studies index](workflows/studies-index-check.yml) | `pull_request` and `push` to `master`/`main`, path-filtered | `verify` | No |
| [PDF pipeline smoke](workflows/pdf-pipeline-smoke.yml) | `pull_request` path-filtered on the PDF pipeline; `workflow_dispatch` | `reproducible` | No |
| [Proposal approved](workflows/proposal-approved.yml) | `issues: labeled` with `proposal-approved` | `comment`, `bootstrap` | **Yes** — `bootstrap` pushes directly to `master` |
| [Portal notifications](workflows/portal-notify.yml) | `issues: labeled`; `pull_request_target: closed` | `notify` | No |
| [Pages deploy retry](workflows/pages-deploy-retry.yml) | `workflow_run` on *pages build and deployment* completing | `retry` | No (re-runs a run) |

Two jobs are gated by more than their trigger, which is the most common source of
"why didn't CI run?":

- **Study PR** is skipped unless the PR carries a study label. A `skipped`
  conclusion on this workflow is normal for non-study PRs.
- **Studies index** and **PDF pipeline smoke** are path-filtered. A PR that
  touches none of their paths produces *no run at all* — see
  [§5 Required checks](#5-required-checks-and-branch-protection) for why that
  matters.

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

`handle_study_update` also covers **renames** (one slug deleted + one added →
`_rename_study.py --metadata-only`) and **removals** (every changed path under
the slug is a deletion, the directory is gone, and `proposal-registry.json` no
longer lists it).

**PDF regeneration is conditional.** `pdf_regeneration_reason()` rebuilds only
when the study markdown changed, a figure inside that study's directory changed,
the PDF pipeline itself changed, or the PDF is missing. Companion-only edits
(decks, research notes) skip the render.

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

The cheap, always-green guard. Runs with `node: 'false'` — no Node, no Chrome, no
PDF rendering — and executes five checks:

| Step | Script | Guards |
|------|--------|--------|
| Verify catalog JSON and index shell | `_verify_studies_index.py` | `index.html` ↔ `README.md` ↔ `catalog-*.json` sync |
| Check study PR router | `_test_ci_study_pr.py` | 34 unit tests over `_ci_study_pr.py` |
| Check PDF reproducibility patches | `_test_pdf_metadata.py` | 8 tests over the date-pinning logic |
| Check the commit-artifacts shell | `_test_commit_artifacts.py` | 4 tests over the push/skip/fork logic |
| Check generated-file writes emit LF | `_test_generated_file_writes.py` | Windows-only CRLF regression |

Two of these exist because of a coverage hole rather than a bug: `commit-artifacts`
is the only part of CI that writes to a branch, both workflows using it need a
label to fire, and `study-pr.yml` resolves it `@master` — so without this job the
action could reach `master` having never run.

It runs on **both** `pull_request` and `push` to the default branch. The two path
filter lists are duplicated verbatim; **edit both or the check silently stops
firing on one side.**

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

### 2.4 Proposal approved — `proposal-approved.yml`

Two independent jobs on the `proposal-approved` label:

- `comment` — re-applies labels and posts the portal instructions.
- `bootstrap` — runs `_bootstrap_proposal_study.py`, waits out any in-flight Pages
  deploy, then **pushes the pre-catalog study directory directly to `master`.**

The Pages wait exists because this site is ~300 MB and stacked deploys fail during
`syncing_files`. See [§6](#6-known-gaps-and-hazards) — this job's push path is
currently the least-exercised part of CI.

### 2.5 Portal notifications — `portal-notify.yml`

Best-effort email to submission-portal contributors via the submissions worker.
No-ops cleanly when `PORTAL_NOTIFY_SECRET` is unset, when the PR is not a portal
PR, or when no `Portal-GitHub: @login` line is present. A failed notify is logged
as a **warning**, never a failure — notifications must not block a merge.

It uses `pull_request_target`, which runs in a privileged context with access to
secrets. It is safe here **only because it never checks out PR code** and only
reads the payload as data. Do not add a checkout step to this workflow.

### 2.6 Pages deploy retry — `pages-deploy-retry.yml`

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
`**Edited on:**`, catalog/index/README sync, PDF regeneration and its embedded
verifiers (SVG, diagrams, fenced code, outline, math — all invoked through
`_study_catalog.regenerate_pdf`), reference link checks when the bibliography
changed, rename and removal metadata, and the router's own unit tests.

**Not enforced anywhere in CI:**

| Gap | Consequence |
|-----|-------------|
| `_sync_agent_rules.py --check` | `AGENTS.md` can drift from `.cursor/rules/*.mdc` and the skill mirrors with nothing to catch it, even though CLAUDE.md makes the sync mandatory |
| 17 of the 21 `Scripts/_test_*.py` suites | Site/infra tests (`_test_studies_api`, `_test_webmcp`, `_test_agent_card`, `_test_auth_md`, `_test_api_catalog`, `_test_dns_aid`, `_test_mcp_server_card`, `_test_web_bot_auth`), pipeline tests (`_test_convert_to_pdf_lists`, `_test_convert_to_pdf_math`, `_test_pdf_to_md`, `_test_glossary_tooltips`, `_test_agent_skills`) and the Jeevan analysis tests never run |
| `infra/` Cloudflare Workers | No build, lint, type-check or deploy check |
| Companion deck pipeline | `_check_deck_layout.py`, `_pptx_to_pdf.py`, `_build_deck_notes_pdf.py` are manual-only (see the `update-study-presentation` skill) |
| Python dependency versions | `requirements.txt` uses `>=` with no upper bound, so a new `markdown` or `pypdf` release changes CI behaviour with no repo change — unlike `Scripts/package.json`, which pins Puppeteer *and* the exact Chrome build |
| Any lint / formatter | No ruff, flake8, mypy, eslint or markdownlint |

All 17 unrun suites pass today, except `_test_sync_transcription_review_xlsx.py`,
which only works as a module (`python -m Scripts._test_sync_transcription_review_xlsx`).

---

## 5. Required checks and branch protection

**Current state — read this before assuming a red check blocks a merge.**

`master` is protected by the repository ruleset **"Protect default branch"**:

- `pull_request` required (0 approving reviews), merge/squash/rebase all allowed
- no force-push, no deletion
- **no `required_status_checks` rule**
- **no bypass actors**

Two consequences follow, and both are load-bearing:

1. **No CI check is required to merge.** A study PR can be merged with `study-pr`
   red, cancelled or skipped. `CONTRIBUTING.md` previously described this as
   configured; it is a recommendation, not the current state.
2. **`github-actions[bot]` has no bypass**, so the direct push to `master` in
   `proposal-approved.yml`'s `bootstrap` job is subject to the pull-request rule.

If required checks are enabled, the check names are `Study PR / study-pr` and
`Studies index / verify` — not the bare workflow names. Because both workflows are
gated (by label and by path filter respectively), marking either *required*
without also enabling **"Do not require status checks on creation"** or accounting
for skipped runs will block unrelated PRs that legitimately produce no run.

---

## 6. Known gaps and hazards

Ordered by how likely they are to bite. None of these are fixed by this document.

**1 — `proposal-approved.yml` bootstrap push is expected to fail.**
The ruleset requiring a pull request on `master` was created 2026-07-09. The last
successful `bootstrap` run was 2026-07-03; the only run since (2026-08-19) failed
earlier, at the Pages-wait step (a `gh run list --jq -r` misuse, since fixed), so
the push has not been attempted under the ruleset. Expect a rules violation on the
next approval. Fix by adding the GitHub Actions app as a bypass actor, or by
routing the bootstrap through a PR instead of a direct push.

**2 — `[skip ci]` plus squash-merge can skip the master-push check.**
`commit-artifacts` appends `[skip ci]` to the regen commit. That is correct on the
branch. But the ruleset allows **squash** merges, and a squash concatenates branch
commit messages into the commit that lands on `master` — carrying `[skip ci]` with
it and skipping the `Studies index` push check that exists to catch post-merge
drift. Prefer merge commits for study PRs, or drop squash from the ruleset's
allowed merge methods.

**3 — Fork PRs diff against the fork's base branch.**
`study-pr.yml` checks out the fork, so `origin` is the fork; `git fetch origin
<base>` then fetches the *fork's* copy. When a contributor's fork is out of sync,
`origin/master...HEAD` can resolve a different merge base than upstream would, and
the router sees a wider changed-path set than the PR really contains. Harmless
when the fork is current. Fix by fetching the base from the upstream URL
explicitly.

**4 — Every action is on a Node 20 major.**
`checkout@v4`, `setup-python@v5`, `setup-node@v4`, `cache@v4`, `github-script@v7`
all emit the Node 20 deprecation warning and are being forced onto Node 24. Bump
majors before the forced-run grace period ends.

**5 — The duplicated path filters in `studies-index-check.yml`** are the easiest
thing in this repository to half-edit. `Scripts/**.py` is in both lists because the
LF-write guard scans every script.

**6 — Unpinned Python dependencies** (see §4) make CI non-hermetic in a repository
whose entire PDF pipeline is built around byte-reproducible output.

---

## 7. Reproducing CI locally

One-time setup: `pip install -r requirements.txt`, then `cd Scripts; npm install`.

Everything `Studies index` runs — fast, no Node, no Chrome:

```bash
python Scripts/_verify_studies_index.py
python Scripts/_test_ci_study_pr.py
python Scripts/_test_pdf_metadata.py
python Scripts/_test_commit_artifacts.py
python Scripts/_test_generated_file_writes.py
```

Everything `PDF pipeline smoke` runs (rewrites the two studies' `.pdf`/`.html` in
place — `git checkout -- Studies/<Slug>` afterwards):

```bash
python Scripts/_verify_pdf_reproducible.py --runs 2
```

The study-PR pipeline's own steps, per changed study — see [AGENTS.md](../AGENTS.md) §7:

```bash
python Scripts/_regenerate_pdf.py <Slug>
python Scripts/_check_references.py --study <Slug>
python Scripts/_quote_tool.py verify --study <Slug>
```

The mandatory sync CI does not check:

```bash
python Scripts/_sync_agent_rules.py --check
```

Every test suite, including the ones CI never runs:

```bash
for f in Scripts/_test_*.py; do echo "== $f"; python "$f" || echo "FAILED"; done
```

`_ci_study_pr.py` itself is not directly runnable outside Actions — it requires
`GITHUB_EVENT_PATH`, `GITHUB_TOKEN` and `GITHUB_REPOSITORY`. Test it through
`_test_ci_study_pr.py`, which fakes the event payload.

---

## 8. Changing CI

- **A new check** belongs in `studies-index-check.yml` if it is fast and needs no
  Node; otherwise weigh it against the Puppeteer cost in `study-pr.yml`. Add its
  script to **both** path filter lists.
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
