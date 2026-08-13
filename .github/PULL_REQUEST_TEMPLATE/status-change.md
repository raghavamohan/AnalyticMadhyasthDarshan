## Status change

<!--
REQUIRED — bare catalog slug and target status, each on its own line.
Do NOT append notes on the Study slug: line.

PR READINESS — open this as a ready-for-review GitHub pull request by default.
`Target status: draft` changes only the study's lifecycle state; it does not
request GitHub's draft-PR state. Use a GitHub draft PR only when explicitly
requested for incomplete PR work.
-->
Study slug: <!-- e.g. The-Ontology-of-Coexistence -->
Target status: draft | released

### Reason

<!-- Brief reason for releasing or reverting to draft -->

### Checklist

- [ ] `Study slug:` is the **bare** catalog slug only (no notes on that line)
- [ ] `Target status:` is exactly `draft` or `released`
- [ ] Handled study status separately from PR readiness (ready for review by default)
- [ ] Did **not** hand-edit catalog status rows or PDF watermarks (CI runs `_set_study_status.py`)
- [ ] Applied label **`status-change`** to this pull request (exactly one study label)
