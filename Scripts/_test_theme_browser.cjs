/* Browser regression checks for generated theme integration. No external API calls. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const chrome = require('./_chrome.js');
const puppeteer = require('puppeteer');
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
    const firstReading = '.hero-actions .btn-primary';
    const firstReadingPath = '/Studies/Why-Humans-Are-Not-Just-Material/Why-Humans-Are-Not-Just-Material.html';
    const assertFirstReading = async () => {
      assert.equal(await page.$eval(firstReading, node => node.textContent.trim()), 'Begin with the human question');
      const destination = new URL(await page.$eval(firstReading, node => node.href));
      assert.equal(destination.pathname, firstReadingPath);
      assert.equal(destination.search, '?from=start-here&stage=1');
    };
    // The recommended route must work before the catalog's JavaScript runs.
    await page.setJavaScriptEnabled(false);
    await page.goto(base + '/Studies/', {waitUntil:'networkidle0'});
    await assertFirstReading();
    await page.setJavaScriptEnabled(true);
    await page.reload({waitUntil:'networkidle0'});
    await assertFirstReading();
    assert.equal(await page.$('.page-nav a[href="submit.html"]'), null, 'Submissions should enter through Contribute');
    assert.match(await page.$eval('#contribute a.contribute-action[href="submit.html"]', node => node.textContent), /My Submissions/);
    await page.addStyleTag({content:'* { scroll-behavior: auto !important; transition: none !important; }'});
    for (const theme of ['light','dark']) {
      if (await page.$eval('html', node => node.dataset.theme) !== theme) await page.click('#theme-toggle');
      await page.waitForFunction(theme => document.documentElement.dataset.theme === theme, {}, theme);
      for (const {width,height} of [{width:1280,height:800},{width:390,height:844},{width:320,height:568}]) {
        await page.setViewport({width,height});
        await page.waitForFunction(() => {
          const offset = document.documentElement.style.getPropertyValue('--page-nav-offset');
          return innerWidth > 820 ? !offset : Math.abs(parseFloat(offset) - document.querySelector('.page-nav').getBoundingClientRect().height) < 1;
        });
        await page.evaluate(() => scrollTo({top:0,behavior:'instant'}));
        const bounds = await page.$eval(firstReading, node => {
          const box = node.getBoundingClientRect();
          return {top:Math.round(box.top),bottom:Math.round(box.bottom),viewport:innerHeight,nav:Math.round(document.querySelector('.page-nav').getBoundingClientRect().height)};
        });
        console.log(`First reading ${theme} ${width}x${height}: ${JSON.stringify(bounds)}`);
        if (process.env.AMD_THEME_SCREENSHOTS) {
          await page.screenshot({path:path.join(process.env.AMD_THEME_SCREENSHOTS,`entrance-${theme}-${width}.png`)});
        }
        assert.ok(bounds.top >= 0 && bounds.bottom <= height, `First reading must fit the initial ${width}x${height} screen in ${theme} theme`);
      }
    }
    if (await page.$eval('html', node => node.dataset.theme) !== 'light') await page.click('#theme-toggle');
    for (const width of [320,390,820,840,900,940,980,1100,1280]) {
      await page.setViewport({width,height:900});
      await page.waitForFunction(() => {
        const offset = document.documentElement.style.getPropertyValue('--page-nav-offset');
        return innerWidth > 820 ? !offset : Math.abs(parseFloat(offset) - document.querySelector('.page-nav').getBoundingClientRect().height) < 1;
      });
      const metrics = await page.evaluate(() => ({width:innerWidth,scroll:document.documentElement.scrollWidth,
        nav:document.querySelector('.page-nav').getBoundingClientRect().height}));
      assert.ok(metrics.scroll <= metrics.width, `Page overflow at ${width}px: ${JSON.stringify(await page.$$eval('body *', nodes => nodes.filter(n => n.getBoundingClientRect().right > innerWidth).slice(0,12).map(n => [n.tagName,n.className,n.getBoundingClientRect().right])))}`);
      const navOverlaps = await page.evaluate(() => {
        const boxes = [...document.querySelectorAll('.page-nav-home, .toc a, .page-nav-tools a, .page-nav-tools .theme-toggle')]
          .filter(node => getComputedStyle(node).display !== 'none' && node.getBoundingClientRect().width > 0)
          .map(node => ({name:(node.getAttribute('aria-label') || node.textContent).trim(), ...node.getBoundingClientRect()}));
        const hits = [];
        for (let i = 0; i < boxes.length; i++) {
          for (let j = i + 1; j < boxes.length; j++) {
            const a = boxes[i], b = boxes[j];
            const overlapX = Math.min(a.right, b.right) - Math.max(a.left, b.left);
            const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
            if (overlapX > 1 && overlapY > 1) hits.push(`${a.name} x ${b.name}`);
          }
        }
        return hits;
      });
      assert.deepEqual(navOverlaps, [], `Nav controls overlap at ${width}px: ${navOverlaps.join('; ')}`);
      await page.evaluate(() => scrollTo({top:0,behavior:'instant'}));
      const entrance = await page.$eval(firstReading, node => {
        const box = node.getBoundingClientRect();
        return {top:box.top,bottom:box.bottom,height:innerHeight,navBottom:document.querySelector('.page-nav').getBoundingClientRect().bottom};
      });
      assert.ok(entrance.top >= 0 && entrance.bottom <= entrance.height, `First reading below initial screen at ${width}px`);
      if (width <= 820) assert.ok(entrance.top >= entrance.navBottom, `First reading obscured by mobile navigation at ${width}px`);
      if (width <= 600) {
        const labels = await page.$$eval('.page-nav-tools .nav-link-label', nodes => nodes.map(node => ({text:node.textContent.trim(),visible:getComputedStyle(node).display !== 'none' && node.getBoundingClientRect().width > 0})));
        assert.deepEqual(labels, [{text:'Search',visible:true},{text:'My Notes',visible:true}], `Mobile tools need understandable labels at ${width}px`);
      }
      if ([320,390,1280].includes(width)) {
        const tree = await page.accessibility.snapshot();
        const flatten = node => node ? [node,...(node.children || []).flatMap(flatten)] : [];
        const nodes = flatten(tree);
        for (const name of ['Begin with the human question','Browse all studies','Search','My Notes']) {
          assert.ok(nodes.some(node => node.role === 'link' && node.name === name), `Accessible link missing: ${name} at ${width}px`);
        }
        const primary = nodes.find(node => node.role === 'link' && node.name === 'Begin with the human question');
        assert.match(primary.description || '', /Recommended first reading: Why Humans Are Not Just Material/);
      }
      if (width <= 820) {
        const mobileNav = await page.evaluate(() => {
          const round = value => Math.round(value);
          const nav = document.querySelector('.page-nav').getBoundingClientRect();
          const toc = [...document.querySelectorAll('.toc a')].map(node => node.getBoundingClientRect());
          const tools = [...document.querySelectorAll('.page-nav-tools a, .page-nav-tools .theme-toggle')].map(node => node.getBoundingClientRect());
          const allTops = [...new Set([...toc, ...tools].map(box => round(box.top)))].sort((a, b) => a - b);
          const toolTop = Math.min(...tools.map(box => round(box.top)));
          const lastTocOnToolRow = toc.filter(box => Math.abs(round(box.top) - toolTop) <= 2).sort((a, b) => a.right - b.right).at(-1);
          return {
            homeDisplay: getComputedStyle(document.querySelector('.page-nav-home')).display,
            rowCount: allTops.length,
            toolRowCount: new Set(tools.map(box => round(box.top))).size,
            toolsLeft: Math.min(...tools.map(box => box.left)),
            toolsRight: Math.max(...tools.map(box => box.right)),
            navRight: nav.right,
            lastTocRight: lastTocOnToolRow ? lastTocOnToolRow.right : null,
          };
        });
        assert.equal(mobileNav.homeDisplay, 'none', `Home mark still visible at ${width}px`);
        assert.ok(mobileNav.rowCount <= (width >= 390 ? 2 : 3), `Mobile nav has ${mobileNav.rowCount} rows at ${width}px`);
        assert.equal(mobileNav.toolRowCount, 1, `Tools split across rows at ${width}px`);
        assert.ok(mobileNav.navRight - mobileNav.toolsRight < 24, `Tools not right-aligned at ${width}px`);
        if (mobileNav.lastTocRight != null) {
          assert.ok(mobileNav.toolsLeft >= mobileNav.lastTocRight - 1, `Tools overlap TOC at ${width}px`);
        }
      }
      if (width === 390) assert.ok(metrics.nav < 100, `Mobile header too tall: ${metrics.nav}`);
      if (width >= 1280) {
        const tocTops = await page.$$eval('.toc a', nodes => nodes.map(node => Math.round(node.getBoundingClientRect().top)));
        assert.equal(new Set(tocTops).size, 1, `TOC wrapped on desktop: ${JSON.stringify(tocTops)}`);
        const chipHeights = await page.evaluate(() => {
          const height = selector => Math.round(document.querySelector(selector).getBoundingClientRect().height);
          return {
            toc: height('.toc a'),
            search: height('.page-nav-search'),
            notes: height('.page-nav-tools a[href="notebook.html"]'),
            theme: height('#theme-toggle'),
          };
        });
        for (const [name, height] of Object.entries(chipHeights)) {
          assert.equal(height, chipHeights.toc, `${name} height ${height}px != TOC ${chipHeights.toc}px`);
        }
      }
      assert.equal(await page.$eval('.path-panel[data-stage="1"] .path-related summary', node => node.textContent.trim()), 'Related studies');
      assert.equal(await page.$('.path-panel[data-stage="1"] .path-related-chips'), null);
      await page.$eval('.path-panel[data-stage="1"] .path-related', details => details.open = true);
      const relatedLayout = await page.$eval('.path-panel[data-stage="1"] .path-related li', row => {
        const title = row.querySelector('.related-study-title').getBoundingClientRect();
        const description = row.querySelector('.related-study-description').getBoundingClientRect();
        return {below:description.top >= title.bottom, right:description.left >= title.right};
      });
      assert.ok(width <= 600 ? relatedLayout.below : relatedLayout.right, `Related description layout at ${width}px`);
      await page.$eval('.path-panel[data-stage="1"] .path-related', details => details.open = false);
      assert.ok(await page.$eval('.path-panel[data-stage="1"]', panel => panel.querySelector('.path-continue').getBoundingClientRect().top >= panel.querySelector('.path-core').getBoundingClientRect().bottom));
      const titleOffsets = await page.$$eval('.hero-identity, .card-title-row, .contribute-heading, .section-heading', rows => rows.filter(row => row.getBoundingClientRect().height > 0).map(row => {
        const icon = row.firstElementChild.getBoundingClientRect();
        const text = row.lastElementChild.getBoundingClientRect();
        // Anonymous flex text boxes use font ink bounds; compare those separately
        // through their container's align-items contract below.
        return {kind:row.className, offset:row.children.length > 1 ? Math.abs(icon.y + icon.height/2 - text.y - text.height/2) : 0,
          alignment:getComputedStyle(row).alignItems};
      }));
      for (const row of titleOffsets) {
        assert.equal(row.alignment, 'center', `${row.kind} at ${width}px`);
        assert.ok(row.offset < 1, `${row.kind} icon offset ${row.offset}px at ${width}px`);
      }
    }
    for (const [stage, next] of [[1,2],[2,3],[3,4],[4,5],[5,1]]) {
      await page.$eval(`.path-panel[data-stage="${stage}"] .path-related`, details => details.open = true);
      const related = await page.$$eval(`.path-panel[data-stage="${stage}"] [data-related-description]`, nodes => nodes.map(node => ({slug:node.dataset.relatedDescription, html:node.innerHTML})));
      const catalog = ['topical','formal','applied'].flatMap(kind => JSON.parse(fs.readFileSync(path.join(root,`Studies/catalog-${kind}.json`),'utf8')));
      for (const item of related) {
        const entry = catalog.find(entry => entry.slug === item.slug);
        assert.ok(entry && item.html.trim(), `Missing description for ${item.slug}`);
        assert.equal(await page.evaluate(({actual,expected}) => {const a=document.createElement('div'),b=document.createElement('div');a.innerHTML=actual;b.innerHTML=expected;return a.textContent===b.textContent;},{actual:item.html,expected:entry.description}), true);
      }
      await page.$eval(`.path-panel[data-stage="${stage}"] .path-related`, details => details.open = false);
      const selector = `.path-panel[data-stage="${stage}"] .path-continue`;
      await page.focus(selector);
      await page.keyboard.press('Enter');
      await page.waitForFunction(next => document.querySelector(`#path-stage-${next}`).checked, {}, next);
    }
    for (const theme of ['light','dark']) {
      if (await page.$eval('html', node => node.dataset.theme) !== theme) await page.click('#theme-toggle');
      await page.waitForFunction(theme => document.documentElement.dataset.theme === theme, {}, theme);
      const headingIcons = await page.$$eval('#approach .section-heading-icon', nodes => nodes.map(node => ({
        badge: node.getBoundingClientRect().width,
        icon: node.querySelector('svg').getBoundingClientRect().width,
        inline: !!node.querySelector('svg path, svg circle'),
        external: !!node.querySelector('use'),
      })));
      assert.equal(headingIcons.length, 4);
      for (const icon of headingIcons) assert.deepEqual(icon, {badge:44,icon:36,inline:true,external:false});
      assert.ok(await page.$eval('.hero-identity .amd-mark', element => element.getBoundingClientRect().width >= 52));
      assert.ok(await page.$('#contribute a[href="submit.html"]'), 'Contribute must retain My Submissions access');
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
    // Exercise the actual newcomer route with keyboard activation and both reader exits.
    for (const width of [1280,390]) {
      await page.setViewport({width,height:900});
      await page.goto(base + '/Studies/', {waitUntil:'networkidle0'});
      await page.focus('.skip-link');
      await page.keyboard.press('Tab');
      assert.equal(await page.$eval(firstReading, node => node === document.activeElement), true, 'First reading follows the skip link in keyboard order');
      assert.ok(await page.$eval(firstReading, node => getComputedStyle(node).outlineStyle !== 'none'), 'First reading has visible keyboard focus');
      await page.keyboard.press('Tab');
      assert.equal(await page.$eval('.hero-browse', node => node === document.activeElement), true, 'Browse follows the recommended first reading in keyboard order');
      assert.ok(await page.$eval('.hero-browse', node => getComputedStyle(node).outlineStyle !== 'none'), 'Browse has visible keyboard focus');
      await page.keyboard.down('Shift');
      await page.keyboard.press('Tab');
      await page.keyboard.up('Shift');
      assert.equal(await page.$eval(firstReading, node => node === document.activeElement), true, 'Backward keyboard navigation returns to the first reading');
      await Promise.all([page.waitForNavigation({waitUntil:'networkidle0'}),page.keyboard.press('Enter')]);
      assert.equal(new URL(page.url()).pathname, firstReadingPath);
      assert.equal(await page.$eval('.study-toolbar-back', node => node.textContent.trim()), 'Back to Start here');
      assert.match(await page.$eval('.study-toolbar-back', node => node.href), /stage=1#path-study-Why-Humans-Are-Not-Just-Material$/);
      assert.match(await page.$eval('.reader-ending', node => node.textContent), /Continue to stage 2/);
      await page.focus('.study-toolbar-back');
      await Promise.all([page.waitForNavigation({waitUntil:'networkidle0'}),page.keyboard.press('Enter')]);
      assert.equal(await page.$eval('#path-stage-1', node => node.checked), true);
      await assertFirstReading();
      await page.focus(firstReading);
      await Promise.all([page.waitForNavigation({waitUntil:'networkidle0'}),page.keyboard.press('Enter')]);
      await page.focus('.reader-ending a:last-child');
      await Promise.all([page.waitForNavigation({waitUntil:'networkidle0'}),page.keyboard.press('Enter')]);
      assert.equal(await page.$eval('#path-stage-2', node => node.checked), true);
      await assertFirstReading(); // Choosing a later stage must not alter the entrance recommendation.
      await page.focus('.hero-browse');
      await page.keyboard.press('Enter');
      assert.equal(new URL(page.url()).hash, '#browse-studies');
      assert.ok(await page.$eval('#browse-studies', node => node.getBoundingClientRect().top >= document.querySelector('.page-nav').getBoundingClientRect().bottom - 1), 'Browse heading clears sticky navigation');
      await page.type('#q', 'Nature of Time');
      await page.waitForFunction(() => document.querySelector('#count').textContent === '1 studies shown');
      assert.match(await page.$eval('#study-Nature-Of-Time .card-title', node => node.textContent), /Nature of Time/);
      await page.focus('#study-Nature-Of-Time .card-title a');
      await Promise.all([page.waitForNavigation({waitUntil:'networkidle0'}),page.keyboard.press('Enter')]);
      assert.match(new URL(page.url()).pathname, /\/Nature-Of-Time\/Nature-Of-Time\.html$/);
    }
    for (const name of ['search','notebook','submit']) {
      await page.goto(`${base}/Studies/${name}.html`, {waitUntil:'networkidle0'});
      assert.ok(await page.$('.amd-home .amd-mark'), `${name} missing common home identity`);
      assert.ok(await page.$(`.site-chrome-link[href="submit.html"] use[href$="#work"]`), `${name} missing submissions icon`);
      assert.ok(await page.$('#theme-toggle'), `${name} missing shared theme toggle`);
    }
    await page.goto(`${base}/Studies/submit.html`, {waitUntil:'networkidle0'});
    assert.ok(await page.$('#theme-toggle .theme-icon-moon use[href$="#moon"]'), 'portal theme toggle missing moon icon');
    assert.ok(await page.$('#theme-toggle .theme-icon-sun use[href$="#sun"]'), 'portal theme toggle missing sun icon');
    assert.ok(await page.$eval('#amd-portal-wait', node => !!node.content.querySelector('.amd-wait')), 'portal missing branded waiter');
    assert.ok(await page.$('#propose-download-draft use[href$="#download"]'), 'portal download action missing icon');
    await page.goto(base + '/Studies/', {waitUntil:'networkidle0'});
    await page.focus('#search-passage-hint a');
    await Promise.all([page.waitForNavigation({waitUntil:'networkidle0'}),page.keyboard.press('Enter')]);
    assert.equal(new URL(page.url()).pathname, '/Studies/search.html');
    await page.type('#collection-query','coexistence');
    await page.click('button[type=submit]');
    await page.waitForFunction(() => !document.querySelector('#collection-search').hasAttribute('aria-busy'));
    assert.equal(await page.$eval('#search-wait', node => getComputedStyle(node).display), 'none');
    assert.match(await page.$eval('.search-status', node => node.textContent), /matching passages/);
    await page.waitForSelector('.search-results a');
    await page.focus('.search-results a');
    await Promise.all([page.waitForNavigation({waitUntil:'networkidle0'}),page.keyboard.press('Enter')]);
    const passageDestination = new URL(page.url());
    assert.equal(passageDestination.searchParams.get('find'), 'coexistence');
    assert.ok(passageDestination.hash, 'Passage search needs a passage destination');
    assert.equal(await page.evaluate(() => !!document.getElementById(decodeURIComponent(location.hash.slice(1)))), true, 'Passage search opens an existing reader anchor');
    await page.goto(base + '/Studies/How-Undivided-Society-Is-Established/discussion.html', {waitUntil:'domcontentloaded'});
    assert.ok(await page.$('#theme-toggle'), 'discussion missing shared theme toggle');
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
    console.log('PASS: first-reading routes and keyboard access, accessible entrance labels, responsive layout, title and passage search, common navigation, discussion failure/retry, reduced motion, and no page errors.');
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => {console.error(error);process.exitCode=1;});
