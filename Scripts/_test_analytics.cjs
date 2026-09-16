const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../infra/site-worker/analytics.js'), 'utf8');
const origin = 'https://analyticmadhyasthdarshan.org';

function run(options = {}) {
  const storage = options.storage || new Map();
  const scripts = [], notices = [];
  const context = {
    URL, location: new URL(options.url || origin + '/Studies/index.html'),
    navigator: {userAgent: options.ua || 'Chrome', webdriver: !!options.webdriver, onLine: !options.offline},
    localStorage: {
      getItem: key => { if (options.blockStorage) throw Error('blocked'); return storage.get(key); },
      setItem: (key, value) => { if (options.blockStorage) throw Error('blocked'); storage.set(key, value); },
      removeItem: key => storage.delete(key),
    },
    history: {replaceState: (_, __, url) => { context.location = new URL(url); }},
    document: {
      readyState: 'complete', querySelector: () => options.existingBeacon || null,
      createElement: tag => ({tag, style: {}, setAttribute(key, value) { this[key] = value; }}),
      head: {appendChild: node => scripts.push(node)}, body: {prepend: node => notices.push(node)},
    },
    __AMD_DISABLE_ANALYTICS__: options.disable,
  };
  context.window = context; context.self = context; context.top = options.iframe ? {} : context;
  vm.createContext(context);
  vm.runInContext(source, context);
  return {context, scripts, notices, storage};
}

const normal = run();
assert.equal(normal.scripts.length, 1);
assert.equal(JSON.parse(normal.scripts[0]['data-cf-beacon']).spa, false);
vm.runInContext(source, normal.context);
assert.equal(normal.scripts.length, 1, 'no duplicate loader');
const off = run({url: origin + '/Studies/index.html?analytics=off&r=abc#section'});
assert.equal(off.scripts.length, 0);
assert.match(off.notices[0].textContent, /visits are excluded/);
assert.equal(off.context.location.search, '?r=abc');
assert.equal(off.context.location.hash, '#section');
assert.equal(run({storage: off.storage}).scripts.length, 0, 'opt-out persists across pages');
assert.equal(run({storage: off.storage, url: origin + '/?analytics=status'}).scripts.length, 0);
const on = run({storage: off.storage, url: origin + '/?analytics=on'});
assert.equal(on.scripts.length, 0, 'preference changes are not visits');
assert.equal(run({storage: on.storage}).scripts.length, 1, 'opt-in takes effect on next page');
for (const options of [
  {webdriver: true}, {ua: 'HeadlessChrome'}, {disable: true}, {offline: true},
  {blockStorage: true}, {iframe: true}, {existingBeacon: true},
  {url: 'http://localhost:8000/Studies/index.html'},
  {url: 'https://amd-site-canary.example.workers.dev/Studies/index.html'},
  {url: origin + '/Studies/portal/preview.html'},
  {url: origin + '/Studies/submit.html'}, {url: origin + '/Studies/notebook.html'},
]) assert.equal(run(options).scripts.length, 0, JSON.stringify(options));
assert.match(run({blockStorage: true, url: origin + '/?analytics=off'}).notices[0].textContent, /blocked saving/);
console.log('Analytics exclusion and visitor-loading tests passed.');

async function browserTest() {
  const chrome = require('./_chrome');
  const puppeteer = require('puppeteer');
  const browser = await puppeteer.launch(chrome.puppeteerLaunchOptions(chrome.resolveChromeExecutable()));
  try {
    const page = await browser.newPage();
    let beacons = 0;
    await page.setRequestInterception(true);
    page.on('request', request => {
      if (request.url().startsWith('https://static.cloudflareinsights.com/')) {
        beacons++;
        return request.respond({status: 200, contentType: 'application/javascript', body: ''});
      }
      // All requests are intercepted: this test never contacts production or sends telemetry.
      if (request.isNavigationRequest()) return request.respond({status: 200, contentType: 'text/html',
        body: '<html><head><script>' + source + '</script></head><body>Test</body></html>'});
      return request.abort();
    });
    await page.goto(origin + '/Studies/index.html');
    assert.equal(beacons, 0, 'real Puppeteer is excluded');
    await page.evaluateOnNewDocument(() => Object.defineProperty(navigator, 'webdriver', {get: () => false}));
    await page.setUserAgent('Mozilla/5.0 Chrome/140.0.0.0 Safari/537.36');
    await page.goto(origin + '/Studies/index.html');
    assert.equal(beacons, 1, 'simulated reader loads beacon');
    await page.goto(origin + '/Studies/index.html?analytics=off');
    assert.match(await page.$eval('[role=status]', n => n.textContent), /visits are excluded/);
    await page.goto(origin + '/Studies/Other.html');
    assert.equal(beacons, 1, 'persistent opt-out prevents any further beacon requests');
    await page.goto(origin + '/Studies/index.html?analytics=on');
    assert.equal(beacons, 1);
    await page.goto(origin + '/Studies/Other.html');
    assert.equal(beacons, 2);
    console.log('Browser persistence, status notice, and intercepted beacon checks passed.');
  } finally { await browser.close(); }
}
if (process.argv.includes('--browser')) browserTest().catch(error => { console.error(error); process.exitCode = 1; });
