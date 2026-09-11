# Asset meanings and expected use

The shared theme was approved on September 11, 2026. This directory preserves
the approved assets and the earlier alternatives. Approval of the kit does not
mean it has been integrated into the website or existing presentation decks.

## Identity marks

| Basename | Represents | Expected use |
| --- | --- | --- |
| `jeevan` | Atma nucleus and four successive faculties: buddhi, citta, vritti, mun, from inside outward | Jeevan-related study identity, covers, chapter openings and relevant study navigation. Use the labelled composition for teaching the faculty names. |
| `akhand-samaj` | Four equal connected sections representing resolution, prosperity, fearlessness and coexistence; a golden atma-associated centre | Site identity, society-related studies, covers and chapter openings. The nucleus is not a fifth goal or central authority. |

The two colours in Akhand Samaj alternate for visual clarity, not rank. A
single-colour reproduction keeps the same whole but does not independently
identify its four sections: use text for the four goals when their identities
matter. Do not use either mark as proof of a philosophical or scientific claim.

## Topic symbols

These are visual mnemonics. Their labels carry the precise meaning; the pictures
do not define the philosophical terms by themselves.

| Basename | Visual / meaning | Expected use |
| --- | --- | --- |
| `resolution` | Eye with gold pupil; clarity and understanding | Resolution and knowledge sections; labelled epistemology navigation. Do not use for surveillance. |
| `prosperity` | Provision bowl and growing sprout; sufficient material provision | Prosperity, economics, production and right-use. Avoid implying unlimited accumulation. |
| `fearlessness` | Two equal people joined in mutual confidence | Fearlessness in society and trust in relationship. Security controls should use their own conventional symbol. |
| `coexistence` | Two intersecting circles; distinct wholes in relation | Coexistence, existence and relational subject headings. Not a diagram of satta's extent or a merger of entities. |
| `learning` | Open book; study and learning | Education, sanskar, references and the labelled Read action. |
| `wisdom` | Compass; discernment and orientation | Vivek, method and evaluation of direction; retain the source term where needed. |
| `science` | Laboratory flask; scientific inquiry | Science, technology and experimental method. Not a claim of empirical verification. |
| `justice` | Balanced scales; just assessment and relationship | Justice, ethics, value and governance sections. |
| `relationships` | Joined links; connection and mutual participation | Relationship values, social behaviour and mutual fulfilment. |
| `family` | Group of people; family and participation | Family studies; explicitly labelled organization topics where appropriate. |
| `ecology` | Growing leaves; ecological participation | Nature, cultivation, ecology and right-use. |
| `health` | Heart and pulse; bodily well-being | Health, body and restraint; not an emergency or medical-status indicator. |
| `work` | Wrench; practical work and making | Work, production and useful activity. Label broader karma discussions explicitly. |
| `model` | Connected nodes; formal relations | State-Dynamic Model, formal studies and systems diagrams. |
| `time` | Clock; duration and temporal inquiry | Nature of Time and duration references. |
| `language` | Speech panel with lines; expression and meaning | Language, definition, terminology and communication studies. |
| `art` | Pencil; artistic making | Aesthetics, expression and design topics. |
| `choice` | Branching path; selection and agency | Free will, choice and alternatives. Does not imply every branch is equally valid. |
| `continuity` | Paired circular arrows; continuity or recurrence | Death, continuity and rebirth topics, accompanied by the title. Avoid using it for status in these same placements. |

## Interface symbols

| Basename | Represents | Expected use |
| --- | --- | --- |
| `search` | Magnifying glass | Search control or search page link |
| `download` | Down arrow into tray | Download a named file; retain file type and size when known |
| `slides` | Presentation screen | Open teaching slides or a presentation artifact |
| `discussion` | Overlapping speech panels | Open a study discussion or comments |
| `audio` | Speaker with sound waves | Listen/read-aloud control, with an explicit accessible action name |
| `pause` | Two vertical bars | Pause active speech, playback or animation |
| `close` | Cross | Close a dismissible panel or dialog |
| `menu` | Three horizontal lines | Open a navigation or action menu |
| `external` | Arrow leaving a frame | Link to an external resource; preserve an ordinary link name |
| `saved` | Check mark | Confirm a completed save, only after persistence succeeds |
| `moon` | Crescent | Switch to dark mode; accessible label describes the action |
| `sun` | Sun and rays | Switch to light mode; accessible label describes the action |
| `notes` | Document with lines | Open personal notes or a notebook |

Pair symbols with visible labels where space permits. Icon-only buttons need
accessible names. Decorative icons beside equivalent text should be hidden from
assistive technology during integration. Disabled/loading state is not success.

## Variants, formats and sizes

Each of the 34 basenames has the following representations:

| File pattern | Expected use |
| --- | --- |
| `icons/<name>-light.svg` | Navy/gold on a light or ivory field; scalable browser artwork |
| `icons/<name>-dark.svg` | Ivory/pale gold on navy or another suitably dark field |
| `icons/<name>-mono.svg` | Single navy colour for monochrome reproduction |
| `png/<name>-light.png`, `-dark.png`, `-mono.png` | Matching transparent 512 × 512 exports for PowerPoint or raster-only applications |
| `icons/<identity>-compact.svg` | Heavier optical cut for small identities, preserving all rings/sections |
| `png/<identity>-compact.png` | 512 px raster master of the compact cut |
| `png/<identity>-16.png`, `-32.png`, `-48.png` | Actual-size compact samples for favicon/interface evaluation |
| `icons/sprite.svg` | Monochrome topic/interface symbols addressed by basename, inheriting `currentColor` |

SVGs use CSS custom properties for their palette. Use the PNG exports in slide
software that does not reliably support these properties. Never stretch marks
or crop out faculty rings. At 16 px, use the silhouette for recognition; it is
not an adequate teaching diagram for counting and naming the faculties.

## Images and explanatory compositions

| File | Represents | Expected use / text alternative |
| --- | --- | --- |
| `illustrations/community-courtyard.png` | Everyday study, useful work and growing food in a shared courtyard | Website hero, chapter illustration or editorial image. Alt: “People studying together, repairing a useful object and tending a garden.” AI-generated artwork, not a photograph or documented event. |
| `illustrations/inner-life.svg` | J1 with the five faculty names and their centre-to-outer-orbit order | Teaching image, reader explainer or Jeevan study artwork. Alt: “Jeevan: atma at the centre, followed outward by buddhi, citta, vritti and mun.” |
| `illustrations/shared-goals.svg` | Revised A1 with all four human goals named | Teaching image, reader explainer or society study artwork. Alt: “Akhand Samaj: resolution, prosperity, fearlessness and coexistence.” |

Keep the editorial image's people and activities visible when cropping for a
particular placement. Labels in explanatory compositions must remain legible.

## Motion and previews

| Asset | Meaning / expected use |
| --- | --- |
| `tokens.css` / `.amd-wait` with Jeevan SVG | Application activity while studies or reader content load; ring opacity varies around a steady nucleus |
| `tokens.css` / `.amd-wait` with Akhand Samaj SVG | Application activity while discussion or social content loads; sections brighten around a steady nucleus |
| `preview.html` | Interactive design specimen: both marks, icon vocabulary, website layout, slide compositions, motion and imagery |
| `preview-identity.png` | Static reference for approved identities, palette and optical variants |
| `preview-symbols.png` | Topic and interface icon reference sheet |
| `preview-website.png` | Website layout example; its actions are illustrative, not connected controls |
| `preview-slides.png` | Cover and human-goal slide style examples; not canonical presentation slides |
| `preview-motion.png` | Static snapshot of waiting-state examples; inspect HTML for motion |
| `preview-images.png` | Image-family reference sheet |
| `preview-mobile.png` | Full narrow-screen specimen for responsive visual review |
| `study-visuals.json` | Approved visual associations for the 27 catalog studies, to guide future integration; not an exhaustive philosophical classification |

Motion is an interface cue, not a depiction of faculty motion or a sequence of
spiritual achievement. Follow the reduced-motion, completion and error-handling
rules in [README.md](README.md#motion-contract).

## Preserved initial alternatives

`explorations/` retains all six initial options, their light/dark/mono SVGs and
the comparison HTML/PNG. It preserves the design history without replacing the
approved identity assets above.

| Option | Meaning / status |
| --- | --- |
| J1 | Concentric atom; selected and developed as `jeevan` |
| J2 | Concentric atom with faculty markers; archived alternative |
| J3 | Centre plus four nodes on one orbit; abstract faculty emblem, not a constitutional diagram |
| A1 | Four-part continuous bond without nucleus; selected, then revised with a golden nucleus as `akhand-samaj` |
| A2 | Four overlapping circles suggesting shared relationship; archived alternative |
| A3 | Rounded square with four goal joints; archived alternative |

Use the main `icons/` and `png/` files for new integration. Earlier exploration
files are static review snapshots and are not rebuilt by `build-theme.cjs`.
