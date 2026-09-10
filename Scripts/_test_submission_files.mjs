import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import test from 'node:test';

const modulePath = fileURLToPath(new URL('../infra/worker/src/submission-files.js', import.meta.url));
const files = await import('data:text/javascript;base64,' + Buffer.from(await readFile(modulePath, 'utf8')).toString('base64'));
const artifact = {artifactType:'note', filePath:'Applications/A/Technical-Note-One.md',fileName:'Technical-Note-One.md'};
const svg = {fileName:'diagram.svg',contentBase64:Buffer.from('<svg xmlns="http://www.w3.org/2000/svg"><image href="detail.png"/></svg>').toString('base64')};
const version = 'a'.repeat(40);

test('figure bundles stay with their applied parent and preserve version proofs', () => {
  const result = files.buildSupplementaryFiles({assets:[{...svg,sourceSha:version}]},artifact);
  assert.equal(result[0].filePath,'Applications/A/diagram.svg');
  assert.equal(result[0].sourceSha,version);
  assert.equal(result[0].encodedContent,svg.contentBase64);
});

test('attachments reject traversal, duplicates, active SVG and malformed raster before writes', () => {
  for (const asset of [{...svg,fileName:'../A.svg'}, {...svg,fileName:'A.svg:stream'},
    {...svg,fileName:'A.html'}, {...svg,fileName:'image.png'}, null,
    {...svg,contentBase64:Buffer.from('<svg onload="alert(1)"/>').toString('base64')},
    {...svg,contentBase64:Buffer.from('<svg><script>alert(1)</script></svg>').toString('base64')}]) {
    assert.throws(() => files.buildSupplementaryFiles({assets:[asset]},artifact), {status:400});
  }
  assert.throws(() => files.buildSupplementaryFiles({assets:[svg,svg]},artifact), {status:400});
  assert.throws(() => files.buildSupplementaryFiles({assets:Array(21).fill(svg)},artifact), {status:400});
});

test('presenter attachment accompanies one PPTX and preserves Unicode Markdown', () => {
  const deck = {artifactType:'presentation',filePath:'Studies/A/Deck.pptx',fileName:'Deck.pptx'};
  const presenter = {fileName:'Presenters-Companion-Deck.md',content:'# Slide 1\r\n\r\n## Delivering the slide\r\nमानव'};
  const result = files.buildSupplementaryFiles({presenter},deck);
  assert.equal(result.length,1);
  assert.equal(Buffer.from(result[0].encodedContent,'base64').toString('utf8'),'# Slide 1\n\n## Delivering the slide\nमानव\n');
  assert.throws(() => files.buildSupplementaryFiles({presenter},artifact),{status:400});
});

test('existing attachments reject stale or missing proofs before writing', async () => {
  let writes = 0;
  const operations = files.submissionFileOperations(async (_path,method) => {
    if (method === 'GET') return {sha:version}; writes++;
  }, (provided,current) => { if (provided !== current) throw Object.assign(new Error('stale'),{status:409}); });
  const file = files.buildSupplementaryFiles({assets:[svg]},artifact)[0];
  await assert.rejects(operations.checkSupplementaryVersion(file,'head',{}),{status:409});
  assert.equal(writes,0);
  file.sourceSha = version;
  await operations.checkSupplementaryVersion(file,'head',{});
  await operations.putSupplementaryFile(file,'submission',{});
  assert.equal(writes,1);
});

test('presenter registration is same-study, unique and idempotent', async () => {
  let manifest = {schema:1,companions:[]}, writes = 0;
  const encode = value => ({sha:version,content:Buffer.from(JSON.stringify(value)).toString('base64')});
  const ops = files.submissionFileOperations(async (path,method,data) => {
    if (method === 'PUT') { writes++;manifest=JSON.parse(Buffer.from(data.content,'base64'));return {}; }
    if (path.includes('presentation-pipeline')) return encode({decks:[{id:'a',source:'Studies/A/Deck.pptx'}]});
    return encode(manifest);
  },()=>{});
  const source = {artifactType:'presenter',fileName:'Presenters-Companion-Deck.md',filePath:'Studies/A/Presenters-Companion-Deck.md'};
  await ops.checkPresenterRegistration(source,{deckFileName:'Deck.pptx'},'head',{});
  assert.equal(writes,0);
  await ops.ensurePresenterManifested(source,{deckFileName:'Deck.pptx'},'branch',{});
  await ops.ensurePresenterManifested(source,{deckFileName:'Deck.pptx'},'branch',{});
  assert.equal(writes,1);
  await assert.rejects(ops.checkPresenterRegistration({...source,fileName:'Presenters-Companion-Other.md'},{deckFileName:'Deck.pptx'},'head',{}),{status:400});
  await assert.rejects(ops.checkPresenterRegistration({...source,filePath:'Applications/B/Presenters-Companion-Deck.md'},{deckFileName:'Deck.pptx'},'head',{}),{status:400});
});
