# Axiology teaching presentation assets

The editable source is `../Axiology-Value-Theory-Madhyasth-Darshan.pptx`.
Its notes pane contains the presenter script and the source locators for every slide.
The 46-slide deck continues Start Here at stage four, Value, and leads into Living.
The main sequence includes saturation and unit activity, effort–motion–result,
chetana and chaitanya, the five faculties, six evaluative perspectives, dedication
between value classes, continuing evaluation, sixfold knowledge, humane conduct,
and the three dimensions of evidence.
Slides 44–46 provide optional terminology and reading references. Allow about
90–105 minutes with discussion, adjusting the pace to the audience.

Regenerate the slides and presenter notes PDFs from the repository root:

```powershell
python Scripts/_build_presentations.py --deck axiology --in-place
```

The PDFs are generated artifacts ignored by Git and published to Cloudflare R2
through the repository's protected-branch workflow. The PPTX and these image
inputs remain in Git. Edit the PPTX directly through the presentation workflow.

## Illustrations

Both images were created with the built-in image-generation tool for this deck.
They depict imagined illustrations, not documented events or identifiable people.
The original files are retained here for future edits and are embedded in the PPTX.

### `axiology-cover.png`

Final prompt:

> Use case: photorealistic-natural. Asset: opening slide background for a scholarly teaching presentation on Axiology, value theory in Madhyasth Darshan. Create a quiet, sophisticated editorial still life of a simple handmade terracotta cup holding clear water, a folded natural cotton cloth, and a modest bowl of grain on a dark wooden table. These ordinary useful things invite reflection on their value in sustaining life. Landscape 16:9 composition. Place all objects in the rightmost third with the cup clearly visible. The left two thirds must be very dark, near-solid deep indigo navy (#1E2447), generously empty for editable white title text added later. Soft warm directional light from the right, muted gold and earthy warm highlights, realistic material texture. Restrained philosophical book-cover quality, no mysticism or religious iconography. No writing, no text, no symbols, no borders, no watermark.

### `axiology-learning.png`

Final prompt:

> Use case: photorealistic-natural. Asset: educational case illustration for a scholarly PowerPoint on learning generosity through everyday participation. A candid, realistic scene in a modest contemporary Indian community kitchen: two adults of different generations stand side by side at a wooden work surface, one learning to portion a simple nutritious meal into several reusable steel lunch containers, the other gently demonstrating with a serving spoon. Their shared practical task is clear, expressions attentive and natural. Respectful, ordinary clothing, no religious insignia, no text, no staged charity or exaggerated poverty. Mid shot including faces and hands and containers, balanced anatomical hands, uncluttered warm neutral background with muted indigo details. Portrait 4:5 image for the right side of a slide. Soft daylight, restrained editorial photography, no arrows, no logos, no labels, no watermark. This is an illustrative imagined teaching case, not documentation of a real person or an event.
