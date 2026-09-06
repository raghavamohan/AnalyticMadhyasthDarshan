# Contributor reliability

Phase 4 adds browser draft recovery, richer previews, source comparisons and
submission receipts to My Submissions. The public site remains static; submission
writes continue through the existing Cloudflare Worker and GitHub.

## Contributor workflow

- Sign in with GitHub for proposals and pull requests. Discussion email sign-in
  is separate. Proposals, submitted source and review conversations are public.
- Drafts save after a short pause, with an explicit saved/unsaved/error message.
  Each account, study, artifact filename and pull-request revision has its own
  workspace. **Start another proposal** creates an independent proposal draft.
- Open **Saved contributor drafts on this browser** to resume a workspace,
  restore a JSON backup, remove an individual draft or clear this account's
  drafts. Older single-key drafts require explicit assignment to the signed-in
  account; they are never silently attributed to somebody using a shared device.
- **Recovery options** restores the latest saved draft or the earlier recovery
  copy. A stale tab cannot overwrite a newer saved version. Download its unsaved
  text first, then recover the saved copy to continue.
- Draft JSON backups contain the current editor text, source baseline, filename,
  presentation bytes and any unresolved receipt. They contain no session,
  GitHub credential or Turnstile token. Keep these files private if the draft is
  private. Import is restricted to the account identified in the backup.
- **Compare with loaded source** shows the changed region and line counts.
  A version conflict requires downloading the draft, loading current source,
  recovering the earlier draft and reconciling the comparison before resubmitting.
  Recovery keeps the newly loaded baseline for that comparison. This is a source
  comparison, not an automatic merge tool.
- Preview renders headings, emphasis, lists, quotes, fenced code, tables,
  KaTeX mathematics and Mermaid diagrams. Images are described without fetching
  them and links do not navigate. The publication pipeline still applies
  metadata, glossary/citation enrichment and PDF pagination. Python-Markdown and
  markdown-it share tested common syntax; unusual Markdown can differ. Review
  the generated CI artifacts before approving publication.
- A submission's workflow state is shown separately from Draft/Released
  publication status. Cards state who acts next and display bounded reviewer
  feedback and failed-check summaries, with links to full reviews and logs.
  In-place portal revision continues to cover owned first-draft PRs; other PR
  branches can be edited on GitHub.

Browser storage is not encrypted and does not sync between devices. Another
person using the same browser profile can access it. Browser eviction or cleanup
can remove it, so downloadable backups remain necessary. IndexedDB keeps at most
100 contributor drafts and 64 MB including recovery copies. Markdown remains
limited to 2 MB and presentations to 10 MB by the submission API. Preview is
limited to 500,000 characters, 2,000 equations and 20 diagrams; oversized or
invalid previews leave the source available. Draft listings load metadata only,
without reading every presentation into memory.

## Submission receipts and deployment

`POST /api/propose`, `/api/submit` and `/api/revise` require a client-generated
UUIDv4 `operationId`. The browser persists it before sending. Read requests get
at most one network/gateway retry; contribution POSTs are never automatically
repeated. Existing authenticated origin, JSON and Turnstile checks remain.

The Worker binds `CONTRIBUTOR_OPERATIONS` to the `ContributorOperations`
Durable Object, using [SQLite-backed storage](https://developers.cloudflare.com/durable-objects/api/sqlite-storage-api/).
The `contributor-receipts-v1` migration
is included in `infra/worker/wrangler.toml`; the existing protected-branch
deployment provisions it. No new secret or manually created database is needed.
The deployment also synchronizes the existing security-header rule, adding only
the preview page to the frame allowlist and permitting embedded math fonts.
The existing Cloudflare token must have the zone-read/response-transform
permissions used by the repository’s security-header tool. Unchanged header
rules produce no write.
If the binding is unavailable, contribution writes return 503 before creating
anything on GitHub. Deploy the Worker and site through the normal merge workflow;
older open portal tabs must refresh to supply the new receipt and source fields.

One object per GitHub user serializes contribution attempts across devices.
An atomic storage transaction claims the operation and a content hash before
external writes. Completed attempts replay their original response. Different
content cannot reuse a receipt. Thirty new attempts per account per UTC hour
are allowed; checking or replaying existing receipts does not consume that quota.
Receipts retain only identifiers, hashes, timestamps and small result metadata,
not draft bodies or authentication tokens. Receipts are retained to prevent old
attempts from being replayed after an arbitrary expiry.

Before replacing existing Markdown, the Worker compares `sourceSha` with the
current GitHub blob. Revisions additionally use GitHub's `sha` update condition,
so a concurrent commit fails instead of being overwritten. Update branches start
from the checked base commit. Presentation uploads retain the existing ownership,
registry and file validation; binary merging is not provided.

`GET /api/operation?id=…` checks a receipt scoped to the signed-in account. An
interrupted write is reconciled using an exact `Portal-Operation` marker in the
GitHub issue/PR or a matching revision commit. A result can be recovered after CI
adds another commit. A recovered PR missing its workflow label identifies that
maintainer action explicitly. A negative GitHub search is never treated as proof
that an issue was not created, because search indexing can lag.

If a receipt has not reached the server, retry **the same receipt and unchanged
content**. A delayed original request cannot then create a duplicate. An
unresolved earlier operation blocks another operation from that account.
Interrupted branches are retained rather than deleted; their deterministic name
is `submission-<slug>-<operationId>` and is shown with unresolved results.

GitHub and Cloudflare do not share a transaction. A Worker crash during validation,
an accepted file update that never reaches PR creation, or an unconfirmed issue
creation can require maintainer investigation. The portal deliberately retains
the receipt and refuses another write in these cases. Inspect the indicated
branch, issue/PR marker and commit history before any administrative repair;
do not delete the receipt simply because a search is empty. There is no public
endpoint that clears uncertain receipts. This is conservative duplicate
prevention, not a claim of exactly-once delivery or automatic recovery from every
GitHub outage. Status-change and deletion request flows remain separate from
these three content-submission receipt routes.

## Verification and maintenance

Run `python Scripts/_test_contributor.py`, the normal enforced script suites,
and `npm test` plus `npx wrangler deploy --dry-run` in `infra/worker`. The route
fixtures use signed test sessions and mock upstream services; they never send
real proposals or pull requests. The discussions Worker's existing security
route check and bundle check also remain green.

For browser checks, run `python Scripts/_serve_contributor_fixture.py` and open
`http://127.0.0.1:8766/Studies/submit.html`. Its harness isolates the draft database
and replaces all API/Turnstile interactions. Select an account, delayed source,
or lost-response outcome using the fixture controls. The standalone
`Studies/portal/draft-tests.html` uses a fresh temporary database and exercises
real IndexedDB conflicts, recovery checkpoints, attachment bytes and cleanup.
These fixtures are never linked from the contributor UI.

Preview libraries are vendored with licenses, versions and SHA-256 checksums in
`Studies/portal/vendor/manifest.json`. markdown-it has its own pinned package
lock; KaTeX matches the PDF toolchain, and Mermaid uses the existing pinned
browser bundle. The opaque preview iframe has a restrictive CSP, sanitized
author HTML, trusted-only math/diagram rendering and no network fetch access.
WOFF2 math fonts are embedded in the preview stylesheet so rendering does not
depend on cross-origin font permissions.

After editing portal assets, run `python Scripts/_build_contributor_assets.py`.
Its `--check` form verifies content-derived asset URLs. Portal libraries load
only when Preview opens; Mermaid loads only for diagram drafts. Portal changes
do not change the PDF renderer or require study PDF regeneration.
