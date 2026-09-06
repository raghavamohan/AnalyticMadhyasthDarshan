import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const drafts = require('../Studies/portal/drafts.js');
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
test('receipt digest ignores refreshed Turnstile tokens and object field order, but binds all actual content',async () => {
  const one = await operations.digestPayload('/api/submit',{slug:'Study',content:'one',turnstileToken:'a'});
  assert.equal(one,await operations.digestPayload('/api/submit',{turnstileToken:'b',content:'one',slug:'Study'}));
  assert.notEqual(one,await operations.digestPayload('/api/submit',{slug:'Study',content:'two'}));
  assert.notEqual(one,await operations.digestPayload('/api/propose',{slug:'Study',content:'one'}));
});
test('concurrent duplicate receipts claim at most one execution',async () => {
  const store=storageFixture(), id=crypto.randomUUID();
  const claims=await Promise.all(Array.from({length:8},() => operations.claimOperation(store,id,'hash','/api/submit')));
  assert.equal(claims.filter(c => c.receipt).length,1);
  assert.equal(claims.filter(c => c.response?.status===409).length,7);
  const changed=await operations.claimOperation(store,id,'different','/api/submit');
  assert.equal((await changed.response.json()).uncertain,true);
  const other=await operations.claimOperation(store,crypto.randomUUID(),'other','/api/submit');
  assert.equal((await other.response.json()).operationId,id);
});
test('completed receipts replay the original response without executing again',async () => {
  const store=storageFixture(),id=crypto.randomUUID(), {receipt}=await operations.claimOperation(store,id,'hash','/api/propose');
  const body={success:true,issueNumber:12,url:'https://github.com/example/repo/issues/12'};
  await operations.finishOperation(store,receipt,Response.json(body),true);
  assert.equal(await store.get('active'),undefined);
  assert.deepEqual(await (await operations.claimOperation(store,id,'hash','/api/propose')).response.json(),body);
  assert.ok((await operations.claimOperation(store,crypto.randomUUID(),'other','/api/propose')).receipt);
});
test('failed validation releases the account; ambiguous GitHub writes keep the receipt locked',async () => {
  const store=storageFixture(), id=crypto.randomUUID(), {receipt}=await operations.claimOperation(store,id,'hash','/api/revise');
  await operations.finishOperation(store,receipt,Response.json({error:'stale source'},{status:409}),false);
  assert.equal(await store.get('active'),undefined);
  const next=await operations.claimOperation(store,crypto.randomUUID(),'next','/api/submit');
  const result=await operations.finishOperation(store,next.receipt,Response.json({error:'connection lost'},{status:502}),true);
  assert.equal((await result.json()).uncertain,true);
  assert.equal(await store.get('active'),next.receipt.id);
  assert.equal((await operations.claimOperation(store,next.receipt.id,'next','/api/submit')).response.status,409);
  await operations.finishOperation(store,next.receipt,Response.json({success:true,number:45}),false);
  assert.equal(await store.get('active'),undefined);
});
