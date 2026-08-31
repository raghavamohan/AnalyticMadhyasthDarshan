/**
 * Rasterise a local HTML file to PNG with headless Chrome.
 *
 * Used by _build_social_cards.py to render Open Graph share cards, so the cards
 * carry the site's own Georgia/Segoe typography instead of whatever font a
 * Pillow-based generator happens to find on the build machine.
 *
 *   node _html_to_png.js <input.html> <output.png> [width] [height]
 *
 * Chrome resolution is shared with _html_to_pdf.js. The pinned-version check
 * runs in non-strict mode here: a card is a fixed-size screenshot, so a
 * different Chrome changes nothing that matters, unlike PDF pagination.
 */
const fs = require('fs');
const path = require('path');

const {
  assertPinnedChrome,
  missingChromeMessage,
  puppeteerLaunchOptions,
  resolveChromeExecutable,
} = require('./_chrome');

const puppeteer = require('puppeteer');

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
    console.error(missingChromeMessage());
    process.exit(1);
  }

  const browser = await puppeteer.launch(puppeteerLaunchOptions(executablePath));
  try {
    await assertPinnedChrome(browser, { strict: false });
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
