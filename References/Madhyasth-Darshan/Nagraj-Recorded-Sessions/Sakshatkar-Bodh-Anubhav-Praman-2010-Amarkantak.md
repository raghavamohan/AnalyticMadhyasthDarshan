# साक्षात्कार – बोध – अनुभव – प्रमाण

**Sakshatkar – Bodh – Anubhav – Praman** — recorded session with Shri A. Nagraj

**Occasion:** *Anubhav Shivir* (Realisation Camp), January 2010, Amarkantak
**Recording:** 45:00; posted by Rakesh Gupta (translator of MVD, SB, JV), <https://youtu.be/gIvVme-Sa5s>
**Audio:** not stored in this repository — **listen at the URL above when checking a timestamp below.** The file transcribed here was `sha256:61be0537960ca72aa64c9cebe02b11acdd0878cd0dfeec3ae55bfbc9061558d6` (35,541,468 bytes, MP3), so a future download can be checked against the copy these timestamps refer to.
**Transcript coverage:** 00:00–44:32, 130 segments
**Compiled:** August 1, 2026 · **Status:** Working transcript and translation — **not** a published or authenticated text

---

## What this file is, and what it is not

This is a **machine-produced transcript of an oral session, with a working English translation**. It has none of the standing of MVD, SB, JV or KD. Treat it as it is labelled:

- **Nobody has authenticated the recording.** Attribution rests on the posting channel (Rakesh Gupta's) and on internal evidence — the speaker recounts the Amarkantak *samadhi* episode in the first person, matching MVD p. 7 and JV p. 13.
- **The Hindi below is reconstructed, not heard.** It is automatic speech recognition, lightly normalised (see Conventions). It has **not** been checked against the audio by a Hindi speaker.
- **The English is a working translation of that reconstruction** — a translation of a transcription of speech, two removes from the source.

**Before quoting any line of this file in a released study, listen to the audio at the cited timestamp.** The reliability marks below say where that matters most.

### Why not use YouTube's captions

YouTube's Hindi auto-captions for this video are unusable: ~6,700 characters for 45 minutes, with multi-minute gaps and corruption that destroys the key terms (*बोध* comes out as "वोट", *ऋतम्भरा* as "सृत्तम्भर्य"). This transcript is ~20,500 characters across 130 segments with no gap over 60 seconds.

### How it was produced

Whisper `large-v3` (int8, CPU, 16 kHz, `language=hi`, `beam_size=5`), in two passes whose difference affects reliability:

| Span | Pass | Character |
|---|---|---|
| 00:00–18:08 | Sequential, no VAD, temperature fallback | Short segments, finer timestamps. **The doctrinal core falls here.** |
| 18:20–44:32 | Batched pipeline, VAD-segmented | Longer merged segments; short utterances at VAD boundaries can be clipped |

The two passes were run over the same 03:00–06:00 span as a control and produced identical wording, which is the basis for trusting the batched span. Raw output before normalisation: [`Sakshatkar-Bodh-Anubhav-Praman-2010-raw-asr.txt`](Sakshatkar-Bodh-Anubhav-Praman-2010-raw-asr.txt).

### Reliability marks

Each segment below carries one:

- **[R] Reliable** — phrasing recurs across segments, or is corroborated by a printed text. Safe to paraphrase.
- **[P] Probable** — single clear occurrence, internally consistent. Usable with the timestamp cited.
- **[U] Uncertain** — reconstructed through evident corruption; sense is a best reading. **Do not quote.**

Where a word is corrupt beyond reconstruction, the Hindi keeps the ASR form and the English marks it `[unclear]`. Passages where the speaker is inaudible or the recording carries only music appear as gaps in the timestamps; they are not silently bridged.

**Where a printed text fixes a degraded passage, it is used — and said so.** A systematic pass over the primary texts (MVD, SB, JV, KD) was run against every **[U]** segment on 2026-08-01. Each segment it improved carries an italic note naming the locus and the reasoning, so the recovery can be rejected on its merits. Words the ASR did not carry are bracketed, always.

The pass moved **seven** segments out of **[U]** — 05:28, 07:33, 14:16, 22:58, 23:27, 29:15, 34:41 — and left the rest, which matters as much: where the corpus had nothing to offer (33:07, *शुकदेव*) or where a term the transcript used turned out **not** to be darshan vocabulary (15:20, *प्रगटनशील*), that is recorded on the segment rather than quietly smoothed over. A search that only ever confirms is not a check.

**Timestamps are the ASR's own.** None is invented. Where one ASR segment ran long enough to split for readability, the continuation keeps the parent timestamp and is marked `cont.` — so every heading here can be located in [`…-raw-asr.txt`](Sakshatkar-Bodh-Anubhav-Praman-2010-raw-asr.txt). There is one such split, at 04:43.

---

## Conventions

**Hindi normalisation.** ASR spellings are corrected to standard Devanagari only where the intended word is unambiguous from context and recurrence: साक्षात कार/सक्षात कर → साक्षात्कार · बोत/वोट/भूत(in-context) → बोध · अन्भव → अनुभव · अध्येन/अध्यान/अधेन → अध्ययन · स्विकार → स्वीकार · सुभाव → स्वभाव · वस्तो/वस्तु → वस्तु · दृष्टापत/दर्श्टा → दृष्टापद · सायम → संयम · समाधी → समाधि · जिग्यासा → जिज्ञासा · अन्संधान → अनुसंधान · तिब्रता → तीव्रता · वस्ता → अवस्था · सहास्तित्व → सह-अस्तित्व. Sentence punctuation is added for readability. **Words the ASR did not carry appear only in square brackets**, and only where a printed text or a cleaner parallel segment fixes them — see the note under *Reliability marks* and the two cases at 22:58 and 24:41. Unbracketed text is always a normalisation of something the ASR produced.

**Terminology.** English follows `MD-Mapping.xlsx` and Rakesh Gupta's published MVD/JV wherever they have a reading. The four title terms are **left transliterated with a gloss on first use**, deliberately: these are the terms under investigation, and fixing an English word for them here would prejudge what the study has to determine.

| Hindi | Rendering here | Authority |
|---|---|---|
| साक्षात्कार | *sakshatkar* — "direct recognition" | MVD p. 126 published English; "revelation" at JV p. 62 |
| बोध | *bodh* — "enlightenment" | MD-Mapping (note: awareness); MVD p. 126 |
| अनुभव | realisation | MD-Mapping; MVD throughout |
| प्रमाण | evidence (*praman*) | MD-Mapping (note: evidence, standard); MVD p. 12 |
| दृष्टापद | the seat of the Seer | दृष्टा = Seer (MD-Mapping); **MVD p. 80** — *दृष्टापद प्रतिष्ठा* is the definition of *तदावलोकन*, published "being established in the seer status in coexistence" |
| जागृति | awakening | MVD |
| रूप / गुण / स्वभाव / धर्म | form / property / essential nature / dharma | KD conventions, settled 2026-07-08 |
| गुणात्मक परिवर्तन | qualitative transformation | MD-Mapping (adjectival compound row) |
| अवस्था | state (*avastha*) | MVD — the four states: पदार्थ, प्राण, जीव, ज्ञान |
| अध्ययन | study | MVD |
| कल्पनाशीलता | imaginativeness | **SB published English** (recurring; e.g. "imaginativeness, freedom of action, and thoughtfulness") |
| कर्मस्वतंत्रता | freedom in action | **MVD published English** ("Freedom in action provides humans with the potential for both progress and decline"); SB uses "freedom of action" |
| विचारशीलता | thoughtfulness | **SB published English** — third member of the same triad |
| तद्रूप / तदाकार / तादात्म्य / तत्सान्निध्य / तदावलोकन | absolute-accordance / absolute-resonance / absolute-oneness / absolute-connectedness / absolute-observance | **MVD p. 80 — published English, not a working gloss.** The prefix *तत्-* denotes *जागृति*: "Awakening is indicated by the word 'absolute'" (MVD p. 80) |
| अनुसंधान | exploration | **MVD p. 280 published English** — *एक-अनुसंधान* is rendered "One - Exploration", the first of the two paths; MVD p. 173 also renders it "exploration" |
| पुरुषार्थ | diligence | **MVD p. 128 published English** — behaviour towards awakening, against *कर्त्तव्य* (duty) and *विवशता* (helplessness) |
| परमार्थ | benevolence | **MVD p. 63 glossary, published English** — in the triad *स्वार्थ / परार्थ / परमार्थ*, "selfish, altruistic and benevolent"; also p. 146 |

**No working glosses remain.** Every term in the table above now rests on published MVD or SB English. That was not true of earlier revisions of this file, and how the flags came down is worth recording, because it bears on how much to trust an "absent from the corpus" claim:

| Term | Was flagged as | Actually | Found in |
|---|---|---|---|
| तद्रूप / तदाकार | working gloss "becoming-of-that-form" | **absolute-accordance / absolute-resonance** | MVD p. 80 |
| कल्पनाशीलता | working gloss | **imaginativeness** — my gloss was right, just unsourced | SB |
| कर्मस्वतंत्रता | working gloss | **freedom in action** — right, unsourced | MVD |
| अनुसंधान | working gloss "research" | **exploration** — and it is MVD p. 280's *first path* | MVD pp. 173, 280 |
| पुरुषार्थ | working gloss "human endeavour" | **diligence** — narrower: conduct directed at awakening | MVD p. 128 |
| परमार्थ | working gloss "the ultimate good" | **benevolence** — an *अर्थ नियोजन* term, not a soteriological one | MVD p. 63 |

Six of six were in the corpus all along. Two of my glosses were right but unsourced; four were wrong, and two of those (*पुरुषार्थ*, *परमार्थ*) were wrong in a way that changed a translation's sense (see 18:48). **The lesson for anyone extending this file: a "working gloss" flag here recorded that I had not searched properly, not that the darshan lacks the term. Search MVD *and* SB, with space-insensitive matching, before inventing English.**

---

## Contents

| § | Timestamps | Subject |
|---|---|---|
| [1](#1-the-agenda) | 00:00–00:29 | The agenda |
| [2](#2-sakshatkar-redefined-word-meaning-vastu) | 00:30–02:53 | *Sakshatkar* redefined: word, meaning, *vastu* |
| [3](#3-the-four-stage-chain) | 03:03–04:52 | The four-stage chain, and that it runs by itself |
| [4](#4-what-is-recognised-and-how-study-does-it) | 05:04–07:20 | What is recognised; study as the means |
| [5](#5-repetition-imaginativeness-and-the-body-as-medium) | 07:21–11:42 | Repetition; imaginativeness; the body as medium |
| [6](#6-study-is-what-succeeds-and-the-stages-get-their-names) | 12:13–15:31 | Study is what succeeds; each stage named |
| [7](#7-samadhi-and-what-was-not-found-in-it) | 15:50–18:08 | *Samadhi*, and what was not found in it |
| [8](#8-the-limit-of-reasoning-and-the-path-restated) | 18:20–21:13 | The limit of reasoning; the path restated |
| [9](#9-the-key-qa-what-anubhav-adds-to-bodh) | 21:58–24:41 | **The key Q&A: what realisation adds to *bodh*** |
| [10](#10-the-artificial-fruit-and-teaching-without-coercion) | 25:17–27:47 | The artificial fruit; teaching without coercion |
| [11](#11-can-sakshatkar-occur-without-study) | 28:16–30:47 | Can *sakshatkar* occur without study? |
| [12](#12-hearsay-self-examination-and-the-limits-of-precedent) | 31:15–34:41 | Hearsay, self-examination, and the limits of precedent |
| [13](#13-a-digression-on-solar-heat-and-nuclear-testing) | 35:15–37:12 | A digression on solar heat and nuclear testing |
| [14](#14-swarga-moksha-and-the-shanti-mantra) | 37:44–41:14 | *Swarga*, *moksha*, and the *shanti mantra* |
| [15](#15-mystery-accumulation-and-what-humans-have-actually-built) | 41:47–44:32 | Mystery, accumulation, and what humans have built |

---

## 1. The agenda

**[00:00] [R]**
> साक्षात्कार, बोध, अनुभव, प्रमाण। साक्षात्कार, बोध, अनुभव, प्रमाण। इन मुद्दों पर थोड़ा सा प्रकाश डालने के लिए कहा गया। एक बात है न।
>
> *Sakshatkar, bodh, realisation, evidence. Sakshatkar, bodh, realisation, evidence. I have been asked to shed a little light on these matters. There is a point here, isn't there.*

**[00:13] [U]**
> अध्ययन। अध्ययन। ठीक है। ठीक है। … साक्षात्कार नहीं है।
>
> *Study. Study. All right. All right. … [unclear] is not sakshatkar.*

---

## 2. *Sakshatkar* redefined: word, meaning, *vastu*

**[00:30] [R]**
> साक्षात्कार के बारे में अभी तक मान्यता है — हम जो आँखों से देखते हैं, इसको साक्षात्कार माना जाता है।
>
> *The accepted view of sakshatkar so far is this: what we see with the eyes is taken to be sakshatkar.*

**[00:41] [P]**
> अभी हम जो अनुसंधान किया है, उसके अनुसार शब्द का अर्थ होता है।
>
> *According to the research we have now done, a word has a meaning.*

**[00:50] [R]**
> जैसे सामने बैठे हुए आदमी का एक किसी का नाम है। नाम को बोलने पर नाम के अर्थ में वह आदमी होता है। होता है कि नहीं होता है?
>
> *For instance, the man sitting in front has a name. When the name is spoken, in the meaning of that name there is that man. Is that so or is it not?*

**[01:02] [R]**
> नाम के अर्थ में आदमी होता है कि नहीं? होता है। उसी प्रकार हर एक शब्द के अर्थ में एक वस्तु होता है — अस्तित्व में।
>
> *In the meaning of the name, is there the man or not? There is. In the same way, in the meaning of every single word there is a vastu — in existence.*

**[01:15] [R]**
> अस्तित्व में वस्तु होता है। जैसे हर एक व्यक्ति का नाम, हर एक वस्तु का नाम, हर एक शब्द का नाम।
>
> *In existence there is the vastu. As with every person's name, every object's name, every word's name.*

**[01:25] [P]**
> हर एक शब्द एक नाम है — क्रिया का नाम है या वस्तु का नाम है। ठीक है। इन क्रियाओं अथवा वस्तुओं के नाम के रूप में जितने भी शब्द का प्रयोग किया है, किताब में लिखा है, जो प्रयोग उसमें पाते हैं — क्रिया के रूप में अथवा वस्तु के रूप में …
>
> *Every word is a name — the name of an activity, or the name of a vastu. All right. However many words have been used as names of these activities or objects, written in books, whatever usage we find there — as activity or as vastu …*

**[01:55] [R]**
> पहले कहता है, आँखों से दिखता है वो साक्षात्कार। अभी तक अपन क्या मानते हैं — आँखों से दिखता है वो साक्षात्कार। अभी जो हम कह रहे हैं, समझ में आता है तो वो साक्षात्कार। दोनों में क्या अंतर है? दोनों में यह अंतर है — जैसे हम वस्तु को देखते हैं, उसमें रूप …
>
> *Formerly it is said: what is visible to the eyes, that is sakshatkar. Until now what do we hold? What is visible to the eyes is sakshatkar. What we are now saying is: when it comes to be understood, that is sakshatkar. What is the difference between the two? The difference is this — as we look at a vastu, in it form …*

**[02:25] [R]**
> मात्रात्मक-गुणात्मक परिवर्तन होता है। हर क्रिया में मात्रात्मक-गुणात्मक परिवर्तन देखने को मिलता है। समय देखने को मिलता है। इसका नाम है साक्षात्कार।
>
> *Quantitative and qualitative transformation occurs. In every activity, quantitative and qualitative transformation is to be observed. Time is to be observed. This is called sakshatkar.*

**[02:38] [R]**
> हर वस्तु में रूप, गुण, स्वभाव, धर्म अविभाज्य रूप में वर्तमान रहता है — तो आपको सुना दिया।
>
> *In every vastu, form, property, essential nature and dharma remain present inseparably — so I have told you.*

**[02:47] [R]**
> ठीक है न। हर [वस्तु] में रूप, गुण, स्वभाव, धर्म — अविभाज्य।
>
> *All right. In every [vastu]: form, property, essential nature, dharma — inseparable.*

**[02:53] [R]**
> हर वस्तु को हम रूप-गुण-स्वभाव[-धर्म] के साथ पहचान पाते हैं — उसका नाम है बोध अथवा साक्षात्कार।
>
> *When we can recognise every vastu together with its form, property, essential nature [and dharma] — that is called bodh, or sakshatkar.*

---

## 3. The four-stage chain

**[03:03] [R]** — *the core statement; recurs at 13:09*
> साक्षात्कार के बाद बोध होता है। उसके लिए अपने को कुछ करना नहीं है। अपने आप से होता है, जीवन में।
>
> *After sakshatkar, bodh occurs. For that one need do nothing oneself. It occurs of itself, in jeevan.*

**[03:11] [R]**
> तो बोध के बाद अनुभव होता है अपने आप में; अनुभव के बाद प्रमाण होता है अपने आप में। इन चारों चीज़ों में से पहली चीज़ साक्षात्कार यदि सफल होता है, तो बाकी तीनों क्रिया अपने आप से होता है। ठीक है।
>
> *So after bodh, realisation occurs of itself; after realisation, evidence occurs of itself. Of these four things, if the first — sakshatkar — succeeds, then the remaining three activities occur by themselves. All right.*

**[03:30] [R]**
> जैसे आँखों से देखने के बाद स्वीकार होना, अस्वीकार होना होता है कि नहीं होता है?
>
> *Just as, after seeing with the eyes, acceptance or rejection follows — does it or does it not?*

**[03:37] [R]**
> यह स्वीकारना चाहिए, नहीं स्वीकारना चाहिए — ऐसा होता है कि नहीं?
>
> *"This should be accepted, this should not be accepted" — does that happen or not?*

**[03:41] [R]**
> बहुत सारी चीज़ें हम देखते हैं; कुछ बात को स्वीकारते हैं, कुछ बात को नहीं स्वीकारते हैं।
>
> *We see a great many things; some we accept, some we do not accept.*

**[03:47] [R]**
> करते हैं कि नहीं? … यह इस तरह से बोध। जो साक्षात्कार की महिमा यह है — साक्षात्कार [के बाद रुकना] नहीं होता है, बोध होता है; बोध होने पर अनुभव होता है; अनुभव होने पर प्रमाण होता है। यह इस प्रकार। प्रमाण होने की स्थिति में, पुनः प्रमाण का बोध होता …
>
> *Do we or not? … Bodh in this way. This is the greatness of sakshatkar — it does not [stop at] sakshatkar; bodh occurs; on bodh occurring, realisation occurs; on realisation occurring, evidence occurs. In this manner. And in the condition of evidence having occurred, again there is bodh of the evidence …*

**[04:17] [R]**
> अपने में अनुभव होता है। उसका प्रमाण क्या हुआ? प्रमाण के रूप में वस्तु का बोध कराने में अधिकार बन गए। क्या बन गए?
>
> *Realisation occurs in oneself. What has become its evidence? In the form of evidence, one has become entitled to bring about bodh of the vastu [in another]. Become what?*

**[04:35] [R]**
> जिस वस्तु का हमें ज्ञान हुआ, अनुभव हुआ — उसका नाम है ज्ञान।
>
> *The vastu of which we came to have knowledge, came to have realisation — that is what is called knowledge.*

**[04:43] [R]** — *the operational definition of praman*
> वह प्रमाण क्या चीज़ है? दूसरे को बोध कराने की ताकत।
>
> *What is that evidence? The power to bring about bodh in another.*

**[04:43 cont.] [U]**
> पुनः और एक बार, और एक बार। तो वस्तु जब हम पहचानते हैं — शब्द के रूप में अस्तित्व में वस्तु को पहचानते हैं — उसमें क्या पहचानना? रूप के साथ गुण, गुण के साथ स्वभाव, स्वभाव के साथ धर्म को पहचानना …
>
> *Again, once more, once more. So when we recognise a vastu — recognise the vastu in existence by way of the word — what is to be recognised in it? With form the property, with property the essential nature, with essential nature the dharma …*

---

## 4. What is recognised, and how study does it

**[05:13] [P]**
> नहीं तो हम समझें, नहीं तो किसी को समझाएँ — उसके लिए क्या करता है? अध्ययन विधि। अध्ययन में रूप, गुण, स्वभाव, धर्म के बारे में चर्चा … स्पष्ट कर दिया।
>
> *Otherwise, whether we ourselves understand or explain to someone — for that, what does one do? The method of study. In study, the discussion of form, property, essential nature, dharma … has been made clear.*

**[05:28] [P]**
> अगर माने रूप के बारे में — आकार, आयतन, घन के रूप में; सम, विषम, मध्यस्थ के रूप में … गुण के रूप में; और स्वभाव को — पदार्थावस्था में अलग, प्राणावस्था में अलग, जीवावस्था में अलग, ज्ञानावस्था में अलग …
>
> *If, that is, as to form — as shape, volume and solid; as generative, degenerative and mediative … as property; and essential nature — different in the material state, different in the pranic state, different in the animal state, different in the knowledge state …*
>
> *Recovered from the primary texts.* The ASR gave `आकार वाईत अन्घन के रूप में, सम्वेश्य मध्यस्य के रूप में`. SB states this exact four-fold analysis: *आकार, आयतन, घन के अर्थ में रुप। सम, विषम, मध्यस्थ के अर्थ में गुण (शक्तियाँ)। रचना, रचना की परंपरा, विरचना के रूप में स्वभाव* — and continues *स्वभाव — (i) पदार्थावस्था में … (ii) प्राणावस्था में …*, which is the very list the speaker goes on to give. MVD p. 47 defines *गुण* the same way: *सम, विषम, मध्यस्थ के रूप में पहचान होती है*. So `वाईत अन्घन` is आयतन, घन and `सम्वेश्य मध्यस्य` is सम, विषम, मध्यस्थ. This also corrects the earlier reading "आकार, [अ]वयव" — रूप is आकार-आयतन-घन in this darshan, not "parts".

**[05:58] [P]**
> नहीं है। अभी इस सभा की पहली मौलिक बात यह है। किसी भी विधि से, और कोई विधि से — यह चारों भाग को सम्मिलित रूप में एक वस्तु को पहचानने की विधि आती है।
>
> *No. Now, the first fundamental point of this gathering is this. By whatever method, by any method — the way of recognising one vastu with all four parts taken together comes about.*

**[06:12] [R]**
> इसके बैकग्राउंड क्या है? अध्ययन। अध्ययन क्या समझ में आता है?
>
> *What is the background of this? Study. What is understood by study?*

**[06:20] [R]**
> वस्तु का स्वरूप — रूप, गुण, स्वभाव — को प्रस्तुत करना; वह अध्ययन है। यदि बिना किसी अध्ययन का होता होगा, तो हम किसी को उसको बताना — तो बताने की क्या ज़रूरत है? अध्ययन विधि से ही यह पूरा होता है।
>
> *To present the nature of the vastu — form, property, essential nature; that is study. If it were to happen without any study, then our telling anyone about it — what need would there be to tell? It is only by the method of study that this is completed.*

**[06:41] [P]**
> अच्छा — रूप के साथ इन सब बातों को स्वीकारने में अधिकार आता है, और उस स्थिति में हम अनुभव कहते हैं।
>
> *Good — in accepting all these things along with form, entitlement comes, and that condition we call realisation.*

**[06:51] [R]**
> उसका क्या बात है? हम दूसरों को समझाने योग्य होते हैं, दूसरों को बोध कराने योग्य होते हैं।
>
> *What does that amount to? We become fit to explain to others, fit to bring about bodh in others.*

**[06:59] [U]**
> ठीक है। इसकी प्रक्रिया के लिए अपन [ने] देखा … विकास कहा। इसमें क्या होता है? … विकास होने के लिए इसकी आवश्यकता होता है। ठीक है। क्लियर? क्लियर हो गए? और कुछ बात?
>
> *All right. For its process we have seen … called development. What happens in this? … For development to occur, this is what is needed. All right. Clear? Has it become clear? Anything else?*

**[07:21] [P]**
> और इसमें कुछ भी आप पूछेंगे, वो उत्तर होगा।
>
> *And whatever you ask in this, there will be an answer.*

---

## 5. Repetition, imaginativeness, and the body as medium

**[07:27] [P]**
> कितनी बार पूछेंगे, वो उतनी बार होगा।
>
> *However many times you ask, that many times it will be [answered].*

**[07:33] [P]**
> … पुनः एक बार साक्षात्कार, [ऋतम्भरा?] … इस स्थिति में प्रज्ञा करते हैं, इस स्थिति में — और एक बार।
>
> *… again, once, sakshatkar, [ritambhara?] … in this condition prajna operates, in this condition — once more.*
>
> ***प्रज्ञा* is a defined term, which raises the mark.** MVD p. 325 glosses it *यथार्थ की पूर्ण अनुमान सहित पूर्ण स्वीकृति क्रिया* (the activity of completely accepting reality, with mature inference), and MVD p. 332 gives a fuller entry ending *… अनुभवमूलक गति और स्थिति सत्य में **बोध व अनुभव*** — i.e. *prajna* is itself characterised in terms of *bodh* and *anubhav*, the two stages under discussion here. The ASR token `अंभो तत्ति` between साक्षात्कार and प्रज्ञा is unrecovered; given 04:10 it may be ऋतम्भरा, which is why it is queried rather than supplied.

**[07:43] [U]**
> एक बार फिर से साक्षात्कार से लेकर … पहले अपना ज्ञान करे …
>
> *Once again, starting from sakshatkar … first let one's own knowing occur …*

**[07:55] [P]**
> अध्ययन कराते हैं — अस्तित्व में, अस्तित्व को मूल में सह-अस्तित्व रूप में बताएँगे। अध्ययन कराते हैं। अस्तित्व के बारे में शब्द के रूप में बोलते हैं, उसके अर्थ को पहचानते हैं, पहचानने के लिए कोशिश करते हैं — वो अर्थ समझ में …
>
> *We conduct study — in existence, we will state existence as being, at root, in the form of coexistence. We conduct study. We speak about existence by way of words, we recognise their meaning, we attempt to recognise it — that meaning comes to be understood …*

**[08:25] [U]**
> … [unclear] एक बार जब रहता है ही … आप ही सोच लो।
>
> *… [unclear] once it is already there … think it over yourselves.*

**[08:38] [P]**
> यह जो अस्तित्व में रहता है — हर शब्द का अस्तित्व में, वस्तु के रूप में रहता है।
>
> *This which remains in existence — every word's [meaning] remains in existence, as a vastu.*

**[08:49] [U]**
> मान लो, कृति — ये किसे नहीं होता है? … किसे नहीं होता है?
>
> *Suppose, a made thing — to whom does this not occur? … to whom does it not occur?*

**[08:55] [P]**
> अस्तित्व में स्वाभाविक रूप में यह बात मानी है — वह हमको समझ में आता है।
>
> *In existence this matter is accepted as natural — that we come to understand.*

**[09:02] [R]**
> समझदारी के रूप में साक्षात्कार होता है; समझदारी के बल [से] अनुभव होता है। पूर्ण हो गया है — समझदारी।
>
> *Sakshatkar occurs in the form of understanding; by the force of understanding, realisation occurs. It has become complete — understanding.*

**[09:24] [P]**
> इसका नाम है दृष्टापद। अब इसमें क्या विवेक हुआ? अभी चक्षु गोचर, ज्ञान गोचर — दो विधि हैं।
>
> *This is called the seat of the Seer. Now what discernment has arisen in this? Now: eye-accessible, knowledge-accessible — there are two modes.*

**[09:38] [P]**
> अभी ज्ञान गोचर कैसे हो गए? हर व्यक्ति के पास कल्पनाशीलता, कर्मस्वतंत्रता है।
>
> *Now, how did it become knowledge-accessible? Every person has imaginativeness and freedom in action.*

**[09:46] [P]**
> अपनी कल्पना के अंदर तदाकार-तद्रूप होने की क्रिया को ज्ञान गोचर [कहा]।
>
> *The activity of coming to take that form, of becoming of that form, within one's own imagination — that is [called] knowledge-accessible.*

**[09:56] [P]**
> हमारे जो कुछ भी शब्द बोला, उसका आशय … वस्तु को समझने वाली, स्वीकार करने वाली क्रिया का नाम है कल्पनाशीलता, कर्मस्वतंत्रता।
>
> *Whatever words we have spoken, their purport … the activity that understands and accepts the vastu is called imaginativeness and freedom in action.*

**[10:08] [R]**
> जीवन में कर्मस्वतंत्रता [है] और कल्पनाशीलता [है] — जीवन में। और कहीं नहीं। रासायनिक-भौतिक वस्तु में नहीं।
>
> *Freedom in action and imaginativeness are in jeevan — in jeevan. Nowhere else. Not in chemical or physical objects.*

**[10:26] [R]**
> … अभी क्या मान किया जा रहा है — हमारा शरीर देखता है। शरीर देखता नहीं है; शरीर एक देखने के लिए माध्यम है। क्या? किसको? रूप को, वस्तु को। वस्तु को देखने के लिए एक माध्यम है। कैसे? दृष्टि गोचर विधि से।
>
> *… now what is being supposed — that our body sees. The body does not see; the body is a medium for seeing. What? Of what? Of form, of the vastu. It is a medium for seeing the vastu. How? By the sight-accessible mode.*

**[10:56] [P]**
> … अध्ययन कराते हैं। वह हम अध्ययन करने वाले अनुभव के रहते हैं। उस विधि से — अनुभवमूलक विधि से — अनुभवगामी पद्धति बनती है। उस विधि से हमारी कल्पनाशीलता में आता है। आप अध्ययन कराओगे, हमारी कल्पना में आ जाता है।
>
> *… we conduct study. We who conduct the study abide in realisation. By that method — the realisation-based way — a realisation-directed method is formed. By that method it comes into our imaginativeness. You will conduct the study, and it comes into our imagination.*

**[11:26] [P]**
> … रूप बनाकर रखता है — यह भौतिकवादी विधि। इसको नहीं मानने वाला आदर्शवादी विधि। नहीं मानने मात्र से बोध नहीं हुआ, और [वे] समझा नहीं पाए। अभी इस विधि से हम समझ सकते हैं।
>
> *… keeps it as a made form — this is the materialist way. The one who does not accept this is the idealist way. Merely by not accepting, bodh did not occur, and [they] could not make it understood. Now, by this method, we can understand.*

**[11:43] [P]**
> तद्रूप-तदाकार होने का एक कंपोनेंट कहा है — वो वस्तु कहा है, ऐसी महिमा कही है। वो उस महिमा को कल्पनाशीलता के रूप में, कर्मस्वतंत्रता के रूप में मैंने अनुभव किया है, जीवन में। ठीक है। इसके आधार पर अध्ययन कर सकते हैं हर व्यक्ति।
>
> *A component of becoming-of-that-form has been stated — that vastu has been stated, such greatness has been stated. That greatness I have realised in the form of imaginativeness, in the form of freedom in action, in jeevan. All right. On this basis every person can study.*

---

## 6. Study is what succeeds, and the stages get their names

**[12:13] [U]**
> … इस बात को कहा था। हाँ, ठीक है। शुद्ध — इसमें तीनों था। तो शुद्धि … जहाँ सुनते हैं, और भौतिक रूप में …
>
> *… this had been said. Yes, all right. Pure — all three were in it. So purity … where we hear, and in material form …*

**[12:24] [U]**
> … ठीक है। यह बात को वेद-विचार ने पूरा किया, अपने जाएँगे, उस परंपरा में मुझे रहा है। ठीक है।
>
> *… all right. This matter the Vedic thought completed; we will go on, in that tradition it has been for me. All right.*

**[12:38] [U]**
> … तब से हम वेद को अध्ययन करने में लगे रहते हैं, कि ऐसा सब कर चुके। ठीक है।
>
> *… since then we remain engaged in studying the Veda, that all this has been done. All right.*

**[12:47] [R]**
> अभी क्या कह रहे हैं? अध्ययन की बैठ कर रहे हैं। अध्ययन क्या होता है? शब्द के अर्थ में वस्तु होता है।
>
> *Now what are we saying? We are settling the matter of study. What is study? In the meaning of a word there is a vastu.*

**[12:54] [R]** — *the most consequential single claim in the session*
> उन शब्दों के अर्थ की वस्तु के रूप में जो वस्तु है, वो अस्तित्व में है। अस्तित्व में वस्तु के रूप में, शब्द के अर्थ में वस्तु मिलती है — उसका नाम है साक्षात्कार। इसका नाम है अध्ययन की सफलता।
>
> *The vastu that stands as the vastu of those words' meaning — it is in existence. In existence, as a vastu, the vastu is found in the meaning of the word — that is called sakshatkar. This is what is called the success of study.*

**[13:09] [R]**
> यदि अध्ययन यदि सफल होता है, उस स्थिति में स्वाभाविक रूप में बोध होता है; यह बोध होने के पश्चात अनुभव होता है; अनुभव होने के पश्चात प्रमाण होता है। प्रमाण होने की क्रिया का नाम है जागृति।
>
> *If study succeeds, then in that condition bodh occurs naturally; after this bodh occurs, realisation occurs; after realisation occurs, evidence occurs. The activity of evidence occurring is called awakening.*

**[13:26] [R]**
> … और अनुभव होने की क्रिया का नाम है … दृष्टापद। दृष्टापद में हम आसीन …
>
> *… and the activity of realisation occurring is called … the seat of the Seer. Seated in the seat of the Seer …*

**[13:36] [P]**
> … होने का वो स्वत्व, वो क्रिया है — वह अनुभव है। जब दृष्टापद में होता है, स्वाभाविक रूप में वेद को प्रमाणित …
>
> *… that ownness of being, that activity — that is realisation. When one is in the seat of the Seer, naturally, to evidence the Veda …*

**[13:45] [R]**
> … ग्रहण करने वाली प्रक्रिया शुरू होता है — उसका नाम है प्रमाण। ये प्रमाण परम वस्तु है। इस दिन से मानव चेतना का उदय होने वाली बात आती है। इससे कम में कभी नहीं होगा, कभी नहीं हुआ। ठीक हो गया है।
>
> *… the process of taking up begins — that is called evidence. This evidence is the ultimate thing. From this day the matter of the dawn of human consciousness arrives. With less than this it will never happen, and it never has happened. That is settled.*

**[14:07] [P]**
> … हमारे अनुसार, न इसे दूसरी कोई विधि से यहाँ पहुँच भी नहीं सकते।
>
> *… according to us, nor can one arrive here by any other method.*

**[14:12] [P]**
> दूसरी कोई विधि है भी नहीं, अभी तक।
>
> *There is no other method at all, as yet.*

**[14:16] [P]**
> तदाकार-तद्रूप विधि ही है, इसमें — करे करो।
>
> *It is only the absolute-resonance / absolute-accordance method, in this — do it.*
>
> *Recovered from the primary texts, and it explains 14:12.* MVD p. 80 defines this exactly: **सह-अस्तित्व में अनुभव ही तद्रूप, तदाकार विधि है** — published as "Realisation in coexistence itself is the way of absolute-accordance and absolute-resonance (*tadakar*)" — *क्योंकि नियम, नियन्त्रण, संतुलन, न्याय, धर्म, सत्य, अनुभव के फलन में प्रमाणित होता है*, the same six-item set as 22:58. The term belongs to a four-member cluster describing the awakened relation to the *ईष्ट* (ideal): *तादात्म्य, तद्रूप, तत्सान्निध्य, तदावलोकन*, where **तदावलोकन is defined as दृष्टापद प्रतिष्ठा** — the seat of the Seer, which is what this session calls *anubhav* (13:26, 15:04). So the speaker's flat claim at 14:12 that *दूसरी कोई विधि है भी नहीं* is not rhetorical overreach: on MVD's own definition, realisation in coexistence **is** the method, so there is nothing for a second method to be.

**[14:23] [P]**
> उसमें क्या क्या है?
>
> *What all is in it?*

**[14:26] [P]**
> पहले से ही अध्ययन कर रहे रहते …
>
> *One has been studying from before …*

**[14:28] [P]**
> रूप, गुण, स्वभाव, धर्म को प्रत्येक में अविभाज्य रूप में — जो कुछ भी साक्षात्कार होता है, चार अवस्था में ही होती है: पदार्थ अवस्था में, प्राण अवस्था में, जीव अवस्था में, ज्ञान अवस्था में। इसके अलावा पाँचवीं अवस्था भी नहीं है।
>
> *Form, property, essential nature, dharma — inseparably in each. Whatever sakshatkar occurs, occurs only in the four states: in the material state, in the pranic state, in the animal state, in the knowledge state. Apart from these there is no fifth state.*

**[14:58] [U]**
> … ये दोनों वहीं से हैं। अपन सोच सकता है।
>
> *… both of these are from there. One can think it over.*

**[15:04] [R]**
> अनुभव होने का नाम है — दूसरा नाम — दृष्टापद।
>
> *The name for realisation occurring — its other name — is the seat of the Seer.*

**[15:10] [P]**
> दृष्टापद में होने के बाद, प्रमाणित होने के बाद होता है — प्रमाण के रूप में हम प्रमाणित करना शुरू [करते हैं]; अभिव्यक्त होने वाली बात प्रवृत्ति रहती है, आत्मा में।
>
> *After being in the seat of the Seer, after being evidenced, it occurs — in the form of evidence we begin to evidence; what comes to be expressed remains as tendency, in atma.*

**[15:20] [U]**
> आत्मा अभिव्यक्ति सहज है, क्योंकि सह-अस्तित्व प्रगटनशील है। आत्मा … जो यहाँ अभिव्यक्तिशील है। इसी आधार पर प्रगटनशील है।
>
> *Atma is expression-natural, because coexistence is self-manifesting. Atma … which here is expression-capable. On this very basis it is self-manifesting.*
>
> ***अभिव्यक्ति सहज* checks out; *प्रगटनशील* does not.** SB uses *अभिव्यक्ति सहज* as a fixed phrase (*जागृत मानव, अभिव्यक्ति सहज रूप में, मानव सहज व्यवहार में सफल हो जाता है*), which supports that half. But neither **प्रकटनशील** nor **प्रकाशनशील** occurs anywhere in MVD, SB, JV or KD, so the ASR's `प्रगटन्शीर` is left in its likelier Hindi form rather than normalised to a term the corpus would license. Do not treat *प्रगटनशील* as darshan vocabulary on this transcript's authority.

**[15:31] [U]**
> वह मानव में, जीवन में, जो मध्यस्थ सहज — जीवन में गठनपूर्ण[ता] … [ASR destroyed] … प्रमाण, मध्य भाग में …
>
> *That which in the human, in jeevan, is mediative-natural — constitution-completeness in jeevan … [ASR destroyed] … evidence, in the middle part …*
>
> *Left uncertain deliberately.* The ASR collapses mid-segment into English and Cyrillic tokens (`Pastor производits in the Ghatan conversation or the Pramona`), so most of this is unrecoverable. Two anchors survive: **गठनपूर्णता** is a defined term — MVD p. 13 lists *गठनपूर्णता, क्रियापूर्णता, आचरणपूर्णता* as a triad, and MVD p. 8 has *गठनपूर्ण परमाणु चैतन्य इकाई — जीवन रूप में*; SB adds *विकास का तात्पर्य गठनपूर्णता, क्रियापूर्णता और आचरणपूर्णता … से है*. Knowing the term does not tell us what the sentence said, so the mark stays **[U]**.

---

## 7. *Samadhi*, and what was not found in it

**[15:50] [R]**
> मात्रात्मक परिवर्तन के रूप में होता है। जीवन में … गुणात्मक परिवर्तन के रूप में होता है।
>
> *It occurs as quantitative transformation. In jeevan … it occurs as qualitative transformation.*

**[16:06] [P]**
> यह पहले से आपको बहुत [बता] दिया है; मैंने बहुत बहुत अभ्यास किया है, रहते हैं। उसके आधार पर तदाकार-तद्रूप होना बनता; दूसरी विधि से कभी नहीं होगा। उसको कैसे हम समझाएँ? … लगता है कि किताब में लिखा है …
>
> *I have told you a great deal of this already; I have practised a very great deal. On that basis becoming-of-that-form comes about; by another method it will never happen. How shall we explain it? … it appears that it is written in the books …*

**[16:36] [R]** — *matches MVD p. 7 and JV p. 13*
> "[अज्ञात को ज्ञात] करना बनता है समाधि में" — यह लिखा [है]। हम समाधि देखा — समाधि में एक भी ज्ञान नहीं हुआ। उल्टा क्या देखते रहे? देखते ही रहे — हमारा आशा, विचार, इच्छा चुप हो गए।
>
> *"Making [the unknown known] comes about in samadhi" — this is what is written. We saw samadhi — in samadhi not one instance of knowledge occurred. What did we go on seeing instead? We just kept watching — our hope, thought and desire fell silent.*

**[16:52] [P]**
> दूसरा क्या देखा? काल, समय, शरीर, स्थान — इनका अभाव होंगे।
>
> *What else did we see? Time, duration, body, place — their absence.*

**[17:01] [P]**
> क्या अभाव हुआ? हमारे ही आशा, विचार, इच्छा — तीनों चुप हैं।
>
> *What became absent? Our own hope, thought and desire — all three are silent.*

**[17:08] [P]**
> यह हम देखते रहे हैं। देखने में वहाँ क्या होगा? बुद्धि ही होगा, यह आत्मा ही होगा।
>
> *This we kept watching. In the watching, what would be there? It would be buddhi itself, it would be atma itself.*

**[17:16] [P]**
> … उस समय में आपको पता भी नहीं था कौन देखता है। "मैं देखता हूँ" [का] सहारा। ठीक है। उसको हम लिखा भी है — मुझको, समाधि के बाद, भूत और भविष्य की पीड़ा वर्तमान में मेरे वर्त नहीं है।
>
> *… at that time you did not even know who sees. The support of "I see." All right. We have written it too — for me, after samadhi, the affliction of past and future does not obtain in my present.*

**[17:34] [R]**
> यह लाइन लिखा है, आप पढ़े हो; उसको लिख दिया है। उसके बाद जब संयम हुआ, जब पता लगा — अनुभव हो गए, हम दृष्टापद में हो गए हैं। किस बात के? सह-अस्तित्व में दृष्टापद।
>
> *This line is written, you have read it; it has been written down. After that, when samyama occurred, when it became known — realisation occurred, we came to be in the seat of the Seer. Of what? The seat of the Seer in coexistence.*

**[18:08] [U]**
> हो गया मानकर … हमारे जो [कारण] का पता है, वह बताया। इसके आधार पर हम इस …
>
> *Taking it as done … what we know of the [cause], that we told. On this basis we …*

---

## 8. The limit of reasoning, and the path restated

**[18:20] [P]**
> … सूत्रित किया, तब पता चला दृष्टापद कहाँ है, अनुभव कहाँ है, और उसके बाद प्रमाण कहाँ है, उसका प्रमाण परंपरा कैसा है — यह सब उसके साथ जुड़ा है। ठीक है। यह दृष्टापद से अनुभव तक …
>
> *… formulated it, then it became known where the seat of the Seer is, where realisation is, and after that where evidence is, and what its tradition of evidence is like — all this is joined with it. All right. From the seat of the Seer to realisation …*

**[18:48] [P]** — *bears on the study's §4.4*
> दृष्टव्य … पुरुषार्थ, मानव के साथ तर्क जुड़ा है। पुरुषार्थ [के साथ] जुड़ा है। और उसके बाद परमार्थ के साथ कोई तर्क नहीं है। तर्क [यहाँ तक] पहुँचते हैं। क्योंकि "कैसे" का उत्तर है, वो सब उसके बाद। इस आधार पर हम अपनी परंपरा …
>
> *What is to be seen … diligence: reasoning is joined with the human. It is joined with diligence. And after that, with benevolence, no reasoning is joined. Reasoning reaches [this far]. Because the answer to "how" — all that is after that. On this basis we, our tradition …*
>
> *Translation corrected 2026-08-01.* An earlier revision rendered these two terms "human endeavour" and "the ultimate good" as working glosses. Both are defined in MVD with published English, and both are narrower than I had them. **पुरुषार्थ = "diligence"**: MVD p. 128 — *जागृति के लिये किये गये व्यवहार को पुरुषार्थ, निर्वाह के लिये किये गये प्रयास को कर्त्तव्य तथा भोग के लिये किये गये व्यवहार को विवशता* ("behaviour towards awakening is called diligence, towards fulfilling relationships duty, towards indulgence helplessness"). **परमार्थ = "benevolence"**: MVD p. 63 glossary places it in the triad *स्वार्थ / परार्थ / परमार्थ* — "selfish, altruistic and benevolent" — defined as the deployment of means (*अर्थ नियोजन*) that brings resolution and universal good; MVD p. 146 adds that *परमार्थ* thought and behaviour are differentiated by *dharma* and *moksha*. So the contrast here is not seen-versus-transcendent but **awakening-directed conduct, with which reasoning travels, against benevolent deployment, with which it does not**.

**[19:24] [U]**
> स्वयं की आवश्यकता … होना चाहिए; इसके लिए दूसरी कोई आवश्यकता नहीं। हर व्यक्ति शुभ चाहते हैं — इस आधार पर इसको प्रस्ताव रखा है। ठीक हो गया है यहाँ तक? अब इसमें और कुछ पूछना है?
>
> *One's own need … must be there; for this no other need. Every person wants the good — on this basis this has been put forward as a proposal. Is it settled this far? Now is there anything more to ask in this?*

**[20:09] [P]**
> और इसमें बहुत पक्का होने के लिए, और उत्साह बढ़ने के लिए, और कैसे इसका [प्रयोग] किया जा सकता है — आप ही सोच सकते हैं। क्योंकि हम कोई बहुत बड़ी भाषा के विद्वान नहीं हैं; सामान्य भाषा हम जानते हैं।
>
> *And for this to become very firm, and for enthusiasm to grow, and how it can be [applied] — you yourselves can think. Because we are no great scholar of language; we know ordinary language.*

**[20:42] [P]**
> … दो पीढ़ी नहीं बैठा होगा; हमारे बाद की दो पीढ़ी यहाँ बैठा होगा — ऐसा मैं सोचता हूँ। आगे: यह रास्ता कैसा है? तो अध्ययन — माने पठन से अध्ययन — पहला भाग। उस अध्ययन की शुरुआत कहाँ से? साक्षात्कार। उस अध्ययन की सफलता कहाँ? दृष्टा …
>
> *… two generations will not be sitting; two generations after us will be sitting here — so I think. Further: what is this road like? Then study — that is, study through reading — the first part. Where does that study begin from? Sakshatkar. Where is the success of that study? The Seer …*

**[21:13] [R]** — *the stage-names, stated a second time*
> जागृति का नाम है प्रमाण की अभिव्यक्ति; और दृष्टापद का दूसरा नाम है अनुभव। ये हर नर-नारी के लिए बहुत आवश्यक है — नहीं है? इसको तय करना अपने … सोचने की बात है। ठीक है।
>
> *Awakening is the name for the expression of evidence; and the other name for the seat of the Seer is realisation. This is very necessary for every man and woman — is it not? To settle this is one's own … a matter for thinking. All right.*

---

## 9. The key Q&A: what *anubhav* adds to *bodh*

**[21:58] [P]**
> **प्रश्न:** हाँ बाबा, एक तो ये बात स्पष्ट होना ज़रूरी है — कल्पना में सूक्ष्म-सूक्ष्मतम बात आता है, ये बात समझ में आया है। यदि समझ में आया है, इसमें क्या सूक्ष्मतम … जोड़ा जाए? हाँ बाबा, दो चीज़ें तो स्पष्ट होना ज़रूरी है, कि …
>
> ***Q:** Yes Baba, first this needs to be clear — the subtle and subtlest comes into imagination, this has been understood. If it has been understood, what subtlest … is to be added in this? Yes Baba, two things do need to be clear, that …*

**[22:28] [R]** — *the question the whole session turns on, and its answer*
> **प्रश्न:** फिर बोध होने के बाद अनुभव होने में और क्या समझ में आया, जिसको अनुभव कहते हैं?
>
> **उत्तर:** कुछ नहीं। साक्षात्कार में जो होता है वो पक्का होता है; उसके अलावा कुछ नहीं होता है।
>
> **प्रश्न:** तो फिर मतलब बोध और अनुभव सब साथ में हो गया?
>
> ***Q:** Then, after bodh occurs, what further is understood in realisation occurring — that which is called realisation?*
>
> ***A:** Nothing. What occurs in sakshatkar becomes firm; apart from that, nothing occurs.*
>
> ***Q:** So then, does that mean bodh and realisation have all happened together?*

**[22:58] [P]**
> ठीक है न। इन दोनों पहुँच गए, [साक्षात्कार के] रूप में। किसमें? साक्षात्कार में। बोध में क्या पहुँचा? धर्म … पहुँचा और स्वभाव पहुँचा। बोध में? हाँ। और इसमें नियम, नियंत्रण, संतुलन, न्याय, धर्म, सत्य — छह … पहुँचा।
>
> *All right. Both of these have arrived, in the form [of sakshatkar]. In what? In sakshatkar. What arrived in bodh? Dharma … arrived, and essential nature arrived. In bodh? Yes. And in this: rule, regulation, balance, justice, dharma, truth — six … arrived.*
>
> *Note on this list.* The ASR here is degraded — it yields seven tokens (`नयम नयम प्रणसन तुलन नयाय धर्म सत्य`) while the speaker says **छह**, six. The reconstruction above is nonetheless determinate, on three independent grounds: the two `नयम` tokens are नियम and नियं[त्रण]; `प्रणसन तुलन` is संतुलन; **23:27 below independently carries नियंत्रण and संतुलन in clean ASR**; and the set is a fixed MVD grouping stated verbatim at **MVD p. 80** — *नियम, नियन्त्रण, संतुलन, न्याय, धर्म, सत्य, अनुभव के फलन में प्रमाणित होता है* ("… is evidenced in the fruition of realisation"), with the same six at **p. 31** and derived as a chain at **p. 173** (*नियम ही नियंत्रण; नियंत्रण ही संतुलन; संतुलन पूर्वक जीना ही मानव में न्याय …*). Seven tokens resolving to exactly the six the speaker announces, matching a printed set tied to *anubhav*, is a reconstruction rather than a guess. Corrected 2026-08-01 per Raghava, who supplied the six; an earlier revision of this file listed five and marked the enumeration uncorrectable.

**[23:27] [P]**
> नियंत्रण में क्या चीज़ें वहाँ पहुँच गए हैं? यदि संतुलन में क्या चीज़ें वहाँ पहुँच गए हैं? न्याय, धर्म, सत्य में क्या चीज़ें वहाँ पहुँच गए हैं? किसमें? साक्षात्कार में। इसमें रूप, गुण, स्वभाव — उसका नाम समग्र रूप में कहा है। ठीक है।
>
> *In regulation, what things have arrived there? In balance, what things have arrived there? In justice, dharma, truth, what things have arrived there? In what? In sakshatkar. In this: form, property, essential nature — that has been called the integral form. All right.*

**[23:54] [U]**
> यह चार-छह छूट गया और यही मिल जाएगा — यह साक्षात्कार। ठीक है। धर्म और सत्ता दोनों पहुँचा। सत्ता कैसे पहुँचा? सह-अस्तित्व रूप में सत्ता पहुँचा — उसका ध्यान कराए रहते हैं। और धर्म जो है, न मानो … सुख धर्म के रूप में …
>
> *These four-six were left out and just this will be found — this is sakshatkar. All right. Both dharma and Omnipotence arrived. How did Omnipotence arrive? Omnipotence arrived in the form of coexistence — we keep drawing attention to it. And dharma, which is, suppose … as the dharma of happiness …*

**[24:18] [P]**
> … और जीवन में आशा-धर्म के रूप में, और प्राण अवस्था में पुष्टि-धर्म के रूप में, पदार्थ अवस्था में अस्तित्व-धर्म के रूप में — यह पहुँच रहे हैं। यह पहुँचने पर बुद्धि में … सत्ता पहुँच रहे …
>
> *… and in jeevan as the dharma of hope, and in the pranic state as the dharma of nourishment, in the material state as the dharma of existence — these are arriving. On these arriving, in buddhi … Omnipotence arriving …*

**[24:41] [P]**
> सह-अस्तित्व … पुनः सह-अस्तित्व बोध होता है। उस समय में क्या जुड़ गया? बुद्धि में जो शेष था वो जुड़ गया। सह-अस्तित्व में से चलकर चिंतन में, चिंतन के रूप में चित्त में पहुँचा — तो क्या जुड़ गया? नियम, नियं[त्रण, संतुलन, न्याय, धर्म,] सत्य पूरा …
>
> *Coexistence … again there is bodh of coexistence. At that time what got joined? What remained in buddhi got joined. Proceeding from coexistence into contemplation, and as contemplation arriving in chitta — then what got joined? Rule, regu[lation, balance, justice, dharma,] truth, complete …*
>
> *The ASR here gives only `नयम नयम तरह सत्य पूरत` — the same six-item set as 22:58, elided in speech. Brackets mark what is supplied from that set (MVD p. 80), not heard.*

---

## 10. The artificial fruit, and teaching without coercion

**[25:17] [P]**
> पहले जड़ क्लियर हो जाए, उसके बाद फल समझ में आता है। यह फल समझ में आ जाए, तो बस जड़ समझने की आवश्यकता बनते हैं। जैसे अपन एक फल खाता है — सेव का — जड़ तो यहाँ नहीं है। इसका जड़ होगा, ऐसा कल्पना में आता है।
>
> *First let the root become clear, after that the fruit comes to be understood. If this fruit comes to be understood, then the need to understand the root arises. As one eats a fruit — an apple — the root is not here. That it will have a root, that comes into imagination.*

**[25:43] [P]**
> यह झाड़ का फल है, यह मिट्टी के रूप में बनाया हुआ फल है, या कागज़ का बनाया हुआ फल है — यह हमको पता लगता है। यह पता लगता है कि नहीं? इन दोनों को अपन कृत्रिमता कहते हैं। कागज़ से यह फल का स्वरूप बनाया हो, उसको कृत्रिम फल [कहते हैं]; और मिट्टी से फल का आकार बना …
>
> *This is the fruit of a tree; this is a fruit made out of clay, or a fruit made of paper — this we come to know. Do we come to know it or not? Both of these we call artificiality. If the shape of this fruit is made from paper, that is [called] an artificial fruit; and made from clay in the form of a fruit …*

**[26:14] [P]**
> वास्तविक फल कौन सा है? जड़ में पकता है। … आज भी वास्तविकता को हम विश्वास करते हैं, कि कृत्रिम फल को? यदि कृत्रिम फल से हम तृप्त हो सकते थे, उसको भी मान देते। …
>
> *Which is the real fruit? The one that ripens on the root. … Even today, do we trust actuality, or the artificial fruit? If we could be satisfied by an artificial fruit, we would grant it too. …*

**[26:50] [P]** — *bears on the study's §6.4*
> यह मंगल-मैत्री से प्रस्तुति की विधि है। इसमें दादागिरी एक भी नहीं है। दादागिरी का [तरीका] ही दूसरा है। वो दादागिरी पहले था — "तुम कुछ नहीं पूछोगे। हम जो कहते हैं …"
>
> *This is a method of presentation through goodwill and friendship. There is not a single instance of bullying in it. The way of bullying is quite another. That bullying was there formerly — "you will ask nothing. What we say …"*

**[27:23] [P]**
> कल्पनाशीलता का … अधिकार है, कर्मस्वतंत्रता का … अधिकार है। इनके प्रयोग से हम साक्षात्कार, बोध, अनुभव करके प्रमाणित कर सकते हैं। मूल बात इतनी है। अभी इस कल्पनाशीलता, कर्मस्वतंत्रता का प्रयोग है, उससे इन बातों को हम प्रमाणित …
>
> *There is … entitlement of imaginativeness, … entitlement of freedom in action. By their use we can, through sakshatkar, bodh and realisation, evidence it. That is the whole root of the matter. Now there is the use of this imaginativeness and freedom in action, by which we evidence these matters …*

**[27:47] [P]**
> चारों अवस्था क्या है? चारों अवस्था में जो रूप, गुण, स्वभाव, धर्म है, उसको प्रमाणित करने की आवश्यकता है; व्याख्या करने की आवश्यकता है; सूचना देने की आवश्यकता है। सूचना किताब से होता है; मनुष्य समझाने से समझ में आता है।
>
> *What are the four states? The form, property, essential nature and dharma in the four states — there is need to evidence it; need to expound it; need to inform of it. Informing happens from books; understanding comes about from a human explaining.*

---

## 11. Can *sakshatkar* occur without study?

**[28:16] [P]**
> अध्ययन की तीव्रता है — अगर अध्ययन की तीव्रता है, तो अध्ययन में तीव्रता, अगर है तीव्रता …
>
> *There is intensity of study — if there is intensity of study, then intensity in study, if there is intensity …*

**[28:43] [P]**
> **प्रश्न:** … तो साक्षात्कार हो सकता है अध्ययन में — यह बात कही गई है। तो इनका कहना यह है कि अगर तीव्रता है जिज्ञासा की, तो अध्ययन के बिना भी साक्षात्कार हो सकता है कि नहीं?
>
> **उत्तर:** बिना ज्ञान की कोई सच्चाई नहीं आएगी। दूसरा विधि है — अनुसंधान। अनुसंधान के लिए समा[धि-संयम] …
>
> ***Q:** … so sakshatkar can occur in study — this has been said. So their question is: if there is intensity of inquisitiveness, can sakshatkar occur even without study, or not?*
>
> ***A:** Without knowledge no truth will come. There is a second method — research. For research, sama[dhi-samyama] …*

**[29:15] [P]**
> … उद्देश्य … ठीक है, आपकी जिज्ञासा; ठीक है, और सह-अस्तित्व विधि से — ठीक है, तब आपको समाधि-संयम से होगा। जो जिस बात की समाधि-संयम बताया है, उसको पूरा करने से ही होगा; दूसरी विधि से होगा नहीं। उसको हम करके देखा।
>
> *… the purpose … all right, your inquisitiveness; all right, and by the coexistence method — all right, then for you it will happen through samadhi-samyama. The samadhi-samyama that has been stated, only by completing that will it happen; by another method it will not. That we did and saw.*
>
> ***अनुसंधान* here is MVD p. 280's first path, and that locks this passage to the printed corpus.** MVD p. 280 states the two processes for eliminating *बौद्धिक रहस्यता* (intellectual mystery) as *एक — अनुसंधान। दो — अनुसरण, अनुकरण, अध्ययन* — published "One - Exploration. Two - Following, Emulation, Study." So when the speaker answers the question at 28:43 with *दूसरा विधि है — अनुसंधान*, he is naming MVD's **Exploration** path — and then says here that it requires *समाधि-संयम* carried out as prescribed, and at 34:07 that expecting it of everyone is *अव्यवहारिक*. Read together, the session assigns the printed two-path scheme a division of labour the printed text leaves open: *anusandhan* for the discoverer, *adhyayan* for everyone else.

**[29:46] [U]**
> जिसकी … जैसे मैं गाँव में रहता हूँ। यदि हम रूप, गुण, स्वभाव आदि के धर्म की बात … इसके अध्ययन करते हैं … वह समझना नहीं चाहता है, तो क्या [करें]? मेरी बात आता है न — वो समझना नहीं चाहता है …
>
> *Whose … as I live in a village. If we [speak] of the matter of form, property, essential nature and so on … we study this … he does not wish to understand — then what [is to be done]? My point comes, doesn't it — he does not wish to understand …*

**[30:16] [U]**
> … क्या करते हैं? वह सूक्ष्मता में जाने की … किसी की इच्छा नहीं बनती है; इसकी सच्चाई के लिए उसकी इच्छा नहीं है। तो … मैं कर रहा हूँ। तो बाबा ने कहा है कि उसको समझे बिना जानने का कुछ माने ही क्या? … ठीक हो गया।
>
> *… what do they do? To go into the subtlety … no one forms the wish; for its truth there is no wish in him. So … I am doing. So Baba has said: without understanding it, what does knowing even mean? … That is settled.*

**[30:47] [P]**
> कोई प्रश्न नहीं है? हो गया, समझ में आ गया? वो कुल मिलाकर क्या है — हम पहले बिना समझे भी ज्ञानी हो सकते हैं, बिना [जाने] ही; ऐसा सोचते हैं। तो उसको हम कहाँ से कहाँ तक, उस बारे में थोड़ा सा सूचना विधि से। देखिए — सुनने-सुनाने की विधि …
>
> *No question? Done, has it been understood? What it all comes to is: we can be knowers even without understanding first, without [knowing]; so we think. So from where to where, on that a little by way of information. See — the method of hearing and telling …*

---

## 12. Hearsay, self-examination, and the limits of precedent

**[31:15] [P]**
> सुनने-सुनाने में क्या आता है? हमारी कल्पनाशीलता तदाकार करता है — हम प्रमाणित नहीं कर सकता। यहाँ तक आता है। हम उसी स्थिति में हम संसार में उपदेश … उपदेश देने के बाद हम अपने में जाँचा — क्या उपदेश दे रहा है इसमें …
>
> *What comes about in hearing and telling? Our imaginativeness takes the form — we cannot evidence it. It comes this far. In that very condition we [give] sermon in the world … after giving the sermon we examined in ourselves — what is being preached in this …*

**[31:48] [P]**
> वह स्वयं … कुछ पूरा करने के लिए, शमन करने के लिए, हम यह सब काम किए। काम करने [से] पहले [उस] जगह में पहुँच गए — समाधि में। वहाँ कोई ज्ञान नहीं हुआ। पहले वाला तो वहाँ से छूट गए — उपदेश[-विधि] से, स्वनिरीक्षण से।
>
> *That itself … to complete something, to quell something, we did all this work. Before doing the work we arrived at [that] place — in samadhi. There no knowledge occurred. The earlier thing was left behind there — the sermon[-method], through self-examination.*

**[32:17] [P]**
> हम समझा कि नहीं? समझ के कर रहा हूँ, जी के कर रहा हूँ, कि लोगों के लिए कह रहा हूँ? … यह निकल गए। वहाँ से हम व्यासित हैं, और कितने लोग व्यासित होंगे — आप इस वर्ष तो गणना कर लो। जिज्ञासा पैदा होना की जगह …
>
> *Did we understand or not? Am I doing it having understood, doing it having lived it, or am I saying it for people's sake? … This got sorted out. From there we are troubled, and how many people would be troubled — you may count this year. In place of inquisitiveness arising …*

**[32:48] [P]**
> स्वनिरीक्षण का अधिकार क्या होगा? वो ही अभिव्यक्ति है न। भी हम कहने में, करने में, जीने में — कितना अंतर है? एक है। उसको सोचने के [लिए] वो ही तो लिखा है वेद-व्यास [ने] — "कर्मण्येकम् मनस्येकम् वचस्येकम् महात्मनाम्" — यह लिखा है।
>
> *What would be the entitlement of self-examination? That itself is the expression. In our saying, doing and living — how much difference is there? It is one. To think about it, that is just what Ved Vyas wrote — "one in action, one in mind, one in speech, of great souls" — this is written.*
>
> *Note: the verse is conventionally cited as मनस्येकं वचस्येकं कर्मण्येकं महात्मनाम्; the speaker's order differs and the ASR may have reordered it further.*

**[33:07] [U]** — *not recoverable from the corpus: **शुकदेव** appears nowhere in MVD, SB, JV or KD, so this reference to the Bhagavata/Brahmasutra material has no internal anchor to check it against.*
> शुकदेव जी … ज्ञान … यह ब्रह्मसूत्र [में] बताया है। तो जब उन्होंने पूछा — क्या शुकदेव ने पूछा — वे ऐसे कि "तुम जैसा कहते हैं, हम भी कह सकते हैं कि हमको ब्रह्म-ज्ञान हो गया है।" तब … और एक लाइन लिख[ा] …
>
> *Shukadeva ji … knowledge … this is stated in the Brahmasutra. So when he asked — did Shukadeva ask — thus: "as you say, we too can say that we have attained knowledge of Brahman." Then … wrote one more line …*

**[33:40] [P]** — *bears on the study's §6.2 and §1.8*
> इसके आधार पर पहले भी यह जिज्ञासा हुई है, इसमें दो राय नहीं है; किन्तु अनुभवमूलक विधि से हुआ है, ऐसा हम कह नहीं सकते हैं। समाधि तो बहुत सारे लोगों को हुआ है; उपदेश में उनका परवर्ती भी हुआ होगा; किन्तु प्रमाण प्रस्तुत करन[े] …
>
> *On this basis this inquisitiveness has arisen before too, there are not two opinions about it; but that it happened by the realisation-based way, that we cannot say. Samadhi has indeed occurred to a great many people; there would have been successors of theirs in preaching too; but as to presenting evidence …*

**[34:07] [P]** — *the general-method claim*
> "सब कोई समाधि-संयम करेगा, अनुसंधान करेगा" — यह अव्यवहारिक बात है। समाधि-संयम — क्या हर व्यक्ति अनुसंधान करके जी पाएगा? नहीं होगा। तब क्या विधि है? सबके लिए पहुँचने की अध्ययन विधि है। पहले श्रुति विधि थी; उस श्रुति व[िधि] …
>
> *"Everyone will do samadhi-samyama, will do research" — this is an impractical matter. Samadhi-samyama — will every person manage to live by doing research? It will not happen. Then what is the method? For everyone to arrive, the method is study. Formerly the method was shruti; that shruti me[thod] …*

**[34:41] [P]**
> … श्रुति विधि से भी व्यापक वस्तु को सत्य समझ नहीं [सके] — यह कहा गया है। वह हक़ीक़त तो यह है। तो उसको अब क्या कह रहे हैं — सह-अस्तित्व को परम सत्य कहा। सह-अस्तित्व में … उसका मूल सूत्र क्या लिखा — "ब्रह्म सत्य, जगत मिथ्या"; [अब] में क्या लिखा — [ब्रह्म सत्य, जगत शाश्वत] …
>
> *… even by the shruti method the pervasive reality could not be understood as truth — this has been said. That is the fact of it. So what are we now calling it — coexistence has been called the ultimate truth. In coexistence … what was written as its root formula — "Brahman is real, the world is unreal"; [now] what is written — [Brahman is real, the world is eternal] …*
>
> *Recovered from the primary texts.* The ASR gave `बर्मसत्य जगत में क्या लिखा` — a fragment. Every term in this segment is a defined one: **श्रुति** is glossed at MVD p. 324 as *यथार्थ रूपी ज्ञान, विवेक, विज्ञान का भाषाकरण* (giving language to knowledge), so "the shruti method" is not loose talk; **व्यापक वस्तु** is core vocabulary (MVD pp. 4, 6, 33). And the formula is the darshan's single most-repeated revision of Vedanta: MVD p. 3 states the inherited version — *वेदान्त के अनुसार ज्ञान "ब्रह्म सत्य, जगत मिथ्या"* — and MVD p. 12 states Nagraj's replacement in the Main Points: **ब्रह्म सत्य, जगत शाश्वत।** SB makes the substitution explicit: *"ब्रह्म सत्य, जगत् मिथ्या" के स्थान पर "ब्रह्म सत्य, जगत शाश्वत्" होने के प्रतिपादन के रूप में प्रस्तुत है*. The bracketed completion is therefore the printed doctrine, not a guess — but it **is** supplied, and is bracketed accordingly.

---

## 13. A digression on solar heat and nuclear testing

*This stretch leaves the session's subject. It is retained for completeness and because it shows the speaker's habitual move from doctrine to physical example. The physics claims here are the speaker's own and are not evaluated.*

**[35:15] [U]**
> अभी सूरज को जलाकर आए हैं आदमी … यहीं, यहीं। अभी यहाँ … इस बार धरती को सूरज बनाने वाले हैं; ऐसे ही लोग वहाँ भी धरती को सूरज बना करके आ गए हैं। अभी इसको बनाना शेष है; उसके बाद … धरती को कराएँगे …
>
> *Men have come having set the sun alight … right here, right here. Now here … this time they are going to make the earth into a sun; such people have there too made the earth into a sun and come. Now this remains to be made; after that … will make the earth …*

**[35:45] [U]**
> और सूरज [में] जितना प्रकाश है, सूरज [में] जितना तापमान है, वो उससे … होने के बाद ही विस्फोट होता है; विस्फोट होने के बाद अनेक … पैदा है। सूरज कितना विस्फोट किया है? आदमी धरती में कितना विस्फोट किया है? यह तो सामान्य व्यक्ति की सोच है।
>
> *And however much light there is in the sun, however much temperature there is in the sun, that from it … only after that does explosion occur; after explosion occurs, many … are produced. How much has the sun exploded? How much has man exploded in the earth? This is the thinking of an ordinary person.*

**[36:17] [U]**
> अभी सूरज में जितना तापमान है, उतने तापमान के बराबर में ये फ़िशन को [सुनाते] हैं। यदि उतने डिग्री का ताप आता है तो सही हुआ; नहीं तो कमी रहे। कमी को पूरा करने के लिए … इसलिए होती जाती है। ये बारंबार हम जो …
>
> *However much temperature there is in the sun, equal to that temperature they [speak of] this fission. If that many degrees of heat comes, then it has been right; otherwise a deficit remains. To make up the deficit … therefore it goes on. This repeatedly, which we …*

**[36:44] [P]**
> अमेरिका अकेले एक हज़ार बार से [अधिक] टेस्ट कर चुका है — न्यूक्लियर टेस्ट। सारे धरती के जो देश मिलकर के तीन हज़ार बार से [अधिक] कर चुका है। भारत [ने] चार बार किया है, पाकिस्तान [ने] चार बार किया है — ऐसा लिखा है, रिपोर्ट …
>
> *America alone has done more than a thousand tests — nuclear tests. All the countries of the earth together have done more than three thousand times. India has done it four times, Pakistan has done it four times — so it is written, the report …*

**[37:12] [P]**
> यदि ये सब देखते हैं, तो आदमी ने कितना खुराफ़ात किया है संसार में अभी तक — उसको सोच लो। सही क्या किया, उसका प्रमाण कहाँ? सहीपन का भी कहीं न कहीं प्रमाण होना चाहिए कि न? …
>
> *If we look at all this, then how much mischief man has done in the world until now — think it over. What did he do rightly, where is the evidence of it? Of rightness too there should be evidence somewhere, should there not? …*

---

## 14. *Swarga*, *moksha*, and the *shanti mantra*

**[37:44] [P]**
> अंतिम ज्ञान स्वर्ग और मोक्ष ही — ऐसा कहा है, हमारे आधार-ग्रंथ में। ठीक है न। और वो स्वर्ग और मोक्ष, ये दोनों इस धरती पर है या और कहीं — इसको बता नहीं पाए। स्वर्ग का, मोक्ष का मॉडल भी ये धरती पर नहीं बता पाए।
>
> *That the final knowledge is only swarga and moksha — so it is said, in our foundational text. All right. And that swarga and moksha, whether these two are on this earth or somewhere else — that they could not state. Nor could they exhibit a model of swarga or of moksha on this earth.*

**[38:14] [U]**
> धरती पे स्वर्ग-मोक्ष को बताया गया है? बताया है? क्या बताया है? … यह [राक्षसपन], नोचना — इसी को बताया है? … स्वर्ग …
>
> *Has swarga-moksha been exhibited on earth? Has it been? What has been exhibited? … this [demonic conduct], tearing at one another — is it this that has been exhibited? … swarga …*

**[38:44] [U]**
> अभी अफ़ग़ानिस्तान में एक जगह पकड़ी है, वहाँ उन्होंने … बना रखी है। नहीं — जितना लिखा है वो उतना ही बताए जाए; उसमें अपना कुछ ओमिशन, एडिशन दोनों नहीं किया जाए। … के अनुसार कहा जाए। अभी हमा …
>
> *Now a place has been seized in Afghanistan, there they have … made. No — as much as is written, let just that much be stated; in it neither omission nor addition of one's own should be made. … let it be said accordingly. Now our …*

**[39:11] [P]**
> और मोक्ष भी यहाँ नहीं है; मोक्ष भी कहीं है — दिव्य लोक का है। दिव्य लोक में मोक्ष [होता] है। दिव्य लोक का वर्णन क्या है? ठीक है। यह सब हो चुका है। और जैसे इसमें जो है न — सर्वप्रथम हम शांति-मंत्र पढ़ते हैं, हम लोग। वेद …
>
> *And moksha too is not here; moksha too is somewhere — it belongs to the divine realm. In the divine realm moksha occurs. What is the description of the divine realm? All right. All this has been done. And as in this — first of all we recite the shanti mantra, we people. The Veda …*

**[39:39] [P]** — *the shanti mantra critique*
> पहले क्या कहते हैं? "द्यौः शान्तिः" — दिव्य [लोक] हो गए। दिव्य लोक में जो रहते हैं वो शांत रहें; धरती में रहने वाले शांत नहीं रहें? जैसे कि दिव्य लोक से आ करके गला काटने आ गए! यही हमारे … के साथ पहले दिन की बात है। वो हवन करता था; हम जब उनके सा[थ] …
>
> *What is said first? "Peace in the heavens" — that is the divine realm. Let those who live in the divine realm be at peace; are those living on the earth not to be at peace? As though they had come from the divine realm to cut throats! This is the matter of the first day with our … He used to perform havan; when we [were] with him …*

**[40:12] [P]**
> तो सबेरे वो हवन करते थे, हमको बैठाते थे; तो हम बैठ भी जाते थे, हम सुनते थे। तो "कुछ बताओ" — एक दिन कहा, "हमसे ये बात मत करो, वापस करो।" "नहीं, वापस नहीं करेंगे, तुमको बताना होगा।" वो भी ऐसे ही अड़ियल है। ठीक है। "देखो, पहले तुमने ये …"
>
> *So in the morning he used to perform havan and seat us; and we would sit, we would listen. So, "say something" — one day he said, "do not discuss this with me, take it back." "No, we will not take it back, you will have to state it." He too is just as obstinate. All right. "Look, first you …"*

**[40:40] [P]**
> "तो दिव्य लोक से कौन तलवार लेकर तुम्हारे सामने आया, जिसको 'शांत रहो' कह रहे हो? वो तुम बता दो — पर्याप्त।" दूसरे दिन हवन करना बंद कर दिया। एक ही समय की बात है — दूसरे दिन अपना हवन बंद कर दिया। इसीलिए मैं उस बारे में बातें …
>
> *"Then who came before you sword in hand from the divine realm, to whom you are saying 'be at peace'? You just state that — that is enough." The next day he stopped performing havan. It is a matter of a single occasion — the next day he stopped his havan. That is why I [do not] talk about that …*

**[41:14] [R]** — *methodological statement*
> हम विचार की समीक्षा किया है; व्यक्ति की समीक्षा करने नहीं गए। व्यक्ति को छोड़ रखा है — व्यवहार, आचार। ठीक है, यह ठीक है, गलत क्या है। दोनों विचारधारा की हम समीक्षा कर [रहे हैं]। इन दोनों विचारधारा के अनुसार मानव का अध्[ययन] …
>
> *We have reviewed ideas; we did not go about reviewing persons. The person we have left aside — conduct, practice. All right, this is right, what is wrong. We are reviewing both streams of thought. According to both these streams of thought, the stu[dy] of the human …*

---

## 15. Mystery, accumulation, and what humans have actually built

**[41:47] [R]**
> … ठीक किया कि गलत किया — यह बात ऐसे है। ठीक है। तो यह सब बातें हो गईं, तो रहस्य से हम कुछ पा नहीं सकते; संग्रह-सुविधा से हम तृप्त नहीं हो सकते। … सुविधा-संग्रह से हम कहीं तृप्त …
>
> *… whether rightly done or wrongly done — the matter is thus. All right. So all these matters are done: from mystery we can gain nothing; by accumulation and amenity we cannot be satisfied. … by amenity and accumulation are we anywhere satisfied …*

**[42:16] [R]**
> रहस्य से कुछ पाएँगे नहीं — पाएँगे नहीं। यह इसके ऊपर सभी सोच सकते हैं, अपना मन … कर सकते हैं। सुविधा-संग्रह से हम तृप्त नहीं हो सकते हैं; तृप्ति-बिंदु मिलेगा नहीं, कितना भी करो आगे …
>
> *From mystery we will gain nothing — will gain nothing. On this everyone can think, can [settle] their own mind. By amenity and accumulation we cannot be satisfied; the point of satisfaction will not be found, however much you go on doing …*

**[42:55] [P]** — *the Kalidasa image*
> उपमा उपलब्धि नहीं हो सकते। उपमा कालिदास है। कालिदास क्या है? अपनी डगाली पर बैठकर उसी डगाली को काट करके गिरकर मरने में लगा। उपमा कालिदास है। यह लिखा है — लिखा है कि नहीं? ऐसा ही बात है। ऐसे ही सब भंडार को लेकर हम चले।
>
> *The simile cannot be an attainment. The simile is Kalidasa. What is Kalidasa? Sitting on his own branch, he set about cutting that very branch, falling and dying. The simile is Kalidasa. This is written — is it written or not? It is just so. Just so we have proceeded, taking up the whole store.*

**[43:32] [U]**
> अपना हम जितना [धार] सकते हैं, उससे जो ज़्यादा हो गया होगा, तब हम कहाँ जाएँगे — ऐसा मैं सोचता हूँ। ठीक है। मतलब आगे ये क्लियर हो गई? माने हर व्यक्ति के पास कल्पनाशीलता है — ये पता लगता है कि न? आपको बोध होता है? न पूछो …
>
> *As much as we can hold, whatever has become more than that, then where shall we go — so I think. All right. Meaning, has this become clear further on? That is, every person has imaginativeness — is that evident or not? Does bodh occur to you? Do ask …*

**[44:01] [P]**
> उसका तो प्रमाण कहाँ है? धरती पर है। यह जितने भी फूस की कुटी से लेकर चलके … मनु जन्मा है, उस समय में न फूस की कुटी थी, न … मंज़िल के [मकान] का था। मनु … धरती पर जब अवतरण हुआ है, उस समय में ऐसा कुछ नहीं था। ठीक है।
>
> *Where then is the evidence of it? It is on the earth. All these, beginning from the thatched hut … Manu was born; at that time there was neither a thatched hut, nor a [house] of storeys. When Manu … descended upon the earth, at that time there was nothing of the sort. All right.*

**[44:32] [P]**
> और उससे अच्छा बनाना शुरू किया; होते होते … कपर की मकान बना लेने लगा। … मकान में बहुत अच्छे से अच्छा बनाते बनाते और महल बनाने लगे। महल बनाते बनाते 275 मंज़िल की … बन गया — यह महल था। …
>
> *And he began to build better than that; gradually … began to build houses of [tile]. … building better and better houses, he began to build palaces. Building palaces, of 275 storeys … came about — this was a palace. …*

---

## Cross-references to the printed corpus

| Session passage | Printed locus | Relation |
|---|---|---|
| Four-stage chain (03:03, 13:09) | MVD p. 12 (§7 प्रमाण): *अनुभव ही प्रमाण … प्रमाण ही जागृत परम्परा* | Session supplies the stage-by-stage mechanism the compact formula omits |
| *Sakshatkar* in *chitta*, *bodh* in *buddhi* (02:53, 22:58) | MVD p. 126 | Printed text gives the faculty mapping; session gives what is recognised (रूप-गुण-स्वभाव-धर्म) |
| Chain through *bodh* → resolve → *chintan* → *praman* (24:41) | MVD p. 99 (*अनुभवमूलक बोध*) | Same chain, printed |
| *sakshatkar* → *avdharna bodh* → realisation → *chintan* | JV p. 62 | Nagraj's first-person ordering, printed |
| *Samadhi* contained no knowing (16:36) | MVD p. 7; JV p. 13 | Session is more emphatic: *एक भी ज्ञान नहीं हुआ* |
| *Praman* as power to produce *bodh* in another (04:43) | JV p. 26 ("proof … lies in our ability to convey it") | Session derives what JV stipulates |
| *Rahasya* yields nothing (41:47, 42:16) | MVD pp. 209, 273–274 | Consistent |
| Materialism and idealism both fail (11:26) | MVD p. 3 | Consistent |
| Four *avasthas*, no fifth (14:28) | MVD, SB throughout | Consistent |
| Six-item set at *bodh* — नियम, नियंत्रण, संतुलन, न्याय, धर्म, सत्य (22:58, 23:27, 24:41) | MVD p. 80 (*… अनुभव के फलन में प्रमाणित होता है*); also p. 32; chain at p. 174 | Printed text carries the set verbatim **and ties it to *anubhav***, which is what fixes the session's degraded enumeration |
| *Rup* = आकार, आयतन, घन; *gun* = सम, विषम, मध्यस्थ (05:28) | SB (four-fold analysis of रूप/गुण/स्वभाव/धर्म); MVD p. 47 (*गुण*) | Printed text supplies the exact triads the ASR mangled |
| *Brahm satya, jagat shashwat* replacing *jagat mithya* (34:41) | MVD p. 3 (inherited formula); **MVD p. 12** (the replacement, in Main Points); SB (explicit substitution) | The session's fragment is the darshan's best-known revision of Vedanta |
| **ऋतम्भरा** as the fourth of आशा, विचार, इच्छा, ऋतम्भरा, प्रमाण (04:10, 07:33) | **MVD p. 76** (glossary: *सत्य से परिपूर्ण संकल्प*); pp. 75, 83; SB throughout | Native darshan term, **not** Patanjali's *ritambhara prajna*; it is the *buddhi*-level power the study renders "resolve" |
| **तदाकार-तद्रूप विधि** (09:46, 11:43, 14:16, 16:06, 31:15) | **MVD p. 80** — *सह-अस्तित्व में अनुभव ही तद्रूप, तदाकार विधि है*; four-term cluster *तादात्म्य/तद्रूप/तत्सान्निध्य/तदावलोकन*; *तदावलोकन = दृष्टापद प्रतिष्ठा*; also p. 149 | **Defined, with published English.** Realisation in coexistence *is* the method — which is why 14:12's "there is no other method" follows from the definition rather than asserting something extra. Absent from SB, JV and KD: an MVD-only cluster |
| *Prajna* characterised via *bodh* and *anubhav* (07:33) | MVD pp. 325, 332 | Defined term, not loose usage |
| **कल्पनाशीलता, कर्मस्वतंत्रता found only in humans** (10:08, 10:26) | **SB** — "humanity has risked its fundamental powers — imaginativeness, freedom of action, and thoughtfulness. These powers are unique because they are **found only in humans** … Such traits and actions are not evident in [the other states]" | Printed text makes the session's claim almost word for word, including the exclusion of *padarth*, *pran* and *jeev avastha*. Also MVD: "It is solely due to **freedom in action** that humans have the opportunity to engage in thought, desire, resolve, realisation" |
| ***अनुसंधान* = MVD's Exploration path** (28:43, 29:15, 34:07) | **MVD p. 280** — *एक — अनुसंधान। दो — अनुसरण, अनुकरण, अध्ययन* → "One - Exploration. Two - Following, Emulation, Study" | The session's "second method" **is** the study's §1.8 first path, and the session is what tells us it requires *samadhi-samyama* and is *अव्यवहारिक* in general |
| *पुरुषार्थ* / *परमार्थ* (18:48) | MVD p. 128 (*diligence*, against duty and helplessness); MVD p. 63 glossary (*benevolence*, in स्वार्थ/परार्थ/परमार्थ); p. 146 | Both narrower than the working glosses first used here; corrected on the segment |
| *Shruti* as *भाषाकरण* of knowledge (34:07, 34:41) | MVD pp. 324, 329 | Gives "the shruti method" a precise sense |
| *Gathanpurnata* (15:31) | MVD pp. 8, 13; SB | Term confirmed; the sentence around it is still lost |
| *Upasana* without symbol-worship; goodwill not coercion (26:50) | KD pp. 35, 42 | Consistent in drift |

## Passages to verify before any released study relies on them

| Timestamp | Why it matters | Mark |
|---|---|---|
| 22:28 | *Anubhav* adds no content beyond *sakshatkar* — reframes the study's account of realisation | **[R]** but load-bearing |
| 34:07 | *Samadhi-samyama* declared impractical as a general method; study is the method for all | **[P]** |
| 14:12 | "There is no other method at all" — sits awkwardly beside 34:07 | **[P]** |
| 04:10 | The recursive stage's name, **ऋतम्भरा**. No longer in doubt as vocabulary — it is a defined Madhyasth Darshan term (MVD p. 76; in the five-fold list at pp. 75, 83 and throughout SB), **not** a borrowing from Patanjali. What still needs the audio is only whether *this* segment says it | **[P]** for the term; the segment's wording unconfirmed |
| 22:58, 24:41 | The six-item set — **resolved**: नियम, नियंत्रण, संतुलन, न्याय, धर्म, सत्य. ASR degraded, but fixed by 23:27 and by MVD p. 80. Cite MVD for the set; cite the session only for its placement at *bodh* | **[P]** |
| 26:50 | Teaching by goodwill, not coercion — bears on teacher-dependence | **[P]** |

## Related files

- Analysis and integration plan: [`Studies/Spiritual-Practice-And-Realization/Research-Note-Sakshatkar-Bodh-Anubhav-Praman-Session.md`](../../../Studies/Spiritual-Practice-And-Realization/Research-Note-Sakshatkar-Bodh-Anubhav-Praman-Session.md)
- Study this supports: [`Studies/Spiritual-Practice-And-Realization/Spiritual-Practice-And-Realization.md`](../../../Studies/Spiritual-Practice-And-Realization/Spiritual-Practice-And-Realization.md)
- Raw ASR before normalisation: [`Sakshatkar-Bodh-Anubhav-Praman-2010-raw-asr.txt`](Sakshatkar-Bodh-Anubhav-Praman-2010-raw-asr.txt)
- Folder conventions: [`README.md`](README.md)
