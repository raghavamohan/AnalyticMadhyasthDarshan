# Planning Note: Make Non-Madhyasth-Darshan References External-Only

**Recorded on:** August 30, 2026

**Baseline:** `master` at `86d02e1`

**Status:** Analysis only. No reference migration has been performed.

## Proposed policy

Retain the Madhyasth Darshan source corpus locally under
`References/Madhyasth-Darshan/`. Treat references from Advaita Vedanta,
comparative philosophy, modern philosophy, science, and applied studies as
external-only sources. Record them in `References/NOT-DOWNLOADED.md` and link
study bibliographies directly to authoritative external locations.

Under this policy, MD-TOPOS is external-only. It concerns Madhyasth Darshan but
is a secondary formal proposal rather than a Madhyasth Darshan primary text; its
stable external location is Zenodo DOI `10.5281/zenodo.16786431`.

## Inventory at the baseline

| Reference category | Tracked files | Size |
|---|---:|---:|
| Advaita Vedanta | 8 | 154.61 MiB |
| Modern philosophy | 16 | 99.94 MiB |
| Science | 13 | 29.00 MiB |
| Comparative philosophy | 6 | 0.99 MiB |
| Applied studies | 1 | 0.69 MiB |
| **Potentially removable total** | **44** | **285.23 MiB** |

The local-reference registry exposes 46 non-Madhyasth-Darshan tags backed by
these 44 files. Two files have multiple tags: the combined Katha/Taittiriya
Upanishads file (`KU`, `TU`) and the SEP moral-psychology snapshot (`SEP 2025`,
`SEP Moral Psychology`).

The retained `References/Madhyasth-Darshan/` tree contains 241 tracked files and
occupies 64.41 MiB at this baseline.

## Current dependencies

- There are 99 non-Madhyasth-Darshan local-reference links across 12 Markdown
  documents.
- Eleven main studies account for 98 bibliography entries. The remaining link
  is in `Technical-Note-MD-TOPOS-And-The-State-Dynamic-Model.md`.
- Thirty-seven of the 44 non-Madhyasth-Darshan files are linked from study or
  application Markdown. Seven are registered but not currently linked there.
- Forty-five study blockquotes are currently checked against non-Madhyasth-
  Darshan local files. Converting those sources to external-only will change
  their quote-tool result to `SKIP_NO_LOCAL_FILE`; CI will continue to run, but
  local quote-verification coverage will be reduced.

Affected Markdown documents:

- `Studies/A-State-Dynamic-Model-Of-Coexistence/Technical-Note-MD-TOPOS-And-The-State-Dynamic-Model.md`
- `Studies/Aesthetics/Aesthetics.md`
- `Studies/Axiology-Value-Theory/Axiology-Value-Theory.md`
- `Studies/Ethics-And-Morals-In-Human-Beings/Ethics-And-Morals-In-Human-Beings.md`
- `Studies/Family-Relationships-And-Values/Family-Relationships-And-Values.md`
- `Studies/How-To-Form-Self-Sustaining-Organizations/How-To-Form-Self-Sustaining-Organizations.md`
- `Studies/How-Undivided-Society-Is-Established/How-Undivided-Society-Is-Established.md`
- `Studies/Nature-Of-Time/Nature-Of-Time.md`
- `Studies/Spiritual-Practice-And-Realization/Spiritual-Practice-And-Realization.md`
- `Studies/The-Epistemology-of-Coexistence/The-Epistemology-of-Coexistence.md`
- `Studies/The-Ontology-of-Coexistence/The-Ontology-of-Coexistence.md`
- `Studies/Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material.md`

## Source-location gaps to resolve first

`Scripts/_reference_downloads.py` records source URLs for 37 of the 44 local
non-Madhyasth-Darshan files. The following seven local files do not have a
download-manifest entry and need an authoritative external location recorded
before deletion:

- `Comparative-Philosophy/Bhattacharya-Jeevan-And-Brain-Relationship.pdf`
- `Comparative-Philosophy/SEP-Natural-Law-Ethics.html`
- `Comparative-Philosophy/SEP-Theological-Voluntarism.html`
- `Modern-Philosophy/SEP-2025-Moral-Psychology-Empirical-Approaches.html`
- `Science/Crockett-2013-Models-of-Morality.pdf`
- `Science/Friston-2010-Free-Energy-Principle.pdf`
- `Science/Guth-2007-Eternal-Inflation.pdf`

The SEP and journal-paper locations can likely be reconstructed from their
citations or document metadata. No public origin for the Bhattacharya paper is
recorded in the repository; resolve that source explicitly or retain it as a
documented exception.

The download manifest also contains a Kuhn 2024 destination that is already
absent locally. It should become an ordinary external-only entry rather than
remain a download candidate.

## Risks and tradeoffs

### Broken published links

Deleting files before rewriting study citations will break Markdown links and
the links embedded in generated study HTML and PDFs. The link migration,
artifact regeneration, registry updates, and deletions must land atomically.

### Reduced quote verification

The quote verifier deliberately skips sources that have no local file. Forty-
five currently verifiable non-Madhyasth-Darshan blockquotes will therefore lose
automated source-text checking. Their citations remain valid, but future textual
drift will be harder to catch automatically.

### External-link stability

DOIs and authoritative publisher or archive pages should be preferred over
temporary PDF URLs. External sources can still move, disappear, or block
automated access, so the repository will have weaker offline reproducibility.

### Git repository size

Removing the 44 files saves approximately 285.23 MiB from the current tree and
future checkout contents. It does not remove the historical blobs from existing
Git history. A history rewrite would be required to reduce historical clone
size; that is a separate, disruptive operation and is not recommended as part of
the reference-policy migration.

### Meaning of “Madhyasth Darshan texts”

The retained `References/Madhyasth-Darshan/` directory includes primary or
working texts, the KD English translation project and page images, terminology-
mapping assets, and recorded-session material. The initial migration should keep
that entire tree. Restricting it to final book PDFs alone would be a separate
corpus-pruning decision.

## Recommended migration sequence

1. Resolve and record authoritative external URLs for all 44 files, especially
   the seven source-location gaps above.
2. Replace every non-Madhyasth-Darshan `../References/...` or
   `../../References/...` link in source Markdown with the authoritative URL.
   Studies must link directly to the source, not to `NOT-DOWNLOADED.md`.
3. Add the 46 logical tags to `References/NOT-DOWNLOADED.md`, grouped by subject.
4. Remove their local-file rows from `References/README.md` and change their
   `References/MANIFEST.md` status from present to external-only. Update study
   coverage summaries and counts.
5. Remove the non-Madhyasth-Darshan entries from
   `Scripts/_reference_downloads.py` and restrict its managed subdirectories so
   routine downloader runs cannot recreate the deleted trees.
6. Delete the tracked contents of `References/Advaita-Vedanta/`,
   `References/Applied-Studies/`, `References/Comparative-Philosophy/`,
   `References/Modern-Philosophy/`, and `References/Science/`.
7. Refresh `Edited on` timestamps and catalog timestamps for all affected main
   studies, then regenerate their HTML and PDF artifacts. Regenerate the SDM
   MD-TOPOS technote HTML and PDF after changing its source link.
8. Run the repository reference audit, full reference integrity checks, studies
   index verification, quote verification, and downloader dry run.

## Acceptance criteria for a future migration

- Only `References/Madhyasth-Darshan/` contains locally stored source materials.
- `References/README.md`, `References/MANIFEST.md`, and
  `References/NOT-DOWNLOADED.md` agree on local versus external status.
- No study or application Markdown, HTML, or PDF links to a removed local file.
- `Scripts/_reference_downloads.py` cannot recreate the external-only sources.
- All external-only entries have an authoritative URL or an explicitly approved
  unavailable-source exception.
- `python Scripts/_audit_references.py` reports no broken local links.
- `python Scripts/_check_references.py` reports zero issues.
- `python Scripts/_verify_studies_index.py` passes after regenerated study
  artifacts and timestamps are synchronized.

## Audit commands used for this note

```powershell
python Scripts/_audit_references.py
python Scripts/_check_references.py
python Scripts/_quote_tool.py verify
git ls-files References
git count-objects -vH
```

This note records a possible future migration. It does not authorize deleting
references, rewriting citations, regenerating studies, or rewriting Git history.
