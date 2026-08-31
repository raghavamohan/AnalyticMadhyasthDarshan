/**
 * Shared Chrome resolution and version pinning for the render scripts.
 *
 * Why this exists: PDF pagination depends on Chrome's hyphenation dictionary.
 * The committed PDFs were built by an older Chrome that hyphenated differently
 * ("philoso-phy" where the current one sets "philosophy"), which changed line
 * breaking and grew one study from 21 pages to 23 -- with identical text. The
 * content was never wrong, but the output was not reproducible, because the
 * renderer could silently be any Chrome on the machine.
 *
 * Two changes close that: puppeteer is pinned to an exact version in
 * package.json (so the Chrome it downloads is fixed), and the build it should
 * produce is recorded there as pdfRender.chrome and asserted at launch. A
 * mismatch now fails loudly instead of quietly repaginating every PDF.
 */
const fs = require('fs');
const os = require('os');
const path = require('path');

// Cursor's agent sandbox sets PUPPETEER_CACHE_DIR to a temp folder that is wiped
// between sessions, which makes Chrome look "missing" on every agent run. Use the
// normal per-user cache unless the caller set an explicit executable path.
function normaliseCacheDir() {
  const persistent = path.join(os.homedir(), '.cache', 'puppeteer');
  const cacheDir = process.env.PUPPETEER_CACHE_DIR ?? '';
  if (
    !process.env.PUPPETEER_EXECUTABLE_PATH &&
    (!cacheDir || cacheDir.includes('cursor-sandbox-cache'))
  ) {
    process.env.PUPPETEER_CACHE_DIR = persistent;
  }
}
normaliseCacheDir();

const puppeteer = require('puppeteer');

const SYSTEM_CHROME_CANDIDATES = [
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
  'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium-browser',
  '/usr/bin/chromium',
];

// GitHub Actions and other Linux CI images often block Chrome's setuid sandbox
// (AppArmor / user namespaces). These flags are standard for headless CI.
const LINUX_CI_CHROME_ARGS = [
  '--no-sandbox',
  '--disable-setuid-sandbox',
  '--disable-dev-shm-usage',
];

const INSTALL_HINT =
  'Install the pinned build once from Scripts/:\n' +
  '  npm ci\n' +
  '  npx puppeteer browsers install chrome';

function pinnedChrome() {
  try {
    const pkg = require('./package.json');
    return (pkg.pdfRender && pkg.pdfRender.chrome) || '';
  } catch (_) {
    return '';
  }
}

/**
 * Locate Chrome, preferring the build puppeteer manages.
 *
 * A system Chrome is whatever the machine happens to have, so it is opt-in
 * through AMD_ALLOW_SYSTEM_CHROME=1 rather than a silent fallback -- that
 * fallback is the most likely reason the committed PDFs were rendered by a
 * different Chrome than the pinned one.
 */
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
  if (process.env.AMD_ALLOW_SYSTEM_CHROME === '1') {
    for (const candidate of SYSTEM_CHROME_CANDIDATES) {
      if (candidate && fs.existsSync(candidate)) {
        return candidate;
      }
    }
  }
  return '';
}

function missingChromeMessage() {
  const found = SYSTEM_CHROME_CANDIDATES.filter((c) => c && fs.existsSync(c));
  let message = `Pinned Chrome not found.\n${INSTALL_HINT}`;
  if (found.length) {
    message +=
      `\n\nA system Chrome is present at ${found[0]}, but it is not used by ` +
      'default because its version is whatever the machine has, and PDF ' +
      'pagination depends on it. To use it anyway, set AMD_ALLOW_SYSTEM_CHROME=1.';
  }
  return message;
}

function puppeteerLaunchOptions(executablePath) {
  const options = { headless: 'new', executablePath };
  if (process.platform === 'linux') {
    options.args = LINUX_CI_CHROME_ARGS;
  }
  return options;
}

/**
 * Compare the launched browser against pdfRender.chrome in package.json.
 *
 * `strict` throws, for output whose layout must be reproducible (PDFs). The
 * social cards pass strict:false: a version difference there changes nothing
 * that matters, so it only warns.
 */
async function assertPinnedChrome(browser, { strict = true } = {}) {
  const expected = pinnedChrome();
  if (!expected) {
    return;
  }
  const raw = await browser.version();
  const actual = (raw.match(/[\d.]+/) || [''])[0];
  if (actual === expected) {
    return;
  }
  const detail =
    `Chrome version mismatch: expected ${expected} (Scripts/package.json ` +
    `pdfRender.chrome), got ${actual}.\n` +
    'PDF pagination depends on the renderer, so this would repaginate every ' +
    `study without changing a word of any of them.\n${INSTALL_HINT}\n` +
    'If the new version is intended, update pdfRender.chrome in the same ' +
    'change as the regenerated PDFs. To override once, set ' +
    'AMD_ALLOW_CHROME_MISMATCH=1.';
  if (process.env.AMD_ALLOW_CHROME_MISMATCH === '1' || !strict) {
    console.warn(`Warning: ${detail}`);
    return;
  }
  throw new Error(detail);
}

module.exports = {
  SYSTEM_CHROME_CANDIDATES,
  LINUX_CI_CHROME_ARGS,
  assertPinnedChrome,
  missingChromeMessage,
  pinnedChrome,
  puppeteerLaunchOptions,
  resolveChromeExecutable,
};
