Choose a template when opening your pull request. **Do not** use this default chooser body as the PR description — open the matching template link so the required fields are present.

### Pull request readiness

Open study pull requests as **ready for review** by default. A study whose status
is `Draft` still uses a normal, ready-for-review GitHub pull request: `Draft`,
`Target status: draft`, and "submit draft" describe the study's catalog/PDF
lifecycle, not GitHub's draft-PR state. Use a GitHub draft PR only when it is
explicitly requested because the pull-request work itself is incomplete.

| Change | Template | Label | Required body field(s) |
|--------|----------|-------|-------------------------|
| Add a new study (after `proposal-approved`) | [new-study](?expand=1&template=new-study.md) | `new-study` | `Proposal issue: #N` and `Slug: <Slug>` |
| Edit, rename, or remove one or more studies (including companion files) | [study-update](?expand=1&template=study-update.md) | `study-update` | `Study slug: <primary Slug>` |
| Change draft ↔ released | [status-change](?expand=1&template=status-change.md) | `status-change` | `Study slug: <Slug>` and `Target status: draft` / `released` |

### Required field format (CI)

`Scripts/_ci_study_pr.py` reads these fields with a line-start regex. Put each on its **own line**, with a **bare catalog slug** (directory name under `Studies/` or `Applications/`).

`new-study` and `status-change` PRs are single-purpose. Use `study-update` for
intentional multi-study edits, including inbound link and section-reference repairs
required by a rename or heading change.

```text
Study slug: The-Ontology-of-Coexistence
```

**Do not** append notes on the same line. These fail catalog lookup:

```text
Study slug: The-Ontology-of-Coexistence (companion presentation deck)
Study slug: The-Ontology-of-Coexistence — pptx only
```

Put explanations in **Summary of changes**, not on the `Study slug:` / `Slug:` / `Target status:` lines.

### When to use a study label

- **Yes** — any change under `Studies/<Slug>/` or `Applications/<Slug>/` (study `.md`, figures, companion `.pptx` / research notes, etc.). Use the matching template and **exactly one** study label.
- **No** — changes only to `Scripts/`, `AGENTS.md`, `.agents/skills/`, `infra/`, `References/` tooling docs, etc. Open a normal PR **without** a study label and without `Study slug:`.

See [CONTRIBUTING.md](../CONTRIBUTING.md) (contributor flow) and [AGENTS.md](../AGENTS.md) §7 (agent / direct-repo checklist).
