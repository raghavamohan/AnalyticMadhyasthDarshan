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
python Scripts/_verify_generated_pdf_delivery.py --workers-dev --artifact-root <presentation-build-root> --artifact-root .
python Scripts/_publish_generated_pdf_worker.py --apply-canary-routes
python Scripts/_verify_generated_pdf_delivery.py --public-canary --artifact-root <presentation-build-root> --artifact-root .
python Scripts/_publish_generated_pdf_worker.py --rollback-routes
```

Do not attach the zone routes until representative study, technical-note,
slides, and presenter-notes objects have been uploaded and verified through the
workers.dev canary.

The canary action attaches four exact-file routes and purges only those URLs.
The production `--apply-routes` action is fail-closed: it refuses to attach the
two prefix routes unless every inventory object exists in R2 with PDF content
type and publisher checksum metadata, then purges every generated PDF URL so an
old GitHub Pages cache entry cannot mask the cutover.

## Rollback

Until repository PDFs are removed, rollback is immediate and does not delete
R2 data:

```powershell
python Scripts/_publish_generated_pdf_worker.py --rollback-routes
```

This removes only the two managed routes when they still point to
`amd-generated-pdfs`. GitHub Pages then resumes serving the repository copies.
