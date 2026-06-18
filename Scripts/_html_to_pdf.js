const fs = require('fs');
const os = require('os');
const path = require('path');

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

const args = process.argv.slice(2);
// Relative input paths resolve against the current working directory; the
// default points at the workspace's Studies folder.
const inputPath = args[0]
  ? path.resolve(process.cwd(), args[0])
  : path.join(workspaceRoot, 'Studies', 'How-To-Form-Self-Sustaining-Organizations.html');
const outputPath = inputPath.replace(/\.html$/, '.pdf');

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

  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath,
  });
  const page = await browser.newPage();

  await page.goto('file:///' + inputPath.replace(/\\/g, '/'), { waitUntil: 'networkidle0' });

  await page.pdf({
    path: outputPath,
    format: 'A4',
    margin: { top: '2.2cm', bottom: '2.2cm', left: '2cm', right: '2cm' },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate:
      '<div style="width:100%;font-size:9pt;font-family:Georgia,serif;color:#666;padding:0 2cm;display:flex;justify-content:space-between;align-items:center;">' +
      '<span>AnalyticMadhyasthDarshan.org</span>' +
      '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>' +
      '</div>',
  });

  await browser.close();
  console.log('PDF written to:', outputPath);
})();
