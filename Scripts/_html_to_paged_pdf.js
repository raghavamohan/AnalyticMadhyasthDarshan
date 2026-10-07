/**
 * Print a self-contained HTML file to PDF at the page size declared by its CSS
 * @page rule, with no Chrome header, footer or margins.
 *
 * Review builds that lay out every sheet in the HTML itself (one fixed-size
 * sheet per source page) use this instead of _html_to_pdf.js, which imposes A4
 * pages, study margins and a site footer. When the page defines
 * window.__layoutPages(), it runs after fonts load and under print media, so
 * measurements match the printed layout; its JSON-serialisable return value is
 * printed as the last stdout line, prefixed "REPORT ".
 *
 * Usage: node Scripts/_html_to_paged_pdf.js <input.html> <output.pdf>
 */
const path = require('path');

const {
  assertPinnedChrome,
  missingChromeMessage,
  puppeteerLaunchOptions,
  resolveChromeExecutable,
} = require('./_chrome');

const puppeteer = require('puppeteer');
const { allowedPdfResource } = require('./_pdf_resource_policy.cjs');

const workspaceRoot = path.resolve(__dirname, '..');

(async () => {
  const [inputArg, outputArg] = process.argv.slice(2);
  if (!inputArg || !outputArg) {
    console.error('Usage: node Scripts/_html_to_paged_pdf.js <input.html> <output.pdf>');
    process.exit(2);
  }
  const inputPath = path.resolve(process.cwd(), inputArg);
  const outputPath = path.resolve(process.cwd(), outputArg);

  const executablePath = resolveChromeExecutable();
  if (!executablePath) {
    console.error(missingChromeMessage());
    process.exit(1);
  }
  // Chrome needs OS paths and locale, not CI or publishing credentials.
  const browserEnv = Object.fromEntries(Object.entries(process.env).filter(([key]) =>
    /^(PATH|SYSTEMROOT|WINDIR|TEMP|TMP|TMPDIR|HOME|USERPROFILE|APPDATA|LOCALAPPDATA|LANG|LC_[A-Z_]+|DISPLAY|XDG_RUNTIME_DIR)$/i.test(key)));
  const browser = await puppeteer.launch({
    ...puppeteerLaunchOptions(executablePath),
    env: browserEnv,
  });
  try {
    // Fitting text to a fixed sheet depends on the renderer's metrics.
    await assertPinnedChrome(browser);
    const page = await browser.newPage();
    await page.setRequestInterception(true);
    page.on('request', request => {
      const allowed = allowedPdfResource(request.url(), request.resourceType(), inputPath,
        path.join(workspaceRoot, 'Assets', 'KaTeX', 'fonts'));
      if (allowed) request.continue();
      else request.abort();
    });
    await page.goto('file:///' + inputPath.replace(/\\/g, '/'), { waitUntil: 'load' });
    await page.emulateMediaType('print');
    await page.evaluate(() => document.fonts.ready);
    const report = await page.evaluate(() => (
      typeof window.__layoutPages === 'function' ? window.__layoutPages() : null
    ));
    await page.pdf({
      path: outputPath,
      preferCSSPageSize: true,
      printBackground: true,
      displayHeaderFooter: false,
      margin: { top: '0', right: '0', bottom: '0', left: '0' },
    });
    console.log('PDF written to:', outputPath);
    console.log('REPORT ' + JSON.stringify(report));
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exit(1);
});
