---
name: generate-study-presentation
description: >-
  Generate a study PowerPoint (.pptx) from curated slides YAML using
  Scripts/_generate_study_presentation.py. Use when creating or updating
  presentation decks from study content; requires python-pptx and npm install
  in Scripts/ for SVG figure rasterization.
---

# Generate a study presentation

## Before you start

1. Presentation content lives in curated YAML — not auto-extracted from the study `.md`.
2. Ensure setup (repo root):

```powershell
pip install -r requirements.txt
cd Scripts
npm install
cd ..
```

`npm install` in `Scripts/` is **required** when slides reference SVG figures.
Puppeteer rasterizes SVGs to PNG for embedding in the `.pptx`.

## Default paths

For study slug `The-Ontology-of-Coexistence`:

| File | Path |
|------|------|
| Slides source | `Studies/<Slug>/<Slug>-ontology-slides.yaml` |
| Output deck | `Studies/<Slug>/<Slug>-ontology.pptx` |
| SVG figures | `Studies/<Slug>/*.svg` (referenced by `figure:` in YAML) |

## Generate

```powershell
python Scripts/_generate_study_presentation.py <Slug>
```

Custom paths:

```powershell
python Scripts/_generate_study_presentation.py <Slug> --slides path/to/slides.yaml --output path/to/output.pptx
```

## Slides YAML schema

```yaml
metadata:
  study: The-Ontology-of-Coexistence
  scope: "Section 1 — Madhyasth Darshan ontology only"

slides:
  - layout: title          # title slide
    title: "Deck title"
    subtitle: "Optional subtitle"
    speaker_notes: "Notes for presenter"

  - layout: content        # default content slide
    title: "Slide title"
    bullets:
      - "Bullet one"
      - "Bullet two"
    quote: "Optional block quote text"
    citation: "SB, p. 48"
    figure: 1-regulation-ladder.svg   # relative to study directory
    speaker_notes: "Fuller prose for live delivery"
```

- `layout`: `title` or `content` (default).
- `figure`: filename under `Studies/<Slug>/`; rasterized via `Scripts/_svg_to_png.js`.
- Keep bullets short — teaching slides, not full essay paragraphs.
- Speaker notes carry fuller exposition from the study.

## Editing workflow

1. Edit `Studies/<Slug>/<Slug>-ontology-slides.yaml`.
2. Run `python Scripts/_generate_study_presentation.py <Slug>`.
3. Open the `.pptx` in PowerPoint and verify bullets, quotes, figures, and notes.

Presentation artifacts do **not** update study `**Edited on:**` or catalog status —
they are companion files, not study body content.

## SVG figures

- Figures must be valid UTF-8 SVG (same rules as study PDF figures).
- Use numeric XML entities in `<text>` for §, ·, —, → if needed.
- Verify study SVGs: `python Scripts/_verify_study_svgs.py Studies/<Slug>/<Slug>.md`

## Completion check

- [ ] `Studies/<Slug>/<Slug>-ontology-slides.yaml` updated
- [ ] `Studies/<Slug>/<Slug>-ontology.pptx` regenerated
- [ ] All referenced `figure:` SVGs render in the deck
- [ ] Speaker notes present where intended
- [ ] Footer shows `AnalyticMadhyasthDarshan.org` and slide numbers

## Rules

- Do not auto-slice study markdown into slides — curated YAML is the source of truth.
- Do not hand-edit `.pptx` as source — edit YAML and regenerate.
- [AGENTS.md](../../AGENTS.md) §3 — SVG figure encoding (shared with PDF pipeline)
