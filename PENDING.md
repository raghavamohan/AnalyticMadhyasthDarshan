# Pending work

This is the **only** project backlog. Plans, review notes, and implementation
docs keep design, history, and how-to. They do not keep a second remaining-work
table.

Reviewed: 18 September 2026 against `master` `4f471bf4` and live
[analyticmadhyasthdarshan.org](https://analyticmadhyasthdarshan.org).

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

1. Author-review the five Start here audio transcripts, beginning with
   [Why Humans Are Not Just Material](Audio/Why-Humans-Are-Not-Just-Material/en/transcript.md)
   (`AUD-01`).
2. Website next: `UX-04`–`UX-06` (device/AT matrix, recovery check, fresh RUM), then `DIS-01`.
3. CI `R1` (Worker canaries before promotion).
4. `R2-RIGHTS` (fourteen retained third-party PDFs).
5. `TR-PILOT` (listen through the five-video transcription pilot).

## Website

Design and evaluation matrix:
[docs/website-improvement-plan.md](docs/website-improvement-plan.md).

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| UX-04 | P1 | later | Device/AT matrix (Safari/iOS, Firefox, TalkBack/VoiceOver/NVDA). Mobile read-aloud shipped; that does not close the evaluation. |
| UX-05 | P1 | later | Production contributor/discussion recovery check. Composer text is not preserved across sign-in. |
| UX-06 | P1 | later | Fresh Cloudflare RUM sample, segmented by catalog / large reader / search / portal and mobile / desktop. Saved baseline is still 30 August 2026 (45 views, catalog LCP p75 2.6 s, TTFB 1.3 s, CLS p75 1.0, INP p75 0). That sample predates `amd-site` cutover. Live catalog HTML is Worker-served (`cfOrigin` 0). Investigate CLS/INP before optimizing. Re-run `python Scripts/_cloudflare_performance.py --export-rum-baseline`. Related: `CF-PDF-CACHE`. |
| DIS-01 | P2 | pending | Reply mail and report control. Session revocation already shipped. Not this cycle. |
| UX-07 | P2 | later | Reading-time cues, argument routes, public reference-library browser. |
| FBK-01 | P2 | deferred | Keep GitHub corrections unless observation shows GitHub is the blocker. |
| WEB-P6 | P3 | deferred | Optional semantic retrieval. Start only if lexical search shows unmet need. |

## Audio

How-to: [docs/start-here-audio-plan.md](docs/start-here-audio-plan.md).
Drafts: [Audio/README.md](Audio/README.md).

`AUD-04` (registry and Listen player) may start in parallel with author review.
Recording (`AUD-03`) waits on `AUD-01` and `AUD-02`.

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| AUD-01 | P1 | pending | Author-review the five English drafts (meaning, spoken clarity, qualifications, 4–5 minute timing, pronunciation). Start with the Human episode. |
| AUD-02 | P1 | pending | Confirm recording language and human versus AI narration. |
| AUD-04 | P1 | pending | Audio registry, R2 delivery, and Start here Listen player. `Scripts/audio-pipeline.json` is not implemented. May proceed in parallel with `AUD-01`. |
| AUD-03 | P1 | pending | Record the Human pilot, time it, and align the transcript. No recording exists yet. After `AUD-01` and `AUD-02`. |
| AUD-05 | P2 | pending | Record the remaining four episodes after the pilot is accepted. |

## CI

How-to: [.github/CI-IMPLEMENTATION.md](.github/CI-IMPLEMENTATION.md).
Operating contract: [.github/CI.md](.github/CI.md).

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| R1 | P1 | pending | Automate pre-promotion API/Worker canaries. Manual same-zone canary existed; `agent-publications.yml` still deploys before the live audit. |
| R2 | P1 | partial | Finish operational acceptance under the new pipeline (proposal through retire, offline readers, rollback). Local coverage advanced; deployed matrix is unfinished. |
| R3 | P2 | pending | Strict slide-PDF byte reproducibility. PR #457: all eight slides PDFs `byte-identical=no`; notes PDFs yes. |
| R4 | P2 | partial | Complete Python/Node patch, runner-image, and font version policy. Pins and fingerprints exist. |
| R5 | P2 | pending | One run summary across PDF/R2/Worker change classes. JSON plans exist. |
| R6 | P3 | pending | Remove transitional CI paths after R2. Disabled Pages retry must not resume publishing. |
| R7 | P3 | pending | Retention, withdrawal, and safe garbage-collection policy. Decision first; no production object deletion as routine publication. |
| R8 | P3 | deferred | Broader reviewed-artifact recovery lookup. Optional; normal reuse through the active receipt already works. |

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

Website `DIS-01` discussion preference routes are listed under Website. The first
30-day Analytics Engine SLO snapshot is
[infra/amd-api-metrics-baseline.json](infra/amd-api-metrics-baseline.json)
(`CF-SLO`).

## References

How-to:
[References/CLOUDFLARE-R2-MIGRATION-PLAN.md](References/CLOUDFLARE-R2-MIGRATION-PLAN.md).

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| R2-RIGHTS | P1 | pending | Rights review for 14 retained third-party PDFs. Move to R2 with a redistribution basis, or cite the canonical external URL. |
| R2-BACKUP | P2 | pending | R2 deletion protection and independent backup. Apply a bucket lock only after confirming legitimate corrections still work. |
| R2-KD | P2 | partial | Keep KD and MSM source PDFs and the two generated KD review PDFs in Git until that translation workflow no longer needs them. Standing exception, not a new job. |
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

Already listed elsewhere: `UX-06` (field RUM), `R1` (Worker canaries before
promotion), `R2-BACKUP` (R2 deletion protection), `API-SMOKE` (authenticated
write smoke), `R6` (remove the inactive Pages retry workflow after operational
acceptance).

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

## Theme

How-to: [Assets/Theme/review.md](Assets/Theme/review.md).
The icon kit itself is delivered.

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| THEME-SITE | P2 | partial | Finish shared-theme integration on remaining site surfaces (landing, social, portal). Some reader/discussion controls already use the sprite. |
| THEME-DECKS | P2 | pending | Apply the shared theme to the eight teaching decks without altering authored evidence. Staged presentation build required. After remaining site surfaces, or in parallel on a deck-only PR. |

## Studies

Catalog `ongoing` rows remain the public catalog. This table is the working
list of first drafts still to write, plus one flagged study edit. Drafts that
already exist are not listed here.

`ST-ILL-01` is the only existing-study edit. The `ST-DRAFT-*` rows follow
catalog / Start here order, not proposal-number order.

| ID | Pri | Status | Remaining need |
| --- | --- | --- | --- |
| ST-ILL-01 | P2 | pending | Add a neighbourhood / group-boundary illustration to [How Undivided Society](Studies/How-Undivided-Society-Is-Established/How-Undivided-Society-Is-Established.md) §3.2. Flagged during audio revision. |
| ST-DRAFT-01 | Catalog | pending | First draft: [Philosophy of Mind and Jeevan](Studies/Philosophy-Of-Mind-And-Jeevan/) (proposal #11). |
| ST-DRAFT-02 | Catalog | pending | First draft: [Chitta, the Brain, and the Architecture of Memory](Studies/Chitta-Brain-And-Memory/) (proposal #27). |
| ST-DRAFT-03 | Catalog | pending | First draft: [Methodology and Hermeneutics](Studies/Methodology-And-Hermeneutics/) (proposal #12). |
| ST-DRAFT-04 | Catalog | pending | First draft: [Education and Sanskar](Studies/Education-And-Sanskar/) (proposal #15). |
| ST-DRAFT-05 | Catalog | pending | First draft: [Governance Justice and Undivided Society](Studies/Governance-Justice-And-Undivided-Society/) (proposal #16). |
| ST-DRAFT-06 | Catalog | pending | First draft: [Prosperity Economics and Right Use](Studies/Prosperity-Economics-And-Right-Use/) (proposal #17). |
| ST-DRAFT-07 | Catalog | pending | First draft: [Nature Ecology and Right Use](Studies/Nature-Ecology-And-Right-Use/) (proposal #18). |
| ST-DRAFT-08 | Catalog | pending | First draft: [Science Technology and Human Purpose](Studies/Science-Technology-And-Human-Purpose/) (proposal #20). |
| ST-DRAFT-09 | Catalog | pending | First draft: [Death Continuity and Rebirth](Studies/Death-Continuity-And-Rebirth/) (proposal #21). |
| ST-DRAFT-10 | Catalog | pending | First draft: [Language Meaning and Definition](Studies/Language-Meaning-And-Definition/) (proposal #22). |
| ST-DRAFT-11 | Catalog | pending | First draft: [Work Action and Karma](Studies/Work-Action-And-Karma/) (proposal #23). |
| ST-DRAFT-12 | Catalog | pending | First draft: [Free Will Choice and Agency](Studies/Free-Will-Choice-And-Agency/) (proposal #24). |
| ST-DRAFT-13 | Catalog | pending | First draft: [Health Body and Restraint](Studies/Health-Body-And-Restraint/) (proposal #25). |
| ST-DRAFT-14 | Catalog | pending | First draft: [God Divinity and the Sacred](Studies/God-Divinity-And-The-Sacred/) (proposal #26). |

## What does not belong here

- Skill, PR, and CI **process checklists** (how to finish one change).
- Scholarly **Open problems** inside a study (published research questions).
- Catalog **Draft** studies that already have a document (they are in progress).
- Session-only agent TodoWrite lists.

## Done in the same registers (do not reopen)

- Website phases 1–5 (PRs #396–#403) and nav/listen fixes #404–#409.
- Public API phases 1–3.
- GPU transcription pipeline (VAD-off, Vulkan).
- Revision 2 of the five Start here transcripts (18 September 2026). Author
  review of that result is `AUD-01`.
- Shared icon/illustration kit in `Assets/Theme/`. Live-site and deck rollout
  remain `THEME-SITE` / `THEME-DECKS`.
- Public site cutover to `amd-site` (`SITE_RELEASES_ENABLED=true`). HTML and
  generated/reference PDFs are Worker-served; do not reopen GitHub Pages hosting.
- Website `SITE-01`, `SITE-02`, `UX-01`–`UX-03`, `OPS-01` (PR #493).
- Infrastructure `CF-SLO`, `CF-ANALYTICS`, `CF-SSL`, and `CF-BOTS` (18 September
  2026). Remaining: `CF-PDF-CACHE` (after `UX-06`) and deferred `CF-HSTS`.
