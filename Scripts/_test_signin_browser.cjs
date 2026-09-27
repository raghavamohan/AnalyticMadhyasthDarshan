/* Shipped sign-in UI against isolated HTTP fixtures; no mail or GitHub writes. */
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), http = require('node:http');
const puppeteer = require('puppeteer'), chrome = require('./_chrome');
const root = path.resolve(__dirname, '..');
const useWebKit = process.argv.includes('--webkit');
const mobileWebKit = useWebKit && process.argv.includes('--mobile');
const navigation = {waitUntil:useWebKit ? 'networkidle' : 'networkidle0'};

(async () => {
  const source = fs.readFileSync(path.join(root,'infra/discussions-worker/src/confirm.js'),'utf8');
  const {confirmationPage} = await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
  let viewer = {loggedIn:false}, posts = 0, confirmations = 0, expired = false;
  let replyEmail = false, reports = [], reportWrites = 0;
  const server = http.createServer(async (req,res) => {
    const url = new URL(req.url, 'http://localhost');
    if (url.pathname === '/api/discuss-auth/verify') {
      const response = confirmationPage();
      response.headers.forEach((v,k) => res.setHeader(k,v));
      return res.end(await response.text());
    }
    if (url.pathname === '/api/discuss-auth/unsubscribe' && req.method === 'GET') {
      const response = confirmationPage(true); response.headers.forEach((v,k)=>res.setHeader(k,v)); return res.end(await response.text());
    }
    if (url.pathname.startsWith('/api/')) {
      res.setHeader('Content-Type','application/json'); res.setHeader('Cache-Control','private, no-store');
      if (url.pathname === '/api/discuss-auth/confirm') {
        let body=''; for await (const chunk of req) body+=chunk;
        assert.equal(JSON.parse(body).token,'fixture-token'); confirmations++;
        viewer={loggedIn:true,userId:'alice',displayName:'Alice'};
        return res.end(JSON.stringify({success:true,returnTo:`http://127.0.0.1:${server.address().port}/Studies/Nature-Of-Time/discussion.html`}));
      }
      if (url.pathname === '/api/discuss-auth/me') return res.end(JSON.stringify(viewer));
      if (url.pathname === '/api/discuss-auth/preferences') {
        if (req.method === 'POST') {let body='';for await(const chunk of req) body+=chunk; replyEmail=JSON.parse(body).replyEmail;}
        return res.end(JSON.stringify({replyEmail}));
      }
      if (url.pathname === '/api/discuss-auth/unsubscribe') {replyEmail=false;return res.end('{"success":true}');}
      if (url.pathname.endsWith('/report')) {
        let body='';for await(const chunk of req) body+=chunk;
        reports.push({id:'report',commentId:'parent',reason:JSON.parse(body).reason,slug:'Nature-Of-Time',body:'A question',authorName:'Reader',status:'visible',sourceUpdatedAt:1}); reportWrites++;
        return res.end('{"success":true}');
      }
      if (url.pathname.endsWith('/resolve')) {reports=[];return res.end('{"success":true}');}
      if (url.pathname === '/api/discussions/reports') return res.end(JSON.stringify({reports,meta:{hasMore:false}}));
      if (url.pathname === '/api/discuss-auth/logout') {viewer={loggedIn:false};return res.end('{"success":true}');}
      if (req.method === 'POST' && url.pathname.endsWith('/comments')) {
        if (expired) {res.statusCode=401;return res.end('{"message":"Your discussion session expired."}');}
        posts++; return res.end('{"success":true}');
      }
      if (url.pathname.startsWith('/api/discussions/')) return res.end(JSON.stringify({viewer,comments:[{id:'parent',authorName:'Reader',body:'A question',createdAt:1,updatedAt:1}],meta:{hasMore:false}}));
      return res.end('{}');
    }
    try {
      const file = path.resolve(root, '.'+decodeURIComponent(url.pathname));
      if (!file.startsWith(root+path.sep)) {res.statusCode=403;return res.end();}
      res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.svg':'image/svg+xml'})[path.extname(file)] || 'application/octet-stream');
      let bytes = fs.readFileSync(file);
      if (url.pathname.endsWith('/discussion.html')) bytes=Buffer.from(bytes.toString().replace('https://amd-discussions.raghavamohan.workers.dev',origin));
      if (url.pathname === '/Studies/submit.html') {
        let html=bytes.toString().replace('<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>','');
        const harness=fs.readFileSync(path.join(root,'Scripts/_test_contributor_harness.js'),'utf8');
        html=html.replace(/<script src="portal\/drafts\.js[^\"]*"><\/script>/,match=>'<script>'+harness.replace(/<\/script/gi,'<\\/script')+'</script>'+match);
        bytes=Buffer.from(html);
      }
      res.end(bytes);
    } catch {res.statusCode=404;res.end();}
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const origin=`http://127.0.0.1:${server.address().port}`;
  let browser, page, stage = 'launch';
  try {
    if (useWebKit) browser=await require('playwright').webkit.launch();
    else {
      browser=await puppeteer.launch(chrome.puppeteerLaunchOptions(chrome.resolveChromeExecutable()));
      await chrome.assertPinnedChrome(browser);
    }
    page=await browser.newPage(mobileWebKit ? {isMobile:true,hasTouch:true,deviceScaleFactor:3,viewport:{width:390,height:900}} : undefined); const errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    page.on('dialog',dialog=>dialog.accept());
    if (useWebKit) await page.route('**/*',route=>route.request().url().startsWith(origin+'/') || /^(data|blob):/.test(route.request().url()) ? route.continue() : route.abort());
    else {
      await page.setRequestInterception(true);
      page.on('request',request=>request.url().startsWith(origin+'/') || /^(data|blob):/.test(request.url()) ? request.continue() : request.abort());
    }
    const discussion=origin+'/Studies/Nature-Of-Time/discussion.html';
    for (const width of mobileWebKit ? [390] : [1280,390]) {
      stage = 'discussion guest recovery '+width;
      viewer={loggedIn:false};
      if (useWebKit) await page.setViewportSize({width,height:900});
      else await page.setViewport({width,height:900});
      await page.goto(discussion,navigation);
      await page.waitForSelector('#comment-panel:not(.hidden)');
      await page.type('#comment-form textarea', 'Before email sign-in '+width);
      await page.reload(navigation);
      assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'Before email sign-in '+width);
      // Scanner-like navigation executes no confirmation request.
      const before=confirmations;
      stage = 'confirmation '+width;
      await page.goto(origin+'/api/discuss-auth/verify#token=fixture-token',navigation);
      assert.equal(confirmations,before); assert.equal(posts,0);
      assert.equal(new URL(page.url()).hash,'');
      await page.focus('#confirm'); assert.equal(await page.evaluate(()=>document.activeElement.id),'confirm');
      await Promise.all([page.waitForNavigation(navigation),page.keyboard.press('Enter')]);
      assert.equal(confirmations,before+1); assert.equal(posts,0);
      stage = 'discussion account recovery '+width;
      assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'');
      await page.click('#discussion-draft-list button');
      assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'Before email sign-in '+width);
      assert.equal(posts,0);
      viewer={loggedIn:true,userId:'bob',displayName:'Bob'};
      await page.reload(navigation);
      assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'');
      viewer={loggedIn:true,userId:'alice',displayName:'Alice'};
      await page.reload(navigation);
      assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'Before email sign-in '+width);
      await page.click('[data-action="reply"]');
      await page.type('.reply-form textarea','Saved reply');
      await page.reload(navigation);
      await page.click('[data-action="reply"]');
      assert.equal(await page.$eval('.reply-form textarea',n=>n.value),'Saved reply');
      await page.waitForSelector('#discussion-reply-email:not([disabled])');
      assert.equal(await page.$eval('#discussion-reply-email',n=>n.checked),false);
      await page.click('#discussion-reply-email');
      await page.waitForFunction(()=>document.getElementById('discussion-preference-status').textContent.includes('enabled'));
      assert.equal(replyEmail,true);
      await page.click('[data-action="report"]');
      await page.type('#discussion-report-dialog textarea','Please review <script>unsafe</script>');
      await page.click('#discussion-report-dialog button[type="submit"]');
      await page.waitForFunction(()=>!document.getElementById('discussion-report-dialog').open);
      assert.equal(reportWrites,1);
      viewer={loggedIn:true,userId:'admin',displayName:'Moderator',isAdmin:true};
      await page.reload(navigation);
      await page.click('#discussion-load-reports');
      await page.waitForSelector('#discussion-reports article');
      assert.ok(await page.$eval('#discussion-reports',n=>n.textContent.includes('<script>unsafe</script>')));
      assert.equal(await page.$eval('#discussion-reports',n=>n.querySelector('script')),null);
      await page.click('#discussion-reports button');
      await page.waitForFunction(()=>!document.querySelector('#discussion-reports article'));
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth));
      await page.goto(origin+'/api/discuss-auth/unsubscribe#token=fixture-unsubscribe',navigation);
      assert.equal(replyEmail,true); assert.equal(new URL(page.url()).hash,'');
      await page.click('#confirm');
      await page.waitForFunction(()=>document.getElementById('status').textContent.startsWith('Reply emails are disabled'));
      assert.equal(replyEmail,false);reports=[];reportWrites=0;
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth));
      await page.evaluate(()=>{localStorage.clear();sessionStorage.clear();});
    }
    viewer={loggedIn:true,userId:'alice',displayName:'Alice'};
    stage = 'discussion expiry';
    await page.goto(discussion,navigation);
    await page.type('#comment-form textarea','Keep after expiry');
    expired=true;
    await page.click('#comment-form button[type="submit"]');
    await page.waitForSelector('#sign-in-panel:not(.hidden)');
    assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'Keep after expiry');
    assert.equal(posts,0); expired=false;
    viewer={loggedIn:true,userId:'bob'};
    await page.reload(navigation);
    assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'');

    const draft='11111111-1111-4111-8111-111111111111';
    stage = 'portal proposal recovery';
    await page.goto(origin+'/Studies/submit.html?tab=propose&draft='+draft,navigation);
    await page.waitForFunction(()=>currentUser?.login==='alice' && document.getElementById('propose-draft-status').textContent);
    await page.type('#p-title','Saved proposal');
    await page.type('#p-desc','Proposal description');
    await page.evaluate(()=>contributor.flush());
    await page.reload(navigation);
    await page.waitForFunction(()=>document.getElementById('p-title').value==='Saved proposal');
    assert.equal(await page.$eval('#p-draft-id',n=>n.value),draft);
    await page.evaluate(async()=>{
      const previous=window.fetch;
      window.fetch=(input,options)=>String(input).includes('/api/operation') ? Promise.resolve(Response.json({message:'Expired'},{status:401})) : previous(input,options);
      await apiFetch('/api/operation?id=fixture');
    });
    assert.equal(await page.evaluate(()=>currentUser),null);
    assert.equal(await page.$eval('#p-title',n=>n.value),'Saved proposal');
    await page.reload(navigation);
    await page.waitForFunction(()=>document.getElementById('p-title').value==='Saved proposal');
    await page.evaluate(()=>sessionStorage.setItem('fixture-account','bob'));
    await page.reload(navigation);
    await page.waitForFunction(()=>currentUser?.login==='bob' && document.getElementById('propose-draft-status').textContent);
    assert.equal(await page.$eval('#p-title',n=>n.value),'');
    assert.deepEqual(errors,[]);
    console.log(`${useWebKit ? 'WebKit' : 'Chromium'} ${await browser.version()} (${mobileWebKit ? 'mobile/touch emulation' : 'desktop/narrow viewport'}): discussion confirmation, draft recovery, reply preferences, private reports, moderator resolution, unsubscribe, expiry, keyboard focus, and GitHub proposal recovery passed.`);
  } catch (error) {
    console.error('Sign-in browser failure:',stage,page?.url());
    if(page) console.error(await page.evaluate(()=>document.body.innerText.slice(-1600)));
    throw error;
  } finally {if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);process.exitCode=1;});
