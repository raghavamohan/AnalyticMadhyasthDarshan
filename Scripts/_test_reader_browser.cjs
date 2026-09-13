/* Reader interaction and print-boundary regression checks against published HTML. */
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), http = require('node:http');
const puppeteer = require('puppeteer');
const chrome = require('./_chrome.js');
const root = path.resolve(__dirname, '..');
(async () => {
  const server = http.createServer((req, res) => {
    try {
      const file = path.resolve(root, '.' + decodeURIComponent(req.url.split('?')[0]));
      if (!file.startsWith(root + path.sep)) return res.writeHead(403).end();
      res.setHeader('Content-Type', ({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml'})[path.extname(file)] || 'application/octet-stream');
      res.end(fs.readFileSync(file));
    } catch { res.writeHead(404).end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser = await puppeteer.launch({executablePath:chrome.resolveChromeExecutable(),headless:true});
    const page = await browser.newPage(), errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.setRequestInterception(true);
    page.on('request', request => request.url().startsWith(base) || request.url().startsWith('data:') ? request.continue() : request.abort());
    const documents = [
      'The-Ontology-of-Coexistence/The-Ontology-of-Coexistence',
      'A-State-Dynamic-Model-Of-Coexistence/A-State-Dynamic-Model-Of-Coexistence',
      'The-Epistemology-of-Coexistence/Research-Template-Jeevan-Activity-Environment-Dossier',
    ];
    if (!process.env.AMD_READER_SPEECH_ONLY) {
      for (const document of documents) for (const width of [1440,390,320]) {
        await page.setViewport({width,height:900});
        await page.goto(`${base}/Studies/${document}.html?from=start-here&stage=2`, {waitUntil:'networkidle0'});
        await page.evaluate(() => localStorage.clear());
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Overflow: ${document}, ${width}`);
        const alignment = await page.$eval('.reader-opening h1', node => {
          const icon = node.querySelector('svg').getBoundingClientRect(), title = node.getBoundingClientRect();
          return Math.abs(icon.top + icon.height/2 - title.top - title.height/2);
        });
        assert.ok(alignment < 1, 'Icon aligns with the whole wrapped title');
        assert.ok(await page.$eval('.study-toolbar', n => n.offsetHeight <= 100));
        assert.match(await page.$eval('.reader-ending', n => n.innerText), /Continue to stage 3/);
        assert.match(await page.$eval('.study-toolbar-back', n => n.href), /stage=2#path-study-/);
        await page.click('#reader-find');
        assert.equal(await page.$eval('#reader-search', n => n.hidden), false);
        if (width < 1180) assert.equal(await page.$eval('.reader-opening', n => n.inert), true);
        await page.click('#reader-tab-display');
        await page.select('#reader-font-size', '22');
        await page.click('[aria-label="Increase text size"]');
        assert.equal(await page.$eval('#reader-font-size', n => n.value), '24');
        for (const theme of ['light','sepia','dark']) {
          await page.select('#reader-color-theme', theme);
          assert.equal(await page.evaluate(() => document.documentElement.dataset.theme), theme);
        }
        await page.select('#reader-color-theme', 'light');
        await page.select('#reader-font-size', '18');
        await page.click('#reader-focus');
        assert.equal(await page.$eval('#reader-tools', n => n.open), false);
        await page.click('#reader-exit-focus');
        if (width < 1180) assert.equal(await page.$eval('.reader-opening', n => n.inert), false);
        await page.emulateMediaType('print');
        assert.equal(await page.$eval('.reader-opening', n => getComputedStyle(n).display), 'none');
        assert.notEqual(await page.$eval('#main h1', n => getComputedStyle(n).display), 'none');
        assert.equal(await page.$eval('#main p', n => getComputedStyle(n).textAlign), 'justify');
        await page.emulateMediaType('screen');
        if (width <= 640) assert.equal(await page.$eval('#main p', n => getComputedStyle(n).textAlign), 'left');
        if (process.env.AMD_READER_SCREENSHOTS) {
          fs.mkdirSync(process.env.AMD_READER_SCREENSHOTS, {recursive:true});
          await page.screenshot({path:path.join(process.env.AMD_READER_SCREENSHOTS, `${document.split('/').pop()}-${width}.png`)});
        }
      }
      const nextStage = await page.$eval('.reader-ending a:last-child', n => n.href);
      await page.goto(nextStage, {waitUntil:'networkidle0'});
      assert.equal(await page.$eval('#path-stage-3', n => n.checked), true, 'Reader continuation opens the requested path stage');
      await page.setViewport({width:390,height:900});
      await page.goto(`${base}/Studies/${documents[0]}.html`, {waitUntil:'networkidle0'});
      await page.click('#reader-find');
      await page.type('#reader-search-query', 'existence');
      await page.click('#reader-search-form button');
      await page.waitForSelector('#reader-search-results li');
      await page.click('#reader-tab-bookmarks');
      await page.type('#reader-bookmark-name', 'Return here');
      await page.click('#reader-bookmark-form [type="submit"]');
      await page.waitForFunction(() => document.querySelector('#reader-bookmark-list').textContent.includes('Return here'));
      await page.click('#reader-tab-notes');
      await page.click('#notes-new');
      await page.waitForSelector('#notes-editor', {visible:true});
      await page.type('#notes-text', 'Reader layout regression note');
      await page.click('#notes-editor [type="submit"]');
      await page.waitForFunction(() => document.querySelector('#notes-list').textContent.includes('Reader layout regression note'));
      await page.reload({waitUntil:'networkidle0'});
      await page.click('#reader-open'); await page.click('#reader-tab-notes');
      await page.waitForFunction(() => document.querySelector('#notes-list').textContent.includes('Reader layout regression note'));
      await page.click('#reader-tab-bookmarks');
      assert.match(await page.$eval('#reader-bookmark-list', n => n.textContent), /Return here/);
    }
    await page.evaluateOnNewDocument(() => {
      const voice = {voiceURI:'test',name:'Test',lang:'en-IN',localService:true,default:true};
      window.testSpeech = {spoken:[],getVoices:() => [voice],addEventListener() {},
        speak(u) { this.spoken.push(u); },cancel() {},resume() {}};
      Object.defineProperty(window,'speechSynthesis',{value:window.testSpeech});
      window.SpeechSynthesisUtterance = class { constructor(text) { this.text = text; } };
    });
    await page.setViewport({width:320,height:700});
    await page.goto(`${base}/Studies/${documents[0]}.html`,{waitUntil:'networkidle0'});
    const paragraphText = await page.evaluate(() => {
      const p = [...document.querySelectorAll('#main p[data-reader-passage]')].find(n => n.offsetHeight > 300 && n.textContent.length > 600);
      window.scrollTo({top:scrollY + p.getBoundingClientRect().top + p.offsetHeight / 2 - 150,behavior:'instant'});
      return p.textContent;
    });
    await page.waitForFunction(() => !document.querySelector('#listen-selection-preview').textContent.startsWith('Author:'));
    await new Promise(resolve => setTimeout(resolve,250));
    await page.click('#reader-read');
    assert.ok(paragraphText.includes(await page.evaluate(() => window.testSpeech.spoken.at(-1).text.trim())), 'starts in the visible paragraph: ' + await page.evaluate(() => window.testSpeech.spoken.at(-1).text));
    assert.ok(!paragraphText.startsWith(await page.evaluate(() => window.testSpeech.spoken.at(-1).text.trim())), 'starts within the visible paragraph instead of repeating its beginning');
    assert.equal(await page.$eval('#reader-tools',n => n.open),false);
    await page.evaluate(() => window.testSpeech.spoken.at(-1).onstart());
    assert.equal(await page.$eval('#reader-read',n => n.textContent),'Pause');
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),'active speech controls fit 320px');
    const spoken = await page.evaluate(() => {
      const u = window.testSpeech.spoken.at(-1);
      u.onboundary({name:'word',charIndex:0});
      return {text:u.text,highlight:[...CSS.highlights.get('reader-speaking')].map(r => r.toString()).join('')};
    });
    assert.ok(spoken.highlight.length && spoken.text.startsWith(spoken.highlight));
    assert.ok(!spoken.highlight.includes(' '),'highlight tracks a word');
    await page.evaluate(() => {
      window.scrollTo({top:document.body.scrollHeight,behavior:'instant'});
      window.testSpeech.spoken.at(-1).onboundary({name:'word',charIndex:0});
    });
    assert.ok(await page.evaluate(() => {
      const r = [...CSS.highlights.get('reader-speaking')][0].getBoundingClientRect();
      return r.top >= document.querySelector('.study-toolbar').getBoundingClientRect().bottom && r.bottom < innerHeight;
    }),'spoken word scrolls into view below the toolbar');
    await page.click('#reader-read');
    assert.equal(await page.$eval('#reader-read',n => n.textContent),'Resume');
    assert.equal(await page.evaluate(() => CSS.highlights.has('reader-speaking')),false);
    if (process.env.AMD_READER_SCREENSHOTS) await page.screenshot({path:path.join(process.env.AMD_READER_SCREENSHOTS,'active-320.png')});
    await page.click('#reader-read-stop');
    assert.equal(await page.$eval('#reader-read',n => n.textContent),'Read');
    assert.deepEqual(errors, []);
    console.log(process.env.AMD_READER_SPEECH_ONLY ? 'Reader browser: visible-line start, word highlighting, scrolling and mobile speech controls passed.' : 'Reader browser: three document types, 320/390/1440px, themes, focus, search, notes/bookmark persistence and print boundary passed.');
  } finally { if (browser) await browser.close(); server.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
