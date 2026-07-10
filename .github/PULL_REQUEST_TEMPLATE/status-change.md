## Status change

<!--
REQUIRED — bare catalog slug and target status, each on its own line.
Do NOT append notes on the Study slug: line.
-->
Study slug: <!-- e.g. The-Ontology-of-Coexistence -->
Target status: draft | released

### Reason

<!-- Brief reason for releasing or reverting to draft -->

### Checklist

- [ ] `Study slug:` is the **bare** catalog slug only (no notes on that line)
- [ ] `Target status:` is exactly `draft` or `released`
- [ ] Did **not** hand-edit catalog status rows or PDF watermarks (CI runs `_set_study_status.py`)
- [ ] Applied label **`status-change`** to this pull request (exactly one study label)
