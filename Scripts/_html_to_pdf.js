const fs = require('fs');
const path = require('path');

const { PDFDocument, StandardFonts, degrees, rgb } = require('pdf-lib');

// Chrome resolution and version pinning are shared with _html_to_png.js.
const {
  assertPinnedChrome,
  missingChromeMessage,
  puppeteerLaunchOptions,
  resolveChromeExecutable,
} = require('./_chrome');

const puppeteer = require('puppeteer');

const workspaceRoot = path.resolve(__dirname, '..');

// Used when no stamp is supplied on the command line. Must match FALLBACK_STAMP
// in Scripts/_pdf_metadata.py.
const FALLBACK_PDF_DATE = new Date(Date.UTC(2020, 0, 1, 0, 0, 0));

/**
 * Parse a PDF date string — `D:YYYYMMDDHHMMSS` with an optional offset — as
 * produced by Scripts/_pdf_metadata.py.
 *
 * The caller supplies this rather than it being scraped from the rendered page:
 * the DOM read was timing-sensitive and could come back empty on a loaded
 * runner, silently substituting a different date and making two renders of the
 * same markdown disagree. Fixed field positions mean no locale or timezone
 * ambiguity here.
 */
function parsePdfDateStamp(stamp) {
  if (!stamp) return null;
  const match = /^D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/.exec(String(stamp).trim());
  if (!match) return null;
  const [, year, month, day, hour, minute, second] = match.map(Number);
  const parsed = new Date(Date.UTC(year, month - 1, day, hour, minute, second));
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

// Draft PDFs go through pdf-lib for the watermark, which rewrites the info dict
// into a compressed object stream where Python's equal-length byte patch cannot
// reach. Pinning the dates here keeps Draft output reproducible without adding a
// second rewrite. Released PDFs never enter this function and are pinned by
// Scripts/_pdf_metadata.py instead.
async function addPageWatermark(pdfPath, label, dateStamp) {
  const pdfBytes = fs.readFileSync(pdfPath);
  const pdfDoc = await PDFDocument.load(pdfBytes);
  const stamp = parsePdfDateStamp(dateStamp) ?? FALLBACK_PDF_DATE;
  pdfDoc.setCreationDate(stamp);
  pdfDoc.setModificationDate(stamp);
  const font = await pdfDoc.embedFont(StandardFonts.HelveticaBold);
  const text = label.toUpperCase();
  const fontSize = 108;

  for (const page of pdfDoc.getPages()) {
    const { width, height } = page.getSize();
    const textWidth = font.widthOfTextAtSize(text, fontSize);
    const textHeight = font.heightAtSize(fontSize);
    page.drawText(text, {
      x: width / 2 - textWidth / 2,
      y: height / 2 - textHeight / 2,
      size: fontSize,
      font,
      color: rgb(0.75, 0.12, 0.12),
      opacity: 0.1,
      rotate: degrees(-45),
    });
  }

  fs.writeFileSync(pdfPath, await pdfDoc.save());
}

// Chrome numbers tagged-PDF structure elements from a counter that is not reset
// per document, so the same markdown rendered twice can produce IDs offset by a
// few — node00000166 in one run, node00000167 in the next. Nothing about the
// document changes, but every byte of every ID does, and for a Draft that
// difference then lands inside a pdf-lib compressed stream where the equal-length
// patching in Scripts/_pdf_metadata.py cannot reach it. That was the intermittent
// divergence _verify_pdf_reproducible.py kept reporting.
//
// Renumbering to a dense 1..N sequence makes the output depend only on the
// document. Three details keep it safe:
//   * every ID is rewritten, not just the /ID entries — /Headers on table cells
//     reference other cells' IDs, and /IDTree indexes them;
//   * the map preserves numeric order, so the /IDTree name tree stays sorted,
//     which PDF requires of a name tree;
//   * the replacement is the same 8-digit width, so no byte offset moves and the
//     xref table stays valid. Same constraint the date pinning works under.
//
// Disabling tagging would also make the output deterministic, and would throw
// away the structure tree that makes these tables navigable. Not a trade worth
// making for a byte comparison.
const STRUCT_ELEMENT_ID = /node(\d{8})/g;

function canonicaliseStructElementIds(pdfPath) {
  // latin1 round-trips arbitrary bytes, so the PDF survives the string pass.
  const text = fs.readFileSync(pdfPath).toString('latin1');
  const seen = new Set();
  for (const match of text.matchAll(STRUCT_ELEMENT_ID)) {
    seen.add(Number(match[1]));
  }
  if (seen.size === 0) {
    return;
  }
  const canonical = new Map();
  [...seen].sort((a, b) => a - b).forEach((original, index) => {
    canonical.set(original, index + 1);
  });
  const rewritten = text.replace(STRUCT_ELEMENT_ID, (whole, digits) => {
    const mapped = canonical.get(Number(digits));
    return mapped === undefined ? whole : 'node' + String(mapped).padStart(8, '0');
  });
  if (rewritten.length !== text.length) {
    throw new Error(
      'Structure element renumbering changed the file length, which would ' +
        'invalidate the xref table. Aborting rather than writing a corrupt PDF.'
    );
  }
  fs.writeFileSync(pdfPath, Buffer.from(rewritten, 'latin1'));
}

async function renderMermaidDiagrams(page) {
  const hasMermaid = await page.evaluate(
    () => document.querySelectorAll('.mermaid').length > 0
  );
  if (!hasMermaid) {
    return;
  }

  const mermaidPath = path.join(__dirname, 'node_modules', 'mermaid', 'dist', 'mermaid.min.js');
  if (!fs.existsSync(mermaidPath)) {
    console.error(
      'Mermaid diagrams found in HTML but mermaid is not installed.\n' +
        'Run once from the repo root:\n' +
        '  cd Scripts; npm install'
    );
    process.exit(1);
  }

  const mermaidScript = fs.readFileSync(mermaidPath, 'utf8');
  await page.addScriptTag({ content: mermaidScript });

  await page.evaluate(async () => {
    window.mermaid.initialize({
      startOnLoad: false,
      theme: 'neutral',
      securityLevel: 'loose',
      flowchart: { htmlLabels: true, useMaxWidth: true },
    });
    await window.mermaid.run({ querySelector: '.mermaid' });
  });

  await page.waitForFunction(
    () => {
      const blocks = document.querySelectorAll('.mermaid');
      if (blocks.length === 0) {
        return true;
      }
      return Array.from(blocks).every((el) => el.querySelector('svg'));
    },
    { timeout: 30000 }
  );
}

const args = process.argv.slice(2);
// Relative input paths resolve against the current working directory; the
// default points at the workspace's Studies folder.
const inputPath = args[0]
  ? path.resolve(process.cwd(), args[0])
  : path.join(workspaceRoot, 'Studies', 'How-To-Form-Self-Sustaining-Organizations.html');
const watermarkLabel = args[1] ?? '';
const outputPath = args[2]
  ? path.resolve(process.cwd(), args[2])
  : inputPath.replace(/\.html$/, '.pdf');
// Optional pinned PDF date (`D:YYYYMMDDHHMMSS+00'00'`), supplied by
// _study_catalog.regenerate_pdf via Scripts/_pdf_metadata.py.
const pdfDateStamp = args[3] ?? '';

/** Working English translations under References/ — not Studies/ catalog PDFs. */
function isTranslationDocument(filePath) {
  const normalized = filePath.replace(/\\/g, '/').toLowerCase();
  const base = path.basename(normalized);
  return (
    base === 'kd-karm-darshan-english.html' ||
    normalized.includes('/kd-karm-darshan-english/')
  );
}

function buildFooterTemplate(editedOnDate) {
  const datePart = editedOnDate
    ? '<span>Edited on: ' + editedOnDate + '</span>'
    : '';
  return (
    '<div style="box-sizing:border-box;width:100%;font-size:9pt;font-family:Georgia,serif;color:#666;padding:0 2cm;display:flex;justify-content:space-between;align-items:center;">' +
    '<span>AnalyticMadhyasthDarshan.org</span>' +
    datePart +
    '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>' +
    '</div>'
  );
}

(async () => {
  const executablePath = resolveChromeExecutable();
  if (!executablePath) {
    console.error(missingChromeMessage());
    process.exit(1);
  }

  const browser = await puppeteer.launch(puppeteerLaunchOptions(executablePath));
  // Pagination depends on Chrome's hyphenation dictionary, so a drifting
  // renderer would repaginate every study without changing a word. Fail before
  // anything is written.
  await assertPinnedChrome(browser);
  const page = await browser.newPage();

  await page.goto('file:///' + inputPath.replace(/\\/g, '/'), { waitUntil: 'load' });

  await renderMermaidDiagrams(page);

  // Only translation documents print the date in their footer, so only they need
  // it read from the page. The PDF's metadata date no longer comes from here.
  let editedOnDate = '';
  if (isTranslationDocument(inputPath)) {
    editedOnDate = await page.evaluate(() => {
      const bodyText = document.body.innerText || '';
      const match = bodyText.match(/\*\*Edited on:\*\*\s*([^\n\r]+)/i) ||
                    bodyText.match(/Edited on:\s*([^\n\r]+)/i);
      return match && match[1] ? match[1].trim() : '';
    });
  }

  await page.pdf({
    path: outputPath,
    format: 'A4',
    margin: { top: '2.2cm', bottom: '2.2cm', left: '2cm', right: '2cm' },
    printBackground: true,
    displayHeaderFooter: true,
    outline: true,
    headerTemplate: '<span></span>',
    footerTemplate: buildFooterTemplate(editedOnDate),
  });

  await browser.close();

  canonicaliseStructElementIds(outputPath);

  if (watermarkLabel) {
    await addPageWatermark(outputPath, watermarkLabel, pdfDateStamp);
  }

  console.log('PDF written to:', outputPath);
})();
