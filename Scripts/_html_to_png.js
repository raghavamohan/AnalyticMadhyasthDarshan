/**
 * Rasterise a local HTML file to PNG with headless Chrome.
 *
 * Used by _build_social_cards.py to render Open Graph share cards, so the cards
 * carry the site's own Georgia/Segoe typography instead of whatever font a
 * Pillow-based generator happens to find on the build machine.
 *
 *   node _html_to_png.js <input.html> <output.png> [width] [height]
 */
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

async function main() {
  const [inputArg, outputArg, widthArg, heightArg] = process.argv.slice(2);
  if (!inputArg || !outputArg) {
    console.error('Usage: node _html_to_png.js <input.html> <output.png> [width] [height]');
    process.exit(1);
  }
  const inputPath = path.resolve(inputArg);
  const outputPath = path.resolve(outputArg);
  if (!fs.existsSync(inputPath)) {
    console.error(`Input HTML not found: ${inputPath}`);
    process.exit(1);
  }
  const width = Number(widthArg) || 1200;
  const height = Number(heightArg) || 630;

  const executablePath = resolveChromeExecutable();
  if (!executablePath) {
    console.error(
      'Chrome not found. Run once from Scripts/: npx puppeteer browsers install chrome',
    );
    process.exit(1);
  }

  const launchOptions = { headless: 'new', executablePath };
  if (process.platform === 'linux') {
    launchOptions.args = LINUX_CI_CHROME_ARGS;
  }

  const browser = await puppeteer.launch(launchOptions);
  try {
    const page = await browser.newPage();
    // deviceScaleFactor 1 keeps the file small; 1200x630 is already the size
    // every crawler wants, so there is nothing to gain from rendering larger.
    await page.setViewport({ width, height, deviceScaleFactor: 1 });
    await page.goto(`file://${inputPath.replace(/\\/g, '/')}`, {
      waitUntil: 'load',
    });
    await page.evaluateHandle('document.fonts.ready');
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    await page.screenshot({ path: outputPath, type: 'png' });
  } finally {
    await browser.close();
  }
  console.log(`PNG written to: ${outputPath}`);
}

main().catch((err) => {
  console.error(err && err.stack ? err.stack : String(err));
  process.exit(1);
});
