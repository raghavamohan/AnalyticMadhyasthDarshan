#!/usr/bin/env python3
"""Read, validate, and optionally export Phase 4 Excel review workbooks.

The reviewer edits ``*-phase4-review.xlsx``. This script reads the workbook
directly without modifying it, validates the review gates, and can refresh the
legacy UTF-8-with-BOM TSV interchange files for downstream text tooling.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


DEFAULT_WORK = Path(r"E:\MD-Transcription")
PILOT_IDS = (
    "KTeH3rM2qK8",
    "OIkSW7QYry4",
    "vuTOjdF6a3k",
    "a1ARueeihmA",
    "pk3UxjDkhiE",
)
ALLOWED_REVIEW = {"UNREVIEWED", "R", "P", "U"}
SEGMENT_FIELDS = (
    "segment_id", "start", "end", "review", "raw_asr", "candidate_hindi",
    "reviewed_hindi", "english", "flags", "evidence", "reviewer", "reviewed_on",
)
CORRECTION_FIELDS = (
    "segment_id", "start", "end", "original_asr", "corrected_hindi", "reason",
    "supporting_evidence", "reviewer", "reviewed_on",
)
SEGMENT_HEADERS = {
    "Segment ID": "segment_id", "Start": "start", "End": "end", "Review": "review",
    "Raw ASR": "raw_asr", "Layer-A Candidate Hindi": "candidate_hindi",
    "Reviewed Hindi": "reviewed_hindi", "English": "english", "Flags": "flags",
    "Evidence": "evidence", "Reviewer": "reviewer", "Reviewed On": "reviewed_on",
}
CORRECTION_HEADERS = {
    "Segment ID": "segment_id", "Start": "start", "End": "end",
    "Original ASR": "original_asr", "Corrected Hindi": "corrected_hindi",
    "Reason": "reason", "Supporting Evidence": "supporting_evidence",
    "Reviewer": "reviewer", "Reviewed On": "reviewed_on",
}
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
DOC_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference)
    if not letters:
        raise ValueError(f"invalid cell reference: {reference}")
    value = 0
    for char in letters.group(0):
        value = value * 26 + ord(char) - 64
    return value - 1


def xml_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(node.text or "" for node in element.iter() if node.tag.endswith("}t"))


def workbook_rows(path: Path, sheet_name: str) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [xml_text(item) for item in root.findall("m:si", NS)]

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall("r:Relationship", REL_NS)
        }
        target = None
        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            if sheet.attrib.get("name") == sheet_name:
                relationship = sheet.attrib.get(f"{{{DOC_REL}}}id")
                target = targets.get(relationship or "")
                break
        if not target:
            raise ValueError(f"{path.name}: worksheet {sheet_name!r} is missing")
        target = target.replace("\\", "/").lstrip("/")
        sheet_path = target if target.startswith("xl/") else f"xl/{target}"
        root = ET.fromstring(archive.read(sheet_path))
        rows: list[list[str]] = []
        for row in root.findall("m:sheetData/m:row", NS):
            values: dict[int, str] = {}
            for cell in row.findall("m:c", NS):
                index = column_index(cell.attrib.get("r", "A1"))
                kind = cell.attrib.get("t", "")
                if kind == "inlineStr":
                    value = xml_text(cell.find("m:is", NS))
                else:
                    node = cell.find("m:v", NS)
                    raw = node.text if node is not None and node.text is not None else ""
                    if kind == "s" and raw:
                        value = shared[int(raw)]
                    elif kind == "b":
                        value = "TRUE" if raw == "1" else "FALSE"
                    else:
                        value = raw
                values[index] = value
            if values:
                width = max(values) + 1
                rows.append([values.get(index, "") for index in range(width)])
        return rows


def table_records(rows: list[list[str]], mapping: dict[str, str]) -> list[dict[str, str]]:
    if not rows:
        return []
    headers = rows[0]
    columns = {index: mapping[header] for index, header in enumerate(headers) if header in mapping}
    missing = set(mapping.values()) - set(columns.values())
    if missing:
        raise ValueError(f"workbook table is missing fields: {sorted(missing)}")
    records: list[dict[str, str]] = []
    for row in rows[1:]:
        record = {field: (row[index] if index < len(row) else "") for index, field in columns.items()}
        if not any(value.strip() for value in record.values()):
            continue
        records.append(record)
    return records


def find_session(work: Path, video_id: str) -> Path:
    sessions = work / "Nagraj-Recorded-Sessions"
    matches = [path for path in sessions.iterdir()
               if path.is_dir() and path.name.endswith("--" + video_id)]
    if len(matches) != 1:
        raise ValueError(f"{video_id}: expected one session folder, found {len(matches)}")
    return matches[0]


def find_workbook(work: Path, session: Path) -> Path:
    local = session / f"{session.name}-phase4-review.xlsx"
    staged = work / "xlsx-review" / local.name
    if local.is_file():
        return local
    if staged.is_file():
        return staged
    raise FileNotFoundError(f"missing review workbook: {local}")


def write_tsv(path: Path, fields: tuple[str, ...], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def verify(work: Path, video_id: str, sync_tsv: bool) -> tuple[list[str], dict[str, object]]:
    session = find_session(work, video_id)
    workbook = find_workbook(work, session)
    provenance_path = session / f"{session.name}-phase4-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    segments = table_records(workbook_rows(workbook, "Segments"), SEGMENT_HEADERS)
    corrections = table_records(workbook_rows(workbook, "Corrections"), CORRECTION_HEADERS)
    # Drop the deliberately blank starter row from Corrections.
    corrections = [row for row in corrections if any(row.values())]
    problems: list[str] = []

    expected = int(provenance.get("native_segments", 0))
    if len(segments) != expected:
        problems.append(f"segment count {len(segments)} does not match provenance {expected}")
    unreviewed = 0
    for row in segments:
        segment_id = row.get("segment_id", "(unknown)")
        review = row.get("review", "").strip().upper()
        if review not in ALLOWED_REVIEW:
            problems.append(f"{segment_id}: invalid Review {review!r}")
            continue
        if review == "UNREVIEWED":
            unreviewed += 1
            continue
        if not row.get("reviewed_hindi", "").strip():
            problems.append(f"{segment_id}: Reviewed Hindi is required")
        if review in {"P", "U"} and not row.get("evidence", "").strip():
            problems.append(f"{segment_id}: {review} requires Evidence")
        if int(provenance.get("target_level", 2)) == 3 and not row.get("english", "").strip():
            problems.append(f"{segment_id}: Level 3 English is required")
        if not row.get("reviewer", "").strip():
            problems.append(f"{segment_id}: Reviewer is required")
        if not row.get("reviewed_on", "").strip():
            problems.append(f"{segment_id}: Reviewed On is required")
    if unreviewed:
        problems.append(f"{unreviewed} segments remain UNREVIEWED")

    for item in provenance.get("decoder_evidence", {}).values():
        evidence = session / item["file"]
        if not evidence.is_file() or sha256(evidence) != item["sha256"]:
            problems.append(f"decoder evidence hash mismatch: {item['file']}")
    audio = work / "audio" / provenance["audio"]["file"]
    if not audio.is_file() or sha256(audio) != provenance["audio"]["sha256"]:
        problems.append("audio hash mismatch")

    if sync_tsv:
        segments_tsv = session / f"{session.name}-phase4-segments.tsv"
        corrections_tsv = session / f"{session.name}-phase4-corrections.tsv"
        write_tsv(segments_tsv, SEGMENT_FIELDS, segments)
        write_tsv(corrections_tsv, CORRECTION_FIELDS, corrections)

    return problems, {
        "video_id": video_id,
        "workbook": str(workbook),
        "segments": len(segments),
        "unreviewed": unreviewed,
        "corrections": len(corrections),
        "target_level": provenance.get("target_level"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--only", nargs="*", choices=PILOT_IDS)
    parser.add_argument("--sync-tsv", action="store_true",
                        help="refresh legacy TSVs from the Excel source using UTF-8 BOM")
    parser.add_argument("--check", action="store_true",
                        help="exit non-zero while any completion gate is pending")
    args = parser.parse_args()

    work = args.work.resolve()
    ids = args.only or list(PILOT_IDS)
    any_problems = False
    for video_id in ids:
        try:
            problems, summary = verify(work, video_id, args.sync_tsv)
        except (FileNotFoundError, ValueError, KeyError, zipfile.BadZipFile,
                ET.ParseError, json.JSONDecodeError) as error:
            problems = [str(error)]
            summary = {"video_id": video_id, "segments": 0, "unreviewed": 0,
                       "corrections": 0, "target_level": "?"}
        gate = "PASS" if not problems else "PENDING"
        print(f"{video_id}: Level {summary['target_level']}; {summary['segments']} segments; "
              f"unreviewed={summary['unreviewed']}; corrections={summary['corrections']}; gate={gate}")
        for problem in problems[:8]:
            print(f"  - {problem}")
        if len(problems) > 8:
            print(f"  - ... {len(problems) - 8} more")
        any_problems = any_problems or bool(problems)
    if args.check and any_problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
