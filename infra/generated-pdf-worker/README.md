# Generated PDF Worker (`amd-generated-pdfs`)

This Worker serves generated study, research/technical-note, presentation, and
presenter-notes PDFs from the existing private Cloudflare R2 bucket while
preserving their public same-origin paths.

The zone route grammar cannot match a filename suffix. Production therefore
uses the two prefix routes `analyticmadhyasthdarshan.org/Studies/*` and
`analyticmadhyasthdarshan.org/Applications/*`. The Worker forwards every
non-PDF request unchanged to the GitHub Pages origin. PDF paths must be in the
generated inventory allowlist; an unpublished or unknown PDF returns a
controlled 404 and never invokes a renderer.

## Build and test

```powershell
python Scripts/_publish_generated_pdf_worker.py --sync-keys
python Scripts/_publish_generated_pdf_worker.py --check
python Scripts/_test_generated_pdf_worker.py
```

The deployment script resolves the R2 bucket through the existing S3 token and
injects it as the `GENERATED_PDFS` binding. The account-specific bucket name is
not committed.

## Staged deployment

```powershell
python Scripts/_publish_generated_pdf_worker.py --deploy-canary
python Scripts/_verify_generated_pdf_delivery.py --workers-dev --all --artifact-root <complete-build-root>
python Scripts/_publish_generated_pdf_worker.py --deploy-production
python Scripts/_publish_generated_pdf_worker.py --apply-routes
python Scripts/_verify_generated_pdf_delivery.py --public --all --artifact-root <complete-build-root>
```

`--deploy-canary` updates the isolated `amd-generated-pdfs-canary` script, never
the production script currently attached to the zone. Do not promote it until
the complete study, technical-note, slides, and presenter-notes inventory has
passed through that workers.dev host.

The production `--apply-routes` action is fail-closed: it refuses to attach the
two prefix routes unless every inventory object exists in R2 with PDF content
type and publisher checksum metadata, then purges every generated PDF URL so an
old GitHub Pages cache entry cannot mask the cutover.

Before production cutover, verify remote completeness independently with
`python Scripts/_publish_generated_pdf_worker.py --check-r2-coverage`. After
attaching the production routes, audit every object with
`python Scripts/_verify_generated_pdf_delivery.py --public --all ...`.

The exact-file `--apply-canary-routes` / `--public-canary` actions remain
available for an initial domain cutover, before broad production routes exist.

## Rollback

Before generated PDFs are removed from Git, route rollback is immediate and does
not delete R2 data:

```powershell
python Scripts/_publish_generated_pdf_worker.py --rollback-routes
```

This removes only routes that still point to `amd-generated-pdfs`. After the
repository cutover, do **not** remove the broad routes: GitHub Pages no longer
has fallback PDF copies. Recover by republishing the last verified objects and,
if needed, redeploying the last known-good production Worker.
