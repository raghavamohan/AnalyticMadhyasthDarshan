# Tier-1 raw ASR — staged corpus

**Status:** staged as raw ASR only — **not promoted**. Do not cite in a released study until a session has been normalised, boilerplate-stripped, reliability-marked, and listened to. See [README.md](README.md) for evidential standing.

## Provenance

| | |
|---|---|
| Source channel | Rakesh Gupta ([@RakeshGuptamadhyasth-darshan](https://www.youtube.com/@RakeshGuptamadhyasth-darshan)) |
| Manifest | `E:\MD-Transcription\manifest-tier1.tsv` (study, duration, video ID, title) |
| Decoder | whisper.cpp + ROCm/HIP, `ggml-large-v3`, language=hi |
| Flags | **no VAD**, **`--max-context 0`** (D10), beam 5, workers 1 |
| Work output | `E:\MD-Transcription\transcripts-gpu-mc0` |
| Staged | 60 recordings, 154,094 words, 23.43 h |

## Mechanical review (D10 re-run)

Run: `python Scripts/_transcribe_review.py --manifest … --transcripts …`

| Metric | Pre-D10 GPU | This corpus (`-mc 0`) |
|---|---|---|
| Words/min | median 111, range 31–153 | median **108**, **88–137** |
| Present | 60/60 | 60/60 |
| `U+FFFD` | ~47 | **131 across 47 files** (D9 — repair on promote) |
| Boilerplate | ~94 / 30 files | **354 across 54 files** (D11 — delete by hand) |

**Density is fixed** — the old 31 wpm loop failure mode is gone. Files are still **not promotion-ready**: expected D11 boilerplate, D9 `U+FFFD`, and the severe consecutive-repeat cases below.

### Severe consecutive loops (`maxrun` ≥ 15)

These need audio-checked repair before trust:

| Video ID | maxrun | top 3-gram | Title |
|---|---|---|---|
| `QA1WhtS2Gzo` | ×59 | कह कह कह | punah anusandhan ya adhyayan kee aavashyakta |
| `MeFEslxQ1XU` | ×57 | कॉफी कॉफी कॉफी | साम्य ऊर्जा - कार्य ऊर्जा |
| `NdlSGSwvqVs` | ×34 | आरण आरण आरण | संस्कार और प्रारब्ध - भाग ३ |
| `1DAyP7XsEXM` | ×24 | वहीं वहीं वहीं | रूप और गुण इन्द्रियगोचर है, स्वभाव और धर्म ज्ञानगोचर है. |
| `pk3UxjDkhiE` | ×20 | नियम नियम नियम | नियम नियंत्रण संतुलन |
| `W6TNMEQIPUA` | ×16 | बड़े बड़े बड़े | संबंधों में प्रयोजनों की पहचान |
| `QgqtqALvMLw` | ×15 | है ठीक है | अनुसन्धान और शोध |

## Index

Each directory holds only the decoder dump `<Slug>--<videoId>-raw-asr.txt`. URL form: `https://youtu.be/<id>`.

| Study | Duration | Directory | Title | URL | wpm | FFFD | boiler | maxrun |
|---|---|---|---|---|---|---|---|---|
| SPR | 1:30:20 | [`sakshatkar-bodh-anubhav--LHmuCc4NveA`](sakshatkar-bodh-anubhav--LHmuCc4NveA/sakshatkar-bodh-anubhav--LHmuCc4NveA-raw-asr.txt) | sakshatkar bodh anubhav | [LHmuCc4NveA](https://youtu.be/LHmuCc4NveA) | 103 | 7 | 12 | 12 |
| SPR | 56:22 | [`nyay-dhrm-sty--8WNTuXNtawg`](nyay-dhrm-sty--8WNTuXNtawg/nyay-dhrm-sty--8WNTuXNtawg-raw-asr.txt) | न्याय - धर्म - सत्य | [8WNTuXNtawg](https://youtu.be/8WNTuXNtawg) | 105 | 5 | 11 | 9 |
| SPR | 53:05 | [`anusndhan-aur-shodh--QgqtqALvMLw`](anusndhan-aur-shodh--QgqtqALvMLw/anusndhan-aur-shodh--QgqtqALvMLw-raw-asr.txt) | अनुसन्धान और शोध | [QgqtqALvMLw](https://youtu.be/QgqtqALvMLw) | 100 | 6 | 2 | 15 |
| SPR | 44:29 | [`smadhi-snym-purvk-gthnpurnta-kriyapurnta-aachrn-pu--Di8YkI5Olzo`](smadhi-snym-purvk-gthnpurnta-kriyapurnta-aachrn-pu--Di8YkI5Olzo/smadhi-snym-purvk-gthnpurnta-kriyapurnta-aachrn-pu--Di8YkI5Olzo-raw-asr.txt) | समाधि-संयम पूर्वक गठनपूर्णता, क्रियापूर्णता, आचरण पूर्णता का अनुसंधान | [Di8YkI5Olzo](https://youtu.be/Di8YkI5Olzo) | 113 | 5 | 6 | 7 |
| SPR | 36:12 | [`punah-anusandhan-ya-adhyayan-kee-aavashyakta--QA1WhtS2Gzo`](punah-anusandhan-ya-adhyayan-kee-aavashyakta--QA1WhtS2Gzo/punah-anusandhan-ya-adhyayan-kee-aavashyakta--QA1WhtS2Gzo-raw-asr.txt) | punah anusandhan ya adhyayan kee aavashyakta | [QA1WhtS2Gzo](https://youtu.be/QA1WhtS2Gzo) | 108 | 2 | 16 | 59 |
| SPR | 30:13 | [`prmanit-hone-ke-uddeshy-ke-sath-hi-sakshatkar-hota--KTeH3rM2qK8`](prmanit-hone-ke-uddeshy-ke-sath-hi-sakshatkar-hota--KTeH3rM2qK8/prmanit-hone-ke-uddeshy-ke-sath-hi-sakshatkar-hota--KTeH3rM2qK8-raw-asr.txt) | प्रमाणित होने के उद्देश्य के साथ ही साक्षात्कार होता है. | [KTeH3rM2qK8](https://youtu.be/KTeH3rM2qK8) | 102 | 0 | 6 | 2 |
| SPR | 24:37 | [`niym-niyntrn-sntuln--pk3UxjDkhiE`](niym-niyntrn-sntuln--pk3UxjDkhiE/niym-niyntrn-sntuln--pk3UxjDkhiE-raw-asr.txt) | नियम नियंत्रण संतुलन | [pk3UxjDkhiE](https://youtu.be/pk3UxjDkhiE) | 101 | 1 | 16 | 20 |
| SPR | 23:41 | [`sadhna-vidhi-aur-adhyyn-vidhi-ka-phl-ek-hi-hai--4tzlDcsegJM`](sadhna-vidhi-aur-adhyyn-vidhi-ka-phl-ek-hi-hai--4tzlDcsegJM/sadhna-vidhi-aur-adhyyn-vidhi-ka-phl-ek-hi-hai--4tzlDcsegJM-raw-asr.txt) | साधना विधि और अध्ययन विधि का फल एक ही है. | [4tzlDcsegJM](https://youtu.be/4tzlDcsegJM) | 132 | 2 | 7 | 5 |
| SPR | 21:51 | [`tadakar-tadroop--rZiMSH-nOiM`](tadakar-tadroop--rZiMSH-nOiM/tadakar-tadroop--rZiMSH-nOiM-raw-asr.txt) | tadakar-tadroop | [rZiMSH-nOiM](https://youtu.be/rZiMSH-nOiM) | 97 | 1 | 4 | 2 |
| SPR | 16:20 | [`only-power-was-visible-in-samadhi-it-became-clear--K7KNzk3uX0k`](only-power-was-visible-in-samadhi-it-became-clear--K7KNzk3uX0k/only-power-was-visible-in-samadhi-it-became-clear--K7KNzk3uX0k-raw-asr.txt) | Only power was visible in Samadhi, it became clear in Sanyam. | [K7KNzk3uX0k](https://youtu.be/K7KNzk3uX0k) | 127 | 2 | 14 | 3 |
| SPR | 13:43 | [`nyay-dhrm-sty-ki-drishti-jivn-men-rhta-hi-hai-uska--EaZcF7ci3hQ`](nyay-dhrm-sty-ki-drishti-jivn-men-rhta-hi-hai-uska--EaZcF7ci3hQ/nyay-dhrm-sty-ki-drishti-jivn-men-rhta-hi-hai-uska--EaZcF7ci3hQ-raw-asr.txt) | न्याय धर्म सत्य की दृष्टि जीवन में रहता ही है, उसका उपयोग करना है. | [EaZcF7ci3hQ](https://youtu.be/EaZcF7ci3hQ) | 117 | 2 | 3 | 11 |
| SPR | 9:04 | [`adhyyn-vidhi-se-bodh-anubhv-mulk-vidhi-se-prman--OIkSW7QYry4`](adhyyn-vidhi-se-bodh-anubhv-mulk-vidhi-se-prman--OIkSW7QYry4/adhyyn-vidhi-se-bodh-anubhv-mulk-vidhi-se-prman--OIkSW7QYry4-raw-asr.txt) | अध्ययन विधि से बोध, अनुभव मूलक विधि से प्रमाण | [OIkSW7QYry4](https://youtu.be/OIkSW7QYry4) | 137 | 1 | 2 | 2 |
| SPR | 8:38 | [`rup-aur-gun-indriygochr-hai-svbhav-aur-dhrm-gyango--1DAyP7XsEXM`](rup-aur-gun-indriygochr-hai-svbhav-aur-dhrm-gyango--1DAyP7XsEXM/rup-aur-gun-indriygochr-hai-svbhav-aur-dhrm-gyango--1DAyP7XsEXM-raw-asr.txt) | रूप और गुण इन्द्रियगोचर है, स्वभाव और धर्म ज्ञानगोचर है. | [1DAyP7XsEXM](https://youtu.be/1DAyP7XsEXM) | 109 | 2 | 1 | 24 |
| SPR | 7:29 | [`smadhi-anishchyta-ke-sath-hai--LwS2ijCCmpY`](smadhi-anishchyta-ke-sath-hai--LwS2ijCCmpY/smadhi-anishchyta-ke-sath-hai--LwS2ijCCmpY-raw-asr.txt) | समाधि अनिश्चयता के साथ है. | [LwS2ijCCmpY](https://youtu.be/LwS2ijCCmpY) | 108 | 0 | 4 | 11 |
| SPR | 7:15 | [`tat-sannidhya-tadakar-tadroop--sGZouRzIllE`](tat-sannidhya-tadakar-tadroop--sGZouRzIllE/tat-sannidhya-tadakar-tadroop--sGZouRzIllE-raw-asr.txt) | tat-sannidhya, tadakar, tadroop | [sGZouRzIllE](https://youtu.be/sGZouRzIllE) | 90 | 0 | 1 | 4 |
| SPR | 5:38 | [`sakshatkar-tk-hi-purusharth-hai--hNA0KL_qAX4`](sakshatkar-tk-hi-purusharth-hai--hNA0KL_qAX4/sakshatkar-tk-hi-purusharth-hai--hNA0KL_qAX4-raw-asr.txt) | साक्षात्कार तक ही पुरुषार्थ है. | [hNA0KL_qAX4](https://youtu.be/hNA0KL_qAX4) | 131 | 0 | 1 | 2 |
| EPI | 40:01 | [`buddhi-ki-kriyaen-dismbr-2008-amrkntk--s9Ffj_u781c`](buddhi-ki-kriyaen-dismbr-2008-amrkntk--s9Ffj_u781c/buddhi-ki-kriyaen-dismbr-2008-amrkntk--s9Ffj_u781c-raw-asr.txt) | बुद्धि की क्रियाएं - दिसम्बर २००८, अमरकंटक | [s9Ffj_u781c](https://youtu.be/s9Ffj_u781c) | 108 | 1 | 5 | 3 |
| EPI | 36:20 | [`bhasha-arth-vstu--kZ6qdNflDWA`](bhasha-arth-vstu--kZ6qdNflDWA/bhasha-arth-vstu--kZ6qdNflDWA-raw-asr.txt) | भाषा - अर्थ - वस्तु | [kZ6qdNflDWA](https://youtu.be/kZ6qdNflDWA) | 103 | 7 | 7 | 2 |
| EPI | 34:20 | [`mnn-ka-mhttv--hg6fQFFPgqQ`](mnn-ka-mhttv--hg6fQFFPgqQ/mnn-ka-mhttv--hg6fQFFPgqQ-raw-asr.txt) | मनन का महत्त्व | [hg6fQFFPgqQ](https://youtu.be/hg6fQFFPgqQ) | 118 | 4 | 1 | 5 |
| EPI | 30:05 | [`gyangochr-ko-prathmikta-di-jae-bhag-2--t15jE0cY9EY`](gyangochr-ko-prathmikta-di-jae-bhag-2--t15jE0cY9EY/gyangochr-ko-prathmikta-di-jae-bhag-2--t15jE0cY9EY-raw-asr.txt) | ज्ञानगोचर को प्राथमिकता दी जाए - भाग २ | [t15jE0cY9EY](https://youtu.be/t15jE0cY9EY) | 125 | 2 | 14 | 4 |
| EPI | 29:42 | [`jivn-men-drishta-vidhi-ka-svrup--ERXwXL1j8t0`](jivn-men-drishta-vidhi-ka-svrup--ERXwXL1j8t0/jivn-men-drishta-vidhi-ka-svrup--ERXwXL1j8t0-raw-asr.txt) | जीवन में दृष्टा विधि का स्वरूप | [ERXwXL1j8t0](https://youtu.be/ERXwXL1j8t0) | 106 | 5 | 1 | 8 |
| EPI | 28:45 | [`trk-ki-sima-adhyyn-abhivykti-smpreshna-prkashn--5E5hu6_IuGs`](trk-ki-sima-adhyyn-abhivykti-smpreshna-prkashn--5E5hu6_IuGs/trk-ki-sima-adhyyn-abhivykti-smpreshna-prkashn--5E5hu6_IuGs-raw-asr.txt) | तर्क की सीमा, अध्ययन, अभिव्यक्ति-सम्प्रेष्णा-प्रकाशन | [5E5hu6_IuGs](https://youtu.be/5E5hu6_IuGs) | 90 | 4 | 1 | 3 |
| EPI | 27:20 | [`gyangochr-ko-prathmikta-di-jae-bhag-1--NzlUJOTQ-uM`](gyangochr-ko-prathmikta-di-jae-bhag-1--NzlUJOTQ-uM/gyangochr-ko-prathmikta-di-jae-bhag-1--NzlUJOTQ-uM-raw-asr.txt) | ज्ञानगोचर को प्राथमिकता दी जाए - भाग १ | [NzlUJOTQ-uM](https://youtu.be/NzlUJOTQ-uM) | 127 | 1 | 17 | 4 |
| EPI | 25:32 | [`jivn-men-drishta-vidhi-aur-anubhv-vidhi--m1mkYOVBfdM`](jivn-men-drishta-vidhi-aur-anubhv-vidhi--m1mkYOVBfdM/jivn-men-drishta-vidhi-aur-anubhv-vidhi--m1mkYOVBfdM-raw-asr.txt) | जीवन में दृष्टा विधि और अनुभव विधि | [m1mkYOVBfdM](https://youtu.be/m1mkYOVBfdM) | 114 | 3 | 4 | 5 |
| EPI | 18:35 | [`karn-gun-gnit-svrup-men-manv-bhasha--eXeMh5nitAw`](karn-gun-gnit-svrup-men-manv-bhasha--eXeMh5nitAw/karn-gun-gnit-svrup-men-manv-bhasha--eXeMh5nitAw-raw-asr.txt) | कारण गुण गणित स्वरूप में मानव भाषा | [eXeMh5nitAw](https://youtu.be/eXeMh5nitAw) | 91 | 1 | 11 | 2 |
| EPI | 15:35 | [`shbd-sprsh-rup-rs-gndh--vuTOjdF6a3k`](shbd-sprsh-rup-rs-gndh--vuTOjdF6a3k/shbd-sprsh-rup-rs-gndh--vuTOjdF6a3k-raw-asr.txt) | शब्द, स्पर्श, रूप, रस, गंध | [vuTOjdF6a3k](https://youtu.be/vuTOjdF6a3k) | 110 | 2 | 0 | 2 |
| EPI | 14:39 | [`indriy-gochr-gyan-gochr-bhag-3--SxFrn056fKo`](indriy-gochr-gyan-gochr-bhag-3--SxFrn056fKo/indriy-gochr-gyan-gochr-bhag-3--SxFrn056fKo-raw-asr.txt) | इन्द्रिय-गोचर ज्ञान-गोचर भाग ३ | [SxFrn056fKo](https://youtu.be/SxFrn056fKo) | 116 | 0 | 1 | 3 |
| EPI | 14:23 | [`indriy-gochr-aur-gyan-gochr-bhag-1--HU0pg3CxdgE`](indriy-gochr-aur-gyan-gochr-bhag-1--HU0pg3CxdgE/indriy-gochr-aur-gyan-gochr-bhag-1--HU0pg3CxdgE-raw-asr.txt) | इन्द्रिय-गोचर और ज्ञान-गोचर - भाग १ | [HU0pg3CxdgE](https://youtu.be/HU0pg3CxdgE) | 113 | 1 | 1 | 3 |
| EPI | 13:56 | [`indriy-gochr-gyan-gochr-bhag-5--SnhhqBRAzng`](indriy-gochr-gyan-gochr-bhag-5--SnhhqBRAzng/indriy-gochr-gyan-gochr-bhag-5--SnhhqBRAzng-raw-asr.txt) | इन्द्रिय-गोचर ज्ञान-गोचर भाग ५ | [SnhhqBRAzng](https://youtu.be/SnhhqBRAzng) | 118 | 2 | 3 | 5 |
| EPI | 13:46 | [`indriy-gochr-gyan-gochr-bhag-2--EE9WUWfJeos`](indriy-gochr-gyan-gochr-bhag-2--EE9WUWfJeos/indriy-gochr-gyan-gochr-bhag-2--EE9WUWfJeos-raw-asr.txt) | इन्द्रिय-गोचर ज्ञान-गोचर भाग-२ | [EE9WUWfJeos](https://youtu.be/EE9WUWfJeos) | 105 | 2 | 2 | 3 |
| EPI | 13:07 | [`hr-vykti-jise-janch-ske-vhi-suchna-hai--eaaYzDKpC3I`](hr-vykti-jise-janch-ske-vhi-suchna-hai--eaaYzDKpC3I/hr-vykti-jise-janch-ske-vhi-suchna-hai--eaaYzDKpC3I-raw-asr.txt) | हर व्यक्ति जिसे जांच सके, वही सूचना है. | [eaaYzDKpC3I](https://youtu.be/eaaYzDKpC3I) | 113 | 1 | 0 | 2 |
| EPI | 13:05 | [`drishta-pd--sddlVcXPVG4`](drishta-pd--sddlVcXPVG4/drishta-pd--sddlVcXPVG4-raw-asr.txt) | दृष्टा पद | [sddlVcXPVG4](https://youtu.be/sddlVcXPVG4) | 102 | 0 | 1 | 2 |
| AXI | 1:02:30 | [`svtv-svtntrta-svrajy--BbfnTJtpQb8`](svtv-svtntrta-svrajy--BbfnTJtpQb8/svtv-svtntrta-svrajy--BbfnTJtpQb8-raw-asr.txt) | स्वत्व - स्वतंत्रता - स्वराज्य | [BbfnTJtpQb8](https://youtu.be/BbfnTJtpQb8) | 128 | 19 | 1 | 2 |
| AXI | 1:01:54 | [`smadhan-smriddhi-purvk-jine-ke-lkshy-ke-arth-men-h---meFJ6dpaYA`](smadhan-smriddhi-purvk-jine-ke-lkshy-ke-arth-men-h---meFJ6dpaYA/smadhan-smriddhi-purvk-jine-ke-lkshy-ke-arth-men-h---meFJ6dpaYA-raw-asr.txt) | समाधान-समृद्धि पूर्वक जीने के लक्ष्य के अर्थ में ही समझना संभव है. | [-meFJ6dpaYA](https://youtu.be/-meFJ6dpaYA) | 112 | 2 | 11 | 6 |
| AXI | 27:47 | [`mngl-maitri-purvk-hi-prbodhn-sphl-ho-skta-hai--hbwR6AyXtWk`](mngl-maitri-purvk-hi-prbodhn-sphl-ho-skta-hai--hbwR6AyXtWk/mngl-maitri-purvk-hi-prbodhn-sphl-ho-skta-hai--hbwR6AyXtWk-raw-asr.txt) | मंगल मैत्री पूर्वक ही प्रबोधन सफल हो सकता है. | [hbwR6AyXtWk](https://youtu.be/hbwR6AyXtWk) | 107 | 0 | 7 | 11 |
| AXI | 27:21 | [`manviyta-purn-aachrn-hi-smjh-ki-ksauti-hai--g8SIxIrhtGA`](manviyta-purn-aachrn-hi-smjh-ki-ksauti-hai--g8SIxIrhtGA/manviyta-purn-aachrn-hi-smjh-ki-ksauti-hai--g8SIxIrhtGA-raw-asr.txt) | मानवीयता पूर्ण आचरण ही समझ की कसौटी है. | [g8SIxIrhtGA](https://youtu.be/g8SIxIrhtGA) | 113 | 2 | 2 | 3 |
| AXI | 23:06 | [`manviyta-purn-aachrn-ka-mhttv--HuZZZ9UvTkA`](manviyta-purn-aachrn-ka-mhttv--HuZZZ9UvTkA/manviyta-purn-aachrn-ka-mhttv--HuZZZ9UvTkA-raw-asr.txt) | मानवीयता पूर्ण आचरण का महत्त्व | [HuZZZ9UvTkA](https://youtu.be/HuZZZ9UvTkA) | 117 | 2 | 6 | 3 |
| AXI | 21:29 | [`snskriti-utsv-aur-vaividhyta--rO6HTVaRklU`](snskriti-utsv-aur-vaividhyta--rO6HTVaRklU/snskriti-utsv-aur-vaividhyta--rO6HTVaRklU-raw-asr.txt) | संस्कृति, उत्सव और वैविध्यता | [rO6HTVaRklU](https://youtu.be/rO6HTVaRklU) | 105 | 0 | 6 | 2 |
| AXI | 20:19 | [`snskar-aur-prarbdh-bhag-3--NdlSGSwvqVs`](snskar-aur-prarbdh-bhag-3--NdlSGSwvqVs/snskar-aur-prarbdh-bhag-3--NdlSGSwvqVs-raw-asr.txt) | संस्कार और प्रारब्ध - भाग ३ | [NdlSGSwvqVs](https://youtu.be/NdlSGSwvqVs) | 112 | 3 | 20 | 34 |
| AXI | 18:55 | [`snbndhon-men-pryojnon-ki-phchan--W6TNMEQIPUA`](snbndhon-men-pryojnon-ki-phchan--W6TNMEQIPUA/snbndhon-men-pryojnon-ki-phchan--W6TNMEQIPUA-raw-asr.txt) | संबंधों में प्रयोजनों की पहचान | [W6TNMEQIPUA](https://youtu.be/W6TNMEQIPUA) | 113 | 1 | 9 | 16 |
| AXI | 16:05 | [`snskar-aur-prarbdh-bhag-5--qMr2t_9w52o`](snskar-aur-prarbdh-bhag-5--qMr2t_9w52o/snskar-aur-prarbdh-bhag-5--qMr2t_9w52o-raw-asr.txt) | संस्कार और प्रारब्ध - भाग ५ | [qMr2t_9w52o](https://youtu.be/qMr2t_9w52o) | 104 | 1 | 11 | 3 |
| AXI | 14:35 | [`sathi-shyogi-smbndh-men-nyay--pJf1837TW1I`](sathi-shyogi-smbndh-men-nyay--pJf1837TW1I/sathi-shyogi-smbndh-men-nyay--pJf1837TW1I-raw-asr.txt) | साथी - सहयोगी सम्बन्ध में न्याय | [pJf1837TW1I](https://youtu.be/pJf1837TW1I) | 128 | 1 | 8 | 2 |
| AXI | 13:58 | [`snskar-aur-prarbdh-bhag-4--3b_aeDU-p2U`](snskar-aur-prarbdh-bhag-4--3b_aeDU-p2U/snskar-aur-prarbdh-bhag-4--3b_aeDU-p2U-raw-asr.txt) | संस्कार और प्रारब्ध - भाग ४ | [3b_aeDU-p2U](https://youtu.be/3b_aeDU-p2U) | 105 | 1 | 26 | 4 |
| AXI | 11:21 | [`snskar-aur-prarbdh-bhag-1--gFQ3FiP3-o4`](snskar-aur-prarbdh-bhag-1--gFQ3FiP3-o4/snskar-aur-prarbdh-bhag-1--gFQ3FiP3-o4-raw-asr.txt) | संस्कार और प्रारब्ध - भाग १ | [gFQ3FiP3-o4](https://youtu.be/gFQ3FiP3-o4) | 101 | 2 | 4 | 8 |
| AXI | 10:40 | [`nyay-aur-smbndh--Z7APu2kSVC4`](nyay-aur-smbndh--Z7APu2kSVC4/nyay-aur-smbndh--Z7APu2kSVC4-raw-asr.txt) | न्याय और सम्बन्ध | [Z7APu2kSVC4](https://youtu.be/Z7APu2kSVC4) | 111 | 0 | 2 | 2 |
| AXI | 9:54 | [`snvedna-aur-muly--SOs_Ggx3AUg`](snvedna-aur-muly--SOs_Ggx3AUg/snvedna-aur-muly--SOs_Ggx3AUg-raw-asr.txt) | संवेदना और मूल्य | [SOs_Ggx3AUg](https://youtu.be/SOs_Ggx3AUg) | 108 | 0 | 1 | 2 |
| ONT | 43:56 | [`kriya-kal-vrtman--s15eeE_9u9M`](kriya-kal-vrtman--s15eeE_9u9M/kriya-kal-vrtman--s15eeE_9u9M-raw-asr.txt) | क्रिया, काल, वर्तमान | [s15eeE_9u9M](https://youtu.be/s15eeE_9u9M) | 102 | 1 | 14 | 6 |
| ONT | 39:57 | [`nity-vrtmanta-2006-jivn-vidya-smmlen--x9_pq65SiP0`](nity-vrtmanta-2006-jivn-vidya-smmlen--x9_pq65SiP0/nity-vrtmanta-2006-jivn-vidya-smmlen--x9_pq65SiP0-raw-asr.txt) | नित्य वर्तमानता - २००६ जीवन विद्या सम्मलेन | [x9_pq65SiP0](https://youtu.be/x9_pq65SiP0) | 121 | 11 | 0 | 2 |
| ONT | 29:16 | [`sthiti-gti--FsCT-uYtBkI`](sthiti-gti--FsCT-uYtBkI/sthiti-gti--FsCT-uYtBkI-raw-asr.txt) | स्थिति-गति | [FsCT-uYtBkI](https://youtu.be/FsCT-uYtBkI) | 111 | 1 | 3 | 2 |
| ONT | 21:31 | [`pd-aur-pd-chkr--DhvRSxtXvEg`](pd-aur-pd-chkr--DhvRSxtXvEg/pd-aur-pd-chkr--DhvRSxtXvEg-raw-asr.txt) | पद और पद चक्र | [DhvRSxtXvEg](https://youtu.be/DhvRSxtXvEg) | 107 | 1 | 17 | 4 |
| ONT | 20:40 | [`pd-pd-chkr-snkrmn-gunatmk-vikas--20QUnYwcSWA`](pd-pd-chkr-snkrmn-gunatmk-vikas--20QUnYwcSWA/pd-pd-chkr-snkrmn-gunatmk-vikas--20QUnYwcSWA-raw-asr.txt) | पद, पद चक्र, संक्रमण, गुणात्मक विकास | [20QUnYwcSWA](https://youtu.be/20QUnYwcSWA) | 104 | 3 | 2 | 2 |
| ONT | 18:25 | [`anukrm-se-hona-rhna--teo0P5KxU-o`](anukrm-se-hona-rhna--teo0P5KxU-o/anukrm-se-hona-rhna--teo0P5KxU-o-raw-asr.txt) | अनुक्रम से होना-रहना | [teo0P5KxU-o](https://youtu.be/teo0P5KxU-o) | 102 | 1 | 8 | 2 |
| ONT | 18:14 | [`samy-uurja-kary-uurja--MeFEslxQ1XU`](samy-uurja-kary-uurja--MeFEslxQ1XU/samy-uurja-kary-uurja--MeFEslxQ1XU-raw-asr.txt) | साम्य ऊर्जा - कार्य ऊर्जा | [MeFEslxQ1XU](https://youtu.be/MeFEslxQ1XU) | 100 | 1 | 15 | 57 |
| ONT | 16:20 | [`samy-stta-kary-uurja-prktn-aur-prvritti--F7bXpQ3Mu-8`](samy-stta-kary-uurja-prktn-aur-prvritti--F7bXpQ3Mu-8/samy-stta-kary-uurja-prktn-aur-prvritti--F7bXpQ3Mu-8-raw-asr.txt) | साम्य सत्ता, कार्य ऊर्जा, प्रकटन और प्रवृत्ति | [F7bXpQ3Mu-8](https://youtu.be/F7bXpQ3Mu-8) | 88 | 1 | 1 | 2 |
| ONT | 14:47 | [`prmanu-men-vikas-vyvstha-ki-smjh--44RcEl-JbU4`](prmanu-men-vikas-vyvstha-ki-smjh--44RcEl-JbU4/prmanu-men-vikas-vyvstha-ki-smjh--44RcEl-JbU4-raw-asr.txt) | परमाणु में विकास, व्यवस्था की समझ | [44RcEl-JbU4](https://youtu.be/44RcEl-JbU4) | 110 | 2 | 1 | 2 |
| ONT | 8:25 | [`yog-snyog-n-ho-aisa-koii-sthiti-hi-nhin-hai--HvUXb4PW7FU`](yog-snyog-n-ho-aisa-koii-sthiti-hi-nhin-hai--HvUXb4PW7FU/yog-snyog-n-ho-aisa-koii-sthiti-hi-nhin-hai--HvUXb4PW7FU-raw-asr.txt) | योग-संयोग न हो, ऐसा कोई स्थिति ही नहीं है. | [HvUXb4PW7FU](https://youtu.be/HvUXb4PW7FU) | 102 | 0 | 3 | 10 |
| ONT | 6:17 | [`sh-astitv-men-yog-snyog--BvqAx3yNE_w`](sh-astitv-men-yog-snyog--BvqAx3yNE_w/sh-astitv-men-yog-snyog--BvqAx3yNE_w-raw-asr.txt) | सह-अस्तित्व में योग-संयोग | [BvqAx3yNE_w](https://youtu.be/BvqAx3yNE_w) | 97 | 0 | 1 | 2 |
| ONT | 4:58 | [`prmanu-men-dhvni-tap-vidyut--a1ARueeihmA`](prmanu-men-dhvni-tap-vidyut--a1ARueeihmA/prmanu-men-dhvni-tap-vidyut--a1ARueeihmA-raw-asr.txt) | परमाणु में ध्वनि-ताप-विद्युत् | [a1ARueeihmA](https://youtu.be/a1ARueeihmA) | 111 | 0 | 0 | 2 |
| ONT | 2:57 | [`prtyavrtn-pravrtn--l7DcCqLFAZM`](prtyavrtn-pravrtn--l7DcCqLFAZM/prtyavrtn-pravrtn--l7DcCqLFAZM-raw-asr.txt) | प्रत्यावर्तन - परावर्तन | [l7DcCqLFAZM](https://youtu.be/l7DcCqLFAZM) | 99 | 1 | 0 | 1 |
| ONT | 2:20 | [`gthnpurn-prmanu--hITrFtQsUac`](gthnpurn-prmanu--hITrFtQsUac/gthnpurn-prmanu--hITrFtQsUac-raw-asr.txt) | गठनपूर्ण परमाणु | [hITrFtQsUac](https://youtu.be/hITrFtQsUac) | 99 | 2 | 0 | 1 |

## Out of scope for this staging

- Hindi normalisation, English translation, `[R]`/`[P]`/`[U]` marks, PDF
- Bulk deletion of subscribe/boilerplate tokens
- Re-decode of the severe loop files

Promotion remains per-session work under the [transcribe-recording](../../../.agents/skills/transcribe-recording/SKILL.md) skill.
