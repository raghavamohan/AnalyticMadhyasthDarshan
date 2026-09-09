# Jeevan icon family

This directory holds the visual identity derived from the Madhyasth Darshan account of *jeevan*: a central **atma** nucleus, **four co-functioning faculties** — mun, vritti, chitta and buddhi — on a shared orbit, and **projection and reflection as one continuous cycle**. Projection is carried in the warm (gold / brown) arcs, reflection in the cool (blue) arcs; the two alternate around the orbit as a single loop. The faint concentric field, fading toward the edge rather than boxing the mark, represents saturation within *satta*.

The whole family is generated from one geometry, so every variant is the same mark restated in a different register.

## Akhand Samaj icon family

The companion Akhand Samaj family is the public mark of undivided society. A
central **atma** nucleus sits inside an **ordered rounded square**. The four
mid-side joints, clockwise from the top, are **resolution**, **prosperity**,
**fearlessness**, and **coexistence** — the human goals as they become evident
in living. The square distinguishes this family from the circular Jeevan cycle.

The four faculty bands of *jeevan* (buddhi, chitta, vritti, mun) are not drawn
here; they belong to the Jeevan family. The four orders of nature are a distinct
conceptual set and are not assigned to these joints.

Large placements use the full ordered square (cut C). Browser tabs and other
placements below about 48 px use a heavier cut of the same figure (cut D).

`artifact-themes.json` assigns icon families to website artifacts. Site generators
use primary assignments for visible identity marks; related assignments are reserved
for future thematic grouping and do not automatically decorate every related study.

**Site favicon.** The published website (studies index, study HTML, discussion pages,
and submission portal) uses the **Akhand Samaj** favicon set:
`akhand-samaj-favicon.ico` / `.svg` / `-16.png` / `-32.png` and
`akhand-samaj-apple-touch-icon.png`. Root copies `favicon.ico` and
`apple-touch-icon.png` cover browsers that request those well-known URLs.
Link tags are emitted by `Scripts/_common.py` → `favicon_link_tags()`.

## Files and intended use

| File | Use |
|---|---|
| `jeevan-badge.svg` / `.png` | Website identity tile, study covers, title slides, social/profile placement |
| `jeevan-symbol-light.svg` / `.png` | Header, footer, diagrams on light backgrounds |
| `jeevan-symbol-dark.svg` / `.png` | Header, footer, diagrams on dark backgrounds |
| `jeevan-watermark-blue.svg` / `.png` | Full-strength navy source for document automation |
| `jeevan-watermark-blue-10.png` | Ready-to-use 10% opacity PDF/PPT watermark |
| `jeevan-monochrome.svg` / `.png` | Grayscale printing and one-colour reproduction |
| `jeevan-reversed.svg` / `.png` | One-colour ivory mark on dark fields |
| `jeevan-favicon.svg` | Scalable browser icon and compact app mark (simplified) |
| `favicon-16.png`, `favicon-32.png`, `favicon-48.png`, `favicon.ico` | Browser favicon assets |
| `apple-touch-icon.png` | 180 px touch/home-screen icon (full mark, full-bleed) |
| `jeevan-icon-family-preview.png` | Visual reference sheet; not a production asset |

### Akhand Samaj files

| File | Use |
|---|---|
| `akhand-samaj-badge.svg` / `.png` | Website tile, artifact cover, title slide, or profile placement |
| `akhand-samaj-symbol-light.svg` / `.png` | Unframed symbol on light backgrounds |
| `akhand-samaj-symbol-dark.svg` / `.png` | Unframed symbol on dark backgrounds |
| `akhand-samaj-monochrome.svg` / `.png` | Grayscale printing and one-colour reproduction |
| `akhand-samaj-reversed.svg` / `.png` | One-colour ivory mark on dark fields |
| `akhand-samaj-watermark-blue.svg` / `.png` | Full-strength navy source for document automation |
| `akhand-samaj-watermark-blue-10.png` | Ready-to-use 10% opacity document watermark |
| `akhand-samaj-compact.svg` / `.png` | Simplified tile for placements around 48–96 px |
| `akhand-samaj-favicon.svg` / `.png` | Small-scale browser and interface mark (cut D of the ordered square) |
| `akhand-samaj-favicon-16.png`, `-32.png`, `-48.png`, `.ico` | Browser favicon assets |
| `akhand-samaj-app-icon.svg` / `.png` | Full-bleed app icon master and 1024 px export |
| `akhand-samaj-apple-touch-icon.png` | 180 px touch/home-screen icon |
| `akhand-samaj-icon-family-preview.png` | Visual reference sheet; not a production asset |

## Colour roles

| Role | On dark fields | On light fields |
|---|---|---|
| Atma nucleus | Warm gold `#D5A477` | Warm brown `#8B5E34` |
| Faculty nodes | Ivory `#F7F4EF` | Deep blue `#1A5276` |
| Projection arcs | Gold `#D5A477` | Brown `#8B5E34` |
| Reflection arcs | Light blue `#B8DAF3` | Deep blue `#1A5276` |
| Satta field / frame | Deep blue `#1A5276` | — |

Full palette: deep blue `#1A5276` · light blue `#B8DAF3` · warm gold `#D5A477` · warm brown `#8B5E34` · ivory `#F7F4EF` · charcoal `#2A241C`.

The Akhand Samaj joints distinguish the four goals with four related golden
tones. Dark fields use `#E8BD92`, `#D5A477`, `#C18A5A`, and `#A66E42`; light
fields use the deeper counterparts `#C58E5D`, `#B77B48`, `#A36A39`, and
`#8B5E34`. The progression is an identifying sequence, not a hierarchy among the
four goals.

## Minimum sizes and the small-scale fallback

- Full radial Jeevan symbol (four faculty nodes legible): 48 px digital or 14 mm print.
- Framed Jeevan badge: 72 px digital or 20 mm print.
- Full Akhand Samaj ordered square (cut C): 64 px digital or 16 mm print.
- Akhand Samaj compact tile (cut D): 48 px digital or 14 mm print.
- Below 48 px, use `akhand-samaj-favicon.svg` (cut D). At 16 px the four joints
  read as thickenings on the square rather than four countable colours; the
  silhouette is atma inside a rounded square.
- **Below 48 px**, the four Jeevan faculty nodes turn illegible, so `jeevan-favicon.svg`
  and the Jeevan raster favicons under `Assets/Icons/favicon-*.png` use a
  deliberately *simplified* mark — the two-tone projection/reflection loop and
  the atma nucleus, without the faculty nodes. The published *site* favicon is
  the Akhand Samaj set, not this Jeevan fallback.

For watermarks, place the unframed navy mark behind content at roughly 8–12% opacity (`jeevan-watermark-blue-10.png` is pre-set to 10%). Use the unframed mark, not the filled badge, so no rectangular field shows through at low opacity.

## Regenerating

The entire family is produced from a single build script, `build-icons.js` (Node + Puppeteer for raster, ImageMagick for `favicon.ico` and the 10% watermark). Install the repository's Node dependencies under `Scripts/` and install ImageMagick separately before rebuilding. Editing the geometry or palette in one place and re-running rebuilds every SVG, PNG, the ICO and the preview sheet in step:

```powershell
$env:NODE_PATH = "$PWD\Scripts\node_modules"; node Assets\Icons\build-icons.js Assets\Icons
```

Puppeteer comes from the PDF pipeline's pinned `Scripts/node_modules`; ImageMagick
is an additional icon-build prerequisite and is not installed by this repository.

Build the Akhand Samaj family separately. The script also copies `akhand-samaj-favicon.ico`
and `akhand-samaj-apple-touch-icon.png` to the repository root as `favicon.ico` and
`apple-touch-icon.png` for browsers that request those well-known URLs:

```powershell
$env:NODE_PATH = "$PWD\Scripts\node_modules"; node Assets\Icons\build-akhand-samaj-icons.js Assets\Icons
```
