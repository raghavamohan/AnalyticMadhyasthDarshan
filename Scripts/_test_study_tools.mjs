/* Exercise the shipped annotation core and worker with browser API test doubles. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {webcrypto} from 'node:crypto';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const C = require('../Assets/reader/notes-core.js'), P = require('../Assets/reader/offline-policy.js');
const path = '/Studies/Test/Test.html', version = 'a'.repeat(64), origin = 'https://example.test';
const passage = {id:'p-one',heading:'section',text:'ज्ञान and jīvan 😀. A cited argument.'};
const anchor = C.makeAnchor(passage,0,18);
const note = {id:'test-note-one',revision:'revision-one',document:path,title:'Test',version,color:'yellow',quote:anchor.quote,note:'Private <img src=x onerror=alert(1)> thoughts.',created:'2026-09-06T00:00:00Z',updated:'2026-09-06T00:00:00Z',anchors:[anchor]};
assert(C.valid(note));
assert.deepEqual(C.parseBackup(C.backup([note])),[note]);
assert(C.markdown([note]).includes('pv=aaaaaaaaaaaaaaaa&section=section#p-one'));
assert(C.markdown([note]).includes(note.note));
assert.equal(C.resolve(anchor,[passage]).start,0);
assert.equal(C.resolve(anchor,[{...passage,id:'moved'}]).passage.id,'moved');
assert.equal(C.resolve(anchor,[{...passage,id:'moved'},{...passage,id:'duplicate'}]),null);
assert.equal(C.resolve(anchor,[{...passage,text:'Changed proposition.'}]),null);
assert.equal(C.resolve(anchor,[{...passage,id:'moved',heading:'other-section'}]),null);
assert.equal(C.resolve({quote:'word',prefix:'',suffix:'',id:'x',heading:'s'},[{id:'x',heading:'s',text:'word word'}]),null);
for (const bad of [{document:'/MySubmissions/index.html'},{document:'https://evil.test/x.html'},{version:'unknown'},{color:'url(evil)'},{anchors:[]},{note:'x'.repeat(12001)},{updated:'bad date'}]) assert.throws(() => C.parseBackup(C.backup([{...note,...bad}])));
assert.throws(() => C.parseBackup(JSON.stringify({format:'amd-study-notes',schema:2,notes:[note]})));
assert.throws(() => C.parseBackup(C.backup([note,note])));
assert.throws(() => C.limits(Array.from({length:201},() => note)));
assert.throws(() => C.limits(Array.from({length:2001},(_,i) => ({...note,document:`/Studies/S${i}/S.html`}))));
assert.throws(() => C.limits(Array.from({length:1000},(_,i) => ({...note,note:'x'.repeat(12000),document:`/Studies/S${i}/S.html`}))));
const polluted = JSON.parse(C.backup([note])); polluted.notes[0].unexpected = {html:'<script>'};
assert(!('unexpected' in C.parseBackup(JSON.stringify(polluted))[0]));

for (const bad of ['/api/notes','/Studies/MySubmissions.html','/Studies/Test/Test.pdf','/Studies/Other/figure.svg','https://evil.test/Assets/reader/reader.js','/Assets/reader/reader.js?token=secret','/Studies/Test/../../secret.png']) assert.equal(P.resource(bad,path,origin),false,bad);
assert(P.resource('/Assets/KaTeX/fonts/KaTeX_Main-Regular.woff2',path,origin));
assert(P.navigation(path+'?find=argument&pv=123&section=section',origin));
assert(!P.navigation(path+'?token=secret',origin));

// Actual worker event handlers, response hashing and transactional cache promotion.
const handlers = {}, storage = new Map(), fetched = [];
const absolute = key => new URL(typeof key === 'string' ? key : key.url || key.href,origin).href;
let failPut = false;
class Cache {
  data = new Map();
  async keys() { return [...this.data.keys()].map(url => ({url})); }
  async match(key) { return this.data.get(absolute(key))?.clone(); }
  async put(key,response) { if (failPut) throw new Error('QuotaExceededError'); this.data.set(absolute(key),response.clone()); }
  async delete(key) { return this.data.delete(absolute(key)); }
}
const caches = {async keys() { return [...storage.keys()]; },async open(name) { if (!storage.has(name)) storage.set(name,new Cache()); return storage.get(name); },async has(name) { return storage.has(name); },async delete(name) { return storage.delete(name); }};
const html = '<html lang="en"><h1>Study</h1></html>', notebook = '<html lang="en">Notebook</html>', asset = 'window.reader = true;';
const contents = new Map([[path,html],['/Studies/notebook.html',notebook],['/Assets/reader/reader.js?v=aaaaaaaaaaaaaaaa',asset]]);
const hash = async text => Buffer.from(await webcrypto.subtle.digest('SHA-256',new TextEncoder().encode(text))).toString('hex');
const bundle = {path,title:'Test',version,resources:await Promise.all([...contents].map(async ([url,body]) => ({url,bytes:Buffer.byteLength(body),sha256:await hash(body)})))};
let manifest = {schema:1,documents:[bundle]}, offline = false, badAsset = '', badKind = '', status = 200;
const fetch = async (request,options) => {
  const url = new URL(absolute(request)); fetched.push({path:url.pathname,options});
  if (offline) throw new TypeError('Network unavailable');
  if (url.pathname === '/Studies/offline-manifest.json') return new Response(JSON.stringify(manifest));
  const value = contents.get(url.pathname + url.search);
  let response = new Response(badAsset === url.pathname && badKind === 'hash' ? 'x'.repeat(value.length) : badAsset === url.pathname && badKind === 'oversize' ? value.repeat(100) : value,{status,headers:badAsset === url.pathname && badKind === 'private' ? {'Cache-Control':'private'} : {}});
  if (badAsset === url.pathname && badKind === 'redirect') Object.defineProperty(response,'redirected',{value:true});
  return response;
};
const self = {AMDOfflinePolicy:P,location:{origin},clients:{claim:async () => {},get:async () => ({url:origin+path})},addEventListener:(type,fn) => { handlers[type] = fn; }};
vm.runInNewContext(fs.readFileSync(new URL('../reader-sw.js',import.meta.url),'utf8'),{self,importScripts:() => {},caches,fetch,crypto:webcrypto,URL,Response,Headers,Uint8Array,TextDecoder,AbortController,setTimeout,clearTimeout});
async function message(type,requested=path,source=origin+path) {
  const output = []; let task;
  handlers.message({data:{type,path:requested},source:{url:source},ports:[{postMessage:data => output.push(data)}],waitUntil:p => { task=p; }});
  await task; return output.at(-1);
}
async function request(url,mode='navigate',method='GET') {
  let task; handlers.fetch({request:{url:new URL(url,origin).href,mode,method},clientId:'reader',respondWith:p => { task=p; }}); return task && await task;
}
assert.equal(await message('SAVE',path,'https://evil.test'),undefined);
assert((await message('SAVE','/api/private')).error);
assert.equal((await message('SAVE')).result.path,path);
assert(fetched.every(f => f.options.credentials === 'omit'));
const saved = (await message('LIST')).result[0]; assert(P.record(saved));
const committed = [...storage.keys()].sort();
for (const kind of ['hash','oversize','private','redirect']) {
  badAsset = '/Assets/reader/reader.js'; badKind=kind;
  assert((await message('SAVE')).error,kind);
  assert.deepEqual([...storage.keys()].sort(),committed,kind+' retains old cache and removes partial copy');
}
badAsset=''; failPut=true; assert((await message('SAVE')).error); failPut=false;
assert.deepEqual([...storage.keys()].sort(),committed);
manifest={schema:1,documents:[{...bundle,resources:[...bundle.resources,{url:'/api/private',bytes:4,sha256:version}]}]};
assert((await message('SAVE')).error); manifest={schema:1,documents:[bundle]};
offline=true;
assert((await (await request(path+'?find=Study&section=section&pv='+version.slice(0,16))).text()).includes('data-offline-copy'));
assert((await (await request('/Studies/notebook.html')).text()).includes('Notebook'));
assert.equal(await (await request('/Assets/reader/reader.js?v=aaaaaaaaaaaaaaaa','cors')).text(),asset);
assert.equal((await request('/Studies/Unsaved/Unsaved.html')).status,503);
assert.equal(await request('/api/session'),undefined);
assert.equal(await request('/Studies/my-submissions.html'),undefined);
assert.equal(await request(path,'navigate','POST'),undefined);
assert.equal(await request('https://evil.test'+path),undefined);
offline=false; status=404; assert.equal((await request(path)).status,404,'An online withdrawal must not serve an obsolete copy'); status=200;
const beforeFetch=fetched.length; assert.equal(await (await request('/Assets/reader/reader.js?v=aaaaaaaaaaaaaaaa','cors')).text(),asset); assert.equal(fetched.length,beforeFetch);
await caches.open('unrelated-app');
const concurrent = await Promise.all([message('SAVE'),message('SAVE')]); assert(concurrent.every(r => r.result));
assert.equal((await message('LIST')).result.length,1); assert.equal([...storage.keys()].filter(n => n.startsWith(P.PREFIX) && n!==P.REGISTRY).length,1);
assert.equal((await message('REMOVE')).error,undefined); assert.equal((await message('LIST')).result.length,0); assert(await caches.has('unrelated-app'));
console.log('Notes anchoring, backup limits and offline worker integrity/recovery contracts passed.');
