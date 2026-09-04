#!/usr/bin/env python3
"""
Legacy extractor retained only to explain why the old audit artifacts are unsafe.

The Karma Darshan Hindi PDF's embedded text layer is corrupt. Automated extraction
from it produced false Hindi tokens even after heuristic repair, so this command is
intentionally disabled. Use rendered source-page images for Hindi verification.

Usage:
    python Scripts/_extract_kd_hindi_terms.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pymupdf as fitz
import openpyxl

from _common import BASE, write_text_lf

KD_DIR = BASE / "References" / "Madhyasth-Darshan" / "KD-Karm-Darshan-English"
KD_PDF = BASE / "References" / "Madhyasth-Darshan" / "KD-karm darshan v5.pdf"
KD_MD = KD_DIR / "KD-Karm-Darshan-English.md"
KD_GLOSSARY_MD = KD_DIR / "KD-Glossary-Additions.md"
MD_MAPPING_XLSX = BASE / "References" / "Madhyasth-Darshan" / "MD-Mapping.xlsx"
AUDIT_MD_OUTPUT = KD_DIR / "KD-Hindi-Terms-Mapping-Audit.md"
JSON_OUTPUT = KD_DIR / "KD-Hindi-Terms-Mapping.json"

# Common Hindi functional words / stopwords / auxiliary forms to exclude
HINDI_STOPWORDS = {
    "में", "के", "है", "का", "से", "को", "की", "और", "भी", "पर", "होने", "होता", "यह", "एक",
    "इस", "ने", "तक", "था", "थी", "थे", "हैं", "ही", "हो", "एवं", "होती", "होते", "पत", "कत",
    "कि", "या", "जो", "वह", "द्वारा", "इन", "उस", "उन", "कर", "करके", "करना", "करने", "हत्",
    "करता", "करती", "करते", "किया", "किये", "रूप", "रूप में", "लिये", "लिए", "साथ", "सब", "ना",
    "कुछ", "किसी", "अन्य", "तरह", "जैसे", "तथा", "अथवा", "अर्थात", "यही", "इसी", "वही", "पह",
    "उसी", "यदि", "तो", "जब", "तब", "जहाँ", "तहाँ", "यहाँ", "वहाँ", "अतः", "इत्यादि", "प्रकार",
    "होना", "होने से", "प्राप्त", "प्रति", "अनुसार", "कारण", "बिना", "अंतर्गत", "अन्तर्गत", "नाहीं", "नहीं",
    "बारे", "मात्र", "फिर", "अपने", "अपनी", "अपना", "हमारे", "हमारी", "हमारा", "मानव", "हुआ", "हुई", "हुए",
    "पाया", "जाता", "जाती", "जाते", "गया", "गई", "गए", "अध्याय", "भाग", "पृष्ठ", "नाम", "कहा", "कहना",
    "इसके", "इसका", "इसकी", "इसके", "ऐसे", "ऐसी", "ऐसा", "सब", "सभी", "ये", "वे", "कोई", "इन्हें", "उन्हें",
    "रहा", "रही", "रहे", "रहता", "रहती", "रहते", "होता", "होती", "होते", "किया", "किया", "किये",
}

FONT_REPAIR_MAP = [
    ("व्यवथिा", "व्यवस्था"),
    ("सहअतिित्व", "सहअस्तित्व"),
    ("अतिित्व", "अस्तित्व"),
    ("जागृतत", "जागृति"),
    ("तिथस्ि", "स्थिति"),
    ("कि्रया", "क्रिया"),
    ("प्रमाणिि", "प्रमाणित"),
    ("परष्ट", "स्पष्ट"),
    ("कशम", "कर्म"),
    ("कमम", "कर्म"),
    ("दशमन", "दर्शन"),
    ("दशशन", "दर्शन"),
    ("अथश", "अर्थ"),
    ("अशथ", "अर्थ"),
    ("गतत", "गति"),
    ("गस्ि", "गति"),
    ("पूवशक", "पूर्वक"),
    ("पूशवक", "पूर्वक"),
    ("आवश्यकिा", "आवश्यकता"),
    ("व्यवहाि", "व्यवहार"),
    ("समािान", "समाधान"),
    ("अथाशि्", "अर्थात्"),
    ("अशथात्", "अर्थात्"),
    ("पूणश", "पूर्ण"),
    ("पूशण", "पूर्ण"),
    ("निशि्चत", "निश्चित"),
    ("प्रत्यत", "प्रत्यक्ष"),
    ("ानने", "जानने"),
    ("सम्परन", "संपन्न"),
    ("िमिा", "क्षमता"),
    ("साथशक", "सार्थक"),
    ("साशथक", "सार्थक"),
    ("तवयिं", "स्वयं"),
    ("वियं", "स्वयं"),
    ("िमम", "धर्म"),
    ("िमश", "धर्म"),
    ("धशम", "धर्म"),
    ("अस्िक", "अधिक"),
    ("कािण", "कारण"),
    ("विस्ि", "विस्तार"),
    ("एविं", "एवं"),
    ("होिा", "होता"),
    ("होिी", "होती"),
    ("होिे", "होते"),
    ("जािा", "जाता"),
    ("िहिा", "रहता"),
    ("कििा", "करता"),
    ("कििे", "करते"),
    ("शिीि", "शरीर"),
    ("वतिु", "वस्तु"),
    ("िििी", "करती"),
    ("आिाि", "आकार"),
    ("प्रकाि", "प्रकार"),
    ("अनुसाि", "अनुसार"),
    ("सवि", "सर्व"),
    ("पणम", "पूर्ण"),
    ("सिंपूणम", "संपूर्ण"),
    ("सम्पूशण", "संपूर्ण"),
    ("तनयंत्रण", "नियंत्रण"),
    ("तनयम", "नियम"),
    ("तनयामक", "नियामक"),
    ("तनरंतर", "निरंतर"),
    ("तनराकार", "निराकार"),
    ("तनष्कषम", "निष्कर्ष"),
    ("तनत्या", "नित्या"),
    ("तनश्चय", "निश्चय"),
    ("तनश्चयता", "निश्चयता"),
    ("स्व ाि", "विचार"),
    ("स्वाि", "विचार"),
    ("स्वाकाि", "स्वीकार"),
    ("तपष्ट", "स्पष्ट"),
    ("तवभाव", "स्वभाव"),
    ("परिंपरा", "परंपरा"),
    ("िात्पयश", "तात्पर्य"),
    ("भौस्िक", "भौतिक"),
    ("बोि", "बोध"),
    ("प्रकि्रया", "प्रक्रिया"),
    ("सिंसात", "संसार"),
    ("जागृि", "जागृत"),
]

DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]+(?:\s*[\-\–\—]\s*[\u0900-\u097F]+)*")
DEVANAGARI_WORD_RE = re.compile(r"[\u0900-\u097F]{2,}")


def repair_pdf_font_artifacts(text: str) -> str:
    """Repair legacy font encoding shifts present in the PDF text layer."""
    t = text
    for old, new in FONT_REPAIR_MAP:
        t = t.replace(old, new)
        
    # Reph fixes: शम -> र्म, शथ -> र्थ, शव -> र्व, शण -> र्ण
    t = t.replace("शम", "र्म").replace("शथ", "र्थ").replace("शव", "र्व").replace("शण", "र्ण")
    
    # Conjunct fixes: तव -> स्व, तथ -> स्थ, स्ि -> ति, तत -> ति
    t = re.sub(r"तव([क-ह])", r"स्व\1", t)
    t = re.sub(r"([क-ह])तथ", r"\1स्थ", t)
    t = re.sub(r"([क-ह])स्ि", r"\1ति", t)
    t = re.sub(r"([क-ह])तत", r"\1ति", t)
    t = re.sub(r"अतिि", "अस्ति", t)
    t = re.sub(r"स्([क-ह])", r"\1ि", t)
    t = re.sub(r"(?<=[क-ह])ि(?=[ \n\.\,\|।\)])", "त", t)
    
    t = (
        t.replace("किने", "करने")
        .replace("किना", "करना")
        .replace("किता", "करता")
        .replace("किते", "करते")
        .replace("औि", "और")
        .replace("पि", "पर")
        .replace("िहना", "रहना")
        .replace("िहे", "रहे")
        .replace("िहा", "रहा")
        .replace("िथा", "तथा")
        .replace("बाि", "बात")
        .replace("साि", "सात")
    )
    return t


def hindi_stem(word: str) -> str:
    """Basic Hindi lemmatization to reduce inflections to root forms."""
    w = word.strip("।|,.- ")
    if len(w) <= 2:
        return w
    
    suffixes = ["पूर्वक", "त्मक", "वश", "गत", "हीन", "युक्त", "ों", "ओं", "एं", "यां", "याँ"]
    for suf in suffixes:
        if w.endswith(suf) and len(w) - len(suf) >= 2:
            w = w[:-len(suf)]
            break
            
    return w


def load_md_mapping() -> dict[str, dict[str, str]]:
    """Load canonical mappings from MD-Mapping.xlsx."""
    if not MD_MAPPING_XLSX.is_file():
        return {}
    
    mapping: dict[str, dict[str, str]] = {}
    wb = openpyxl.load_workbook(MD_MAPPING_XLSX, read_only=True, data_only=True)
    ws = wb.active
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        raw_hindi = str(row[0]).strip()
        english = str(row[1]).strip() if row[1] is not None else ""
        note = str(row[5]).strip() if len(row) > 5 and row[5] is not None else ""
        
        variants = [v.strip() for v in raw_hindi.split(",") if v.strip()]
        for v in variants:
            mapping[v] = {
                "hindi": v,
                "english": english,
                "note": note,
                "source": "MD-Mapping.xlsx",
            }
            st = hindi_stem(v)
            if st not in mapping:
                mapping[st] = {
                    "hindi": v,
                    "english": english,
                    "note": note,
                    "source": "MD-Mapping.xlsx",
                }
    wb.close()
    return mapping


def load_kd_glossary_additions() -> dict[str, dict[str, str]]:
    """Load KD additions and overrides from KD-Glossary-Additions.md."""
    if not KD_GLOSSARY_MD.is_file():
        return {}
    
    mapping: dict[str, dict[str, str]] = {}
    table_row_re = re.compile(
        r"^\|\s*(?P<hindi>[^|]+)\s*\|\s*(?P<translit>[^|]+)\s*\|\s*(?P<english>[^|]+)\s*\|\s*(?P<note>[^|]*)\s*\|$"
    )
    
    in_table = False
    for line in KD_GLOSSARY_MD.read_text(encoding="utf-8").splitlines():
        if line.startswith("| Hindi |"):
            in_table = True
            continue
        if not in_table or line.startswith("| :") or not line.startswith("|"):
            continue
        m = table_row_re.match(line.strip())
        if not m:
            continue
        raw_hindi = m.group("hindi").strip()
        translit = m.group("translit").strip()
        english = m.group("english").strip()
        note = m.group("note").strip()
        
        for v in [x.strip() for x in raw_hindi.split(",") if x.strip()]:
            mapping[v] = {
                "hindi": v,
                "transliteration": translit,
                "english": english,
                "note": note,
                "source": "KD-Glossary-Additions.md",
            }
            st = hindi_stem(v)
            if st not in mapping:
                mapping[st] = {
                    "hindi": v,
                    "transliteration": translit,
                    "english": english,
                    "note": note,
                    "source": "KD-Glossary-Additions.md",
                }
    return mapping


def extract_contextual_mappings_from_markdown(kd_md_text: str) -> dict[str, str]:
    """Extract English -> Hindi or Hindi -> English pairs embedded in KD markdown text."""
    contextual: dict[str, str] = {}
    
    p1 = re.compile(r"([A-Za-z0-9\s\,\–\-\—\/\']+)\s*\(([\u0900-\u097F\s\,\–\-\—\/]+)\)")
    for match in p1.finditer(kd_md_text):
        en_part = match.group(1).strip()
        hi_part = match.group(2).strip()
        if len(en_part) > 2 and len(hi_part) > 1:
            contextual[hi_part] = en_part
            
    p2 = re.compile(r"([\u0900-\u097F\s\-\–]+)\s*\(([A-Za-z0-9\s\,\–\-\—\/]+)\)")
    for match in p2.finditer(kd_md_text):
        hi_part = match.group(1).strip()
        en_part = match.group(2).strip()
        if len(hi_part) > 1 and len(en_part) > 2:
            contextual[hi_part] = en_part

    return contextual


def extract_hindi_terms_from_pdf() -> Counter[str]:
    """Extract Hindi terms from KD Hindi source PDF."""
    if not KD_PDF.is_file():
        return Counter()

    doc = fitz.open(str(KD_PDF))
    full_text = "\n".join([page.get_text("text") for page in doc])
    doc.close()
    
    repaired = repair_pdf_font_artifacts(full_text)
    words = DEVANAGARI_WORD_RE.findall(repaired)
    
    filtered = Counter()
    for w in words:
        w_clean = w.strip("।|,.- ")
        if w_clean and w_clean not in HINDI_STOPWORDS and len(w_clean) >= 2:
            filtered[w_clean] += 1
            
    return filtered


def extract_hindi_terms_from_md() -> Counter[str]:
    """Extract Devanagari terms embedded in KD English markdown text."""
    if not KD_MD.is_file():
        return Counter()
    
    text = KD_MD.read_text(encoding="utf-8")
    dev_matches = DEVANAGARI_RE.findall(text)
    
    counter = Counter()
    for match in dev_matches:
        term = match.strip("।|,.- ")
        if term and term not in HINDI_STOPWORDS:
            counter[term] += 1
            
    return counter


def main() -> int:
    print(
        "DISABLED: the Karma Darshan Hindi PDF has a corrupt embedded text layer.\n"
        "Use rendered source-page images for Hindi verification; do not regenerate "
        "KD-Hindi-Terms-Mapping.* from this script.",
        file=sys.stderr,
    )
    return 2

    # Historical implementation retained below for provenance only.
    parser = argparse.ArgumentParser(
        description="Extract and map Karma Darshan Hindi root words against current translation glossaries."
    )
    parser.add_argument(
        "--audit-out",
        type=Path,
        default=AUDIT_MD_OUTPUT,
        help="Path for markdown audit report",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=JSON_OUTPUT,
        help="Path for JSON mapping output",
    )
    args = parser.parse_args()

    print("=== Karma Darshan Hindi Root Words & Mapping Audit ===")
    
    # 1. Load Glossaries
    md_lookup = load_md_mapping()
    kd_additions = load_kd_glossary_additions()
    
    master_lookup: dict[str, dict[str, str]] = {}
    master_lookup.update(md_lookup)
    master_lookup.update(kd_additions)
    
    print(f"Loaded {len(md_lookup)} entries from MD-Mapping.xlsx")
    print(f"Loaded {len(kd_additions)} entries from KD-Glossary-Additions.md")
    print(f"Total unique mapped terms in master glossary: {len(master_lookup)}")

    # 2. Extract Hindi terms from text sources
    pdf_terms = extract_hindi_terms_from_pdf()
    md_terms = extract_hindi_terms_from_md()
    
    kd_md_text = KD_MD.read_text(encoding="utf-8") if KD_MD.is_file() else ""
    contextual_map = extract_contextual_mappings_from_markdown(kd_md_text)

    all_terms: Counter[str] = Counter()
    all_terms.update(pdf_terms)
    all_terms.update(md_terms)
    
    for hi in kd_additions:
        all_terms[hi] += 1

    print(f"Extracted {len(all_terms)} unique candidate Hindi terms/roots from Karma Darshan.")

    # 3. Perform Mapping & Stemming Analysis
    mapped_records = []
    unmapped_records = []
    
    source_stats = Counter()

    for term, count in all_terms.most_common():
        stemmed = hindi_stem(term)
        
        if term in master_lookup:
            entry = master_lookup[term]
            src = entry["source"]
            source_stats[src] += 1
            mapped_records.append({
                "hindi": term,
                "root_stem": stemmed,
                "english": entry.get("english", ""),
                "source": src,
                "occurrences": count,
                "note": entry.get("note", ""),
            })
        elif stemmed in master_lookup:
            entry = master_lookup[stemmed]
            src = entry["source"]
            source_stats[f"{src} (Stemmed)"] += 1
            mapped_records.append({
                "hindi": term,
                "root_stem": stemmed,
                "english": entry.get("english", ""),
                "source": f"{src} (Stemmed)",
                "occurrences": count,
                "note": f"Stemmed to base root '{stemmed}'",
            })
        elif term in contextual_map:
            source_stats["KD-MD-Contextual"] += 1
            mapped_records.append({
                "hindi": term,
                "root_stem": stemmed,
                "english": contextual_map[term],
                "source": "KD-MD-Contextual",
                "occurrences": count,
                "note": "Extracted from inline parenthetical translation in KD-Karm-Darshan-English.md",
            })
        else:
            parts = re.split(r"[\s\-\–\—]", term)
            if len(parts) > 1:
                sub_ens = []
                for p in parts:
                    pst = hindi_stem(p)
                    if p in master_lookup:
                        sub_ens.append(master_lookup[p].get("english", p))
                    elif pst in master_lookup:
                        sub_ens.append(master_lookup[pst].get("english", pst))
                if len(sub_ens) == len(parts):
                    compound_en = " - ".join(sub_ens)
                    source_stats["Compound-Derived"] += 1
                    mapped_records.append({
                        "hindi": term,
                        "root_stem": stemmed,
                        "english": compound_en,
                        "source": "Compound-Derived",
                        "occurrences": count,
                        "note": f"Derived from compound parts: {', '.join(parts)}",
                    })
                    continue
            
            source_stats["UNMAPPED_GAP"] += 1
            unmapped_records.append({
                "hindi": term,
                "root_stem": stemmed,
                "occurrences": count,
                "status": "UNMAPPED (GAP)",
            })

    total_terms = len(all_terms)
    mapped_count = len(mapped_records)
    gap_count = len(unmapped_records)
    coverage_pct = (mapped_count / total_terms * 100) if total_terms else 0.0

    print("\n--- Mapping Coverage Summary ---")
    print(f"Total Unique Terms Analyzed: {total_terms}")
    print(f"Mapped Terms:               {mapped_count} ({coverage_pct:.1f}%)")
    for k, v in source_stats.items():
        if k != "UNMAPPED_GAP":
            print(f"  - {k}: {v}")
    print(f"Unmapped Gap Terms:         {gap_count} ({100 - coverage_pct:.1f}%)")

    # 4. Write Output Reports
    out_json_data = {
        "summary": {
            "total_terms": total_terms,
            "mapped_terms": mapped_count,
            "gap_terms": gap_count,
            "coverage_percentage": round(coverage_pct, 2),
            "sources_breakdown": dict(source_stats),
        },
        "mapped_records": mapped_records,
        "unmapped_gaps": unmapped_records,
    }
    
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(args.json_out, json.dumps(out_json_data, ensure_ascii=False, indent=2))
    print(f"\nWrote JSON mapping database to: {args.json_out.resolve()}")

    report_lines = [
        "# Karma Darshan Hindi Root Words & Terminology Mapping Audit",
        "",
        "This audit extracts all Hindi root words, technical terms, and core concepts from *Karma Darshan* (source text & working translation), maps them against current translation glossaries (`MD-Mapping.xlsx` and `KD-Glossary-Additions.md`), and identifies terminology coverage and gaps.",
        "",
        "## 1. Summary Statistics",
        "",
        f"- **Total Unique Terms Extracted:** `{total_terms}`",
        f"- **Mapped Terms:** `{mapped_count}` (`{coverage_pct:.1f}%` coverage)",
        f"- **Unmapped Gaps:** `{gap_count}` (`{100 - coverage_pct:.1f}%` missing entries)",
        "",
        "### Mapping Source Breakdown",
        "",
        "| Source | Term Count | Percentage |",
        "| :--- | :--- | :--- |",
    ]

    for src, cnt in source_stats.most_common():
        report_lines.append(f"| `{src}` | {cnt} | {(cnt/total_terms*100):.1f}% |")

    report_lines.extend([
        "",
        "## 2. Key Mapped Terms (Sample)",
        "",
        "| Hindi Term | Root Stem | English Translation Used | Source | Occurrences | Note |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ])

    for rec in mapped_records[:50]:
        report_lines.append(
            f"| {rec['hindi']} | {rec['root_stem']} | {rec['english']} | {rec['source']} | {rec['occurrences']} | {rec.get('note','')} |"
        )

    report_lines.extend([
        "",
        "## 3. High-Priority Gaps & Unmapped Terms",
        "",
        "The following terms occur in Karma Darshan texts but are currently missing explicit entries in `KD-Glossary-Additions.md` or `MD-Mapping.xlsx`:",
        "",
        "| Hindi Term | Root Stem | Occurrences in Text | Status / Recommendation |",
        "| :--- | :--- | :--- | :--- |",
    ])

    for rec in unmapped_records[:60]:
        report_lines.append(
            f"| {rec['hindi']} | {rec['root_stem']} | {rec['occurrences']} | Needs evaluation & glossary entry |"
        )

    report_lines.extend([
        "",
        "---",
        "*Report auto-generated by `Scripts/_extract_kd_hindi_terms.py`.*",
    ])

    write_text_lf(args.audit_out, "\n".join(report_lines))
    print(f"Wrote Markdown audit report to:  {args.audit_out.resolve()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
