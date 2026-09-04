# Nagraj Recorded Sessions — working transcripts and translations

Transcripts of **recorded talks and dialogues** with Shri A. Nagraj, with working English translations. These sit apart from MVD, SB, JV, AVD, JVD and KD, and they are **not** primary texts in the sense those are.

## What these are

Oral material. Nagraj taught in dialogue for decades, and recordings survive that state mechanism the printed books leave implicit. Where a session bears on a study's argument, it is transcribed here so the study can cite something stable instead of a video timestamp.

**Only promoted References artefacts live in this folder.** Unpromoted Tier-1 ASR and working cohort drafts are kept outside the repository at `E:\MD-Transcription\Nagraj-Recorded-Sessions\` (see that folder's README and [`TRANSCRIPTION-PROGRAM.md`](TRANSCRIPTION-PROGRAM.md)).

## Standing as evidence — the constraint that governs this folder

Every file here is **two removes from the source**: a machine transcription of speech, then a working translation of that transcription. Neither step has been checked by a Hindi speaker against the audio unless a file says so explicitly.

Consequences, and they are not optional:

1. **A recorded session never outweighs a printed text.** Where they differ, the printed text governs and the difference is worth recording as a finding.
2. **Nothing here is quoted in a released study without listening to the audio** at the cited timestamp. Each transcript carries per-segment reliability marks and a table of the passages that most need this.
3. **Attribution is by channel and internal evidence, not authentication.** No recording here has been authenticated by the Madhyasth Darshan tradition or by an archive.
4. **Oral teaching is occasion-bound.** A session answers the people in the room. A claim made once, to one audience, is weaker evidence of settled doctrine than the same claim in a book — and stronger evidence of what the speaker actually thought than a paraphrase would be. Both halves of that matter.

Studies citing this material should attribute it as a **recorded session with date and timestamp**, never as though it were MVD/JV/KD, and should say in an Editorial Note that the source is oral and machine-transcribed.

## Layout

```
Nagraj-Recorded-Sessions/
├── README.md                                  ← this file: conventions
├── TRANSCRIPTION-PROGRAM.md                   ← programme log (D1–D12)
└── Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/
    ├── …-2010-Amarkantak.md|.html|.pdf
    └── …-2010-raw-asr.txt
```

**Append the video ID to the directory name** for any new session. Slug-only names collide on this channel. The 2010 transcript predates that rule and keeps its plain slug (`Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak`, video `gIvVme-Sa5s`).

## Contents

| Session | Duration | Subject | Files |
|---|---|---|---|
| *Sakshatkar – Bodh – Anubhav – Praman* (2010 Amarkantak) | 45:00 | Four-stage cognitive sequence | [md](Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak.md) · [PDF](Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak.pdf) · [raw](Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-raw-asr.txt) |

The `.md` is the source of truth; `.html` and `.pdf` are generated. Regenerate with the sanctioned pipeline (AGENTS.md §3 — never pandoc or an ad-hoc converter):

```powershell
python Scripts/_convert_to_pdf.py "References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak.md"
node Scripts/_html_to_pdf.js "References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak.html"
```

**Devanagari in the PDF** renders through Windows' **Nirmala UI**, picked up by Chromium's font fallback — no font is declared for it in the pipeline stylesheet. Two consequences. Nirmala UI has no italic face, so `_convert_to_pdf.py` sets `font-synthesis-style: none` to stop Chromium faking one inside blockquotes (a synthetic oblique distorts matras and makes editorial `[brackets]` read as vowel marks); Latin text is unaffected because Georgia ships a true italic. And on a machine without a Devanagari system font, the Hindi will render as tofu — check a page of output, not just that the command succeeded.

## Audio and video are not stored here

Only transcripts live in this folder. Recordings are **not** copied into the repository — each session's source URL is in its transcript header and in [`../../NOT-DOWNLOADED.md`](../../NOT-DOWNLOADED.md).

This has a direct cost, and it should be understood rather than worked around: the reliability marks below tell a reader to go and listen at a given timestamp, and that now depends on the external recording remaining reachable. **If a source URL goes dead, the [U] and [P] segments become unverifiable** and should be treated as unusable rather than promoted by default. Keeping a private local copy of the audio for verification work is sensible; committing it here is not the practice.

**Provenance and rights.** Each session's uploader and URL are recorded in its transcript header and in [`../../MANIFEST.md`](../../MANIFEST.md). Rights rest with whoever published the recording.

**If audio is ever added** — the repository sets `* text=auto eol=lf` in `.gitattributes` and declares binary types explicitly. `.mp3` and the other audio/video extensions are **not** in that list. Add the extension as `binary` *before* committing any such file: relying on `text=auto` to guess correctly is one heuristic away from silent EOL corruption of a large binary. Also consider git-LFS first — audio stays in history permanently, and `.git` is already several hundred MB.

## Method

Transcription uses **Whisper `large-v3`**. YouTube's own Hindi auto-captions have proved unusable for this material — for the 2010 session they carried roughly a third of the text with multi-minute gaps and corrupted the key terms outright (*बोध* → "वोट").

Only **no-VAD** decoding is complete for this material. See D7 in [`TRANSCRIPTION-PROGRAM.md`](TRANSCRIPTION-PROGRAM.md). Prefer sequential no-VAD for doctrinally dense passages.

### Citing page numbers from the `.md` extracts — read this first

Recovering a garbled passage means citing the printed text, and the companion `.md` extracts will mislead you about page numbers in two different ways. Both were found the hard way on 2026-08-01, after a first pass of this transcript shipped with roughly twenty wrong citations.

**MVD: `page-N` is a footer, not a heading.** The marker sits at the *end* of page N's text, so **content following marker `page-N` is on page N+1**. A script that attributes a line to "the last marker above it" is off by one, every time. Verified: PDF page 80's first line is *ज्ञानावस्था में ईष्ट सेवन का लक्ष्य…*, which in the markdown appears immediately after `page-79`.

**JV: there are no page markers.** `JV-Jeevan-Vidya-An-Introduction.md` contains just **eight** bare-number lines across the whole book (1, 4, 7, 36, 72, 92, 122, 170). They are not per-page markers and must not be read as such — treating the nearest one as a page number produced a citation 26 pages out.

**So: take page numbers from the PDF, not the extract.** For MVD and JV the PDF page equals the printed page, so this is a direct lookup:

```powershell
python -c "import pymupdf,re; d=pymupdf.open(r'References/Madhyasth-Darshan/MVD-Madhyasth-Darshan-Coexistentialism.pdf'); n=lambda s: re.sub(r'\s+','',s); k=n('<devanagari phrase>'); print([i+1 for i in range(d.page_count) if k in n(d[i].get_text())])"
```

Use the extract to *find* wording (it is searchable and the PDF's Devanagari sometimes is not), then confirm the page in the PDF before citing it.

**Practical note.** The transcription environment is not committed to this repository. Work audio and unpromoted ASR live under `E:\MD-Transcription\`.

## Adding a session

1. Transcribe with the method above from a local copy of the audio; keep the raw ASR output as a separate `-raw-asr.txt` file so normalisations stay auditable. Do not commit the audio. Keep unpromoted drafts under `E:\MD-Transcription\Nagraj-Recorded-Sessions\` until ready for References.
2. Normalise Devanagari **only where the intended word is unambiguous**, and never supply words the ASR did not carry. List the normalisations in the file.
3. Translate following `../MD-Mapping.xlsx` and Rakesh Gupta's published MVD/SB/JV wherever they have a reading. Flag terms with no mapping row as working glosses rather than inventing an authority for them.
4. Mark every segment **[R]** reliable / **[P]** probable / **[U]** uncertain, and add a table of passages needing audio verification.
5. Record the source URL, uploader, date, place and duration in the transcript header, and note the recording's SHA-256 if you have a copy — so a future copy can be checked against the one that was transcribed.
6. Add a row to the Contents table above, an entry in [`../../NOT-DOWNLOADED.md`](../../NOT-DOWNLOADED.md) for the recording, and a row in [`../../MANIFEST.md`](../../MANIFEST.md) if a study cites it.
