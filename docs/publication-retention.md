# Publication retention, retirement and withdrawal

Normal publication is additive. Retain every published release, build receipt,
deployment receipt, path/MIME binding and every object reachable from them
indefinitely. This preserves saved readers, offline resource closures, citations
and complete rollback. The reference manifest remains the authority for reference
storage; reference objects and authoring files are outside garbage collection.

Unreferenced staging objects may be considered after **90 full days**. A candidate
must be content addressed under `site/objects/`, unreachable from **all** retained
release/build/asset records, unchanged in two inventories, and covered by a
download-verified independent backup containing the same bucket, key, size,
ETag and checksum. Missing, corrupt or ambiguous evidence stops planning.
Unknown keys, policy records, reference objects and receipt/index keys are retained.

`Scripts/_plan_r2_gc.py` is a read-only planner. It verifies the downloaded backup
archives, inventories the live bucket, validates retained records and reports
candidates. It has no delete option and is not called by normal publication.
An actual cleanup requires a separate reviewed exact-key plan and explicit
maintainer authorization, a fresh reachability/active-state check immediately
before deletion, and a recovery drill. Bucket locks are a separate decision under
R2-BACKUP; this policy does not apply or relax any lock.

## Retirement and corrections

Retirement removes a study from the next current catalog, API inventory and
canonical reader/PDF paths. Its retained release remains readable at the old
revision. Corrections produce new content-addressed bytes and a new coherent
release; old bytes are preserved. Neither operation is a hard withdrawal.

## Hard withdrawal

A rights, privacy or integrity withdrawal is a separate maintainer operation.
Record the reason, approved public paths and scope, including companion paths,
Markdown, PDFs and independently hashed assets. Remove current catalog/search/
offline discovery, then deploy a path denial **before** considering object removal.
The denial must cover canonical and query-bound historical URLs, direct Worker
and preview hosts, APIs/MCP content reads and retained asset bindings. Verify every
surface returns a withdrawn response and that unaffected paths still work.
Downloaded/offline copies cannot be revoked remotely; do not claim otherwise.

Retained bytes may remain private for recovery/audit when that is permitted by
the withdrawal decision. Reference withdrawal also updates the reviewed reference
manifest and public delivery mapping. Never infer redistribution rights from
storage location or delete a shared blob while an unaffected path still needs it.

Rollback must preserve the current withdrawal policy. A retained Worker version
that predates the denial is ineligible: restore the retained content through the
current withdrawal-aware runtime, or obtain a separately reviewed recovery plan.
The normal rollback command refuses to activate an old version when a hard
withdrawal is registered. A withdrawal is not considered complete until deployed
denial evidence has been recorded; source edits or garbage collection alone do
not establish withdrawal.
