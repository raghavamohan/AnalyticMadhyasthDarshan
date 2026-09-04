# Cloudflare R2 reference migration: plan and checkpoint

**Updated:** September 4, 2026

**Checkpoint commit:** `8e915e8` on `master` (PR #372 merged)

**Current status:** The public cutover is implemented and live for every artifact
whose redistribution status has been approved, including all eight approved Advaita
Vedanta PDFs. The remaining large files stay in Git until their rights are resolved.
The two active translation source PDFs and two generated KD review PDFs also remain
in Git by design. Git history has not been rewritten.

## Restart checkpoint

| Item | Current state |
|---|---|
| R2 bucket | Private `amd-reference-archive` |
| Delivery Worker | Existing `amd-generated-pdfs`, with a second R2 binding |
| Public route | `analyticmadhyasthdarshan.org/References/*` |
| Public R2 PDFs | 24 objects, 272.74 MiB |
| Private original HTML | 12 objects, 1.76 MiB |
| Removed from current Git tree | 35 uploaded payloads plus 1 generated HTML |
| Retained for rights review | 15 PDFs, 28.94 MiB |
| Retained active translation PDFs | KD and MSM sources plus 2 generated KD review PDFs, 81.60 MiB |
| External-only generated derivatives | 11 PDFs, 5.18 MiB |
| Generated on demand | 1 transcript HTML, 0.15 MiB |
| Manifest | `References/r2-artifacts.json`, 67 artifact records |
| Public verification | All 24 objects passed S3 checks and the full canary delivery audit |
| Fresh-clone proof | All 24 hydrated and checksum-verified without credentials |
| Next action | Complete rights review for the 15 retained PDFs; defer Git history cleanup until separately approved |

No secret values are recorded in this repository. The current S3 credential was
sufficient for create/probe/upload/verify work. The current Cloudflare API token
was sufficient to bind the bucket, deploy the Worker, and attach the route.

## Architecture and invariants

- Git remains the source of truth for Markdown, provenance, checksums, build tools,
  mappings, and editable translation work.
- Approved immutable PDFs live in R2 and retain their established public
  `/References/...` paths.
- The same private bucket separates public objects from private archival originals
  by prefix; another R2 bucket is not required for this phase.
- The Worker serves only exact manifest-listed public objects. All other
  `/References/*` requests pass through to GitHub Pages, which keeps retained files
  and repository control documents available.
- Original third-party HTML snapshots are private. Cleaned Markdown remains in Git.
  A derivative PDF is public only when the manifest records a redistribution basis.
- Generated study/application HTML links to other studies' `.html` readers. Source
  citations link to R2 PDFs, retained Git PDFs, or the canonical publisher page as
  dictated by the manifest.
- PDFs are never generated during an HTTP request. CI generates and verifies them,
  then publishes immutable outputs.
- KD and MSM are the two active translation exceptions. Their Hindi source PDFs and
  editable workspaces remain in Git. The generated KD English and interleaved
  Hindi-English review PDFs also remain in Git while that translation is active;
  all four PDFs are explicitly recorded in the artifact manifest.

## Follow-up register

| Follow-up | Status | Completion condition |
|---|---|---|
| Rights review for 15 retained third-party PDFs | Open | Each artifact has an authoritative source and explicit redistribution basis, then moves to R2; otherwise its citation moves to a canonical external URL |
| KD and MSM translation exceptions | Ongoing | Keep their two source PDFs and the two generated KD review PDFs in Git until the active translation workflow no longer requires them |
| R2 deletion protection and independent backup | Open hardening | Choose a retention policy, verify backup recovery, and apply a bucket lock only after confirming it will not block legitimate corrections |
| Git history cleanup | Deferred by owner on September 4, 2026 | Schedule a separate maintenance window with backup tags, branch freeze, force-push coordination, and collaborator re-clones |

The history item is deliberately not part of routine migration work. Removing payloads
from the current tree prevents future binary growth, but old blobs remain in existing
Git history and continue to affect clone/repository storage until a coordinated history
rewrite is performed.

## Rights boundary

### Public in R2

The 24 public objects comprise eight owner-approved Advaita Vedanta PDFs, six
owner-approved Madhyasth Darshan PDFs, the 2010 Nagraj transcript PDF, openly licensed
MD-TOPOS, Limanowski, Melloni, Tufft, and Crockett papers, and public-domain Mach,
McTaggart, Russell, and Whitehead works.
Their exact URLs, object keys, hashes, sizes, licenses, and publication state are in
`r2-artifacts.json`.

### External only

Nine Stanford Encyclopedia of Philosophy entries link to SEP because its terms
allow linking but not electronic redistribution. Poorvam and Carroll also link to
their canonical pages pending a clear redistribution grant. Their cleaned Markdown
is retained for review/build reproducibility; their generated PDFs are not served.

### Retained in Git pending review

The following 15 PDFs are deliberately excluded from the R2 public allowlist:

- Comparative philosophy: Bhattacharya and Vivekananda's *Practical Vedanta*.
- Modern philosophy: Frankish and Hashemi.
- Science: Arnold, Ashtekar–Singh, Baehni, Chalmers, Feynman, Friston, Guth,
  Kotiuga–Lahtinen, Nagel, Strawson, and Terekhovich.

These files remain publicly reachable through the existing GitHub Pages origin.
Moving bytes to private R2 would not itself grant redistribution permission, while
removing them now would break citations. Resolve each license/source record before
changing its manifest storage policy.

## Completed phases

### Phase 0 — Protect active translation work

Complete. KD and MSM source PDFs, workspaces, `MD-Mapping.xlsx`, and mapping sources
remain in Git.

### Phase 1 — Inventory, provenance, rights, and checksums

Complete for the current boundary. `r2-artifacts.json` records all 67 artifacts and
distinguishes public R2, private original, Git-retained, external-only, and generated
states. This includes both generated KD working-review PDFs. Rights review remains
intentionally open only for the 15 listed third-party PDFs.

### Phase 2 — Resolver and credential-free hydration

Complete. The common resolver uses an approved tracked file or the ignored,
SHA-verified cache. `python Scripts/_hydrate_references.py --all-public` hydrates all
public objects without Cloudflare credentials. Audit, integrity, quote, and PDF tools
use the resolver.

### Phase 3 — Normalize archived HTML

Complete. Twelve snapshots were normalized to reviewable Markdown and deterministically
renderable PDFs. Original HTML was uploaded only to the private archive prefix. Only
the public-domain McTaggart derivative is in the public R2 allowlist; the other eleven
link to their canonical publishers.

For normalized derivatives, the cleaned Markdown and embedded fonts determine the
content, while Chromium's PDF container encoding still varies by host operating system.
Verification therefore pins page count and extracted-text digest across platforms;
Linux CI produces the canonical bytes published to R2. Existing source PDFs remain
subject to exact byte and SHA-256 checks.

### Phase 4 — Storage and delivery

Complete for routing and delivery. The existing Worker now has separate generated-PDF
and reference bucket bindings. The reference route, allowlist, pass-through behavior,
GET/HEAD/range/ETag/MIME handling, and canary deployment have been verified.

Deletion protection and an independent off-provider backup remain operational
hardening tasks. Do not add an expiry lifecycle to canonical objects. Apply a bucket
lock only after choosing a retention period, because an over-broad lock can prevent
legitimate corrections.

### Phase 5 — Upload and reconcile

Complete through the Advaita tranche. Thirty-six R2 objects were uploaded and
hash-verified: 24 public PDFs and 12 private HTML originals. The manifest records
their published state. Re-running the
publisher is idempotent.

### Phase 6 — Link cutover and regeneration

Complete. Migrated Markdown links were rewritten, affected canonical study timestamps
and catalogs were synchronized, and affected study/technical-note HTML/PDF artifacts
were regenerated through repository pipelines. Cross-study web navigation resolves to
HTML rather than Markdown or PDF. External-only sources resolve to canonical pages.

### Phase 7 — Remove uploaded payloads from the current Git tree

Complete for all currently approved artifacts, including the eight-file Advaita
tranche merged in PR #372. Parent commits and Git history remain rollback sources.
A clean cache hydration followed by `_check_references.py` passed for all 24 public
R2 PDFs.

## Remaining phases

### Phase 8 — Resolve retained PDFs

In progress. The site owner confirmed redistribution rights for all eight Advaita
Vedanta PDFs. They are recorded as approved, uploaded with their original checksums,
included in the production Worker allowlist, and removed from the current Git tree.
Fifteen PDFs remain under review.

For each artifact:

1. record an authoritative source URL and explicit license or permission;
2. mark it `r2-public` only when redistribution is supported;
3. upload and verify it before changing links or deleting the Git copy;
4. otherwise keep it in Git or replace the citation with a canonical external link;
5. repeat the fresh-cache integrity and public delivery suites.

This is the next functional phase. It does not require a new bucket.

### Phase 9 — Lean translation workspaces

The two immutable source PDFs and two generated KD review PDFs remain explicit active
translation exceptions. After the hydrator has been used in real KD/MSM translation
work, consider moving immutable page images and generated workspace renderings to R2.
Retain editable Markdown, mappings, glossaries, and ledgers. Do not remove any of the
four retained PDFs until the user explicitly changes the exception or the active
translation workflow no longer needs them.

### Phase 10 — Optional Git history cleanup

Deferred by the owner on September 4, 2026. Removing files from the current tree
prevents future binary growth but does not shrink old clones or remove blobs already
stored in GitHub history. Before revisiting this phase, measure the remote impact and
remaining pack. Any `git filter-repo` operation requires a separately approved
maintenance event, backup tags, a branch freeze, force-push coordination, and
collaborator re-clones.

## Verification and resume commands

From the repository root:

```powershell
python Scripts/_reference_artifacts.py --check
python Scripts/_rewrite_manifest_reference_links.py --check
python Scripts/_build_reference_pdfs.py --all --output-root tmp/reference-delivery-build
python Scripts/_hydrate_references.py --all-public
python Scripts/_check_references.py
python Scripts/_audit_references.py
python Scripts/_verify_published_document_links.py
python Scripts/_verify_studies_index.py
python Scripts/_verify_reference_delivery.py
node Scripts/_test_generated_pdf_worker.mjs
```

The protected-branch workflow builds the same public reference inventory, publishes it
to R2, deploys a canary, verifies both generated study PDFs and references, promotes
the Worker, and performs a public audit.

## Rollback

- Before merge, restore deleted files from the branch's parent and revert the Worker
  route if a cutover defect is found.
- After merge, revert the migration commit; do not delete R2 objects during incident
  response.
- Keep R2 objects through at least one complete release/CI cycle.
- Use manifest checksums to distinguish a routing/configuration rollback from a
  content rollback.

## Merge gate

- Manifest and unit tests pass.
- Canary delivery checks pass for all 24 R2 PDFs; production delivery is audited by
  the protected-branch workflow after merge.
- A clean cache can hydrate and pass the full reference checker without secrets.
- No generated study HTML contains cross-study `.md`/`.pdf` navigation or a removed
  reference path.
- Catalogs and study timestamps match.
- CI workflow parses and its generated Worker allowlist matches the manifest.
- `git diff --check` is clean and no token or credential appears in the diff.
