# Research Note: *Sakshatkar – Bodh – Anubhav – Praman* — a recorded session with A. Nagraj

**Author:** Raghava Mohan Madhwapathi ([analyticmadhyasthdarshan.org](https://analyticmadhyasthdarshan.org))

**Edited on:** September 27, 2026, 2:53 PM IST

**Status:** Internal research note (not a catalog entry). Compiled to support [*Spiritual Practice and Realization*](Spiritual-Practice-And-Realization.md), especially §§1.2–1.16, §4.2, and the open problems in §6.

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

**The full transcript and translation live in References**, not here: [`References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak.md`](https://analyticmadhyasthdarshan.org/References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak.pdf) — all 130 segments, normalised Hindi with English, per-segment reliability marks, and cross-references to the printed corpus. Raw ASR before normalisation: [`…-raw-asr.txt`](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/blob/master/References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/Sakshatkar-Bodh-Anubhav-Praman-2010-Amarkantak/Sakshatkar-Bodh-Anubhav-Praman-2010-raw-asr.txt). Folder conventions and the constraints on citing oral material: [`Nagraj-Recorded-Sessions/README.md`](https://github.com/raghavamohan/AnalyticMadhyasthDarshan/blob/master/References/Madhyasth-Darshan/Nagraj-Recorded-Sessions/README.md). This note quotes only the load-bearing passages; the transcript is the source of record.

**Three classes of reliability, marked throughout.**

- **Reliable** — phrase recurs across segments, or is corroborated by a printed text. This is a textual reliability judgement, not confirmation against the audio; load-bearing paraphrases still require that check.
- **Probable** — single clear occurrence, ASR internally consistent. Usable as provisional oral testimony with the timestamp and verification limit stated.
- **Uncertain** — reconstructed through evident ASR corruption. Flagged `[uncertain]`. **Do not quote in a released study without listening to the audio.**

**On the Hindi below.** ASR spellings have been normalised to standard Devanagari where the intended word is unambiguous (साक्षात कार → साक्षात्कार, बोत/वोट → बोध, अन्भव → अनुभव, अध्येन/अध्यान → अध्ययन, स्विकार → स्वीकार, सुभाव → स्वभाव, वस्तो → वस्तु, दृष्टापद/दृष्टापत → दृष्टापद). These are **reconstructions, not a verified transcript**. English renderings are mine and are working translations.

**Standing as evidence.** This is a teaching session, not a composed text. It is first-person report and oral exposition — the same evidential class the study's §1.16 assigns to the founder's autobiographical material, with the further discount that no one has authenticated the recording or the transcript. Its value is the proposed account of sequence and mechanism recovered from the working transcript. Repetition and agreement with print do not verify what the recording actually says.

**What a corpus pass changed, and why that reframes this note.** A systematic search of MVD, SB, JV and KD against every degraded segment (2026-08-01) recovered seven of them and settled six terms this note had earlier carried as invented glosses. The upshot is that **most of what looked like the session's own doctrine is in the printed corpus already** — the ladder's terminology (*ऋतम्भरा*, *प्रज्ञा*, *श्रुति*, *तद्रूप/तदाकार*), the six-item set at *bodh*, the two-path scheme, the *rup–gun* triads. The session's distinctive contribution is narrower and more interesting than a first reading suggested: not new doctrine, but **sequencing, mechanism, and the practical division of labour between the two paths**. Where this note now cites a printed locus, prefer it — the session is corroboration.

**Citations here are verified against the PDFs, not the markdown extracts.** An earlier revision of this note carried roughly twenty wrong page numbers. MVD's `.md` marks pages with a `page-N` *footer*, so content following the marker is on page N+1; JV's `.md` has only eight stray bare numbers and no pagination at all (one citation was 26 pages out). Every MVD and JV page below was re-derived by searching the PDF directly. The study's own pre-existing citations were correct throughout; the error was confined to this note's additions.

---

## 1. What the session is about

The opening states the agenda (00:00, **reliable**):

> साक्षात्कार, बोध, अनुभव, प्रमाण — इन मुद्दों पर थोड़ा सा प्रकाश डालने के लिए कहा गया।
>
> *Sakshatkar, bodh, anubhav, praman — I have been asked to shed a little light on these matters.*

The four terms are the subject of the whole session, which presents their ordered relation as one process. The study sets out that relation at §1.11. An ordered explanation need not imply four isolated periods: complete *bodh* in *buddhi* coincides with *anubhav* in *atma* in the printed account (MVD, p. 207).

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

**Cross-reference.** MVD p. 126 assigns the terms to faculties: affirmation of coexistence through study is *manan* in *mun* (in the form of acceptance), *tulan* in *vritti* (*गुणात्मक विधि से*, by the qualitative method), *sakshatkar* in *chitta*, and *bodh* in *buddhi*. It does not prescribe completion of *manan* before *tulan* begins. MVD p. 295 also describes the complete development of *mun* through *manan* of *vritti*'s justice-based thoughts. These are interrelated functions, not proof of a compulsory preparation timetable. The learner's study explicitly includes *shravan*, *manan*, and *arth-bodh* — listening, reflection, and understanding meaning (MVD, p. 257).

The session's *रूप-गुण-स्वभाव-धर्म* analysis concerns *what sakshatkar recognises*. MVD p. 273 adds a printed qualification: form, property, and essential nature can be understood, while *dharma* can only be realised, through study and adherence to the step-by-step instructions of one who has attained realisation.

---

## 3. The chain, and that it is automatic after the first step

The core passage (03:03–03:30, **reliable** — the phrasing recurs at 13:09):

> साक्षात्कार के बाद बोध होता है। उसके लिए अपने को कुछ करना नहीं है — अपने आप से होता है, जीवन में। बोध के बाद अनुभव होता है अपने आप में; अनुभव के बाद प्रमाण होता है अपने आप में। इन चारों चीज़ों में से पहली चीज़ साक्षात्कार यदि सफल होता है, तो बाकी तीनों क्रिया अपने आप से होता है।
>
> *After sakshatkar, bodh occurs. For that one need do nothing oneself — it occurs of itself, in jeevan. After bodh, anubhav occurs of itself; after anubhav, praman occurs of itself. Of these four, if the first — sakshatkar — succeeds, the remaining three activities occur by themselves.*

The analogy is ordinary perception (03:30, **reliable**): once you have seen something with your eyes, acceptance or rejection follows without further effort.

**Relation to the printed account.** MVD p. 7 reports *samadhi–dhyan–dharana* as the founder's practice. This oral passage describes the later activities as following naturally from successful study; it does not prescribe a separate technique for each. The automaticity remains a claim recovered from the working transcript. MVD p. 207 places complete *bodh* and *anubhav* together, and pp. 286–287 likewise connect *atma-bodh* with realisation in coexistence. The sequence should therefore not be read as requiring a waiting period between their completion.

---

## 4. *Sakshatkar* is the success condition of study

Stated twice, and this is the single most consequential claim for the study (12:54–13:09, **reliable**):

> शब्द के अर्थ में वस्तु के रूप में जो वस्तु है, वो अस्तित्व में है। … उसका नाम है साक्षात्कार। इसका नाम है अध्ययन की सफलता। यदि अध्ययन सफल होता है, उस स्थिति में स्वाभाविक रूप में बोध होता है; बोध होने के पश्चात अनुभव होता है; अनुभव होने के पश्चात प्रमाण होता है।
>
> *The vastu that stands as the meaning of a word is in existence. … That is called sakshatkar. This is what the success of study is called. If study succeeds, then in that condition bodh occurs naturally; after bodh, anubhav; after anubhav, praman.*

The point recurs (06:12, **reliable**): *इसका बैकग्राउंड क्या है? अध्ययन।* — "What is the background of this? Study." And 05:13: *उसके लिए क्या करता है? अध्ययन विधि* — study is what one actually does.

**This speaks directly to §6.6 of the study** ("The detail of practice"). The session places study at the centre of the recommended practice and calls *sakshatkar* its success. The printed account says "Study itself is worship" (MVD, p. 150), and begins the journey with methodical study (AVD, p. 223). Study includes listening, reflection, and understanding meaning (MVD, p. 257); *dhyan* focuses the faculties for understanding and, after realisation, for evidence (MVD, pp. 284–285). This supports study together with refinement, attention, and conduct. It does not establish that these have no practical disciplines or that sustained contemplation is excluded.

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

**This is a substantive identification.** In this account *praman* includes the expression of awakening, extending beyond a person's verbal report. Conveyability and conduct belong to the manifestation of realised understanding. This preserves the printed statement that realisation itself is ultimate evidence, together with the links to behaviour, work, and awakened tradition (MVD, p. 12). The stage-names themselves were not located in the printed passages reviewed: MVD p. 80 gives establishment in the seer status as the definition of *tadavalokan*, and MVD p. 33 says that awakened humans are recognisable in the seer status. The study therefore cites the session, not these printed passages, for *drashtapad* and *jagriti* as names of the stages.

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

That set is not the session's invention and does not depend on the recording. MVD states it verbatim and, decisively for this section, ties it to *anubhav*: *नियम, नियन्त्रण, संतुलन, न्याय, धर्म, सत्य, अनुभव के फलन में प्रमाणित होता है* — "is evidenced in the fruition of realisation" (MVD, p. 80). The same six appear at MVD p. 32, and p. 174 derives them as a chain (*नियम ही नियंत्रण; नियंत्रण ही संतुलन; संतुलन पूर्वक जीना ही मानव में न्याय …*). The printed account evidences these six in the fruition of realisation; it does not say that they are absent from every prior activity of understanding. The working session proposes that they are understood in *bodh*/*sakshatkar* and become firm in *anubhav*. **Cite MVD for the set and its fruition; attribute the stronger sequencing claim to the working session.**

**What the passage supports.** The working transcript presents *anubhav* as the consolidation (*पक्का होना*) of what *sakshatkar* recognises. Its stronger assertion that nothing further is understood still needs verification against the audio at 22:28. AVD p. 224 defines knowing, believing, and recognising as definitive understanding, and attaining the point of satisfaction in these as realisation. That printed definition supports a connected account of understanding and its satisfaction; by itself it does not establish that every later activity adds no content. MVD p. 207 places complete *bodh* and *anubhav* together, while p. 273 distinguishes understanding form, property, and essential nature from realising *dharma*. The study preserves these relations without reducing realisation to an idle repetition of recognition.

---

## 7. *Samadhi*: the negative finding in his own voice

The autobiographical passage the study's §1.3 rests on, here stated orally (16:36–17:08, **reliable**):

> हम समाधि देखा — समाधि में एक भी ज्ञान नहीं हुआ। उल्टा क्या देखते रहे? देखते ही रहे — हमारा आशा, विचार, इच्छा चुप हो गए। … काल, समय, शरीर, स्थान — इनका अभाव।
>
> *We saw samadhi — in samadhi not one instance of knowledge occurred. What did we go on seeing instead? We just kept watching — our hope, thought and desire fell silent. … Time, body, place — their absence.*

And what he wrote about it (17:16–17:30, **probable**):

> मुझको समाधि के बाद, भूत और भविष्य की पीड़ा वर्तमान में वर्त नहीं है।
>
> *For me, after samadhi, the affliction of past and future does not obtain in the present.*

Then the turn (17:30, **reliable**): *उसके बाद जब संयम हुआ, जब पता लगा, अनुभव हुआ — हम दृष्टापद में हो गए हैं, सह-अस्तित्व में।* — "After that, when samyama occurred, when it became known, anubhav occurred — we came to be in drashtapad, in coexistence."

**Cross-reference.** MVD p. 7, JV pp. 12–13. The working transcription *समाधि में एक भी ज्ञान नहीं हुआ* appears broader than the printed "the event of knowing the unknown did not occur". It must not silently widen the printed finding into a denial of all awareness: the autobiographical account retains the awareness of "I am", while the founder's questions remain unanswered. The evidential problem is his inability to present the attained *samadhi* as proof of the understanding sought. The study distinguishes that finding from the darshan's positive status for realised understanding as evidence (MVD, p. 12).

---

## 8. *Samadhi–samyama* is declared impractical as a general method

This passage bears on §1.12, §6.2 and §6.5 together (34:07, **probable**). Its printed counterparts are AVD pp. 72–74, which ask why the traditional methods are not recommended and answer that the silence method yields only self-limited happiness, that success within a lifetime cannot be assured, and that silence is against the nature of *jeevan*; AVD p. 225, which names the two ways as exploration and study with inquiry; and MVD pp. 280–281, which describe exploration as the route of a seeker accomplished in *samadhi*:

> सब कोई समाधि-संयम करेगा, अनुसंधान करेगा — यह अव्यवहारिक बात है। समाधि-संयम, क्या हर व्यक्ति अनुसंधान करके जी पाएगा? नहीं होगा। तब क्या विधि है? सबके लिए पहुँचने की अध्ययन विधि है। पहले श्रुति विधि थी …
>
> *That everyone will do samadhi-samyama and research — this is impractical. Samadhi-samyama: will every person manage to live by doing research? It will not happen. Then what is the method? For everyone to arrive, the method is study. Earlier the method was shruti …*

Immediately before (33:40, **probable**):

> समाधि तो बहुत सारे लोगों को हुआ है … किन्तु अनुभवमूलक विधि से हुआ है, ऐसा हम कह नहीं सकते।
>
> *Many people have attained samadhi … but that it happened by the realisation-based way, that we cannot say.*

And on *shruti* (34:41, **probable** after recovery): the working transcript criticises an earlier *shruti* method for not bringing the pervasive reality (*व्यापक वस्तु*) to be understood as truth, and replaces *"ब्रह्म सत्य, जगत मिथ्या"* with *"ब्रह्म सत्य, जगत शाश्वत"*. The printed contrast is also present (MVD, pp. 3, 12). The meaning of *shruti* in this retrospective oral passage needs its own context and audio check. In the darshan's faculty definitions *shruti* means giving language to understanding (MVD, pp. 324, 329); that definition alone does not show that the criticised earlier method has the same sense. Neither use should be confused with *shravan*, listening, which is explicitly part of the learner's study (MVD, p. 257).

**The decisive link: *अनुसंधान* is MVD's own first path.** This is what makes the section usable rather than merely suggestive. MVD p. 280 — the passage §1.12 quotes — states the two processes for eliminating *बौद्धिक रहस्यता* as *एक — अनुसंधान। दो — अनुसरण, अनुकरण, अध्ययन*, published "One - Exploration. Two - Following, Emulation, Study." So when the session answers a question about bypassing study with *दूसरा विधि है — अनुसंधान* (28:43), it is naming **MVD's Exploration path by its Hindi name**; when it says that path runs through *समाधि-संयम* carried out as prescribed (29:15, **probable**); and when it calls expecting it of everyone *अव्यवहारिक* (34:07) — the three statements together assign the printed two-path scheme a **division of labour**: *anusandhan* for the discoverer, *adhyayan* for everyone else. AVD pp. 72–74 and 225 state the same allocation in print.

**Consequence for the study.** §1.12 presents study as the generally recommended route, with the session as provisional corroboration, and §6.2 asks about warrant and transmission. The recommendation does not make the teacher's role merely pedagogical: the teacher is also described as the bearer and carrier of the evidence of awakening (AVD, p. 261). The learner's examination of teaching remains necessary (AVD, pp. 225–226); §6.4 considers that requirement alongside dedication to the realised teacher (MVD, pp. 273, 317).

**The scope of the apparent counter-evidence.** At 14:12 the working transcript reads *दूसरा कोई विधि है भी नहीं* — "there is no other method at all" — followed by *तदाकार-तद्रूप विधि ही है*. This load-bearing wording still requires an audio check. MVD p. 80 states *सह-अस्तित्व में अनुभव ही तद्रूप, तदाकार विधि है* — "Realisation in coexistence itself is the way of absolute-accordance and absolute-resonance." That sentence belongs to the account of pursuing the ideal (*ishta-sevan*), whose goals are oneness, accordance, abiding near, and continuous observance of the ideal, and the ideal is awakening. It suggests a distinction between accordance with the ideal through realisation and the practical routes towards realisation discussed at 34:07. This is a contextual reading to test against the recording, not a settled reconciliation. The p. 80 sentence does not support the stronger reading that method and realisation are analytically identical.

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

**Use.** §6.4 sets out a textual tension between full dedication in obedience to a realised human (MVD, p. 317) and adherence to a realised person's instructions (MVD, p. 273) on one side, and each learner's examination and acceptance or rejection of what is presented (AVD, pp. 225–226) on the other. The first quotation supports a stance of teaching through goodwill and allowing questions. It does not negate the teacher's stated role as bearer of evidence (AVD, p. 261). The second supports criticism of ideas, while the self-examination passage at 31:15–32:48 asks whether one says, does, and lives the same thing. All remain working oral testimony pending the relevant audio checks.

---

## 10. Other material, lower priority

- **The artificial-fruit analogy** (25:17–26:50, **probable**). A clay or paper fruit can be recognised as *कृत्रिम*; only fruit ripening on the root is *वास्तविक*. *यदि कृत्रिम फल से हम तृप्त हो सकते थे, उसको भी मान देते* — "if we could be satisfied by artificial fruit, we would grant it too." A usable image for the darshan's satisfaction criterion.
- **Reasoning has a limit** (18:48, **probable**): *पुरुषार्थ के साथ तर्क जुड़ा है; उसके बाद परमार्थ के साथ कोई तर्क नहीं है*. Both terms are narrower than they look, and an earlier revision of this note mistranslated them. **पुरुषार्थ = "diligence"** — conduct directed at awakening, against *कर्त्तव्य* (duty) and *विवशता* (helplessness), MVD p. 128. **परमार्थ = "benevolence"** — an *अर्थ नियोजन* term in the triad *स्वार्थ / परार्थ / परमार्थ*, "selfish, altruistic and benevolent" (MVD p. 63 glossary; also p. 146). So the claim is that reasoning travels with awakening-directed conduct but not with benevolent deployment — **not** a seen/transcendent contrast. Bears on §4.4 and on the epistemology companion, but the corrected reading is the narrower one.
- ***Kalpanashilta* and *karmswatantrata* are in *jeevan*, not the body** (10:08–10:26, **reliable**): *शरीर देखता नहीं है; शरीर देखने के लिए माध्यम है* — the body does not see; it is a medium for seeing. **SB makes the session's claim almost word for word**, including the exclusion the session states: humanity has risked its fundamental powers, "imaginativeness, freedom of action, and thoughtfulness … These powers are unique because they are **found only in humans** … Such traits and actions are not evident in" the material, pranic or animal states. MVD adds that it is "solely due to **freedom in action** that humans have the opportunity to engage in thought, desire, resolve, realisation." Supports §1.9 and [*Philosophy of Mind and Jeevan*](../Philosophy-Of-Mind-And-Jeevan/Philosophy-Of-Mind-And-Jeevan.md) — and note that both terms carry published English (*imaginativeness*, *freedom in action*), so the study can use them without inventing vocabulary.
- **Materialism and idealism both faulted** (11:26, **probable**), matching MVD p. 3 and the study's §1.15.
- ***Rahasya* and accumulation** (41:47–42:16, **reliable**): *रहस्य से हम कुछ पा नहीं सकते; संग्रह-सुविधा से हम तृप्त नहीं हो सकते* — matching §1.5 and §1.15. With the Kalidasa image of sitting on a branch and cutting it (42:55).
- **Critique of *swarga* and *moksha*** (37:44–39:39, **probable**): no model of either is exhibited on this earth; and a pointed reading of the *shanti mantra* — if peace is invoked for those in the *divi loka*, are those on earth to be left unpeaceful? Relevant to [*God, Divinity and the Sacred*](../God-Divinity-And-The-Sacred/God-Divinity-And-The-Sacred.md) rather than here.
- **Four *avasthas* only** (14:28, **probable**): *sakshatkar* occurs in *padarth*, *pran*, *jeev*, *gyan* *avastha*; there is no fifth.

**A term I initially misread.** At 04:10 the recursive stage — *प्रमाण होने की स्थिति में पुनः प्रमाण का बोध होता है* — is named, and the ASR renders it "सृत्तम्भर्य". I first read that as possibly **ऋतम्भरा** and flagged it as a likely borrowing of Patanjali's *ritambhara prajna* (YS 1.48), notable against §1.4's rejection of Patanjali's *samyama*. That framing was wrong, and checking the corpus is what showed it.

***ऋतम्भरा* is native Madhyasth Darshan vocabulary with its own glossary entry**: MVD p. 76 — *ऋतम्भरा :- सत्य सहज वैभव की अभिव्यक्ति करने की संपूर्ण पृष्ठभूमि। सत्य से परिपूर्ण संकल्प* ("the entire ground for expressing the natural glory of truth; resolve filled with truth"). More significantly it is the **fourth member of the darshan's standard five-fold projection of *jeevan***: *आशा, विचार, इच्छा, ऋतम्भरा, प्रमाण* — hope, thought, desire, *ritambhara*, evidence — at MVD pp. 75, 83 and repeatedly through SB, mapping onto *mun, vritti, chitta, buddhi, atma*.

This matters for the study directly, and it needs a distinction this note first missed. MVD p. 275 lists the activity sequence as hope, thought, desire, resolve, and realisation in existence, and its Hindi there is *संकल्प* (resolve) and *अस्तित्वानुभूति* (realisation in existence), not *ऋतम्भरा* and *प्रमाण*. The five-fold list of powers at MVD pp. 75 and 84 is the one that reads *आशा, विचार, इच्छा, ऋतम्भरा, प्रामाणिकता*. MVD p. 76 defines the two terms separately: *ऋतम्भरा* as resoluteness, "a resolve suffused with truth", and *संकल्प* as resolve, the intellectual activity that sustains a rightly made acceptance. So there is **no Patanjali borrowing to explain**, and the study's glossary carries *ritambhara* (resoluteness) and *sankalp* (resolve) as distinct terms. Whether this particular segment utters the word still needs the audio; that the word is the darshan's own no longer does.

---

## 11. Proposed integration

| # | Change | Where | Basis | Rests on |
|---|---|---|---|---|
| 1 | Explain recognition, understanding, realisation, and evidence with the faculty correspondences; distinguish learner study from a compulsory timetable | §1.11 | MVD pp. 12, 99, 126, 207, 257, 295; JV p. 62; §§2–5 above | **Printed** for the connected account and concurrent completion; working session for the stage-names and automaticity |
| 2 | Define realisation as the satisfaction of definitive understanding; attribute the stronger consolidation claim to the working session | §1.11 and glossary | §6 above (22:28); **AVD p. 224**; MVD pp. 80, 207, 273 | **Printed** for satisfaction; session for nothing further being understood |
| 3 | Present conveyability and conduct as expressions of realisation, usable in assessing a claim to it | §§1.11, 1.13, 6.3 | §5 above; MVD p. 12 (*प्रमाण ही जागृत परम्परा*) | Printed + session |
| 4 | Present study with listening, reflection, understanding meaning, focused attention, refinement, and conduct | §§1.6, 6.6 | §4 above (12:54); **MVD pp. 150, 257, 284–285**; AVD p. 223 | **Printed**, with provisional session corroboration |
| 5 | Assign the two paths: *anusandhan* for the discoverer, *adhyayan* for all | §§1.12, 6.2 | §8 above; **MVD pp. 280–281**; **AVD pp. 72–74, 225** | **Printed + session** |
| 6 | Preserve inquiry and learner examination alongside the teacher's role as bearer of evidence | §6.4 | §9 above (26:50, 31:15–32:48, 41:14); MVD pp. 273, 317; AVD pp. 225–226, 261 | Working session for the founder's stance; print for both obligations |
| 7 | Distinguish *ऋतम्भरा* (resoluteness) from *संकल्प* (resolve) | §1.9 and glossary | **MVD pp. 75–76, 84, 275** | **Printed** |
| 8 | Read *तद्रूप/तदाकार विधि* in its p. 80 context of pursuing the ideal | §1.11 | **MVD p. 80**, published English; MVD p. 150; KD p. 40 | **Printed** |
| 9 | Glossary: the faculty and practice terms, distinguishing *shravan* from *shruti* and removing compulsory *manan–tulan* chronology | Appendix | MVD pp. 126, 257, 295, 324, 329; throughout | Printed |
| 10 | Editorial Note on the oral corpus as evidence; References entry for the session | Editorial Notes; References | §Provenance above | — |

**Standing after the printed-corpus passes.** The stage-names, automaticity, the stronger claim that nothing further is understood, and the particular oral statements about pedagogy still depend on the working transcript. Printed definitions support a connected account without independently proving every stronger oral formulation. The load-bearing passages at 22:28, 34:07, and 14:12 require the checks identified in the transcript's verification section. Oral material should remain attributed by timestamp with this limit visible; neither this note nor its agreement with print substitutes for listening to the recording.

**What this note does not settle.** The session is a teaching occasion with a sympathetic audience; it is not an argument for the sequence against alternatives. It does not supply a diagnostic procedure for unsuccessful practice. The printed texts state conditions under which reflection and *upasana* fail (MVD, p. 284; KD, p. 38), and assign successful study jointly to teachers, guardians, teaching, and educational content and procedure (MVD, p. 270). If the automaticity claim is accepted, a missing later activity raises a question about whether *sakshatkar* was achieved; the claim itself also remains open to examination. Confidence that a stage has occurred is not the same as its occurrence. The texts reviewed do not supply a public case series that adjudicates these alternatives.
