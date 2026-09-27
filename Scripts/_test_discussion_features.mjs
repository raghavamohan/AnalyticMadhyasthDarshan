import assert from 'node:assert/strict';
import test from 'node:test';
import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
import worker from '../infra/discussions-worker/src/index.js';
import {insertComment} from '../infra/discussions-worker/src/db.js';
import {createSession} from '../infra/discussions-worker/src/auth.js';
import {getPreferences,setPreferences,unsubscribeToken,unsubscribe,deliverReplies} from '../infra/discussions-worker/src/notifications.js';
import {reportComment} from '../infra/discussions-worker/src/moderation.js';

function fixture() {
  const sql = new DatabaseSync(':memory:');
  for (const file of ['0001_init.sql','0002_sessions.sql','0003_magic_return.sql','0004_notifications_reports.sql'])
    sql.exec(readFileSync(new URL('../infra/discussions-worker/migrations/'+file,import.meta.url),'utf8'));
  const db = {prepare(source) {
    const statement = sql.prepare(source);
    const bound = (...args) => ({
      first:async()=>statement.get(...args) || null,
      all:async()=>({results:statement.all(...args)}),
      run:async()=>({meta:{changes:Number(statement.run(...args).changes)}}),
    });
    return {...bound(),bind:bound};
  }, async batch(statements) {
    sql.exec('BEGIN');
    try { const values=[]; for (const statement of statements) values.push(await statement.run()); sql.exec('COMMIT'); return values; }
    catch(error) {sql.exec('ROLLBACK');throw error;}
  }};
  sql.exec("INSERT INTO users (id,email,display_name,created_at) VALUES ('alice','alice@example.org','Alice',1),('bob','bob@example.org','Bob',1),('admin','admin@example.org','Admin',1); INSERT INTO threads (slug,title,created_at) VALUES ('Test','Test',1)");
  const env = {DB:db,SESSION_SECRET:'discussion-test-secret',SITE_ORIGIN:'https://analyticmadhyasthdarshan.org',ADMIN_EMAILS:'admin@example.org',RESEND_API_KEY:'test-only'};
  return {db,sql,env};
}
async function comment(db,id,userId,parentId=null) {return insertComment(db,{id,userId,parentId,threadSlug:'Test',body:'Comment '+id});}
async function request(env,path,{user='alice',method='GET',body}={}) {
  const token = await createSession(env,{userId:user,email:user+'@example.org',displayName:user});
  return worker.fetch(new Request(env.SITE_ORIGIN+path,{method,headers:{Origin:env.SITE_ORIGIN,'Content-Type':'application/json',Cookie:'amd_discuss_session='+token},...(body===undefined ? {} : {body:JSON.stringify(body)})}),env);
}
test('reply preferences default off, are account scoped and require boolean consent',async()=>{
  const {db,sql,env}=fixture();
  assert.deepEqual(await getPreferences(db,'alice'),{replyEmail:false});
  assert.equal((await request(env,'/api/discuss-auth/preferences',{method:'POST',body:{replyEmail:'yes'}})).status,400);
  assert.equal((await request(env,'/api/discuss-auth/preferences',{method:'POST',body:{replyEmail:true}})).status,200);
  assert.deepEqual(await getPreferences(db,'alice'),{replyEmail:true});
  const epoch=sql.prepare("SELECT epoch FROM discussion_preferences WHERE user_id='alice'").get().epoch;
  await setPreferences(db,'alice',true);
  assert.equal(sql.prepare("SELECT epoch FROM discussion_preferences WHERE user_id='alice'").get().epoch,epoch);
  assert.deepEqual(await getPreferences(db,'bob'),{replyEmail:false});
  sql.close();
});
test('reply outbox enrolls only opted-in direct parent and excludes self replies',async()=>{
  const {db,sql}=fixture(); await comment(db,'parent','alice');
  await comment(db,'off','bob','parent');
  assert.equal(sql.prepare('SELECT COUNT(*) AS n FROM reply_outbox').get().n,0);
  await setPreferences(db,'alice',true);
  await comment(db,'self','alice','parent'); await comment(db,'reply','bob','parent');
  assert.equal(sql.prepare('SELECT COUNT(*) AS n FROM reply_outbox').get().n,1);
  assert.equal(sql.prepare('SELECT recipient_id FROM reply_outbox').get().recipient_id,'alice');
  sql.close();
});
test('outbox failure does not lose comment; retry uses stable payload/key and parallel claims send once',async()=>{
  const {db,sql,env}=fixture(); await setPreferences(db,'alice',true); await comment(db,'parent','alice'); await comment(db,'reply','bob','parent');
  const previous=globalThis.fetch,calls=[];
  globalThis.fetch=async(url,options)=>{assert.equal(url,'https://api.resend.com/emails');calls.push(options); if(calls.length===1) throw new Error('lost response'); return Response.json({id:'mail-id'});};
  try {
    const now=Date.now()+1;
    await deliverReplies(env,now); assert.equal(sql.prepare("SELECT state FROM reply_outbox").get().state,'pending');
    assert.equal(sql.prepare("SELECT COUNT(*) AS n FROM comments WHERE id='reply'").get().n,1);
    await Promise.all([deliverReplies(env,now+300000),deliverReplies(env,now+300000)]);
    assert.equal(calls.length,2); assert.equal(calls[0].body,calls[1].body);
    assert.equal(calls[0].headers['Idempotency-Key'],calls[1].headers['Idempotency-Key']);
    assert.equal(sql.prepare('SELECT state,payload FROM reply_outbox').get().state,'sent');
    assert.equal(sql.prepare('SELECT payload FROM reply_outbox').get().payload,null);
    assert.equal(sql.prepare('SELECT provider_id FROM reply_outbox').get().provider_id,'mail-id');
    assert.equal(JSON.parse(calls[0].body).text.includes('Comment reply'),false);
  } finally {globalThis.fetch=previous;sql.close();}
});
test('unsubscribe GET has no effect; POST requires valid signed token and cannot disable newer opt-in',async()=>{
  const {db,sql,env}=fixture(); await setPreferences(db,'alice',true);
  const epoch=sql.prepare("SELECT epoch FROM discussion_preferences WHERE user_id='alice'").get().epoch;
  const token=await unsubscribeToken(env,'alice',epoch);
  const page=await worker.fetch(new Request(env.SITE_ORIGIN+'/api/discuss-auth/unsubscribe#token='+token),env);
  assert.equal(page.status,200); assert.match(await page.text(),/Disable reply emails/);
  assert.deepEqual(await getPreferences(db,'alice'),{replyEmail:true});
  assert.equal(await unsubscribe(db,env,token+'bad'),false);
  assert.equal(await unsubscribe(db,env,token),true); assert.deepEqual(await getPreferences(db,'alice'),{replyEmail:false});
  await setPreferences(db,'alice',true); await unsubscribe(db,env,token); assert.deepEqual(await getPreferences(db,'alice'),{replyEmail:true});
  const unsafe=await worker.fetch(new Request(env.SITE_ORIGIN+'/api/discuss-auth/unsubscribe',{method:'POST',headers:{Origin:'https://evil.example','Content-Type':'application/json'},body:JSON.stringify({token})}),env);
  assert.equal(unsafe.status,403);sql.close();
});
test('hidden comments or withdrawn consent cancel mail; expired uncertain jobs are never resent',async()=>{
  const {db,sql,env}=fixture(); await setPreferences(db,'alice',true); await comment(db,'parent','alice'); await comment(db,'reply','bob','parent');
  const previous=globalThis.fetch; globalThis.fetch=()=>{throw new Error('No email allowed');};
  try {
    await setPreferences(db,'alice',false);await deliverReplies(env,Date.now()+1);
    assert.equal(sql.prepare('SELECT state FROM reply_outbox').get().state,'cancelled');
    await setPreferences(db,'alice',true); await comment(db,'hidden','bob','parent');
    sql.exec("UPDATE comments SET status='hidden' WHERE id='hidden'");await deliverReplies(env,Date.now()+1);
    assert.equal(sql.prepare("SELECT state FROM reply_outbox WHERE comment_id='hidden'").get().state,'cancelled');
    await comment(db,'old','bob','parent');sql.exec("UPDATE reply_outbox SET first_attempt=1 WHERE comment_id='old'");await deliverReplies(env);
    assert.equal(sql.prepare("SELECT state FROM reply_outbox WHERE comment_id='old'").get().state,'uncertain');
  } finally {globalThis.fetch=previous;sql.close();}
});
test('reports are deduplicated, quota bounded and private; resolution does not hide comments',async()=>{
  const {db,sql,env}=fixture();await comment(db,'parent','bob');
  const path='/api/discussions/Test/comments/parent/report';
  assert.equal((await request(env,path,{method:'POST',body:{reason:'Review this'}})).status,201);
  assert.equal((await request(env,path,{method:'POST',body:{reason:'Repeated'}})).status,200);
  assert.equal(sql.prepare('SELECT COUNT(*) AS n FROM discussion_reports').get().n,1);
  assert.equal((await request(env,path,{user:'bob',method:'POST',body:{reason:'Own'}})).status,400);
  assert.equal((await request(env,'/api/discussions/reports')).status,403);
  const admin=await request(env,'/api/discussions/reports',{user:'admin'}); assert.equal(admin.status,200);
  const report=(await admin.json()).reports[0];assert.equal('reporter_id' in report,false);
  assert.equal((await request(env,'/api/discussions/reports/'+report.id+'/resolve',{user:'admin',method:'POST',body:{}})).status,200);
  assert.equal(sql.prepare("SELECT status FROM comments WHERE id='parent'").get().status,'visible');
  for(let i=0;i<10;i++){await comment(db,'c'+i,'bob');await reportComment(db,'alice','c'+i,'Test','Reason');}
  assert.equal(sql.prepare("SELECT COUNT(*) AS n FROM discussion_reports WHERE reporter_id='alice'").get().n,10);
  sql.close();
});
