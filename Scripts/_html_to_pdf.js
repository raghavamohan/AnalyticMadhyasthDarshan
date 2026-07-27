const fs = require('fs');
const os = require('os');
const path = require('path');

const { PDFDocument, StandardFonts, degrees, rgb } = require('pdf-lib');

// Cursor's agent sandbox sets PUPPETEER_CACHE_DIR to a temp folder that is wiped
// between sessions, which makes Chrome look "missing" on every agent run. Use the
// normal per-user cache unless the caller set an explicit executable path.
const persistentPuppeteerCache = path.join(os.homedir(), '.cache', 'puppeteer');
const cacheDir = process.env.PUPPETEER_CACHE_DIR ?? '';
if (
  !process.env.PUPPETEER_EXECUTABLE_PATH &&
  (!cacheDir || cacheDir.includes('cursor-sandbox-cache'))
) {
  process.env.PUPPETEER_CACHE_DIR = persistentPuppeteerCache;
}

const puppeteer = require('puppeteer');

const workspaceRoot = path.resolve(__dirname, '..');

const SYSTEM_CHROME_CANDIDATES = [
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium-browser',
  '/usr/bin/chromium',
];

function resolveChromeExecutable() {
  if (process.env.PUPPETEER_EXECUTABLE_PATH) {
    return process.env.PUPPETEER_EXECUTABLE_PATH;
  }

  let managed = '';
  try {
    managed = puppeteer.executablePath();
  } catch (_) {
    managed = '';
  }
  if (managed && fs.existsSync(managed)) {
    return managed;
  }

  for (const candidate of SYSTEM_CHROME_CANDIDATES) {
    if (candidate && fs.existsSync(candidate)) {
      return candidate;
    }
  }

  return '';
}

// GitHub Actions and other Linux CI images often block Chrome's setuid sandbox
// (AppArmor / user namespaces). These flags are standard for headless CI.
const LINUX_CI_CHROME_ARGS = [
  '--no-sandbox',
  '--disable-setuid-sandbox',
  '--disable-dev-shm-usage',
];

function puppeteerLaunchOptions(executablePath) {
  const options = {
    headless: 'new',
    executablePath,
  };
  if (process.platform === 'linux') {
    options.args = LINUX_CI_CHROME_ARGS;
  }
  return options;
}

const MONTHS = {
  january: 0, february: 1, march: 2, april: 3, may: 4, june: 5,
  july: 6, august: 7, september: 8, october: 9, november: 10, december: 11,
};

// Used when a document has no parseable `**Edited on:**` line. Must match
// FALLBACK_STAMP in Scripts/_pdf_metadata.py.
const FALLBACK_PDF_DATE = new Date(Date.UTC(2020, 0, 1, 0, 0, 0));

/**
 * Parse `**Edited on:**` text such as "June 30, 2026, 11:33 AM IST".
 *
 * The digits are treated as UTC deliberately: reading them as local time would
 * make the bytes depend on the build machine's timezone, so a developer in IST
 * and a CI runner in UTC would disagree on the same markdown. Returns null when
 * the text does not match.
 */
function parseEditedOn(text) {
  if (!text) return null;
  const match = /^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4}),\s*(\d{1,2}):(\d{2})\s*([AaPp])\.?[Mm]/
    .exec(String(text).trim());
  if (!match) return null;
  const month = MONTHS[match[1].toLowerCase()];
  if (month === undefined) return null;
  let hour = Number(match[4]) % 12;
  if (match[6].toLowerCase() === 'p') hour += 12;
  const parsed = new Date(Date.UTC(
    Number(match[3]), month, Number(match[2]), hour, Number(match[5]), 0));
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

// Draft PDFs go through pdf-lib for the watermark, which rewrites the info dict
// into a compressed object stream where Python's equal-length byte patch cannot
// reach. Pinning the dates here keeps Draft output reproducible without adding a
// second rewrite. Released PDFs never enter this function and are pinned by
// Scripts/_pdf_metadata.py instead.
async function addPageWatermark(pdfPath, label, editedOnText) {
  const pdfBytes = fs.readFileSync(pdfPath);
  const pdfDoc = await PDFDocument.load(pdfBytes);
  const stamp = parseEditedOn(editedOnText) ?? FALLBACK_PDF_DATE;
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
    '<div style="width:100%;font-size:9pt;font-family:Georgia,serif;color:#666;padding:0 2cm;display:flex;justify-content:space-between;align-items:center;">' +
    '<span>AnalyticMadhyasthDarshan.org</span>' +
    datePart +
    '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>' +
    '</div>'
  );
}

(async () => {
  const executablePath = resolveChromeExecutable();
  if (!executablePath) {
    console.error(
      'Chrome not found for PDF generation.\n' +
        'Run once from the repo root:\n' +
        '  cd Scripts; npx puppeteer browsers install chrome\n' +
        'Or set PUPPETEER_EXECUTABLE_PATH to your local Chrome/Chromium binary.'
    );
    process.exit(1);
  }

  const browser = await puppeteer.launch(puppeteerLaunchOptions(executablePath));
  const page = await browser.newPage();

  await page.goto('file:///' + inputPath.replace(/\\/g, '/'), { waitUntil: 'load' });

  await renderMermaidDiagrams(page);

  // Read `**Edited on:**` for every document: Draft PDFs use it to pin their
  // metadata dates. It is only *printed* in the footer for translation
  // documents, which is the pre-existing behaviour.
  const editedOnText = await page.evaluate(() => {
    const bodyText = document.body.innerText || '';
    const match = bodyText.match(/\*\*Edited on:\*\*\s*([^\n\r]+)/i) ||
                  bodyText.match(/Edited on:\s*([^\n\r]+)/i);
    return match && match[1] ? match[1].trim() : '';
  });
  const editedOnDate = isTranslationDocument(inputPath) ? editedOnText : '';

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

  if (watermarkLabel) {
    await addPageWatermark(outputPath, watermarkLabel, editedOnText);
  }

  console.log('PDF written to:', outputPath);
})();
