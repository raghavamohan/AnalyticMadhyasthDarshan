# Continuous integration — maintainer reference

The review gate checks an immutable commit. Preparation produces reviewable
files before review. Publication stages a complete website revision before it
can replace the live revision. Study-authoring rules remain in
[AGENTS.md](../AGENTS.md); contributor instructions are in
[CONTRIBUTING.md](../CONTRIBUTING.md).

## Workflows and ownership

| Workflow | Trigger | Responsibility | Writes |
|---|---|---|---|
| [Studies index](workflows/studies-index-check.yml) | Every PR, master/main push, explicit prepared-SHA dispatch | Required `verify` aggregate: metadata, generated files, tests, applicable document builds | Only final commit status for explicit bot dispatch |
| [Study check](workflows/study-pr.yml) | Reusable workflow called by the aggregate | Build affected Markdown PDFs and presentations; fail on generated-file drift | Temporary build outputs only |
| [Prepare study](workflows/prepare-study.yml) | Open/synchronize/reopen of same-repository portal draft PR | Run lifecycle generators and export declared changes | Artifact only; token is read-only |
| [Accept prepared study](workflows/accept-prepared-study.yml) | Successful preparation run | Validate payload and current PR head; commit prepared files; queue exact-SHA verification; mark ready | One non-force commit on the same PR branch |
| [Proposal approved](workflows/proposal-approved.yml) | Approval label or explicit issue dispatch | Create metadata and a Planned catalog row through a verified PR | Bootstrap branch, PR, issue instructions |
| [Publish site](workflows/publish-site.yml) | Every master push; explicit merged-SHA dispatch | Serialize publication and reconcile merged issue metadata | Publication services; no Git writes |
| [Generated PDF publish](workflows/generated-pdf-publish.yml) | Reusable publication workflow | Build/cache complete PDF families; stage and audit the complete site | R2 and Workers, only from master |
| [Submission portal Worker](workflows/submission-worker-deploy.yml) | Relevant PR/master paths | Test and bundle APIs; deploy only from master | API Workers |
| PDF/presentation smoke | Relevant tooling paths or manual dispatch | Additional reproducibility checks | Temporary outputs only |
| Portal notifications | Issue labels and closed PR metadata | Contributor notifications | No checkout of PR code |
| Pages deploy retry | Failed legacy Pages run | Transitional retry; disabled by `SITE_RELEASES_ENABLED=true` | Rerun only |

## Required review gate

Keep **`verify`**, with the GitHub Actions integration, as the required context.
It runs unconditionally and succeeds only when both `checks` and `study-check`
succeed. A failed, cancelled, or skipped dependency fails the aggregate.
Presentation work inside `study-check` may skip only when its source planner
finds no presentation inputs changed. Labels organize reviews and notifications;
they never switch validation off. Strict/up-to-date branch protection is recommended
so the verified upstream base remains relevant at merge.

`_verify_ci_context.py` checks out the exact PR head and fetches the upstream
repository's exact base SHA, including for forks. Explicit prepared-head runs
also require the live PR head to match the requested SHA. A moved ref fails.
Body edits trigger cheap validation of current intent; document selection remains
based on paths and source inputs.

The read-only lifecycle validator checks source/catalog timestamps and status,
first-draft approval, complete removals, and cross-study section references.
The index verifier checks catalog JSON, README, index bootstrap, Start here,
sitemap, LLM catalogs, search and offline manifests. The glossary check and agent
mirror check remain required. `_run_test_suites.py` discovers all `_test_*.py`
suites except the explicit, explained `HELD` entries; adding a suite adds it to CI.

Document builds use the repository's pinned renderers and existing SVG, math,
diagram, fenced-code, outline, layout and presentation verifiers. Review PDFs
are downloadable Actions artifacts. `_generated_artifacts.py --check-clean`
then rejects tracked or untracked generated drift. No validation job pushes a
repair, changes a timestamp, patches an issue, or receives publishing secrets.

## Preparing portal submissions

The portal opens a **GitHub draft PR** while generated files are incomplete.
This is separate from a study's Draft/Released status. Revising an existing PR
returns it to draft before committing source. Once preparation is accepted,
the PR becomes ready for review; the required gate still controls merging.
Local and fork contributors generate their files before opening a ready PR.

`_ci_study_pr.py` is the preparation router. It infers first draft, update,
deletion and status change from paths and body fields. It preserves the existing
single-study restrictions for first drafts/status changes and supports multi-study
updates. Same-status requests are true no-ops. Rename preparation uses
`--skip-issue`; `_reconcile_proposal_issues.py` updates issue titles/slugs from
merged metadata, independently of site publication.

Preparation runs with a read-only token, no saved checkout credential and no
Cloudflare secrets. Its payload is untrusted. The `workflow_run` consumer checks
the producer workflow, source SHA, same-repository open draft PR, upstream branch,
file count, decoded byte limit and output contract. It executes only default-branch
code, validates paths/symlinks, and rechecks the PR immediately before a normal
non-force push. A newer contributor commit makes acceptance fail safely.

The output contract includes all catalog fan-out: Studies JSON/README/index,
discussion/search/offline files, root sitemap/LLM files, feedback issue template,
companion registry and generated-PDF key module. Lifecycle source and metadata
updates and complete deletions are supported. Unexpected files fail before staging;
ignored PDFs are never committed. Bootstrap uses the same contract.

GitHub-token writes still require an explicit verification dispatch. The trusted
writer posts pending `verify` on its exact commit and dispatches the full aggregate
with `report_sha` and `pr_number`. Dispatch failure becomes a failed status. Review
jobs themselves have no status-writing token. Bootstrap uses the same exact-SHA
status, waits for success and merges using `--match-head-commit`.

## Proposal approval

Approval registers `.proposal-meta.json`, the registry and a Planned row. It creates
no public Markdown reader, HTML stub, PDF or discussion page. Existing historical
Markdown stubs remain authoring records; their HTML/discussion outputs are removed.
The authenticated portal can create a starter from approved metadata on demand.

`_publication_inventory.py` supplies shared public eligibility. Only Draft/Released
parents enter reader/PDF/search/site inventories. Sitemap and landing-page links
obey the same status rule. Links from published papers to Planned studies resolve
to their catalog cards. Publication validation rejects Planned reader files.

Bootstrap rechecks that the issue is open and approved, preserves existing author
inputs on retries, resumes its branch, and refuses a previously closed-unmerged PR.
It requires Actions PR creation to be enabled in repository settings. Where the
workflow token cannot read administrative settings, the PR-create endpoint remains
the authoritative policy check and failure explains the required setting.

There is no Pages wait. After merge, bootstrap explicitly dispatches publication
for the merge SHA because token-created merges do not guarantee another push run.
A retry after merge also requeues publication without rewriting the workspace.
Closed/declined issue #420 must not be used as a bootstrap test.

## Complete website releases

`_site_release.py` builds a disposable assets tree and `release.json`, binding the
source commit, actual file SHA-256/size, PDF source hashes, publication status and
output contract to one revision. The source checkout is never transformed in place.
Private metadata, tooling, Planned readers and ignored local files are excluded.

Own-site files are staged at `site/objects/<sha256>` in the generated-PDF bucket.
Release manifests live at `site/releases/<revision>.json`. Existing objects must
match their checksum and length; collisions fail. The manifest is uploaded only
after every object verifies. Partial uploads cannot change the active deployment.
References retain their separate rights/storage manifest and bucket. Large,
Git-retained references use bounded static-asset segments, never the generated-PDF
R2 bucket; the Worker streams them with range support.

The publisher uploads Workers Static Assets, deploys `amd-site-canary`, and audits
every listed URL (GET/checksum for documents and discovery; HEAD/size for other
assets). Only then can it upload/promote a version of `amd-site`. Worker code,
static assets and the embedded release manifest move as one deployment. Canonical
URLs require revalidation; compiled reader links, dynamic fetches and saved offline
bundles carry the release query `r=<revision>`. Older open pages can fetch retained
files from their own manifest while new navigation receives the current revision.

Publication is serialized and rechecks the active revision immediately before
promotion. An older/unrelated source commit cannot replace a newer release.
Different output bytes for an already-published source commit also fail: record
renderer changes in a new commit. Post-promotion failure restores the previous
Worker version. A deployment receipt supports explicit rollback:

```powershell
python Scripts/_publish_site_release.py --rollback <retained-revision>
```

Rollback requires the corresponding retained Cloudflare Worker version. The first
rollout deliberately has **no automatic garbage collection**: publication never
deletes immutable objects. Removal immediately drops canonical routes from the new
manifest; retained revision URLs remain available for rollback/offline continuity.
Review a retention/withdrawal policy before adding destructive maintenance.

`/.well-known/publication.json` exposes the active source SHA, release revision and
study statuses. The portal reads repository catalogs/registry from **one Git SHA
per request**, caches by SHA, and shows publication confirmation separately from
authoring readiness. An unavailable endpoint is unknown, never a claim of success.

## Caches and rendering cost

Complete Markdown, presentation and reference caches retain exact family checksums
and source/renderer fingerprints. Only protected-branch builds save caches. PRs do
not create trusted publication caches. Restored artifacts are verified against
their current sources before upload.

Within a cold Markdown family, each document has a separate sealed PDF cache keyed
by source, local figures, transitive rendering code, fonts, own status/description,
link-target inventory and runtime. Editing one paper can reuse unchanged papers.
The restored directory may use a prefix fallback; each PDF still needs its exact
document key and checksum, and full verification runs after assembly. Renderer
changes invalidate affected keys. Shared glossary and screen-only reader asset
bytes do not themselves invalidate PDFs. No generated output depends on the clock.

## Rollout and recovery

The code supports a staged migration. Until `SITE_RELEASES_ENABLED=true`, normal
publication retains the legacy PDF publisher and stages/audits the new canary.
The new Worker is not a claim that production has already switched.

1. Merge the preparation/verification changes and ensure Actions can create PRs.
   Require the existing `verify` context with strict branch protection. Keep merge
   commits enabled while bootstrap still uses the legacy skip-token action.
2. Let `Publish site` build a complete release and audit its canary. Resolve all
   failures. Record the manifest and current routes before migration.
3. Set `SITE_RELEASES_ENABLED=true` and dispatch `Publish site` on master. This
   disables legacy publishing/Pages retry and promotes the audited Worker without
   changing public routes. Stop legacy Pages automatic builds by changing its
   build source to GitHub Actions; retain the old deployment for migration recovery.
4. Rebuild the same release bundle from its exact source and verified PDF artifacts.
   Run `_cutover_site_release.py --release-root <bundle>` to audit the production
   workers.dev endpoint and review route ownership, then add `--apply`. The command
   installs the site route, removes legacy PDF/reference overrides, purges affected canonical
   URLs and audits the public hostname. Failure restores the changed route entries.
5. Confirm public revision, Read/Download status, ranges, API routing and an open old
   reader across the next deployment. Preserve release objects and prior versions.

Required existing credentials: Cloudflare API token/zone, generated R2 endpoint,
bucket and keys, plus the reference bucket variable. The Cloudflare token needs
Workers Scripts, Workers Routes and cache-purge permissions. The direct-assets API
uses its short-lived upload JWT, not an R2 credential.
See [Cloudflare direct uploads](https://developers.cloudflare.com/workers/static-assets/direct-upload/)
and [GitHub Actions permissions](https://docs.github.com/en/rest/actions/permissions).

## Local verification

```powershell
python Scripts/_verify_studies_index.py
python Scripts/_sync_glossary_html.py --check
python Scripts/_sync_agent_rules.py --check
python Scripts/_run_test_suites.py
python Scripts/_validate_study_change.py --base-ref origin/master
python Scripts/_build_markdown_pdfs.py --changed-since origin/master --output-root tmp/pdfs/review
python Scripts/_site_release.py --artifact-root tmp/pdfs/complete --output-root tmp/site-release-review
python Scripts/_site_release.py --output-root tmp/site-release-review --verify
```

After reader-asset changes, regenerate published HTML with `_convert_to_pdf.py`,
then rebuild search/offline/catalog outputs. These controls do not change study
content timestamps. After canonical Markdown edits, follow the full timestamp and
PDF rules in AGENTS.md. A second generator pass must produce no diff.

New regression suites cover output-contract deletions/forbidden writes, exact-head
acceptance, bootstrap recovery, deterministic packaging, path exclusion, failed
uploads, immutable collisions, historical revision reads, ranges, cache headers and
retirement. API fixtures check one repository snapshot and draft-before-revision
ordering. Smoke and end-to-end deployment checks complement these fixtures.
