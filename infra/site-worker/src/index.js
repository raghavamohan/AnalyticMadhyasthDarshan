import RELEASE from './release.js';
import { servePdf } from './pdf.js';
import { REFERENCE_PDF_KEYS } from './generated-pdf-keys.js';

const references = new Set(REFERENCE_PDF_KEYS);
const fail = (status, text) => new Response(text, {status, headers:{'Cache-Control':'no-store','Content-Type':'text/plain; charset=utf-8'}});

function canonicalPath(pathname, files) {
  let key;
  try { key = decodeURIComponent(pathname); } catch (_) { return null; }
  if (key.includes('\\') || key.split('/').some(p => p === '.' || p === '..')) return null;
  if (files[key]) return key;
  if (files[key.replace(/\/$/,'') + '/index.html']) return key.replace(/\/$/,'') + '/index.html';
  if (files[key + '.html']) return key + '.html';
  return key;
}

function headersFor(record, revision, immutable) {
  return new Headers({'Content-Type':record.type,'Content-Length':String(record.bytes),
    'ETag':`"${record.sha256}"`,'X-AMD-Release':revision,'X-AMD-SHA256':record.sha256,
    'Cache-Control':immutable ? 'public, max-age=31536000, immutable, no-transform' : 'public, max-age=0, must-revalidate',
    'X-Content-Type-Options':'nosniff','Accept-Ranges':'bytes'});
}

function rangeFor(header, size) {
  if (!header) return [0,size-1];
  const match = /^bytes=(\d*)-(\d*)$/.exec(header);
  if (!match || (!match[1] && !match[2])) throw new Error('Invalid range');
  const start = match[1] ? Number(match[1]) : Math.max(0,size-Number(match[2]));
  const end = match[1] && match[2] ? Math.min(size-1,Number(match[2])) : size-1;
  if (start > end || start >= size || !Number.isSafeInteger(start) || !Number.isSafeInteger(end)) throw new Error('Invalid range');
  return [start,end];
}

async function staticResponse(request, env, key, record, revision, historical) {
  const headers = headersFor(record,revision,new URL(request.url).searchParams.has('r'));
  const ifMatch = request.headers.get('If-Match');
  if (ifMatch && !ifMatch.split(',').some(e=>e.trim()===headers.get('ETag') || e.trim()==='*')) return new Response(null,{status:412,headers});
  if ((request.headers.get('If-None-Match') || '').split(',').some(e => e.trim().replace(/^W\//,'') === headers.get('ETag') || e.trim() === '*')) return new Response(null,{status:304,headers});
  if (request.method === 'HEAD') return new Response(null,{headers});
  if (historical) {
    let range;
    if (request.headers.has('Range') && (!request.headers.has('If-Range') || request.headers.get('If-Range')===headers.get('ETag'))) {
      try {const [start,end]=rangeFor(request.headers.get('Range'),record.bytes);range={offset:start,length:end-start+1};}
      catch (_) {return new Response(null,{status:416,headers:{'Content-Range':`bytes */${record.bytes}`}});}
    }
    const object = await env.GENERATED_PDFS.get(record.key,range?{range}:undefined);
    if (!object) return fail(404,'This saved release is no longer retained.');
    if (object.range) {
      const {offset,length}=object.range;
      headers.set('Content-Length',String(length));
      headers.set('Content-Range',`bytes ${offset}-${offset+length-1}/${record.bytes}`);
      return new Response(object.body,{status:206,headers});
    }
    return new Response(object.body,{headers});
  }
  if (!record.parts) {
    const url = new URL(request.url); url.pathname = key; url.search = '';
    const assetHeaders = new Headers(request.headers);
    for (const name of ['If-Match','If-None-Match','If-Modified-Since','If-Unmodified-Since']) assetHeaders.delete(name);
    if (assetHeaders.has('If-Range')) {
      if (assetHeaders.get('If-Range')!==headers.get('ETag')) assetHeaders.delete('Range');
      assetHeaders.delete('If-Range');
    }
    const response = await env.ASSETS.fetch(new Request(url,{method:request.method,headers:assetHeaders}));
    if (!response.ok) return fail(503,'The static release is incomplete.');
    if (response.status === 206) {
      headers.set('Content-Range',response.headers.get('Content-Range'));
      headers.set('Content-Length',response.headers.get('Content-Length'));
    }
    return new Response(response.body,{status:response.status,headers});
  }
  let start,end;
  const range = request.headers.get('Range') && (!request.headers.has('If-Range') || request.headers.get('If-Range')===headers.get('ETag')) ? request.headers.get('Range') : null;
  try { [start,end] = rangeFor(range,record.bytes); }
  catch (_) { return new Response(null,{status:416,headers:{'Content-Range':`bytes */${record.bytes}`}}); }
  const size=16*1024*1024, first=Math.floor(start/size), last=Math.floor(end/size);
  let index=first;
  const stream = new ReadableStream({async pull(controller) {
    try {
      if (index<=last) {
        const url=new URL(record.parts[index],request.url);
        const part=await env.ASSETS.fetch(url);
        if (!part.ok) throw new Error('Missing reference segment');
        const bytes=new Uint8Array(await part.arrayBuffer());
        controller.enqueue(bytes.subarray(index===first?start-index*size:0,index===last?end-index*size+1:bytes.length));
        index++;
      }
      if (index>last) controller.close();
    } catch(error) { controller.error(error); }
  }});
  headers.set('Content-Length',String(end-start+1));
  if (range) headers.set('Content-Range',`bytes ${start}-${end}/${record.bytes}`);
  return new Response(stream,{status:range?206:200,headers});
}

export async function handle(request, env, current = RELEASE) {
  const url=new URL(request.url);
  if (url.pathname.startsWith('/api/')) return fetch(request);
  if (url.pathname === '/.well-known/publication.json') {
    return new Response(request.method==='HEAD'?null:JSON.stringify({schema:1,revision:current.revision,sourceSha:current.sourceSha,studies:current.studies}),
      {headers:{'Content-Type':'application/json','Cache-Control':'no-store','X-AMD-Release':current.revision,'Access-Control-Allow-Origin':'*'}});
  }
  let manifest=current;
  const revision=url.searchParams.get('r');
  if (revision && !/^[a-f0-9]{64}$/.test(revision)) return fail(400,'Invalid release');
  if (revision && revision !== current.revision && !url.pathname.startsWith('/References/')) {
    const object=await env.GENERATED_PDFS.get(`site/releases/${revision}.json`);
    if (!object) return fail(404,'Release is no longer retained');
    manifest=await object.json();
    if (manifest.schema!==1 || manifest.revision!==revision) return fail(503,'Invalid release manifest');
  }
  const key=canonicalPath(url.pathname,manifest.files);
  if (!key) return fail(400,'Invalid path');
  if (references.has(key.slice(1))) return servePdf(request,env.REFERENCE_PDFS,key.slice(1));
  const record=manifest.files[key];
  if (!record || !/^[a-f0-9]{64}$/.test(record.sha256) || record.key!==`site/objects/${record.sha256}` || (manifest!==current && !record.archive)) return fail(404,'Not published');
  if (!['GET','HEAD','OPTIONS'].includes(request.method)) return fail(405,'Method Not Allowed');
  if (record.archive && key.endsWith('.pdf')) {
    const response=await servePdf(request,env.GENERATED_PDFS,record.key);
    const headers=new Headers(response.headers);
    headers.set('X-AMD-Release',manifest.revision);
    headers.set('Cache-Control',revision?'public, max-age=31536000, immutable, no-transform':'public, max-age=0, must-revalidate');
    return new Response(response.body,{status:response.status,headers});
  }
  if (request.method==='OPTIONS') return new Response(null,{status:204,headers:{Allow:'GET, HEAD, OPTIONS'}});
  return staticResponse(request,env,key,record,manifest.revision,manifest!==current);
}

export default {fetch:(request,env)=>handle(request,env)};
export {canonicalPath,rangeFor};
