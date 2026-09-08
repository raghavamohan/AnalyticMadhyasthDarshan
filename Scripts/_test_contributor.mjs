import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const drafts = require('../Studies/portal/drafts.js');
const actionOperations = require('../Studies/portal/action-operations.js');
const source = await readFile(new URL('../infra/worker/src/operations.js',import.meta.url),'utf8');
const operations = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));

export function storageFixture() {
  const values = new Map(); let queue = Promise.resolve();
  const store = {
    get:async key => structuredClone(values.get(key)),
    put:async (key,value) => {values.set(key,structuredClone(value));},
    delete:async key => values.delete(key),
    transaction:action => {
      const result = queue.then(async () => {
        const before = structuredClone(values);
        try {return await action(store);} catch(error) {values.clear();for(const [k,v] of before) values.set(k,v);throw error;}
      }); queue = result.catch(() => {}); return result;
    },
  };
  return store;
}
test('draft identities isolate accounts, studies, artifact files and PR revisions', () => {
  const base={account:'Alice',kind:'submit',mode:'update',slug:'Study',artifact:'note',target:'Research-Note-One.md',pr:''};
  assert.equal(drafts.key(base),drafts.key({...base,account:'alice'}));
  const variants=[base,{...base,account:'bob'},{...base,slug:'Other'},{...base,artifact:'study'},
    {...base,target:'Research-Note-Two.md'},{...base,pr:'1'},{...base,pr:'2'},{...base,mode:'new'},
    {...base,target:'__new__',file:'Research-Note-A.md'},{...base,target:'__new__',file:'Research-Note-B.md'}];
  assert.equal(new Set(variants.map(drafts.key)).size,variants.length);
  assert.notEqual(drafts.key({...base,slug:'a|b',target:'c'}),drafts.key({...base,slug:'a',target:'b|c'}));
});
test('malformed backups fail before a transaction can overwrite any draft', () => {
  for (const data of [null,{content:{}},{presentation:{fileName:'../../x.pptx',contentBase64:'AA=='}},{source:{content:'old',sha:'unknown'}},{operation:{id:'bad',path:'/api/propose'}}])
    assert.throws(() => drafts.validate(data));
  assert.equal(drafts.validate({content:'# Safe text',author:'Contributor'}).content,'# Safe text');
});
test('dashboard action receipts are account-scoped and never retain transient credentials',() => {
  const values=new Map(), storage={
    getItem:key => values.get(key) ?? null,
    setItem:(key,value) => values.set(key,value),
    removeItem:key => values.delete(key),
  };
  const store=actionOperations.create(storage), id='123e4567-e89b-42d3-a456-426614174000';
  const operation={id,path:'/api/status-change',payload:{slug:'Test-Study',targetStatus:'released',reason:'',sourceSha:'a'.repeat(40)},created:'2026-09-08T00:00:00.000Z',retryAllowed:false,state:'inProgress'};
  store.save('Alice',operation);
  assert.deepEqual(store.load('alice'),operation);
  assert.equal(store.load('bob'),null);
  assert.throws(() => store.save('alice',{...operation,payload:{...operation.payload,turnstileToken:'secret'}}));
  assert.throws(() => store.save('alice',{...operation,path:'/api/submit'}));
  store.clear('ALICE');
  assert.equal(store.load('alice'),null);
});
test('receipt digest ignores refreshed Turnstile tokens and object field order, but binds all actual content',async () => {
  const one = await operations.digestPayload('/api/submit',{slug:'Study',content:'one',turnstileToken:'a'});
  assert.equal(one,await operations.digestPayload('/api/submit',{turnstileToken:'b',content:'one',slug:'Study'}));
  assert.notEqual(one,await operations.digestPayload('/api/submit',{slug:'Study',content:'two'}));
  assert.notEqual(one,await operations.digestPayload('/api/propose',{slug:'Study',content:'one'}));
});
test('all public contribution writes use receipts with deterministic recovery metadata',() => {
  assert.deepEqual([...operations.operationPaths].sort(),[
    '/api/delete-artifact','/api/propose','/api/revise','/api/status-change','/api/submit',
  ]);
  const id='123e4567-e89b-42d3-a456-426614174000', data={slug:'Test-Study'};
  assert.equal(operations.operationLabel('/api/propose',data),'study-proposal');
  assert.equal(operations.operationLabel('/api/revise',data),'new-study');
  assert.equal(operations.operationLabel('/api/status-change',data),'status-change');
  assert.equal(operations.operationLabel('/api/delete-artifact',data),'study-update');
  assert.equal(operations.operationBranchName('/api/submit',data,id),`submission-Test-Study-${id}`);
  assert.equal(operations.operationBranchName('/api/status-change',data,id),`status-Test-Study-${id}`);
  assert.equal(operations.operationBranchName('/api/delete-artifact',data,id),`deletion-Test-Study-${id}`);
  assert.deepEqual(operations.operationResource({id,phase:'uncertain',recoveryBranch:`status-Test-Study-${id}`}),{
    success:false,operationId:id,state:'uncertain',uncertain:true,retryAllowed:false,
    recoveryBranch:`status-Test-Study-${id}`,
    error:'This operation is being checked. Check its result; do not send a second copy.',
  });
});
test('concurrent duplicate receipts claim at most one execution',async () => {
  const store=storageFixture(), id=crypto.randomUUID();
  const claims=await Promise.all(Array.from({length:8},() => operations.claimOperation(store,id,'hash','/api/submit')));
  assert.equal(claims.filter(c => c.receipt).length,1);
  assert.equal(claims.filter(c => c.response?.status===409).length,7);
  const replayStates=await Promise.all(claims.filter(c => c.response).map(async c => (await c.response.clone().json()).state));
  assert.deepEqual(new Set(replayStates),new Set(['inProgress']));
  const changed=await operations.claimOperation(store,id,'different','/api/submit');
  assert.equal((await changed.response.json()).state,'uncertain');
  const other=await operations.claimOperation(store,crypto.randomUUID(),'other','/api/submit');
  assert.equal((await other.response.json()).operationId,id);
});
test('completed receipts replay the original response without executing again',async () => {
  const store=storageFixture(),id=crypto.randomUUID(), {receipt}=await operations.claimOperation(store,id,'hash','/api/propose');
  const body={success:true,issueNumber:12,url:'https://github.com/example/repo/issues/12'};
  const completed=await operations.finishOperation(store,receipt,Response.json(body),true);
  assert.equal(await store.get('active'),undefined);
  assert.deepEqual(await completed.json(),{...body,operationId:id,state:'complete',completed:true,retryAllowed:false,result:body});
  assert.deepEqual(await (await operations.claimOperation(store,id,'hash','/api/propose')).response.json(),{...body,operationId:id,state:'complete',completed:true,retryAllowed:false,result:body});
  assert.ok((await operations.claimOperation(store,crypto.randomUUID(),'other','/api/propose')).receipt);
});
test('failed validation releases the account; ambiguous GitHub writes keep the receipt locked',async () => {
  const store=storageFixture(), id=crypto.randomUUID(), {receipt}=await operations.claimOperation(store,id,'hash','/api/revise');
  await operations.finishOperation(store,receipt,Response.json({error:'stale source'},{status:409}),false);
  assert.equal(await store.get('active'),undefined);
  const next=await operations.claimOperation(store,crypto.randomUUID(),'next','/api/submit');
  const result=await operations.finishOperation(store,next.receipt,Response.json({error:'connection lost'},{status:502}),true);
  assert.equal((await result.json()).state,'uncertain');
  assert.equal(await store.get('active'),next.receipt.id);
  assert.equal((await operations.claimOperation(store,next.receipt.id,'next','/api/submit')).response.status,409);
  await operations.finishOperation(store,next.receipt,Response.json({success:true,number:45}),false);
  assert.equal(await store.get('active'),undefined);
});
test('account write quota publishes remaining capacity and an exact retry delay',async () => {
  const store=storageFixture();
  for (let index=0;index<30;index++) {
    const claim=await operations.claimOperation(store,crypto.randomUUID(),`hash-${index}`,'/api/propose');
    assert.ok(claim.receipt);
    assert.match(claim.rateLimitHeaders['RateLimit-Policy'],/account-write/);
    assert.match(claim.rateLimitHeaders.RateLimit,new RegExp(`r=${29-index}`));
    await operations.finishOperation(store,claim.receipt,Response.json({success:true}),false);
  }
  const limited=await operations.claimOperation(store,crypto.randomUUID(),'over-limit','/api/propose');
  assert.equal(limited.response.status,429);
  assert.match(limited.response.headers.get('RateLimit'),/r=0/);
  assert.match(limited.response.headers.get('Retry-After'),/^\d+$/);
});
