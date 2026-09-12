/* Browser regression checks for generated theme integration. No external API calls. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const puppeteer = require('puppeteer');
const chrome = require('./_chrome.js');
const root = path.resolve(__dirname, '..');
const types = {'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml','.png':'image/png'};

(async () => {
  const server = http.createServer((request, response) => {
    let file = path.resolve(root, '.' + decodeURIComponent(request.url.split('?')[0]));
    if (!file.startsWith(root + path.sep)) return response.writeHead(403).end();
    try {
      if (fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
      response.setHeader('Content-Type', types[path.extname(file)] || 'application/octet-stream');
      response.end(fs.readFileSync(file));
    } catch { response.writeHead(404).end(); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  let browser;
  try {
    browser = await puppeteer.launch({executablePath:chrome.resolveChromeExecutable(),headless:true});
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    let pendingDiscussion, holdDiscussion = true, failDiscussion = true;
    await page.setRequestInterception(true);
    page.on('request', request => {
      if (request.url().includes('/api/discussions/How-Undivided-Society-Is-Established?')) {
        if (request.method() === 'OPTIONS') {
          void request.respond({status:204,headers:{'Access-Control-Allow-Origin':base,'Access-Control-Allow-Credentials':'true',
            'Access-Control-Allow-Methods':'GET, OPTIONS','Access-Control-Allow-Headers':'content-type'}});
          return;
        }
        const respond = () => request.respond({status:failDiscussion ? 503 : 200,contentType:'application/json',
          headers:{'Access-Control-Allow-Origin':base,'Access-Control-Allow-Credentials':'true'},
          body:JSON.stringify(failDiscussion ? {error:'Temporary test failure'} : {comments:[],viewer:{loggedIn:false},meta:{hasMore:false}})});
        if (holdDiscussion) pendingDiscussion = respond;
        else void respond();
      } else if (request.url().startsWith(base) || request.url().startsWith('data:')) void request.continue();
      else void request.abort();
    });
    await page.goto(base + '/Studies/', {waitUntil:'networkidle0'});
    for (const width of [320,390,820,1280]) {
      await page.setViewport({width,height:900});
      const metrics = await page.evaluate(() => ({width:innerWidth,scroll:document.documentElement.scrollWidth,
        nav:document.querySelector('.page-nav').getBoundingClientRect().height}));
      assert.ok(metrics.scroll <= metrics.width, `Page overflow at ${width}px: ${JSON.stringify(await page.$$eval('body *', nodes => nodes.filter(n => n.getBoundingClientRect().right > innerWidth).slice(0,12).map(n => [n.tagName,n.className,n.getBoundingClientRect().right])))}`);
      if (width === 390) assert.ok(metrics.nav < 145, `Mobile header too tall: ${metrics.nav}`);
    }
    for (const theme of ['light','dark']) {
      await page.evaluate(theme => document.documentElement.dataset.theme = theme, theme);
      const headingIcons = await page.$$eval('#approach .section-heading-icon', nodes => nodes.map(node => ({
        badge: node.getBoundingClientRect().width,
        icon: node.querySelector('svg').getBoundingClientRect().width,
        inline: !!node.querySelector('svg path, svg circle'),
        external: !!node.querySelector('use'),
      })));
      assert.equal(headingIcons.length, 4);
      for (const icon of headingIcons) assert.deepEqual(icon, {badge:44,icon:36,inline:true,external:false});
      assert.ok(await page.$eval('.hero-identity .amd-mark', element => element.getBoundingClientRect().width >= 52));
      const selector = `.approach-illustration .illustration-${theme}`;
      await page.$eval(selector, image => image.scrollIntoView({block:'center',behavior:'instant'}));
      await page.waitForFunction(selector => {const image = document.querySelector(selector); return image.complete && image.naturalWidth > 0;}, {}, selector);
      assert.ok(await page.$eval(selector, image => image.getBoundingClientRect().height > 0));
      assert.equal(await page.$eval(`.approach-illustration .illustration-${theme === 'light' ? 'dark' : 'light'}`, image => getComputedStyle(image).display), 'none');
      assert.ok(await page.$('#approach .section-card .approach-illustration'));
      if (process.env.AMD_THEME_SCREENSHOTS) {
        await page.screenshot({path:path.join(process.env.AMD_THEME_SCREENSHOTS,`integrated-${theme}.png`),fullPage:true});
        await page.setViewport({width:390,height:900});
        await page.$eval(selector, image => image.scrollIntoView({block:'center',behavior:'instant'}));
        await page.screenshot({path:path.join(process.env.AMD_THEME_SCREENSHOTS,`integrated-mobile-${theme}.png`)});
        await page.$eval('#contribute', section => section.scrollIntoView({block:'start',behavior:'instant'}));
        await page.screenshot({path:path.join(process.env.AMD_THEME_SCREENSHOTS,`contribute-mobile-${theme}.png`)});
        await page.setViewport({width:1280,height:900});
      }
    }
    for (const name of ['search','notebook','submit']) {
      await page.goto(`${base}/Studies/${name}.html`, {waitUntil:'networkidle0'});
      assert.ok(await page.$('.amd-home .amd-mark'), `${name} missing common home identity`);
    }
    await page.goto(base + '/Studies/search.html', {waitUntil:'networkidle0'});
    await page.type('#collection-query','coexistence');
    await page.click('button[type=submit]');
    await page.waitForFunction(() => !document.querySelector('#collection-search').hasAttribute('aria-busy'));
    assert.equal(await page.$eval('#search-wait', node => getComputedStyle(node).display), 'none');
    assert.match(await page.$eval('.search-status', node => node.textContent), /matching passages/);
    await page.goto(base + '/Studies/How-Undivided-Society-Is-Established/discussion.html', {waitUntil:'domcontentloaded'});
    await page.waitForSelector('#comment-list[aria-busy="true"] .amd-wait');
    await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
    assert.equal(await page.$eval('.amd-wait .goal', node => getComputedStyle(node).animationName), 'none');
    await page.waitForFunction(() => !!document.querySelector('#comment-list .amd-wait'));
    for (let tries = 0; !pendingDiscussion && tries < 50; tries++) await new Promise(resolve => setTimeout(resolve,20));
    assert.ok(pendingDiscussion, 'No discussion request intercepted');
    await pendingDiscussion();
    await page.waitForSelector('#comments-error:not(.hidden)');
    assert.equal(await page.$eval('#comment-list', node => node.getAttribute('aria-busy')), null);
    assert.equal(await page.$('#comment-list .amd-wait'), null);
    failDiscussion = false; holdDiscussion = false;
    await page.click('#comments-retry');
    await page.waitForFunction(() => !document.querySelector('#comment-list').hasAttribute('aria-busy'));
    await page.waitForSelector('#comments-error.hidden');
    assert.equal(await page.$eval('#comment-list', node => node.getAttribute('aria-busy')), null);
    assert.equal(await page.$('#comment-list .amd-wait'), null);
    assert.deepEqual(errors, []);
    console.log('PASS: responsive layout, common navigation, search, discussion failure/retry, reduced motion, and no page errors.');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => {console.error(error);process.exitCode=1;});
