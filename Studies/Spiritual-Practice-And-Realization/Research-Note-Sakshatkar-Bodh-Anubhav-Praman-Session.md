# Research Note: *Sakshatkar – Bodh – Anubhav – Praman* — a recorded session with A. Nagraj

**Author:** Raghava Mohan Madhwapathi ([analyticmadhyasthdarshan.org](https://analyticmadhyasthdarshan.org))

**Edited on:** August 1, 2026, 8:56 PM IST

**Status:** Internal research note (not a catalog entry). Compiled to support [*Spiritual Practice and Realization*](Spiritual-Practice-And-Realization.md), especially §§1.1–1.13, §4.2, and the open problems in §6.

**Source:** *साक्षात्कार - बोध - अनुभव - प्रमाण* — dialogue with A. Nagraj, *Anubhav Shivir*, January 2010, Amarkantak. Posted by Rakesh Gupta (MVD's translator), <https://youtu.be/gIvVme-Sa5s>. Duration 45:00; transcript covers 00:00–44:32.

---

## Provenance and reliability — read before quoting

This is an **oral source**, machine-transcribed. Nothing here has the standing of the printed texts, and the note is written so that the difference stays visible.

**How the transcript was produced.** YouTube's own Hindi auto-captions are unusable: ~6,700 characters for 45 minutes, with multi-minute holes and heavy corruption (*बोध* rendered as "वोट"). The transcript underlying this note was produced locally with **Whisper `large-v3`** (int8, CPU) at 16 kHz: ~20,500 characters across 130 segments, continuous with no gap over 60 seconds — roughly three times the text, without holes. Two decoding passes were used, and the difference matters for how much weight a passage can bear:

| Span | Pass | Character |
|---|---|---|
| 00:00–18:27 | Sequential, no VAD, `beam_size=5`, temperature fallback | Short segments, finer timestamps. **The doctrinal core falls here.** |
| 18:20–44:32 | Batched pipeline, VAD-segmented, `beam_size=5` | Longer merged segments; short utterances at VAD boundaries can be clipped |

Where the two passes overlap (03:00–06:00) the wording is identical, which is the basis for trusting the batched span.

**The full transcript and translation live in References**, not here: [`References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak.md`](../../References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak.md) — all 130 segments, normalised Hindi with English, per-segment reliability marks, and cross-references to the printed corpus. Raw ASR before normalisation: [`…-raw-asr.txt`](../../References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-raw-asr.txt). Folder conventions and the constraints on citing oral material: [`Nagraj-Recorded-Sessions/README.md`](../../References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/README.md). This note quotes only the load-bearing passages; the transcript is the source of record.

**Three classes of reliability, marked throughout.**

- **Reliable** — phrase recurs across segments, or is corroborated by a printed text. Safe to paraphrase.
- **Probable** — single clear occurrence, ASR internally consistent. Usable with the timestamp cited.
- **Uncertain** — reconstructed through evident ASR corruption. Flagged `[uncertain]`. **Do not quote in a released study without listening to the audio.**

**On the Hindi below.** ASR spellings have been normalised to standard Devanagari where the intended word is unambiguous (साक्षात कार → साक्षात्कार, बोत/वोट → बोध, अन्भव → अनुभव, अध्येन/अध्यान → अध्ययन, स्विकार → स्वीकार, सुभाव → स्वभाव, वस्तो → वस्तु, दृष्टापद/दृष्टापत → दृष्टापद). These are **reconstructions, not a verified transcript**. English renderings are mine and are working translations.

**Standing as evidence.** This is a teaching session, not a composed text. It is first-person report and oral exposition — the same evidential class the study's §1.13 assigns to the founder's autobiographical material, with the further discount that no one has authenticated the recording or the transcript. Its value is that it states, in the founder's own voice, mechanism the printed corpus leaves implicit.

**What a corpus pass changed, and why that reframes this note.** A systematic search of MVD, SB, JV and KD against every degraded segment (2026-08-01) recovered seven of them and settled six terms this note had earlier carried as invented glosses. The upshot is that **most of what looked like the session's own doctrine is in the printed corpus already** — the ladder's terminology (*ऋतम्भरा*, *प्रज्ञा*, *श्रुति*, *तद्रूप/तदाकार*), the six-item set at *bodh*, the two-path scheme, the *rup–gun* triads. The session's distinctive contribution is narrower and more interesting than a first reading suggested: not new doctrine, but **sequencing, mechanism, and the practical division of labour between the two paths**. Where this note now cites a printed locus, prefer it — the session is corroboration.

**Citations here are verified against the PDFs, not the markdown extracts.** An earlier revision of this note carried roughly twenty wrong page numbers. MVD's `.md` marks pages with a `page-N` *footer*, so content following the marker is on page N+1; JV's `.md` has only eight stray bare numbers and no pagination at all (one citation was 26 pages out). Every MVD and JV page below was re-derived by searching the PDF directly. The study's own pre-existing citations were correct throughout; the error was confined to this note's additions.

---

## 1. What the session is about

The opening states the agenda (00:00, **reliable**):

> साक्षात्कार, बोध, अनुभव, प्रमाण — इन मुद्दों पर थोड़ा सा प्रकाश डालने के लिए कहा गया।
>
> *Sakshatkar, bodh, anubhav, praman — I have been asked to shed a little light on these matters.*

The four terms are the subject of the whole session. **None of the three — *sakshatkar*, *bodh*, *praman* — appears anywhere in the study as currently drafted**, and the study treats *anubhav* as an undifferentiated whole ("realisation"). The session presents them as four ordered stages of one process.

---

## 2. *Sakshatkar* redefined against ordinary usage

Nagraj first states the received sense and rejects it (00:30, **reliable**):

> साक्षात्कार के बारे में अभी तक मान्यता है — हम जो आँखों से देखते हैं, इसको साक्षात्कार माना जाता है।
>
> *The accepted view of sakshatkar so far is this: what we see with the eyes is taken to be sakshatkar.*

His replacement runs through meaning. Every word has an *artha*, and that *artha* is a *vastu* in *astitva* — illustrated with the ordinary case of a name picking out the person in front of you (00:50–01:25, **reliable**). Recognition of that *vastu* is recognition of four things inseparably present (02:38–02:53, **reliable**):

> हर वस्तु में रूप, गुण, स्वभाव, धर्म अविभाज्य रूप में वर्तमान रहता है। … हर वस्तु को हम रूप-गुण-स्वभाव-धर्म के साथ पहचान पाते हैं — उसका नाम है बोध अथवा साक्षात्कार।
>
> *In every vastu, form, property, essential nature and dharma are present inseparably. … When we can recognise every vastu together with its form, property, essential nature and dharma — that is called bodh, or sakshatkar.*

He marks the contrast explicitly (01:55, **probable**): what was formerly called *sakshatkar* is what appears to the eyes; what he means is what comes to be understood. At 09:24 the two are named as **चक्षु गोचर** and **ज्ञान गोचर** — eye-accessible and knowledge-accessible (**probable**).

**Cross-reference.** MVD p. 126 already maps the ladder onto the faculties: affirmation of coexistence through study is *manan* in *mun*, *tulan* in *vritti* (*गुणात्मक विधि से*, by the qualitative method), ***sakshatkar* in *chitta***, and ***bodh* in *buddhi***. The session's *रूप-गुण-स्वभाव-धर्म* analysis is the missing account of *what sakshatkar recognises*.

---

## 3. The chain, and that it is automatic after the first step

The core passage (03:03–03:30, **reliable** — the phrasing recurs at 13:09):

> साक्षात्कार के बाद बोध होता है। उसके लिए अपने को कुछ करना नहीं है — अपने आप से होता है, जीवन में। बोध के बाद अनुभव होता है अपने आप में; अनुभव के बाद प्रमाण होता है अपने आप में। इन चारों चीज़ों में से पहली चीज़ साक्षात्कार यदि सफल होता है, तो बाकी तीनों क्रिया अपने आप से होता है।
>
> *After sakshatkar, bodh occurs. For that one need do nothing oneself — it occurs of itself, in jeevan. After bodh, anubhav occurs of itself; after anubhav, praman occurs of itself. Of these four, if the first — sakshatkar — succeeds, the remaining three activities occur by themselves.*

The analogy is ordinary perception (03:30, **reliable**): once you have seen something with your eyes, acceptance or rejection follows without further effort.

**This corrects a reading the printed texts invite.** MVD p. 7's *samadhi–dhyan–dharana* is a sequence the practitioner *performs*. This chain is not: only the first rung is worked at, and it is worked at through study (§4 below). The study's §1.3 treats the inverted ladder as the method; this session locates the method one level down.

---

## 4. *Sakshatkar* is the success condition of study

Stated twice, and this is the single most consequential claim for the study (12:54–13:09, **reliable**):

> शब्द के अर्थ में वस्तु के रूप में जो वस्तु है, वो अस्तित्व में है। … उसका नाम है साक्षात्कार। इसका नाम है अध्ययन की सफलता। यदि अध्ययन सफल होता है, उस स्थिति में स्वाभाविक रूप में बोध होता है; बोध होने के पश्चात अनुभव होता है; अनुभव होने के पश्चात प्रमाण होता है।
>
> *The vastu that stands as the meaning of a word is in existence. … That is called sakshatkar. This is what the success of study is called. If study succeeds, then in that condition bodh occurs naturally; after bodh, anubhav; after anubhav, praman.*

The point recurs (06:12, **reliable**): *इसका बैकग्राउंड क्या है? अध्ययन।* — "What is the background of this? Study." And 05:13: *उसके लिए क्या करता है? अध्ययन विधि* — study is what one actually does.

**This speaks directly to §6.6 of the study** ("The absence of practice detail"), which observes that *samyama* is named but not described such that another could follow it, and that study is prescribed without a curriculum. The session's answer is that there is no technique beyond study — study *is* the practice, and *sakshatkar* is the name of its succeeding. §6.6 should be rewritten to say that, and to note that the answer is oral.

---

## 5. Each stage's activity is named

At 13:09–13:45 and again 20:42–21:13 the stages get named activities (**reliable**, stated twice):

| Stage | Named activity | Timestamp |
|---|---|---|
| *anubhav* | **दृष्टापद** — the seat of the seer | 13:26, 15:04, 21:13 |
| *praman* | **जागृति** — awakening | 13:09, 21:13 |

> जागृति का नाम है प्रमाण की अभिव्यक्ति; और दृष्टापद का दूसरा नाम है अनुभव। (21:13)
>
> *Awakening is the name for the expression of praman; and the other name for drashtapad is anubhav.*

**This is a substantive identification the study does not have.** *Praman* is not evidence-as-testimony offered to an audience — its activity *is* awakening. Consequently the study's framing of conveyability and conduct as *external criteria substituted for private certainty* (§1.10, §6.3, and the Conclusion) does not match the darshan's own architecture, in which these are the terminal stage of the cognitive process itself.

At 04:43 (**reliable**) *praman* is given its operational sense:

> वह प्रमाण क्या चीज़ है? दूसरे को बोध कराने की ताकत।
>
> *What is that praman? The power to bring about bodh in another.*

And 06:51 (**reliable**): *हम दूसरों को समझाने योग्य होते हैं, दूसरों को बोध कराने योग्य होते हैं* — "we become fit to explain to others, fit to bring about bodh in others."

**Cross-reference.** This is JV p. 26's "The proof of our comprehension lies in our ability to convey it to others" — but derived, not stipulated. MVD p. 12 (§7 प्रमाण) states the same chain compactly: *अनुभव ही प्रमाण* … *प्रमाण ही जागृत परम्परा* — "Realisation itself is the ultimate evidence … Evidence itself is awakened tradition."

---

## 6. The key Q&A: what *anubhav* adds to *bodh*

A participant asks the sharpest question in the session (22:28, **reliable** — the question and its answer are both clear):

> **प्रश्न:** फिर बोध होने के बाद अनुभव होने में और क्या समझ में आया, जिसको अनुभव कहते हैं?
>
> **उत्तर:** कुछ नहीं। साक्षात्कार में जो होता है वो पक्का होता है — उसके अलावा कुछ नहीं होता है।
>
> ***Q:** After bodh, then, what further is understood in anubhav — that which is called anubhav?*
>
> ***A:** Nothing. What occurs in sakshatkar becomes firm — apart from that, nothing occurs.*

The questioner presses: so bodh and anubhav happen together? The reply (22:58, **probable**) is that both are already reached *in* sakshatkar, and distinguishes what arrives at which rung — *dharma* and *swabhav* at *bodh*, and then a set of six: **नियम, नियंत्रण, संतुलन, न्याय, धर्म, सत्य** (rule, regulation, balance, justice, *dharma*, truth).

That set is not the session's invention and does not depend on the recording. MVD states it verbatim and, decisively for this section, ties it to *anubhav*: *नियम, नियन्त्रण, संतुलन, न्याय, धर्म, सत्य, अनुभव के फलन में प्रमाणित होता है* — "is evidenced in the fruition of realisation" (MVD, p. 80). The same six appear at MVD p. 32, and p. 174 derives them as a chain (*नियम ही नियंत्रण; नियंत्रण ही संतुलन; संतुलन पूर्वक जीना ही मानव में न्याय …*). So the printed corpus already places these six at the *anubhav* stage, and the session's contribution is to locate their arrival one rung earlier, at *bodh*/*sakshatkar*, with *anubhav* only firming them. **Cite MVD for the set; cite the session only for the placement.**

**This is the most important single finding for the study.** The later stages add **no new content**; they are the consolidation (*पक्का होना*) of what *sakshatkar* delivered. The study currently treats *anubhav* as realisation with distinct content of its own (§1.1, and the glossary entry). On this account *anubhav* is not a further cognition but the firming of one.

---

## 7. *Samadhi*: the negative finding in his own voice

The autobiographical passage the study's §1.2 rests on, here stated orally (16:36–17:08, **reliable**):

> हम समाधि देखा — समाधि में एक भी ज्ञान नहीं हुआ। उल्टा क्या देखते रहे? देखते ही रहे — हमारा आशा, विचार, इच्छा चुप हो गए। … काल, समय, शरीर, स्थान — इनका अभाव।
>
> *We saw samadhi — in samadhi not one instance of knowledge occurred. What did we go on seeing instead? We just kept watching — our hope, thought and desire fell silent. … Time, body, place — their absence.*

And what he wrote about it (17:16–17:30, **probable**):

> मुझको समाधि के बाद, भूत और भविष्य की पीड़ा वर्तमान में वर्त नहीं है।
>
> *For me, after samadhi, the affliction of past and future does not obtain in the present.*

Then the turn (17:30, **reliable**): *उसके बाद जब संयम हुआ, जब पता लगा, अनुभव हुआ — हम दृष्टापद में हो गए हैं, सह-अस्तित्व में।* — "After that, when samyama occurred, when it became known, anubhav occurred — we came to be in drashtapad, in coexistence."

**Cross-reference.** MVD p. 7, JV p. 13. The phrase *समाधि में एक भी ज्ञान नहीं हुआ* is stronger than the printed "the event of knowing the unknown did not occur", and §1.2's two-claim analysis (phenomenological + evidential) survives it intact.

---

## 8. *Samadhi–samyama* is declared impractical as a general method

This passage bears on §1.8, §6.2 and §6.5 together, and has no printed counterpart I have found (34:07, **probable**):

> सब कोई समाधि-संयम करेगा, अनुसंधान करेगा — यह अव्यवहारिक बात है। समाधि-संयम, क्या हर व्यक्ति अनुसंधान करके जी पाएगा? नहीं होगा। तब क्या विधि है? सबके लिए पहुँचने की अध्ययन विधि है। पहले श्रुति विधि थी …
>
> *That everyone will do samadhi-samyama and research — this is impractical. Samadhi-samyama: will every person manage to live by doing research? It will not happen. Then what is the method? For everyone to arrive, the method is study. Earlier the method was shruti …*

Immediately before (33:40, **probable**):

> समाधि तो बहुत सारे लोगों को हुआ है … किन्तु अनुभवमूलक विधि से हुआ है, ऐसा हम कह नहीं सकते।
>
> *Many people have attained samadhi … but that it happened by the realisation-based way, that we cannot say.*

And on *shruti* (34:41, **probable** after recovery): the *shruti* method could not bring the pervasive reality (*व्यापक वस्तु*) to be understood as truth; what he calls the ultimate truth is coexistence, and the root formula is revised from *"ब्रह्म सत्य, जगत मिथ्या"* to *"ब्रह्म सत्य, जगत शाश्वत"* — MVD p. 3 states the inherited version, MVD p. 12 the replacement, and SB the substitution explicitly. *श्रुति* is itself a defined term: *यथार्थ रूपी ज्ञान, विवेक, विज्ञान का भाषाकरण*, "giving language to knowledge" (MVD pp. 324, 329), so "the *shruti* method" is precise usage, not loose talk.

**The decisive link: *अनुसंधान* is MVD's own first path.** This is what makes the section usable rather than merely suggestive. MVD p. 280 — the passage §1.8 already quotes — states the two processes for eliminating *बौद्धिक रहस्यता* as *एक — अनुसंधान। दो — अनुसरण, अनुकरण, अध्ययन*, published "One - Exploration. Two - Following, Emulation, Study." So when the session answers a question about bypassing study with *दूसरा विधि है — अनुसंधान* (28:43), it is naming **MVD's Exploration path by its Hindi name**; when it says that path runs through *समाधि-संयम* carried out as prescribed (29:15, **probable**); and when it calls expecting it of everyone *अव्यवहारिक* (34:07) — the three statements together assign the printed two-path scheme a **division of labour the printed text leaves open**: *anusandhan* for the discoverer, *adhyayan* for everyone else.

**Consequence for the study.** §1.8 records the two paths without saying which is for whom, and §6.2 treats entry into the circle as unresolved. The session supplies the missing allocation in the founder's voice, in MVD's own vocabulary. That resolves §6.2's question in one direction and sharpens §6.4: if study is sufficient for everyone, teacher-dependence is pedagogical, not evidential.

**The apparent counter-evidence dissolves.** At 14:12 he says *दूसरा कोई विधि है भी नहीं* — "there is no other method at all" — which I first recorded as sitting awkwardly beside 34:07. It does not. The sentence continues *तदाकार-तद्रूप विधि ही है*, and **MVD p. 80 defines that method as realisation in coexistence itself**: *सह-अस्तित्व में अनुभव ही तद्रूप, तदाकार विधि है*. On that definition there is nothing for a second method to *be* — the claim is analytic. The two statements operate at different levels: 14:12 is about what the method *is*, 34:07 about which route to it is practicable for whom. No reconciliation is needed.

---

## 9. Anti-authoritarian pedagogy — bears on §6.4

Two statements, both useful (26:50, **probable**):

> यह मंगल मैत्री से प्रस्तुति की विधि है। इसमें दादागिरी एक भी नहीं है। दादागिरी पहले था — "तुम कुछ नहीं पूछोगे।"
>
> *This is a method of presentation through goodwill and friendship. There is not a single instance of bullying in it. Bullying was the earlier way — "you will ask nothing."*

And on his own critical method (41:14, **reliable**):

> हम विचार की समीक्षा किया है; व्यक्ति की समीक्षा करने नहीं गए।
>
> *We have reviewed ideas; we did not go about reviewing persons.*

**Use.** §6.4 identifies a tension between requiring a disciplined relation to a realised teacher and claiming that understanding must be conveyable to anyone. The first quotation is direct evidence for the reading §6.4 says the texts do not supply — that the teacher's role is pedagogical and carries no evidential weight. The second is a methodological statement worth citing in the study's own defence of comparative criticism.

---

## 10. Other material, lower priority

- **The artificial-fruit analogy** (25:17–26:50, **probable**). A clay or paper fruit can be recognised as *कृत्रिम*; only fruit ripening on the root is *वास्तविक*. *यदि कृत्रिम फल से हम तृप्त हो सकते थे, उसको भी मान देते* — "if we could be satisfied by artificial fruit, we would grant it too." A usable image for the darshan's satisfaction criterion.
- **Reasoning has a limit** (18:48, **probable**): *पुरुषार्थ के साथ तर्क जुड़ा है; उसके बाद परमार्थ के साथ कोई तर्क नहीं है*. Both terms are narrower than they look, and an earlier revision of this note mistranslated them. **पुरुषार्थ = "diligence"** — conduct directed at awakening, against *कर्त्तव्य* (duty) and *विवशता* (helplessness), MVD p. 128. **परमार्थ = "benevolence"** — an *अर्थ नियोजन* term in the triad *स्वार्थ / परार्थ / परमार्थ*, "selfish, altruistic and benevolent" (MVD p. 63 glossary; also p. 146). So the claim is that reasoning travels with awakening-directed conduct but not with benevolent deployment — **not** a seen/transcendent contrast. Bears on §4.4 and on the epistemology companion, but the corrected reading is the narrower one.
- ***Kalpanashilta* and *karmswatantrata* are in *jeevan*, not the body** (10:08–10:26, **reliable**): *शरीर देखता नहीं है; शरीर देखने के लिए माध्यम है* — the body does not see; it is a medium for seeing. **SB makes the session's claim almost word for word**, including the exclusion the session states: humanity has risked its fundamental powers, "imaginativeness, freedom of action, and thoughtfulness … These powers are unique because they are **found only in humans** … Such traits and actions are not evident in" the material, pranic or animal states. MVD adds that it is "solely due to **freedom in action** that humans have the opportunity to engage in thought, desire, resolve, realisation." Supports §1.9 and [*Philosophy of Mind and Jeevan*](../Philosophy-Of-Mind-And-Jeevan/Philosophy-Of-Mind-And-Jeevan.md) — and note that both terms carry published English (*imaginativeness*, *freedom in action*), so the study can use them without inventing vocabulary.
- **Materialism and idealism both faulted** (11:26, **probable**), matching MVD p. 3 and the study's §1.12.
- ***Rahasya* and accumulation** (41:47–42:16, **reliable**): *रहस्य से हम कुछ पा नहीं सकते; संग्रह-सुविधा से हम तृप्त नहीं हो सकते* — matching §1.4 and §1.12. With the Kalidasa image of sitting on a branch and cutting it (42:55).
- **Critique of *swarga* and *moksha*** (37:44–39:39, **probable**): no model of either is exhibited on this earth; and a pointed reading of the *shanti mantra* — if peace is invoked for those in the *divi loka*, are those on earth to be left unpeaceful? Relevant to [*God, Divinity and the Sacred*](../God-Divinity-And-The-Sacred/God-Divinity-And-The-Sacred.md) rather than here.
- **Four *avasthas* only** (14:28, **probable**): *sakshatkar* occurs in *padarth*, *pran*, *jeev*, *gyan* *avastha*; there is no fifth.

**A term I initially misread.** At 04:10 the recursive stage — *प्रमाण होने की स्थिति में पुनः प्रमाण का बोध होता है* — is named, and the ASR renders it "सृत्तम्भर्य". I first read that as possibly **ऋतम्भरा** and flagged it as a likely borrowing of Patanjali's *ritambhara prajna* (YS 1.48), notable against §1.3's rejection of Patanjali's *samyama*. That framing was wrong, and checking the corpus is what showed it.

***ऋतम्भरा* is native Madhyasth Darshan vocabulary with its own glossary entry**: MVD p. 76 — *ऋतम्भरा :- सत्य सहज वैभव की अभिव्यक्ति करने की संपूर्ण पृष्ठभूमि। सत्य से परिपूर्ण संकल्प* ("the entire ground for expressing the natural glory of truth; resolve filled with truth"). More significantly it is the **fourth member of the darshan's standard five-fold projection of *jeevan***: *आशा, विचार, इच्छा, ऋतम्भरा, प्रमाण* — hope, thought, desire, *ritambhara*, evidence — at MVD pp. 75, 83 and repeatedly through SB, mapping onto *mun, vritti, chitta, buddhi, atma*.

This matters for the study directly. §1.9 renders that fourth term as "**resolve**" from MVD p. 275; the Hindi behind it is *ऋतम्भरा*, and MVD p. 76 glosses it as *संकल्प* — resolve — which confirms the study's existing translation while naming the term it translates. So there is **no Patanjali borrowing to explain**, and the glossary should carry *ritambhara* as the Hindi for the *buddhi*-level power the study already discusses. Whether this particular segment utters the word still needs the audio; that the word is the darshan's own no longer does.

---

## 11. Proposed integration

| # | Change | Where | Basis | Rests on |
|---|---|---|---|---|
| 1 | New section stating the four-stage ladder, its faculty mapping, the stage-names *drashtapad* and *jagriti*, and that stages 2–4 are automatic | New §1.10, after §1.9; renumber onward | MVD pp. 12, 99, 126; JV p. 62; §§2–5 above | **Printed** |
| 2 | Amend *anubhav* as consolidation rather than further cognition | §1.1 and glossary | §6 above (22:28); MVD p. 80 for the six-item set at *anubhav* | Printed + session |
| 3 | Recast conveyability as the ladder's terminal rung, not an external check | §1.11 (was 1.10), §6.3, Conclusion | §5 above; MVD p. 12 (*प्रमाण ही जागृत परम्परा*) | Printed + session |
| 4 | Rewrite: study *is* the practice; the corpus is silent on technique because there is none beyond study | §6.6 | §4 above (12:54) | Session |
| 5 | Assign the two paths: *anusandhan* for the discoverer, *adhyayan* for all — and record that the founder calls the former *अव्यवहारिक* in general | §1.8, §6.2 | §8 above; **MVD p. 280** supplies the two-path vocabulary the session uses | **Printed + session** |
| 6 | Note evidence that the teacher's role is pedagogical, not evidential | §6.4 | §9 above (26:50) | Session |
| 7 | Name *ऋतम्भरा* as the Hindi behind §1.9's "resolve" | §1.9 and glossary | **MVD p. 76** glossary; five-fold list at pp. 75, 83 | **Printed** |
| 8 | Add *तद्रूप/तदाकार विधि* — realisation in coexistence *is* the method, hence no second method | §1.5 or §1.10 | **MVD p. 80**, published English | **Printed** |
| 9 | Glossary: *Sakshatkar*, *Bodh*, *Praman*, *Drashtapad*, *Ritambhara*, *Prajna*, *Tadroop/Tadakar*, *Manan*, *Tulan* | Appendix | throughout | Printed |
| 10 | Editorial Note on the oral corpus as evidence; References entry for the session | Editorial Notes; References | §Provenance above | — |

**Sequencing, revised after the corpus pass.** The earlier version of this table said items 4–6 "rest on the session alone" and should wait for the audio. That is now true of only **items 4 and 6**. Item 5 — the change that most improves the study — turned out to rest on **MVD p. 280's own two-path vocabulary**, with the session supplying only the allocation between them; and items 7 and 8 are purely printed findings that need no audio at all. So the printed-anchor set is items 1, 2, 3, 5, 7, 8, 9, and all of them can be drafted now.

Items 4 and 6 remain session-only. Both are worth including — they are the answers to §6.6 and §6.4 — but they should be attributed in the study as **oral testimony with a timestamp**, not as doctrine, and the audio should be checked before the study is released.

**What this note does not settle.** The session is a teaching occasion with a sympathetic audience; it is not an argument for the ladder against alternatives. Nothing in it addresses what the study's §6.5 raises — what follows when practice does not produce *sakshatkar* — and the automatic-cascade claim of §3 above arguably makes that gap worse, since a failure anywhere downstream would have to be re-described as a failure of study.
