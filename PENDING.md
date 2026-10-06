# Pending work

This is the **only** project backlog. Plans, review notes, and implementation
docs keep design, history, and how-to. They do not keep a second remaining-work
table.

Reviewed: 18 September 2026 against `master` `4f471bf4` and live
[analyticmadhyasthdarshan.org](https://analyticmadhyasthdarshan.org).

Editorial follow-ups added on 26 September 2026 from the
[studies readability review](docs/studies-readability-review-2026-09-26.md);
this was not a new audit of the other categories.

CI R1–R8 completed on 27 September 2026 after the public and isolated deployed acceptance exercises.

Status: **pending** (not started), **partial** (started, unfinished),
**later** (needed, not this cycle), **deferred** (do not start unless a stated
gate is met).

Within each category, rows are ordered **P1 → P2 → P3**, and within a
priority **pending / partial → later → deferred**. That order is the work
order. Cross-links stay in the owning category (for example field RUM is
`UX-06`, not a second Infrastructure row).

When an item is finished, remove the row and add a one-line note under
**Done in the same registers**. Do not leave a stale copy in a subdirectory.

## Next

1. Accept wording and check timed delivery of the revised Start here audio transcripts, beginning with
   [Why Humans Are Not Just Material](Audio/Why-Humans-Are-Not-Just-Material/en/transcript.md)
   (`AUD-01`).
2. Website next: accept the deployed smaller sign-in/recovery scope (`AUTH-02` / `UX-05`). Contributions retain GitHub sign-in; discussions retain email sign-in. The full `AUTH-01` migration is deferred unless explicitly resumed. `UX-04`/`UX-06` remain later.
3. `R2-RIGHTS` (fourteen retained third-party PDFs).
4. `TR-PILOT` (listen through the five-video transcription pilot).

YouTube (`YT-01`) is planned and is not in this cycle.

## Website

Design and evaluation matrix:
[docs/website-improvement-plan.md](docs/website-improvement-plan.md).

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| AUTH-02 | P1 | partial | Smaller sign-in improvements deployed with D1 migration `0003_magic_return.sql`; active Worker fingerprint, live confirmation page and 13 production read-only checks verified on 27 September 2026. Remaining: accept the real email/GitHub return flows. See [contributor reliability](docs/contributor-reliability.md). |
| UX-05 | P1 | partial | Account-scoped contributor/discussion draft recovery implemented; local Windows Chromium and Playwright WebKit desktop/narrow viewport, mobile/touch emulation and keyboard checks passed. Remaining: deployed recovery acceptance with an agreed test mailbox/account, including expiry, cancellation, reply recovery and real Safari/iOS checks. No unified-account cutover is planned. |
| UX-04 | P1 | later | Device/AT matrix (Safari/iOS, Firefox, TalkBack/VoiceOver/NVDA). Mobile read-aloud shipped; that does not close the evaluation. |
| UX-06 | P1 | later | Fresh Cloudflare RUM sample, segmented by catalog / large reader / search / portal and mobile / desktop. Saved baseline is still 30 August 2026 (45 views, catalog LCP p75 2.6 s, TTFB 1.3 s, CLS p75 1.0, INP p75 0). That sample predates `amd-site` cutover. Live catalog HTML is Worker-served (`cfOrigin` 0). Investigate CLS/INP before optimizing. Re-run `python Scripts/_cloudflare_performance.py --export-rum-baseline`. Related: `CF-PDF-CACHE`. |
| AUTH-01 | P1 | deferred | Full [unified email sign-in migration](docs/unified-email-sign-in-plan.md), including email-owned contributions, website review replies/corrections and OAuth retirement. Owner chose the smaller existing-login scope on 27 September 2026. Start only on an explicit decision to resume. |
| UX-08 | P2 | partial | Homepage first-reading action, tool hierarchy and shared introduction implemented; local desktop/narrow, keyboard, accessible-label and title/passage search checks pass. Remaining: a brief reader exercise asking a newcomer where to begin and why, and a returning reader to find a known title and passage; see the [readability review](docs/studies-readability-review-2026-09-26.md#7-homepage-and-reader-improvements). |
| UX-07 | P2 | later | Reading-time cues, argument routes, public reference-library browser. Include persistent path orientation for direct/search arrivals, meaningful stage names, and distinct satellite/formal-study placement; see the [readability review](docs/studies-readability-review-2026-09-26.md#7-homepage-and-reader-improvements). |
| WEB-P6 | P3 | deferred | Optional semantic retrieval. Start only if lexical search shows unmet need. |

## Audio

How-to: [docs/start-here-audio-plan.md](docs/start-here-audio-plan.md).
Drafts: [Audio/README.md](Audio/README.md).

`AUD-04` (registry and Listen player) may start in parallel with author review.
Recording (`AUD-03`) waits on `AUD-01` and `AUD-02`.

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| AUD-01 | P1 | partial | Revision 3 editorial review against the current studies completed on 26 September 2026; [all five scripts](Audio/README.md) revised for coverage, accuracy, and spoken clarity. Remaining: author wording acceptance, pronunciation, and a timed read to confirm 4–5 minutes. Start with the Human episode. |
| AUD-02 | P1 | pending | Confirm recording language and human versus AI narration. |
| AUD-04 | P1 | pending | Audio registry, R2 delivery, and Start here Listen player. `Scripts/audio-pipeline.json` is not implemented. May proceed in parallel with `AUD-01`. |
| AUD-03 | P1 | pending | Record the Human pilot, time it, and align the transcript. No recording exists yet. After `AUD-01` and `AUD-02`. |
| AUD-05 | P2 | pending | Record the remaining four episodes after the pilot is accepted. |

## YouTube

How-to: [docs/youtube-channel-plan.md](docs/youtube-channel-plan.md).

Weekly current-affairs series. Separate from Start here audio (`AUD-*`) and
from catalog studies. `coexistentialism.org` is the public door; studies stay
on analyticmadhyasthdarshan.org.

`YT-02` waits on `YT-01`. `YT-03` stays deferred until at least four episodes
are public.

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| YT-01 | P2 | pending | Create the YouTube channel: name, art, About, and website `https://coexistentialism.org`. Confirm the spoken language before recording. |
| YT-02 | P2 | pending | Publish the first episode in the plan's format, with one primary study URL on analyticmadhyasthdarshan.org. After `YT-01`. |
| YT-03 | P3 | deferred | Thin channel home on coexistentialism.org, and a light Watch link from the cited study. Start only after four published episodes. Do not clone the catalog or embed YouTube in study readers. |

## CI

How-to: [.github/CI-IMPLEMENTATION.md](.github/CI-IMPLEMENTATION.md).
Operating contract: [.github/CI.md](.github/CI.md).

No pending CI workitems. R1–R8 completion and its public/deployed acceptance
receipts are recorded in the implementation document above.

## API

How-to: [docs/public-api-improvement-plan.md](docs/public-api-improvement-plan.md),
[docs/api-operations.md](docs/api-operations.md).

Phases 1–3 are implemented. Hourly read-only synthetics run.

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| API-SMOKE | P1 | pending | Authenticated production write smoke with an agreed disposable GitHub record and authorized mailbox. |
| API-P4 | P3 | deferred | Versioning, ETags, generated clients. Start only when a real non-browser client depends on the API. |
| API-A2A | P3 | deferred | A2A task protocol. No work until a stateful agent task cannot be an MCP read or ordinary HTTP request. |
| API-OAUTH | P3 | deferred | Agent OAuth authorization server. Separate from human GitHub OAuth. Not needed for a store app. |

Website `DIS-01` discussion preference routes are complete (see Done below). The first
30-day Analytics Engine SLO snapshot is
[infra/amd-api-metrics-baseline.json](infra/amd-api-metrics-baseline.json)
(`CF-SLO`).

## References

How-to:
[References/CLOUDFLARE-R2-MIGRATION-PLAN.md](References/CLOUDFLARE-R2-MIGRATION-PLAN.md).

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| R2-RIGHTS | P1 | pending | Rights review for 14 retained third-party PDFs. Move to R2 with a redistribution basis, or cite the canonical external URL. |
| REF-AA | P1 | partial | *Avartansheel Arthshastra* (AA) is mirrored as [`AA-avartanshil-arthashastra.pdf`](References/Madhyasth-Darshan/AA-avartanshil-arthashastra.pdf) (official download, 2024 printing) and registered in References README/MANIFEST, `r2-artifacts.json` and `CLAUDE.md`. Remaining: locate *Vyavaharvadi Samajshastra* and *Manav Vyavahar Darshan*; and settle AA's redistribution basis. The imprint reserves all rights to Divyapath Sansthan and permits copying for personal study only, so the Git copy is held as an active-translation exception with rights `review-required`, like MSM ([plan §8](docs/prosperity-economics-study-plan.md#8-sources)). |
| REF-AA-TR | P1 | partial | Working English translation of AA in the [AA workspace](References/Madhyasth-Darshan/AA-Avartansheel-Arthshastra-English/README.md), following the KD method. Phase 0 is done: source pinned (SHA-256, 164 PDF pages, printed = PDF − 10), 164 page images with `Scripts/_aa_render_page_images.py --check`, README, glossary additions seeded with candidate economic terms, and review ledger. Phase 1 has the chapter-level inventory and special-layout pages. **Next:** inventory the sub-headings in each chapter; get approval for the proposed 12-page pilot (PDF p. 3; printed pp. 1, 9, 25, 27, 44, 68, 91, 101, 109, 122, 149); then the Phase 2 terminology pilot. Gate for `ST-DRAFT-06`: the complete first-pass translation must exist before drafting ([plan §8–§9](docs/prosperity-economics-study-plan.md#8-sources)). |
| R2-BACKUP | P2 | partial | Independent private [Google Drive backup](docs/r2-google-drive-backup.md) of both R2 buckets completed on 26 September 2026: 3,322 objects, 12 archive parts, download SHA-256 verification and local recovery drill. Remaining: choose deletion-protection retention and confirm legitimate corrections/withdrawals still work before applying bucket locks. |
| R2-KD | P2 | partial | Keep KD, MSM and AA source PDFs and the two generated KD review PDFs in Git until that translation workflow no longer needs them. Standing exception, not a new job. |
| REF-KD-P3 | P2 | partial | Phase 3 — sentence-level bilingual review in batches of at most five printed pages. Complete source-review coverage at the saved checkpoint: printed pp. 1–29 and 135–153 (48 pages); p. 30 has only a targeted passage check. Both PDFs rebuilt and verified. **Exact next batch: printed pp. 30–34 (Hindi PDF positions 55–59)**; then pp. 35–49, 50–134, and front matter by explicit PDF position. Use the [review ledger](References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Source-Image-Review-Ledger.md) for accepted evidence; earlier selective checks do not certify whole pages. |
| REF-KD-P4 | P2 | partial | Phase 4 — bounded primary-source investigation is recorded in the glossary and [review ledger](References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Source-Image-Review-Ledger.md#interpretive-limits-of-the-sequential-batches). The functional mapping of कासा–आकूति–मेधा is confirmed; its English names, contextual विन्यास and the members of ता-त्रय remain provisional. Resolve those terms and the compact or ambiguous readings recorded for the priority and sequential batches through further source evidence or author-informed review. Keep provisional wording explicit; changes to approved terminology require a recorded decision. |
| REF-KD-P5 | P2 | pending | Phase 5 — after all source-review batches, complete an English-only continuous reading, recheck resulting changes against Hindi, reconcile terminology across chapters, and verify final HTML/English PDF/bilingual PDF completeness and page pairing. Keep the unpublished working-translation status until explicitly released. |
| R2-HISTORY | P3 | deferred | Git history rewrite to drop old reference blobs. Owner deferred 4 September 2026. Needs a separate freeze/re-clone window. Also covers generated-PDF Git history (`M5` in the publishing ledger). |

## Infrastructure

Cloudflare edge, site Worker, RUM, and API telemetry. How-to:
[Scripts/_cloudflare_performance.py](Scripts/_cloudflare_performance.py),
[docs/reader-analytics.md](docs/reader-analytics.md),
[docs/api-operations.md](docs/api-operations.md),
[infra/site-worker/README.md](infra/site-worker/README.md).

Live on 18 September 2026: `SITE_RELEASES_ENABLED=true`; catalog HTML carries
`X-AMD-Release`; `cfOrigin` is 0 on catalog, generated PDF, reference PDF, and
`/api/studies/health`. Zone SSL is Full (Strict). GitHub Pages is no longer the
public HTML/PDF origin. Do not reopen that cutover.

Already listed elsewhere: `UX-06` (field RUM), `R2-BACKUP` (R2 deletion
protection), and `API-SMOKE` (authenticated write smoke).

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| CF-PDF-CACHE | P2 | later | Generated study PDFs remain `must-revalidate` (live HEAD 18 Sep 2026). Catalog HTML with a revision is immutable for a year. Measure with `UX-06` before lengthening PDF cache or adding revisioned PDF URLs. |
| CF-HSTS | P3 | deferred | Optional submission of `analyticmadhyasthdarshan.org` to the HSTS preload list. The header already includes `preload`. Hard to undo. |

## Transcription

How-to:
[References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/TRANSCRIPTION-PROGRAM.md](References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/TRANSCRIPTION-PROGRAM.md),
[outputs/phase4-docs/PHASE-4-PILOT-STATUS.md](outputs/phase4-docs/PHASE-4-PILOT-STATUS.md).

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| TR-PILOT | P1 | pending | Human listening pass on the five-video pilot. Excel workbooks exist; 394 native segments remain UNREVIEWED. |
| TR-SERIES | P2 | pending | Transcribe the 17-part सहअस्तित्ववादी विज्ञान series (20.1 h). Not started. |
| TR-CHANNEL | P3 | pending | Full-channel transcription of the remaining ~150 h. |
| TR-SBAP | P2 | pending | Before Spiritual Practice and Realization is released, check the audio of the 2010 Amarkantak session *Sakshatkar – Bodh – Anubhav – Praman* at the segments the study cites (03:03–03:30, 04:43, 12:54, 13:09, 17:30, 21:13, 22:28, 26:50, 31:15–32:48, 34:07, 41:14). |

## Theme

How-to: [Assets/Theme/review.md](Assets/Theme/review.md).
The icon kit itself is delivered.

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| THEME-DECKS | P2 | pending | Apply the shared theme to the eight teaching decks without altering authored evidence. Staged presentation build required. |

## Studies

Catalog `ongoing` rows remain the public catalog. This table is the working
list of first drafts still to write, plus flagged study edits. Drafts that
already exist are not listed here.

The `ST-READ-*` work follows the [readability review](docs/studies-readability-review-2026-09-26.md):
preserve every study's full substantive information and improve understanding,
with no length target or removal of detail as a readability remedy. Completed
ontology reviews remain closed. The `ST-DRAFT-*` rows follow catalog / Start
here order, not proposal-number order.

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| ST-READ-01 | P1 | partial | Independent prose pilot completed in Why Humans and Axiology: six-perspective definitions, all value/faculty tables, source support and qualifications retained; caregiver explanations and content-retention review complete. Reader feedback collection is ongoing; assess the original/revised passages with those responses before claiming comprehension improvement. See the [implementation record](docs/studies-readability-review-2026-09-26.md#11-independent-implementation-on-4-october-2026). |
| ST-READ-02 | P1 | partial | Independent Ontology and Epistemology revisions completed: full exposition retained, conceptual connections and examples explained, section identifiers preserved, and affected references/companions repaired and rebuilt. Reader-dependent assessment and any resulting iteration remain deferred while feedback collection continues, as requested on 4 October 2026. See the [implementation record](docs/studies-readability-review-2026-09-26.md#11-independent-implementation-on-4-october-2026). |
| ST-FIX-01 | P2 | done | Updated Epistemology’s Spiritual Practice and Realization link/scope. Verified and corrected the Activity Anatomy Pass One §5 MVD locators against printed pp. 339–348, including the originally flagged bhakti/tanmayata and mamta/udarta entries. Rebuilt affected outputs. |
| ST-FIX-02 | P2 | done | Corrected Ethics §3.2 to whole-group guidance of priya–hita–labha by nyaya–dharma–satya, preserving the distinct behaviour/thought/realisation correspondence. Aligned criticism, Editorial Notes and bibliography; repaired two quotation mismatches found during verification and rebuilt outputs. |
| ST-ILL-01 | P2 | done | Added the shared-water neighbourhood/group-boundary illustration to Undivided Society §3.2, distinguishing practical differences from exclusion from justice and participation. Rebuilt outputs and reconciled the existing audio review note. |
| ST-READ-03 | P2 | pending | Extend the validated explanatory and comparative-fairness approach to the other released studies, including Nature of Time, Self-Sustaining Organizations, Undivided Society, and the formal reconstruction; preserve all substantive and formal information, verify content retention, and inspect companion/audio consequences under the [review](docs/studies-readability-review-2026-09-26.md#4-recommended-changes-by-study). |
| ST-DRAFT-01 | Catalog | pending | First draft: [Philosophy of Mind and Jeevan](Studies/Philosophy-Of-Mind-And-Jeevan/) (proposal #11). |
| ST-DRAFT-02 | Catalog | pending | First draft: [Chitta, the Brain, and the Architecture of Memory](Studies/Chitta-Brain-And-Memory/) (proposal #27). |
| ST-DRAFT-03 | Catalog | pending | First draft: [Methodology and Hermeneutics](Studies/Methodology-And-Hermeneutics/) (proposal #12). |
| ST-DRAFT-04 | Catalog | pending | First draft: [Education and Sanskar](Studies/Education-And-Sanskar/) (proposal #15). |
| ST-DRAFT-05 | Catalog | pending | First draft: [Governance Justice and Undivided Society](Studies/Governance-Justice-And-Undivided-Society/) (proposal #16). |
| ST-DRAFT-06 | Catalog | deferred | First draft: [Prosperity Economics and Right Use](Studies/Prosperity-Economics-And-Right-Use/) (proposal #17). **Gate:** do not start drafting until the AA working translation (`REF-AA-TR`) exists (author decision, 6 October 2026). The thesis, *avartansheelata* source map, outline, comparative programme and open author decisions (title, formal note, scale) are in the [study plan](docs/prosperity-economics-study-plan.md). |
| ST-DRAFT-07 | Catalog | pending | First draft: [Nature Ecology and Right Use](Studies/Nature-Ecology-And-Right-Use/) (proposal #18). |
| ST-DRAFT-08 | Catalog | pending | First draft: [Science Technology and Human Purpose](Studies/Science-Technology-And-Human-Purpose/) (proposal #20). |
| ST-DRAFT-09 | Catalog | pending | First draft: [Death Continuity and Rebirth](Studies/Death-Continuity-And-Rebirth/) (proposal #21). |
| ST-DRAFT-10 | Catalog | pending | First draft: [Language Meaning and Definition](Studies/Language-Meaning-And-Definition/) (proposal #22). |
| ST-DRAFT-11 | Catalog | pending | First draft: [Work Action and Karma](Studies/Work-Action-And-Karma/) (proposal #23). |
| ST-DRAFT-12 | Catalog | pending | First draft: [Free Will Choice and Agency](Studies/Free-Will-Choice-And-Agency/) (proposal #24). |
| ST-DRAFT-13 | Catalog | pending | First draft: [Health Body and Restraint](Studies/Health-Body-And-Restraint/) (proposal #25). |
| ST-DRAFT-14 | Catalog | pending | First draft: [God Divinity and the Sacred](Studies/God-Divinity-And-The-Sacred/) (proposal #26). |
| ST-DRAFT-15 | P2 | done | [Artificial Intelligence and Coexistence](Studies/Artificial-Intelligence-And-Coexistence/) restored as a Draft (PR #555) and expanded in first-draft PR #556; the [personal AI assistant technical note](Studies/Artificial-Intelligence-And-Coexistence/Technical-Note-The-Personal-AI-Assistant.md) moved beside it with only its parent pointer changed, following the [proposal review](docs/ai-assistant-proposal-review-2026-10-04.md). Its 31-slide companion deck (speaker notes only, no Presenter's Companion) is registered as `personal-ai-assistant` in its own `study-update` PR. |

## Extensions

Projects that extend the collection beyond the site's catalog studies.

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| BOOK-01 | P2 | partial | The complete first manuscript draft of *The Human Possibility* is in [Markdown](Primer/madhyasth-darshan-primer.md), with a locally generated PDF ([build instructions](Primer/README.md#build-both-pdfs)), following the approved [book plan](Primer/madhyasth-darshan-primer-book-plan.md): six parts, twenty chapters, four explanatory figures, glossary, chapter source notes, opening portrait/wish and final Hindi song. Selected primary passages, conceptual coverage, narrative continuity and rendered layout have been checked. Following reader approval of the Chapter 1 revision, Chapters 2–20 now use the same teaching approach: a brief recognisable situation, an early philosophical proposal, connected explanation of its concepts, and a return to their fulfilment in living. Closing questions test understanding and application; selected source notes and the knowledge–wisdom–science glossary entry have been aligned with the revised explanations. Next, test Chapters 3, 8, 17 and 19 with intended readers for comprehension, concept relationships and the limits of examples; use that feedback for revision, then complete the whole-manuscript publication source audit, copyedit and final proof. The book remains in `Primer/` outside the study catalog; the separate Ethics-study correction is ST-FIX-02. |

## What does not belong here

- Skill, PR, and CI **process checklists** (how to finish one change).
- Scholarly **Open problems** inside a study (published research questions).
- Catalog **Draft** studies that already have a document (they are in progress).
- Session-only agent TodoWrite lists.

## Done in the same registers (do not reopen)

- References `REF-KD-P2` (4 October 2026): revised and independently rechecked printed pp. 135–138 and 146 against Hindi images, with a targeted p. 30 correction; rebuilt the English and bilingual PDFs (182/364 pages), checked all English-page pairings and layout, and updated the two retained output hashes. Detailed evidence and interpretive limits are in the [KD review ledger](References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Source-Image-Review-Ledger.md).

- References `REF-KD-P1` and `REF-KD-LEDGER` (4 October 2026): rebuilt the KD glossary workbook with the August 31 decisions, preserving base mapping values; reconciled the historical passage checks on pp. 30, 35–37 and 42 including the p. 37 relative-clause scope; replaced the obsolete plan reference; recorded the review/resumption method. Evidence is in the [KD review ledger](References/Madhyasth-Darshan/KD-Karm-Darshan-English/KD-Source-Image-Review-Ledger.md). Continued translation work remains in `REF-KD-P3`–`REF-KD-P5`.

- Book `BOOK-01` planning and source analysis: approved concept/chapter map, connected groups, three-eshana comparison and example catalogue, with guiding questions and cumulative scene development aligned to *The Human Possibility*, and the final drafting comments incorporated after source checks for terminology, relationships, prosperity and continuity; natural acceptance, health/restraint, sanskar/continuity, ten council levels and evaluative-triad mapping resolved in the [plan's source decisions](Primer/madhyasth-darshan-primer-book-plan.md#verified-decisions-for-chapter-sources) on 2 October 2026. Manuscript and production work remain in BOOK-01; applying the finding to the separate Ethics study is ST-FIX-02.

- Website `DIS-01`: opt-in direct-reply mail, durable retries, safe unsubscribe and private reporting/moderation implemented in [PR #534](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/534). SQLite and Chromium/WebKit checks pass; the owner confirmed the authorized test email arrived in Spam on 27 September 2026, and local unsubscribe passed. Inbox placement is not established. Publication follows PR merge.

- `CI-D1-DEPLOY`: owner corrected the migration token's D1 Edit permission; [deployment retry](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/actions/runs/36290075273) succeeded for both Workers, applied `0003_magic_return.sql`, and passed active-version, confirmation-page and 13 production read-only checks (27 September 2026). Workflow diagnostics and credential isolation are in [PR #533](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/533).

- CI `R1`–`R8` and `PPTX-DIAG-01`: completed through [PR #517](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/pull/517) and its tested lifecycle repairs, with all five public phases, older-dashboard Live navigation, six retained-history reads, 11 isolated deployed offline/recovery checks, same-zone canaries, strict PDF repeat renders, font contracts, summaries, retention policy and trusted recovery verified; fixture #518 retired and closed (27 September 2026). See [.github/CI-IMPLEMENTATION.md](.github/CI-IMPLEMENTATION.md#public-lifecycle-acceptance-26-27-september).

- `ST-ONT-02`: implemented the [Section 1 teaching-order and Editorial Notes review](docs/ontology-review-2026-09-20.md), including source-qualified prose changes, consolidated notes, section-reference repairs across related studies, substantive harmonisation of both teaching decks and the presenter's scripts, and rebuilt artifacts (20 September 2026).

- `ST-ONT-01`: implemented the [ontology review](docs/ontology-review-2026-09-19.md), including primary-text corrections, comparative coverage, cross-study terminology, prose, companions and teaching decks (19 September 2026).

- Website phases 1–5 (PRs #396–#403) and nav/listen fixes #404–#409.
- Public API phases 1–3.
- GPU transcription pipeline (VAD-off, Vulkan).
- Revisions 2 and 3 of the five Start here transcripts (18 and 26 September
  2026). Revision 3 reconciles the current studies and strengthens conceptual
  coverage, comparisons, and spoken introductions. Wording acceptance and timed
  delivery remain in `AUD-01`.
- Shared icon/illustration kit in `Assets/Theme/`. Site surfaces (landing
  nav, social cards, portal wait/toggle) shipped as `THEME-SITE`. Deck
  rollout remains `THEME-DECKS`.
- Public site cutover to `amd-site` (`SITE_RELEASES_ENABLED=true`). HTML and
  generated/reference PDFs are Worker-served; do not reopen GitHub Pages hosting.
- Website `SITE-01`, `SITE-02`, `UX-01`–`UX-03`, `OPS-01` (PR #493).
- Shared `amd-theme` toggle, dual-search hint, reader progress/offline, mobile
  glossary sheet, Start here chips, and portal `<div class="back-link">` UX
  repairs.
- Infrastructure `CF-SLO`, `CF-ANALYTICS`, `CF-SSL`, and `CF-BOTS` (18 September
  2026). Remaining: `CF-PDF-CACHE` (after `UX-06`) and deferred `CF-HSTS`.
