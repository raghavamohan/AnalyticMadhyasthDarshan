/**
 * Rasterize an SVG file to PNG for embedding in study presentations.
 * Usage: node Scripts/_svg_to_png.js <svg-path> <png-path>
 */
const fs = require('fs');
const path = require('path');
const os = require('os');
const puppeteer = require('puppeteer');

const persistentPuppeteerCache = path.join(os.homedir(), '.cache', 'puppeteer');

async function executablePath() {
  try {
    return puppeteer.executablePath();
  } catch {
    return undefined;
  }
}

async function main() {
  const svgPath = process.argv[2];
  const pngPath = process.argv[3];
  if (!svgPath || !pngPath) {
    console.error('Usage: node _svg_to_png.js <svg-path> <png-path>');
    process.exit(1);
  }

  const absSvg = path.resolve(svgPath);
  const absPng = path.resolve(pngPath);
  const svgContent = fs.readFileSync(absSvg, 'utf8');

  const widthMatch = svgContent.match(/\bwidth="(\d+)"/);
  const heightMatch = svgContent.match(/\bheight="(\d+)"/);
  const width = widthMatch ? Number(widthMatch[1]) : 960;
  const height = heightMatch ? Number(heightMatch[1]) : 540;

  const html = `<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;background:white;">
${svgContent}
</body></html>`;

  const executable = await executablePath();
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: executable,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    cacheDirectory: persistentPuppeteerCache,
  });

  try {
    const page = await browser.newPage();
    await page.setViewport({ width, height, deviceScaleFactor: 2 });
    await page.setContent(html, { waitUntil: 'networkidle0' });
    const svgHandle = await page.$('svg');
    if (!svgHandle) {
      throw new Error(`No <svg> root in ${absSvg}`);
    }
    await svgHandle.screenshot({ path: absPng, type: 'png' });
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
