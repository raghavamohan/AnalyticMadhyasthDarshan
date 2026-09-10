// Execute the shipped portal against the local-only API fixture. No external
// request is allowed, including OAuth, Turnstile, GitHub and production writes.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const puppeteer = require('puppeteer');
const {resolveChromeExecutable, puppeteerLaunchOptions, assertPinnedChrome} = require('./_chrome');

async function main() {
  const origin = process.argv[2], output = path.resolve(process.argv[3]);
  assert.match(origin, /^http:\/\/127\.0\.0\.1:\d+$/);
  await fs.mkdir(output, {recursive:true});
  const browser = await puppeteer.launch(puppeteerLaunchOptions(resolveChromeExecutable()));
  const results = [], errors = [];
  let page;
  try {
    await assertPinnedChrome(browser);
    page = await browser.newPage();
    await page.setViewport({width:1280,height:900});
    page.on('pageerror', error => errors.push(error.message));
    page.on('dialog', dialog => dialog.accept());
    await page.setRequestInterception(true);
    page.on('request', request => {
      const url = request.url();
      if (url.startsWith(origin + '/') || url.startsWith('data:') || url.startsWith('blob:')) request.continue();
      else request.abort();
    });
    async function visit(query) {
      await page.goto(origin+'/Studies/submit.html?'+query,{waitUntil:'networkidle0'});
      await page.waitForFunction(() => typeof contributor !== 'undefined' && currentUser?.login === 'alice');
      await page.waitForFunction(() => document.getElementById('submit-draft-status').textContent && document.getElementById('propose-draft-status').textContent);
      assert.deepEqual(errors,[]);
    }
    await visit('tab=submit&mode=update&slug=Test-Study&artifact=presenter&target=Presenters-Companion-Test.md');
    await page.waitForFunction(() => document.getElementById('s-presenter-deck').value === 'Test-Deck.pptx');
    assert.equal(await page.$eval('#s-presenter-deck',el=>el.disabled),true);
    await page.waitForFunction(() => contributor.sourceSha && document.getElementById('s-content').value.includes('Delivery text'));
    await page.evaluate(async () => {
      document.getElementById('s-content').value = '# Slide 1\n\n## Delivering the slide\n\nRevised presenter text.\n';
      document.getElementById('s-author').value = 'Alice';
      scheduleDraftSave(); await contributor.checkpoint();
    });
    await page.reload({waitUntil:'networkidle0'});
    await page.waitForFunction(() => document.getElementById('s-content').value.includes('Revised presenter text'));
    results.push({scenario:'presenter ownership and draft recovery',status:'passed'});
    await page.click('#s-submit-btn');
    await page.waitForFunction(() => document.getElementById('fixture-payload').textContent.includes('"deckFileName"'));
    let payload = await page.$eval('#fixture-payload',el=>JSON.parse(el.textContent));
    assert.equal(payload.artifactType,'presenter');
    assert.equal(payload.deckFileName,'Test-Deck.pptx');
    assert.equal(payload.sourceSha,'a'.repeat(40));
    results.push({scenario:'presenter update submission',status:'passed'});

    await visit('tab=submit&mode=update&slug=Test-Study&artifact=note&target=__new__');
    const note = path.join(output,'Technical-Note-Acceptance.md'), svg = path.join(output,'acceptance.svg');
    await fs.writeFile(note,'# Acceptance note\n\n![Diagram](acceptance.svg)\n');
    await fs.writeFile(svg,'<svg xmlns="http://www.w3.org/2000/svg"><text x="0" y="20">Fixture</text></svg>');
    await (await page.$('#s-file')).uploadFile(note);
    await page.waitForFunction(() => document.getElementById('s-content').value.includes('Acceptance note'));
    await (await page.$('#s-assets')).uploadFile(svg);
    await page.waitForFunction(() => uploadedAssets.length === 1);
    await page.evaluate(async () => {document.getElementById('s-author').value='Alice';await contributor.checkpoint();});
    await page.reload({waitUntil:'networkidle0'});
    await page.waitForFunction(() => uploadedAssets.length === 1 && document.getElementById('s-content').value.includes('acceptance.svg'));
    results.push({scenario:'note plus figure survives page reload',status:'passed'});
    await page.select('#fixture-submit','lost');
    await page.click('#s-submit-btn');
    await page.waitForFunction(() => document.getElementById('fixture-payload').textContent.includes('acceptance.svg'));
    payload = await page.$eval('#fixture-payload',el=>JSON.parse(el.textContent));
    assert.equal(payload.assets[0].fileName,'acceptance.svg');
    assert.equal(payload.fileName,'Technical-Note-Acceptance.md');
    assert.equal(await page.evaluate(() => contributor.pending),true);
    await page.evaluate(async () => {await contributor.checkpoint();});
    await page.reload({waitUntil:'networkidle0'});
    await page.waitForFunction(() => contributor.pending && uploadedAssets.length === 1);
    await page.click('#submit-check-result');
    await page.waitForFunction(() => !contributor.pending);
    results.push({scenario:'multi-file request retains receipt after lost response',status:'passed'});

    await visit('tab=propose');
    await page.select('#p-collection','applied');
    await page.evaluate(async () => {document.getElementById('p-title').value='Applied fixture';scheduleProposeDraftSave();await contributor.flush();});
    await page.reload({waitUntil:'networkidle0'});
    await page.waitForFunction(() => document.getElementById('p-collection').value === 'applied');
    results.push({scenario:'applied proposal selection survives draft recovery',status:'passed'});
    await visit('tab=dashboard');
    await page.waitForSelector('[data-delete-selected]');
    await page.$eval('.submission-files',el=>el.open=true);
    const boxes = await page.$$('[data-select-companion]');
    assert.equal(boxes.length,3);
    await boxes[0].click(); await boxes[1].click();
    await page.screenshot({path:path.join(output,'companion-selection.png'),fullPage:true});
    await page.click('[data-delete-selected]');
    await page.waitForFunction(() => document.getElementById('fixture-payload').textContent.includes('"artifacts"'));
    payload = await page.$eval('#fixture-payload',el=>JSON.parse(el.textContent));
    assert.equal(payload.artifacts.length,2);
    assert.ok(payload.artifacts.every(file=>file.artifactType!=='study' && file.sourceSha==='a'.repeat(40)));
    results.push({scenario:'bulk companion removal excludes canonical study',status:'passed'});
    await page.screenshot({path:path.join(output,'portal.png'),fullPage:true});
    assert.deepEqual(errors,[]);
  } finally {
    if (page && !page.isClosed()) {
      await page.screenshot({path:path.join(output,'portal.png'),fullPage:true}).catch(()=>{});
      await fs.writeFile(path.join(output,'browser-state.json'),JSON.stringify(await page.evaluate(() => ({
        url:location.href, content:document.getElementById('s-content')?.value,
        artifact:document.getElementById('s-artifact')?.value, target:document.getElementById('s-target')?.value,
        deck:document.getElementById('s-presenter-deck')?.value,
        alerts:Array.from(document.querySelectorAll('[role="alert"],.alert,.draft-status')).map(el=>el.textContent),
      })).catch(()=>({})),null,2)+'\n');
    }
    await fs.writeFile(path.join(output,'browser-results.json'),JSON.stringify({environment:'isolated browser fixture',results,errors},null,2)+'\n');
    await browser.close();
  }
  console.log(JSON.stringify(results));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
