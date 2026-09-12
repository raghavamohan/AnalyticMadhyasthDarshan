/* Publish the approved A1 compact geometry at the existing favicon URLs.
   This only updates local files; deployment uses the repository workflow. */
const fs = require('fs');
const path = require('path');
const chrome = require('../../Scripts/_chrome.js');
const puppeteer = require('../../Scripts/node_modules/puppeteer');
const root = path.resolve(__dirname, '../..');
const target = path.join(root, 'Assets/Icons');
function ico(images) {
  const header = Buffer.alloc(6 + 16 * images.length);
  header.writeUInt16LE(1, 2); header.writeUInt16LE(images.length, 4);
  let offset = header.length;
  images.forEach(({size, data}, i) => {
    const entry = 6 + i * 16;
    header[entry] = size; header[entry + 1] = size;
    header.writeUInt16LE(1, entry + 4); header.writeUInt16LE(32, entry + 6);
    header.writeUInt32LE(data.length, entry + 8); header.writeUInt32LE(offset, entry + 12);
    offset += data.length;
  });
  return Buffer.concat([header, ...images.map(i => i.data)]);
}
(async () => {
  const source = fs.readFileSync(path.join(__dirname, 'icons/akhand-samaj-compact.svg'), 'utf8');
  const svg = source.replace('--amd-icon:#1A5276;--amd-accent:#B47B46', '--amd-icon:#F7F4EF;--amd-accent:#D5A477')
    .replace(/(<svg[^>]*>)/, '$1<rect width="240" height="240" rx="36" fill="#1A5276"/>');
  fs.writeFileSync(path.join(target, 'akhand-samaj-favicon.svg'), svg);
  const browser = await puppeteer.launch({executablePath: chrome.resolveChromeExecutable(), headless: true});
  try {
    const page = await browser.newPage();
    const images = [];
    for (const size of [16, 32, 48, 180, 512]) {
      await page.setViewport({width: size, height: size, deviceScaleFactor: 1});
      const artwork = size === 180 ? svg.replace('rx="36"', 'rx="0"') : svg;
      await page.setContent(`<style>html,body{margin:0;background:transparent}svg{display:block;width:${size}px;height:${size}px}</style>${artwork}`);
      const data = Buffer.from(await page.screenshot({omitBackground: true}));
      const name = size === 180 ? 'akhand-samaj-apple-touch-icon.png' : size === 512 ? 'akhand-samaj-favicon.png' : `akhand-samaj-favicon-${size}.png`;
      fs.writeFileSync(path.join(target, name), data);
      if (size <= 48) images.push({size, data});
    }
    const bundle = ico(images);
    fs.writeFileSync(path.join(target, 'akhand-samaj-favicon.ico'), bundle);
    fs.writeFileSync(path.join(root, 'favicon.ico'), bundle);
    fs.copyFileSync(path.join(target, 'akhand-samaj-apple-touch-icon.png'), path.join(root, 'apple-touch-icon.png'));
  } finally { await browser.close(); }
  console.log('Approved A1 favicon, touch icon and root copies updated.');
})().catch(error => { console.error(error); process.exitCode = 1; });
