#!/usr/bin/env node
/** Build Excel-native Phase 4 transcription review workbooks.
 *
 * Run this script from a temporary directory whose node_modules is a junction
 * to the Codex workspace dependency runtime. The permanent Python pipeline
 * treats the generated .xlsx workbook as the reviewer-facing source of truth.
 */
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const PILOT_IDS = [
  "KTeH3rM2qK8",
  "OIkSW7QYry4",
  "vuTOjdF6a3k",
  "a1ARueeihmA",
  "pk3UxjDkhiE",
];

function parseArgs(argv) {
  const args = { work: "E:\\MD-Transcription", outputDir: null, previewDir: null, force: false, only: [] };
  for (let i = 2; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === "--work") args.work = argv[++i];
    else if (token === "--output-dir") args.outputDir = argv[++i];
    else if (token === "--preview-dir") args.previewDir = argv[++i];
    else if (token === "--force") args.force = true;
    else if (token === "--only") {
      while (i + 1 < argv.length && !argv[i + 1].startsWith("--")) args.only.push(argv[++i]);
    } else throw new Error(`unknown argument: ${token}`);
  }
  return args;
}

function parseTsv(text) {
  const lines = text.replace(/^\uFEFF/, "").split(/\r?\n/).filter((line) => line.length > 0);
  if (!lines.length) return [];
  const headers = lines[0].split("\t");
  return lines.slice(1).map((line) => {
    const values = line.split("\t");
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
  });
}

async function readTextShared(file) {
  // fs.readFile works for ordinary Excel sharing mode. If Excel has opened the
  // TSV exclusively, the aggregate queue remains a safe migration fallback.
  return fs.readFile(file, "utf8");
}

async function exists(file) {
  try { await fs.access(file); return true; } catch { return false; }
}

async function findSession(sessionsDir, videoId) {
  const entries = await fs.readdir(sessionsDir, { withFileTypes: true });
  const matches = entries.filter((entry) => entry.isDirectory() && entry.name.endsWith(`--${videoId}`));
  if (matches.length !== 1) throw new Error(`${videoId}: expected one session folder, found ${matches.length}`);
  return path.join(sessionsDir, matches[0].name);
}

function safeSheetName(value) {
  return value.replace(/[\\/?*\[\]:]/g, "-").slice(0, 31);
}

function styleTitle(range) {
  range.format = {
    fill: "#17365D",
    font: { name: "Nirmala UI", size: 18, bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
    wrapText: true,
  };
  range.format.rowHeight = 34;
}

function styleSection(range) {
  range.format = {
    fill: "#D9EAF7",
    font: { name: "Nirmala UI", size: 12, bold: true, color: "#17365D" },
    verticalAlignment: "center",
  };
  range.format.rowHeight = 24;
}

function normalizeRows(rows) {
  return rows.map((row) => ({
    segment_id: row.segment_id ?? "",
    start: row.start ?? "",
    end: row.end ?? "",
    review: row.review || "UNREVIEWED",
    raw_asr: row.raw_asr ?? "",
    candidate_hindi: row.candidate_hindi ?? "",
    reviewed_hindi: row.reviewed_hindi ?? "",
    english: row.english ?? "",
    flags: row.flags ?? "",
    evidence: row.evidence ?? "",
    reviewer: row.reviewer ?? "",
    reviewed_on: row.reviewed_on ?? "",
  }));
}

async function loadRows(sessionDir, stem, videoId, aggregateRows) {
  const tsv = path.join(sessionDir, `${stem}-phase4-segments.tsv`);
  try {
    const rows = parseTsv(await readTextShared(tsv));
    if (rows.length) return normalizeRows(rows);
  } catch (error) {
    if (!["EBUSY", "EACCES", "EPERM"].includes(error.code)) throw error;
  }
  const fallback = aggregateRows.filter((row) => row.video_id === videoId);
  if (!fallback.length) throw new Error(`${videoId}: cannot read segment TSV and aggregate fallback is empty`);
  return normalizeRows(fallback);
}

async function loadCorrections(sessionDir, stem) {
  const file = path.join(sessionDir, `${stem}-phase4-corrections.tsv`);
  try { return parseTsv(await readTextShared(file)); } catch { return []; }
}

function buildInstructions(sheet, meta, provenance, segmentCount, audioPath) {
  sheet.showGridLines = false;
  sheet.mergeCells("A1:H1");
  sheet.getRange("A1").values = [[`Phase 4 review — ${meta.title}`]];
  styleTitle(sheet.getRange("A1:H1"));
  sheet.getRange("A3:B9").values = [
    ["Video ID", meta.id],
    ["Duration", meta.dur],
    ["Target", `Level ${provenance.target_level}`],
    ["Segments", segmentCount],
    ["YouTube", provenance.source_url],
    ["Local audio", audioPath],
    ["Audio SHA-256", provenance.audio?.sha256 ?? ""],
  ];
  sheet.getRange("A3:A9").format = { fill: "#EAF2F8", font: { name: "Nirmala UI", bold: true, color: "#17365D" } };
  sheet.getRange("B3:B9").format = { font: { name: "Nirmala UI", color: "#172033" }, wrapText: true };
  sheet.mergeCells("A11:H11");
  sheet.getRange("A11").values = [["How to review"]];
  styleSection(sheet.getRange("A11:H11"));
  const rules = [
    "1. Play each interval shown in Start–End and compare Raw ASR with the Layer-A candidate.",
    "2. Enter exactly what is heard in Reviewed Hindi; use minimal punctuation.",
    "3. Set Review to R (clear), P (limited ambiguity), or U (unresolved).",
    "4. For P or U, explain the uncertainty in Evidence. Record every wording change on Corrections.",
    "5. Repair U+FFFD only from audio. Delete boilerplate only after checking adjacent genuine speech.",
    "6. For Level 3, enter English only after the Hindi is locked. Do not edit Raw ASR or Candidate Hindi.",
    "7. Save this workbook normally. The pipeline reads this .xlsx directly; TSV files are legacy interchange only.",
  ];
  sheet.getRange(`A12:H${11 + rules.length}`).merge(true);
  sheet.getRange(`A12:A${11 + rules.length}`).values = rules.map((rule) => [rule]);
  sheet.getRange(`A12:H${11 + rules.length}`).format = {
    font: { name: "Nirmala UI", size: 11, color: "#172033" },
    wrapText: true,
    verticalAlignment: "top",
  };
  sheet.getRange(`A12:H${11 + rules.length}`).format.rowHeight = 28;
  const summaryRow = 20;
  sheet.mergeCells(`A${summaryRow}:H${summaryRow}`);
  sheet.getRange(`A${summaryRow}`).values = [["Review progress"]];
  styleSection(sheet.getRange(`A${summaryRow}:H${summaryRow}`));
  sheet.getRange(`A${summaryRow + 1}:B${summaryRow + 5}`).values = [
    ["Unreviewed", null], ["Reliable [R]", null], ["Probable [P]", null], ["Uncertain [U]", null], ["Completed", null],
  ];
  const end = segmentCount + 1;
  sheet.getRange(`B${summaryRow + 1}:B${summaryRow + 5}`).formulas = [
    [`=COUNTIF('Segments'!$D$2:$D$${end},"UNREVIEWED")`],
    [`=COUNTIF('Segments'!$D$2:$D$${end},"R")`],
    [`=COUNTIF('Segments'!$D$2:$D$${end},"P")`],
    [`=COUNTIF('Segments'!$D$2:$D$${end},"U")`],
    [`=COUNTIF('Segments'!$D$2:$D$${end},"<>UNREVIEWED")`],
  ];
  sheet.getRange(`A${summaryRow + 1}:A${summaryRow + 5}`).format.font = { name: "Nirmala UI", bold: true, color: "#17365D" };
  sheet.getRange(`B${summaryRow + 1}:B${summaryRow + 5}`).format = { fill: "#FFF2CC", font: { name: "Nirmala UI", bold: true, color: "#7F6000" }, numberFormat: "0" };
  sheet.getRange("A1:H30").format.borders = { preset: "inside", style: "thin", color: "#D9E2F3" };
  sheet.getRange("A1:A30").format.columnWidth = 22;
  sheet.getRange("B1:B30").format.columnWidth = 72;
  sheet.getRange("C1:H30").format.columnWidth = 12;
  sheet.freezePanes.freezeRows(1);
  return sheet;
}

function buildSegments(sheet, rows, videoId) {
  sheet.showGridLines = false;
  const headers = ["Segment ID", "Start", "End", "Review", "Raw ASR", "Layer-A Candidate Hindi", "Reviewed Hindi", "English", "Flags", "Evidence", "Reviewer", "Reviewed On"];
  const matrix = [headers, ...rows.map((row) => [
    row.segment_id, row.start, row.end, row.review, row.raw_asr, row.candidate_hindi,
    row.reviewed_hindi, row.english, row.flags, row.evidence, row.reviewer, row.reviewed_on,
  ])];
  const endRow = matrix.length;
  sheet.getRange(`A1:L${endRow}`).values = matrix;
  sheet.getRange("A1:L1").format = {
    fill: "#17365D",
    font: { name: "Nirmala UI", bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "medium", color: "#17365D" },
  };
  sheet.getRange("A1:L1").format.rowHeight = 32;
  sheet.getRange(`A2:L${endRow}`).format = {
    font: { name: "Nirmala UI", size: 11, color: "#172033" },
    verticalAlignment: "top",
    wrapText: true,
    borders: { insideHorizontal: { style: "thin", color: "#D9E2F3" } },
  };
  sheet.getRange(`D2:D${endRow}`).format.fill = "#FFF2CC";
  sheet.getRange(`G2:H${endRow}`).format.fill = "#FFF9E6";
  sheet.getRange(`J2:L${endRow}`).format.fill = "#FFF9E6";
  sheet.getRange(`E2:F${endRow}`).format.fill = "#F2F6FA";
  sheet.getRange(`D2:D${endRow}`).dataValidation = { rule: { type: "list", values: ["UNREVIEWED", "R", "P", "U"] } };
  sheet.getRange(`D2:D${endRow}`).conditionalFormats.add("containsText", { text: "UNREVIEWED", format: { fill: "#FFF2CC", font: { color: "#7F6000", bold: true } } });
  sheet.getRange(`D2:D${endRow}`).conditionalFormats.add("cellIs", { operator: "equal", formula: '"R"', format: { fill: "#E2F0D9", font: { color: "#375623", bold: true } } });
  sheet.getRange(`D2:D${endRow}`).conditionalFormats.add("cellIs", { operator: "equal", formula: '"P"', format: { fill: "#DDEBF7", font: { color: "#1F4E78", bold: true } } });
  sheet.getRange(`D2:D${endRow}`).conditionalFormats.add("cellIs", { operator: "equal", formula: '"U"', format: { fill: "#FCE4D6", font: { color: "#C00000", bold: true } } });
  sheet.getRange(`A2:D${endRow}`).format.horizontalAlignment = "center";
  sheet.getRange(`A2:L${endRow}`).format.rowHeight = 72;
  const widths = [13, 15, 15, 14, 46, 46, 46, 42, 34, 36, 18, 16];
  widths.forEach((width, index) => { sheet.getRangeByIndexes(0, index, endRow, 1).format.columnWidth = width; });
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(4);
  const table = sheet.tables.add(`A1:L${endRow}`, true, `Segments_${videoId.replace(/[^A-Za-z0-9]/g, "")}`);
  table.style = "TableStyleMedium2";
  table.showBandedRows = true;
  table.showFilterButton = true;
  return sheet;
}

function buildCorrections(sheet, corrections, videoId) {
  sheet.showGridLines = false;
  const headers = ["Segment ID", "Start", "End", "Original ASR", "Corrected Hindi", "Reason", "Supporting Evidence", "Reviewer", "Reviewed On"];
  const data = corrections.length ? corrections.map((row) => [
    row.segment_id ?? "", row.start ?? "", row.end ?? "", row.original_asr ?? "",
    row.corrected_hindi ?? "", row.reason ?? "", row.supporting_evidence ?? "",
    row.reviewer ?? "", row.reviewed_on ?? "",
  ]) : [["", "", "", "", "", "", "", "", ""]];
  const matrix = [headers, ...data];
  const endRow = matrix.length;
  sheet.getRange(`A1:I${endRow}`).values = matrix;
  sheet.getRange("A1:I1").format = { fill: "#17365D", font: { name: "Nirmala UI", bold: true, color: "#FFFFFF" }, wrapText: true };
  sheet.getRange(`A2:I${endRow}`).format = { font: { name: "Nirmala UI", size: 11 }, wrapText: true, verticalAlignment: "top", fill: "#FFF9E6" };
  sheet.getRange(`A2:I${endRow}`).format.rowHeight = 54;
  const widths = [13, 15, 15, 42, 42, 28, 36, 18, 16];
  widths.forEach((width, index) => { sheet.getRangeByIndexes(0, index, endRow, 1).format.columnWidth = width; });
  sheet.freezePanes.freezeRows(1);
  const table = sheet.tables.add(`A1:I${endRow}`, true, `Corrections_${videoId.replace(/[^A-Za-z0-9]/g, "")}`);
  table.style = "TableStyleMedium2";
  table.showFilterButton = true;
  return sheet;
}

function flattenObject(value, prefix = "") {
  const rows = [];
  if (value === null || typeof value !== "object") return [[prefix, value ?? ""]];
  if (Array.isArray(value)) return [[prefix, value.join("; ")]];
  for (const [key, child] of Object.entries(value)) {
    const name = prefix ? `${prefix}.${key}` : key;
    if (child !== null && typeof child === "object" && !Array.isArray(child)) rows.push(...flattenObject(child, name));
    else rows.push([name, Array.isArray(child) ? child.join("; ") : child ?? ""]);
  }
  return rows;
}

function buildProvenance(sheet, provenance) {
  sheet.showGridLines = false;
  const rows = [["Field", "Value"], ...flattenObject(provenance)];
  sheet.getRange(`A1:B${rows.length}`).values = rows;
  sheet.getRange("A1:B1").format = { fill: "#17365D", font: { name: "Nirmala UI", bold: true, color: "#FFFFFF" } };
  sheet.getRange(`A2:A${rows.length}`).format = { fill: "#EAF2F8", font: { name: "Nirmala UI", bold: true, color: "#17365D" } };
  sheet.getRange(`B2:B${rows.length}`).format = { font: { name: "Nirmala UI" }, wrapText: true };
  sheet.getRange(`A1:A${rows.length}`).format.columnWidth = 42;
  sheet.getRange(`B1:B${rows.length}`).format.columnWidth = 92;
  sheet.getRange(`A1:B${rows.length}`).format.borders = { preset: "insideHorizontal", style: "thin", color: "#D9E2F3" };
  sheet.freezePanes.freezeRows(1);
  return sheet;
}

async function buildWorkbook({ meta, provenance, rows, corrections, audioPath, output, previewDir }) {
  const workbook = Workbook.create();
  // Create every cross-referenced sheet before writing formulas.
  const instructionsSheet = workbook.worksheets.add("Instructions");
  const segmentsSheet = workbook.worksheets.add("Segments");
  const correctionsSheet = workbook.worksheets.add("Corrections");
  const provenanceSheet = workbook.worksheets.add("Provenance");
  buildInstructions(instructionsSheet, meta, provenance, rows.length, audioPath);
  buildSegments(segmentsSheet, rows, meta.id);
  buildCorrections(correctionsSheet, corrections, meta.id);
  buildProvenance(provenanceSheet, provenance);

  const inspect = await workbook.inspect({ kind: "sheet,table", maxChars: 2500, tableMaxRows: 3, tableMaxCols: 5 });
  console.log(`${meta.id} inspect: ${inspect.ndjson.replace(/\s+/g, " ").slice(0, 900)}`);
  const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "formula error scan" });
  if (/"count"\s*:\s*[1-9]/.test(errors.ndjson)) throw new Error(`${meta.id}: formula error scan found matches`);

  if (previewDir) {
    await fs.mkdir(previewDir, { recursive: true });
    const ranges = { Instructions: "A1:H25", Segments: `A1:L${Math.min(rows.length + 1, 12)}`, Corrections: "A1:I5", Provenance: "A1:B18" };
    for (const [sheetName, range] of Object.entries(ranges)) {
      const preview = await workbook.render({ sheetName, range, scale: 1.2, format: "png" });
      const name = `${meta.id}-${safeSheetName(sheetName).toLowerCase()}.png`;
      await fs.writeFile(path.join(previewDir, name), new Uint8Array(await preview.arrayBuffer()));
    }
  }
  const xlsx = await SpreadsheetFile.exportXlsx(workbook);
  await xlsx.save(output);
}

async function main() {
  const args = parseArgs(process.argv);
  const work = path.resolve(args.work);
  const sessionsDir = path.join(work, "Nagraj-Recorded-Sessions");
  // The normal review location is beside each session's evidence. An explicit
  // output directory is useful only for staging and visual QA.
  const outputDir = args.outputDir ? path.resolve(args.outputDir) : null;
  if (outputDir) await fs.mkdir(outputDir, { recursive: true });
  const manifest = parseTsv(await fs.readFile(path.join(work, "manifest-phase4-pilot.tsv"), "utf8"));
  const manifestById = new Map(manifest.map((row) => [row.id, row]));
  const aggregateRows = parseTsv(await fs.readFile(path.join(work, "PHASE-4-REVIEW-QUEUE.tsv"), "utf8"));
  const ids = args.only.length ? args.only : PILOT_IDS;
  for (const videoId of ids) {
    if (!PILOT_IDS.includes(videoId)) throw new Error(`${videoId}: not in fixed Phase 4 pilot`);
    const meta = manifestById.get(videoId);
    if (!meta) throw new Error(`${videoId}: missing from pilot manifest`);
    const sessionDir = await findSession(sessionsDir, videoId);
    const stem = path.basename(sessionDir);
    const provenance = JSON.parse(await fs.readFile(path.join(sessionDir, `${stem}-phase4-provenance.json`), "utf8"));
    const rows = await loadRows(sessionDir, stem, videoId, aggregateRows);
    const corrections = await loadCorrections(sessionDir, stem);
    const output = path.join(outputDir || sessionDir, `${stem}-phase4-review.xlsx`);
    if (await exists(output) && !args.force) throw new Error(`refusing to overwrite existing workbook: ${output}`);
    const audioPath = path.join(work, "audio", provenance.audio.file);
    await buildWorkbook({ meta, provenance, rows, corrections, audioPath, output, previewDir: args.previewDir ? path.resolve(args.previewDir) : null });
    console.log(`wrote ${output}`);
  }
}

main().catch((error) => { console.error(error.stack || error.message); process.exit(1); });
