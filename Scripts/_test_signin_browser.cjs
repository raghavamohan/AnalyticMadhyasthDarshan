/* Shipped sign-in UI against isolated HTTP fixtures; no mail or GitHub writes. */
const assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path'), http = require('node:http');
const puppeteer = require('puppeteer'), chrome = require('./_chrome');
const root = path.resolve(__dirname, '..');

(async () => {
  const source = fs.readFileSync(path.join(root,'infra/discussions-worker/src/confirm.js'),'utf8');
  const {confirmationPage} = await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
  let viewer = {loggedIn:false}, posts = 0, confirmations = 0, expired = false;
  const server = http.createServer(async (req,res) => {
    const url = new URL(req.url, 'http://localhost');
    if (url.pathname === '/api/discuss-auth/verify') {
      const response = confirmationPage();
      response.headers.forEach((v,k) => res.setHeader(k,v));
      return res.end(await response.text());
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
    browser=await puppeteer.launch(chrome.puppeteerLaunchOptions(chrome.resolveChromeExecutable()));
    await chrome.assertPinnedChrome(browser);
    page=await browser.newPage(); const errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    page.on('dialog',dialog=>dialog.accept());
    await page.setRequestInterception(true);
    page.on('request',request=>request.url().startsWith(origin+'/') || /^(data|blob):/.test(request.url()) ? request.continue() : request.abort());
    const discussion=origin+'/Studies/Nature-Of-Time/discussion.html';
    for (const width of [1280,390]) {
      stage = 'discussion guest recovery '+width;
      viewer={loggedIn:false};
      await page.setViewport({width,height:900});
      await page.goto(discussion,{waitUntil:'networkidle0'});
      await page.waitForSelector('#comment-panel:not(.hidden)');
      await page.type('#comment-form textarea', 'Before email sign-in '+width);
      await page.reload({waitUntil:'networkidle0'});
      assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'Before email sign-in '+width);
      // Scanner-like navigation executes no confirmation request.
      const before=confirmations;
      stage = 'confirmation '+width;
      await page.goto(origin+'/api/discuss-auth/verify#token=fixture-token',{waitUntil:'networkidle0'});
      assert.equal(confirmations,before); assert.equal(posts,0);
      assert.equal(new URL(page.url()).hash,'');
      await page.focus('#confirm'); assert.equal(await page.evaluate(()=>document.activeElement.id),'confirm');
      await Promise.all([page.waitForNavigation({waitUntil:'networkidle0'}),page.keyboard.press('Enter')]);
      assert.equal(confirmations,before+1); assert.equal(posts,0);
      stage = 'discussion account recovery '+width;
      assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'');
      await page.click('#discussion-draft-list button');
      assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'Before email sign-in '+width);
      assert.equal(posts,0);
      viewer={loggedIn:true,userId:'bob',displayName:'Bob'};
      await page.reload({waitUntil:'networkidle0'});
      assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'');
      viewer={loggedIn:true,userId:'alice',displayName:'Alice'};
      await page.reload({waitUntil:'networkidle0'});
      assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'Before email sign-in '+width);
      await page.click('[data-action="reply"]');
      await page.type('.reply-form textarea','Saved reply');
      await page.reload({waitUntil:'networkidle0'});
      await page.click('[data-action="reply"]');
      assert.equal(await page.$eval('.reply-form textarea',n=>n.value),'Saved reply');
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth));
      await page.evaluate(()=>{localStorage.clear();sessionStorage.clear();});
    }
    viewer={loggedIn:true,userId:'alice',displayName:'Alice'};
    stage = 'discussion expiry';
    await page.goto(discussion,{waitUntil:'networkidle0'});
    await page.type('#comment-form textarea','Keep after expiry');
    expired=true;
    await page.click('#comment-form button[type="submit"]');
    await page.waitForSelector('#sign-in-panel:not(.hidden)');
    assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'Keep after expiry');
    assert.equal(posts,0); expired=false;
    viewer={loggedIn:true,userId:'bob'};
    await page.reload({waitUntil:'networkidle0'});
    assert.equal(await page.$eval('#comment-form textarea',n=>n.value),'');

    const draft='11111111-1111-4111-8111-111111111111';
    stage = 'portal proposal recovery';
    await page.goto(origin+'/Studies/submit.html?tab=propose&draft='+draft,{waitUntil:'networkidle0'});
    await page.waitForFunction(()=>currentUser?.login==='alice' && document.getElementById('propose-draft-status').textContent);
    await page.type('#p-title','Saved proposal');
    await page.type('#p-desc','Proposal description');
    await page.evaluate(()=>contributor.flush());
    await page.reload({waitUntil:'networkidle0'});
    await page.waitForFunction(()=>document.getElementById('p-title').value==='Saved proposal');
    assert.equal(await page.$eval('#p-draft-id',n=>n.value),draft);
    await page.evaluate(async()=>{
      const previous=window.fetch;
      window.fetch=(input,options)=>String(input).includes('/api/operation') ? Promise.resolve(Response.json({message:'Expired'},{status:401})) : previous(input,options);
      await apiFetch('/api/operation?id=fixture');
    });
    assert.equal(await page.evaluate(()=>currentUser),null);
    assert.equal(await page.$eval('#p-title',n=>n.value),'Saved proposal');
    await page.reload({waitUntil:'networkidle0'});
    await page.waitForFunction(()=>document.getElementById('p-title').value==='Saved proposal');
    await page.evaluate(()=>sessionStorage.setItem('fixture-account','bob'));
    await page.reload({waitUntil:'networkidle0'});
    await page.waitForFunction(()=>currentUser?.login==='bob' && document.getElementById('propose-draft-status').textContent);
    assert.equal(await page.$eval('#p-title',n=>n.value),'');
    assert.deepEqual(errors,[]);
    console.log('Desktop/mobile discussion confirmation, guest/account/reply recovery, expiry, keyboard focus, and GitHub proposal recovery passed.');
  } catch (error) {
    console.error('Sign-in browser failure:',stage,page?.url());
    if(page) console.error(await page.evaluate(()=>document.body.innerText.slice(-1600)));
    throw error;
  } finally {if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
})().catch(error=>{console.error(error);process.exitCode=1;});
