# Analytic Madhyasth Darshan — agent orientation

Rigorous analytic studies of **Madhyasth Darshan** (Co-existentialism), the philosophy founded by Shri A. Nagraj. Each study reads the primary texts, states the darshan's claims, and compares them critically with physics and natural sciences, Advaita Vedanta, and modern Western philosophy where relevant.

**Standing rules:** [AGENTS.md](AGENTS.md) is the **source of truth** for all agent and maintainer workflows. Cursor loads the same content through `.cursor/rules/*.mdc` mirrors (one file per AGENTS.md section). After editing `AGENTS.md` (§1–§9) or any `.agents/skills/**/SKILL.md`, run `python Scripts/_sync_agent_rules.py` and `python Scripts/_sync_agent_rules.py --check` before finishing; commit sync output in the same commit as the canonical edit.

---

## Repository layout

| Path | Role |
|------|------|
| `Studies/<Slug>/<Slug>.md` | **Source of truth** for each topical or formal study; companion `.html` and `.pdf` are generated |
| `Studies/README.md`, `Studies/index.html`, `Studies/catalog-*.json` | Public catalog (must stay in sync) |
| `Applications/<Slug>/` | Applied studies — concrete instantiations of formal templates |
| `References/` | Local mirrors of cited sources; audit in `MANIFEST.md`; external-only works in `NOT-DOWNLOADED.md` |
| `Scripts/` | Study lifecycle, PDF pipeline, reference checks, catalog builders |
| `.agents/skills/` | Canonical agent skills (`.cursor/skills/` and `.opencode/skills/` mirror this) |
| `infra/` | Cloudflare Workers (submission portal, discussions) |

Companion files (research notes, figures) may live under `Studies/<Slug>/` without being catalog entries. Only `Studies/<Slug>/<Slug>.md` drives the catalog row and main PDF.

---

## AGENTS.md sections (follow all that apply)

| § | Topic | When it applies |
|---|--------|-----------------|
| §1 | `**Edited on:**`, catalog timestamps, PDF regeneration | Every topical study content edit |
| §2 | `Studies/index.html` ↔ `Studies/README.md` ↔ `catalog-*.json` sync | Catalog or index shell changes |
| §3 | Markdown → PDF pipeline (`Scripts/_regenerate_pdf.py` only) | Generating or refreshing study PDFs |
| §4 | Study prose style — scholarly essay, not AI scaffold | All topical studies |
| §5 | `## Standpoint and scope` section | All topical studies |
| §6 | Reference checks (`Scripts/_check_references.py`) | Bibliography or `References/` changes |
| §7 | Feature branch + labeled PR for any `Studies/` change | Always for study work |
| §8 | LF line endings everywhere | Always |
| §9 | PowerShell shell conventions (no `&&`/`||`, quote paths with spaces) | Always |

Contributor-facing flow: [CONTRIBUTING.md](CONTRIBUTING.md). Study format and tone: [Studies/README.md](Studies/README.md).

---

## Mandatory workflows (quick reference)

### Study edit

1. Work on a **feature branch**, never `master`/`main`.
2. Refresh `**Edited on:**` with real IST time: `Get-Date -Format "MMMM d, yyyy, h:mm tt"` then append ` IST`.
3. Update matching **Last updated on** in both `Studies/README.md` and `Studies/index.html` (abbreviated month in catalogs: `Jun`).
4. Regenerate PDF: `python Scripts/_regenerate_pdf.py <Slug>`.
5. If citations changed: `python Scripts/_check_references.py` (and `python Scripts/_quote_tool.py verify --study <Slug>` when quoting local sources).
6. Open a PR with exactly one label — `new-study`, `study-update`, or `status-change` — and the required body field from [`.github/PULL_REQUEST_TEMPLATE/`](.github/PULL_REQUEST_TEMPLATE/).

### References

- Local paths use `../References/...` in study markdown.
- When adding or replacing files under `References/`, update `References/README.md` and `References/MANIFEST.md`.
- Do not commit empty files or HTML saved as `.pdf`.

### PDF pipeline

Never use pandoc, VS Code export, or ad-hoc converters. One-time setup: `pip install -r requirements.txt`; `cd Scripts; npm install`.

---

## Agent skills

Skills in `.agents/skills/` orchestrate `Scripts/_*.py` and defer content/style rules to AGENTS.md:

`manage-studies` · `add-study` · `remove-study` · `rename-study` · `set-study-status` · `download-references` · `check-references` · `regenerate-study-pdf` · `update-study-presentation`

---

## References — primary Madhyasth Darshan texts

Stored under `References/Madhyasth-Darshan/`:

| Tag | Text | Translation |
|-----|------|-------------|
| **MVD** | *Madhyasth Darshan — Co-existentialism* | Rakesh Gupta |
| **SB** | *Samadhanatmak Bhautikvad* (Resolution Centred Materialism) | Rakesh Gupta |
| **JV** | *Jeevan Vidya: An Introduction* | Rakesh Gupta |
| **AVD** | *Adhyatmvad* (Realisation Centred Spiritualism) | Sanjeev Chopra (WIP) |
| **JVD** | *Janvad* (Behaviour Centred Public Discourse) | Sanjeev Chopra (WIP) |
| **KD** | *Manav Karm Darshan* (Hindi, v5) | Hindi source PDF; working English translations of section 3 in `KD-Karm-Darshan-English/` (not published translations) |
| **MD** | `MD-Mapping.xlsx` | Chapter/page mapping spreadsheet |

Other traditions and modern sources live under `References/Advaita-Vedanta/`, `Comparative-Philosophy/`, `Science/`, `Modern-Philosophy/`, and `Applied-Studies/`. See [References/README.md](References/README.md) and [References/MANIFEST.md](References/MANIFEST.md).

---

## Environment

- **OS / shell:** Windows with PowerShell — chain commands with `;`, not `&&`.
- **Line endings:** LF only (`.gitattributes` enforces `eol=lf`).
- **Site:** [analyticmadhyasthdarshan.org](https://analyticmadhyasthdarshan.org)
