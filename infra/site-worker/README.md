# Complete site delivery

`src/index.js` serves one release manifest together with its static assets and
immutable generated PDFs. `release.js` is a development placeholder. The publisher
injects the complete manifest, the existing PDF serving module, and reference keys
as Worker modules; do not deploy this directory directly with the placeholder.

Build, canary, promotion, public-route migration, and rollback commands are
documented in [the CI runbook](../../.github/CI.md). Public migration is separately
gated by `SITE_RELEASES_ENABLED` and the cutover command. Until that migration,
GitHub Pages and the legacy PDF Worker remain the public hosts.

The Worker requires `ASSETS`, `GENERATED_PDFS`, and `REFERENCE_PDFS` bindings. All
file access is constrained by the release or approved reference inventory. Removal
drops canonical URLs; retained release URLs remain readable. There is no automatic
object deletion or retention expiry in this initial implementation.

Run `python Scripts/_test_site_release.py` from the repository root to exercise the
publisher failure paths and the real Worker against in-memory bindings.
