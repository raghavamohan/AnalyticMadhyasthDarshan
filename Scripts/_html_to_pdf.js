const puppeteer = require('puppeteer');
const path = require('path');

const workspaceRoot = path.resolve(__dirname, '..');

const args = process.argv.slice(2);
// Relative input paths resolve against the current working directory; the
// default points at the workspace's Studies folder.
const inputPath = args[0]
  ? path.resolve(process.cwd(), args[0])
  : path.join(workspaceRoot, 'Studies', 'How-To-Form-Self-Sustaining-Organizations.html');
const outputPath = inputPath.replace(/\.html$/, '.pdf');

(async () => {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  await page.goto('file:///' + inputPath.replace(/\\/g, '/'), { waitUntil: 'networkidle0' });
  
  await page.pdf({
    path: outputPath,
    format: 'A4',
    margin: { top: '2.2cm', bottom: '2.2cm', left: '2cm', right: '2cm' },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="width:100%;text-align:center;font-size:9pt;font-family:Georgia,serif;color:#666;"><span class="pageNumber"></span></div>',
  });

  await browser.close();
  console.log('PDF written to:', outputPath);
})();
