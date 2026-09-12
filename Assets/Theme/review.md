# Review: icons, images and motion

Reviewed against local master `5d127b3d`, then developed on
`codex/shared-visual-theme`. This is a design review and a new shared asset kit;
it does not claim the new theme is deployed or the canonical decks are updated.

## Coverage and evidence

All eight decks in `Scripts/presentation-pipeline.json` were opened read-only
through PowerPoint and exported to slide images. All 192 slides were reviewed
as contact sheets. Selected icon-bearing slides were also inspected at full
size, including Ontology 18, Epistemology 6 and Undivided Society 15. This was
an iconography/style review, not a new substantive review of every slide claim
or a final layout gate for modified presentations.

The review also inspected `Assets/Icons`, `Assets/Social`, the local generated
Studies landing page in a browser, the index generator, discussion-page loading
states, reader controls and the portal sources. Observations concern the local
repository version; a separately deployed production revision was not verified.

## Deck-by-deck findings

| Deck / slides | Observed design | Recommended treatment |
| --- | --- | --- |
| Axiology / 25 | Cambria/Calibri; deep indigo `#1E2447`, muted gold `#9A6414`; photographic still-life cover; tables and prose dominate | Keep the cover's everyday material subject. Introduce the shared illustration style for future covers; add restrained topic symbols to section openings, not to each table cell. |
| State-Dynamic Model / 30 | Indigo title/section slides with concentric motifs; small ring marks beside titles; mostly native text, boxes and arrows | Adopt J1 on cover and chapter breaks. Use model/work/relationship symbols where they convey subject matter. Do not label every material unit with the Jeevan mark. |
| Undivided Society / 23 | Five coloured vertical bars on cover; blue, green, brown and purple section coding; scales, hand/heart, book, leaf and shield on slide 15 | Use revised A1 as identity. Preserve the existing five-part argument's labelled section distinctions. Use a common stroke style for topic icons. Fearlessness should read as confidence in relationship; keep a shield for security/protection where that is the intended subject. |
| Epistemology comparison / 12 | Concentric cover motifs; handshake/cycle/gear reused across knowledge, knower and validation, then across other conceptual triples | Replace ambiguous repeated pictograms with explicit subject symbols or plain labels. J1 must not imply that every compared tradition endorses the same account of the knower. |
| Epistemology / 36 | Same indigo/gold template; title ring motifs; repeated handshake/cycle/gear imagery, including knowledge/wisdom/science on slide 6 | Use a labelled eye for understanding, compass for discernment, flask for inquiry, with wording determining meaning. Keep body/Jeevan distinctions and authored faculty descriptions intact. |
| Ontology comparison / 18 | Same template; coloured comparison tables distinguish traditions; decorative nuclei/rings on the cover | Keep comparison colours and row labels. Restrict the Jeevan identity to the deck identity and relevant Madhyasth Darshan content, rather than using it as an undifferentiated symbol of all traditions. |
| Ontology / 28 | Navy/indigo blocks, gold accents and concentric motifs; slide 18 already contains the labelled centre plus four-ring faculty diagram | J1 is directly compatible with that established teaching diagram. Preserve the diagram's labels and source citation. Keep illustrations of satta/units distinct from the identity mark of Jeevan. |
| Why Humans Are Not Just Material / 20 | Same template; concentric headers and cover image; predominantly prose/cards and comparison tables | Adopt J1 for identity, use it on the Jeevan side of the body/Jeevan distinction, and retain explicit labels for physicalism and Advaita. Do not add decorative icons to every argument. |

All decks use Cambria and Calibri in their directly styled text. Their shared
typography is an asset to preserve. The larger inconsistency is the semantic
use and visual weight of pictograms, followed by the different blue/gold values.

## Website and waiting states

The website is predominantly typographic. It is not literally without icons:
the local page has a search symbol and sun/moon theme glyphs, and an Akhand Samaj
favicon is configured through `Scripts/_common.py`. However, the identity and
subject marks are largely absent from the visible header and study journey.
Social cards in `Assets/Social` are typographic as well.

The index generator's topic journey is already coherent: Human, Existence,
Knowledge, Value and Living. Map these to Jeevan, coexistence, resolution/eye,
justice and Akhand Samaj respectively. Retain words and stage numbers; icons
support recognition rather than replace navigation text.

Discussion pages have an explicit “Loading comments…” state in
`Scripts/_build_discussion_pages.py`, including existing busy-state handling.
Reader notes disable controls while loading in `Assets/reader/study-tools.js`.
These need a small consistent indicator beside the truthful status text.
The index's existing target-flash animation is navigation feedback, not a loader.
No coherent shared branded loader was found in the inspected code.

## Proposed common theme

1. **Identity:** J1 and A1 with gold centre; one geometry per family, plus an
   optical compact cut. No new symbolic meanings in decorative background rings.
2. **Topics:** nineteen line icons covering the four human goals and the main
   study domains. Same stroke widths, round joins and restrained gold accents.
3. **Interface:** thirteen familiar symbols for search, download, slides,
   discussion, audio, pause, close, menu, external links, saved state, dark/light
   mode and notes. Learning/open-book doubles as the labelled Read action.
4. **Imagery:** one editorial courtyard scene for everyday participation, and two
   labelled concept compositions. The illustration palette extends the identity
   with restrained plant green. Neither the scene nor a diagram is evidence for
   the philosophical assertions.
5. **Motion:** quiet opacity variation around a fixed centre. CSS honours reduced
   motion and exposes a pause mechanism in the specimen. Real use must stop when
   the operation ends and expose failure/retry state when appropriate.
6. **Type and layout:** keep established scholarly serif headings and readable
   sans-serif supporting text. Use white/ivory surfaces and ample space; reserve
   navy backgrounds for covers, chapter breaks and compact identity tiles.

The four-goal icon metaphors are proposals, not definitions: prosperity is a
provision bowl with growth, fearlessness is mutual confidence between equals,
coexistence is two connected wholes, and resolution is clarity of sight. Always
keep the accompanying words; an image cannot independently convey the full term.

## Deliverables and checked behaviour

- 34 distinct vector symbols, each in light, dark and monochrome variants.
- Compact identity cuts retain all four rings/sections and the nucleus.
- 512 px transparent PNG exports for presentation use; 16/32/48 px identity samples.
- A proposed assignment for each of the 27 current catalog studies.
- Two explanatory compositions and one generated editorial illustration.
- Responsive website and slide visual specimens, plus working waiting examples.
- Renderer checks cover missing images, JavaScript exceptions, desktop/mobile
  horizontal overflow, pause behaviour and reduced-motion fallback.

## Implementation sequence

The supplied theme is ready for design review. Applying it across the live site
and the eight teaching decks is a separate integration stage, with these exact
owners and checks:

| Surface | Source to update | Preserve / verify |
| --- | --- | --- |
| Landing page header, journey and catalog | `Scripts/_build_studies_index.py` | Stage order, actions, labels, responsive layout; regenerate and run index verifier |
| Study readers and toolbars | `Scripts/_convert_to_pdf.py`, reader CSS/JS | Icon buttons need names; reader-only changes must not add noise to study PDF output |
| Discussion waiting and actions | `Scripts/_build_discussion_pages.py` | Busy state, live status, completion, failure and retry behaviour |
| Portal and notebook controls | Their current generators and `Studies/portal` sources | Existing validation, authentication and operation semantics |
| Social images | `Scripts/_build_social_cards.py` | Title/status seals, dimensions and existing sharing metadata |
| Favicon and Apple touch icon | `Scripts/_common.py` and declared root icon copies | New compact identity at 16/32/48 px; update legacy naming/documentation deliberately |
| Eight teaching decks | Their canonical PPTX sources | Inspect objects, replace icons without touching authored evidence/notes; run layout gate and staged presentation build |

Do not copy the visual specimen's placeholder actions into production as working
buttons. They are intentionally static layout examples. Actual integration must
connect the icons to the site's existing actions and error handling.

Before deck rollout, preserve each deck's canvas dimensions and source-note
ownership. Rebuild slides and notes PDFs through the declared manifest, verify
all changed pages and use the shared companion finalizer. Do not regenerate
canonical study PDFs for a design-kit-only change.
