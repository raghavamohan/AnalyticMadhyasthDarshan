import assert from 'node:assert/strict';
import {handle,rangeFor} from './index.js';

const checksum='a'.repeat(64), revision='b'.repeat(64), old='c'.repeat(64);
const record={sha256:checksum,bytes:3,key:`site/objects/${checksum}`,type:'text/html',archive:true};
const current={schema:1,revision,sourceSha:'d'.repeat(40),studies:{A:{status:'released'}},files:{'/Studies/A/A.html':record}};
const historical={...current,revision:old,studies:{A:{status:'draft'}},files:{'/Studies/A/A.html':record,'/Studies/Retired/Retired.html':record}};
let assetReads=0, objectReads=0;
const env={ASSETS:{async fetch(request){assetReads++;return new Response('new');}},GENERATED_PDFS:{async get(key,options){
  objectReads++;
  if(key===`site/releases/${old}.json`)return {json:async()=>historical};
  if(key===record.key){const range=options?.range;return {body:range?'l':'old',...(range?{range}:{})};}
  return null;
}}};
const get=(path,init)=>handle(new Request('https://example.test'+path,init),env,current);
let response=await get('/Studies/A/A.html');
assert.equal(await response.text(),'new');assert.equal(response.headers.get('X-AMD-Release'),revision);
assert.match(response.headers.get('Cache-Control'),/must-revalidate/);
assert.doesNotMatch(response.headers.get('Cache-Control'),/no-transform/);
response=await get('/Studies/A/A.html?r='+revision);
assert.equal(await response.text(),'new');
assert.match(response.headers.get('Cache-Control'),/immutable, no-transform/);
response=await get('/Studies/A/A.html?r='+old);
assert.equal(await response.text(),'old');assert.equal(response.headers.get('X-AMD-Release'),old);
assert.match(response.headers.get('Cache-Control'),/immutable/);
assert.match(response.headers.get('Cache-Control'),/no-transform/);
assert.equal((await get('/Studies/Planned/Planned.html')).status,404);
assert.equal((await get('/Studies/Retired/Retired.html')).status,404);
assert.equal(await (await get('/Studies/Retired/Retired.html?r='+old)).text(),'old');
assert.equal((await get('/Studies/A/A.html?r=invalid')).status,400);
assert.equal((await get('/Studies/A/A.html?r='+'e'.repeat(64))).status,404);
let before=assetReads+objectReads;
response=await get('/Studies/A/A.html',{method:'HEAD'});
assert.equal(await response.text(),'');assert.equal(response.headers.get('Content-Length'),'3');
assert.equal(before,assetReads+objectReads);
assert.equal((await get('/Studies/A/A.html',{headers:{'If-None-Match':`W/"${checksum}"`}})).status,304);
assert.equal((await get('/Studies/A/A.html',{headers:{'If-Match':'"bad"'}})).status,412);
response=await get('/Studies/A/A.html?r='+old,{headers:{Range:'bytes=1-1'}});
assert.equal(response.status,206);assert.equal(response.headers.get('Content-Range'),'bytes 1-1/3');assert.equal(await response.text(),'l');
assert.equal((await get('/Studies/A/A.html?r='+old,{headers:{Range:'bytes=9-'}})).status,416);
assert.deepEqual(rangeFor('bytes=-2',3),[1,2]);assert.throws(()=>rangeFor('bytes=1-0',3));
const publication=await (await get('/.well-known/publication.json')).json();
assert.equal(publication.sourceSha,current.sourceSha);assert.equal(publication.studies.A.status,'released');
env.ASSETS.fetch=async()=>new Response('absent',{status:404});
assert.equal((await get('/Studies/A/A.html')).status,503);
// New packaging redirects canonical HTML once, then serves stable bytes at the
// selected release. Retained legacy manifests still use their baked-in pins.
current.deliveryVersion=2;
response=await get('/Studies/A/A.html?find=term');
assert.equal(response.status,302);
assert.equal(new URL(response.headers.get('Location')).searchParams.get('r'),revision);
assert.equal(new URL(response.headers.get('Location')).searchParams.get('find'),'term');
assert.equal(response.headers.get('Cache-Control'),'no-store');
const asset={...record,type:'text/css'};
env.GENERATED_PDFS.get=async key=>{
  if(key===`site/assets/Assets/old.css/${checksum}.json`)return {json:async()=>({schema:1,path:'/Assets/old.css',record:asset})};
  if(key===record.key)return {body:'old'};
  return null;
};
response=await get('/Assets/old.css?v='+checksum);
assert.equal(await response.text(),'old');
assert.match(response.headers.get('Cache-Control'),/immutable/);
assert.equal((await get('/Assets/other.js?v='+checksum)).status,404,'Content hashes cannot change the path or MIME type of an asset');
assert.equal((await get('/Studies/A/A.html?v='+checksum)).status,400);
console.log('Site Worker revision, range, cache, retirement and incomplete-release tests passed.');
