// Keep a real saved reader open while the isolated deployment changes.
const assert = require('node:assert/strict');
const readline = require('node:readline');
const puppeteer = require('puppeteer');
const {resolveChromeExecutable,puppeteerLaunchOptions,assertPinnedChrome} = require('./_chrome');

(async () => {
  const base=process.argv[2], documentPath=process.argv[3];
  assert.match(base,/^https:\/\/amd-ci-drill-[a-f0-9]+\.[a-z0-9-]+\.workers\.dev$/);
  const browser=await puppeteer.launch(puppeteerLaunchOptions(resolveChromeExecutable()));
  try {
    await assertPinnedChrome(browser);
    const page=await browser.newPage();
    await page.setRequestInterception(true);
    page.on('request',request=>request.url().startsWith(base+'/') || /^(data|blob):/.test(request.url()) ? request.continue() : request.abort());
    const lines=readline.createInterface({input:process.stdin});
    for await(const line of lines) {
      const command=JSON.parse(line);
      try {
        if(command.action==='save') {
          await page.goto(base+documentPath+'?r='+command.revision,{waitUntil:'networkidle0'});
          await page.evaluate(async ({documentPath,revision})=>{
            await navigator.serviceWorker.register('/reader-sw.js',{scope:'/'});
            const registration=await navigator.serviceWorker.ready;
            await new Promise((resolve,reject)=>{
              const channel=new MessageChannel(), timer=setTimeout(()=>reject(new Error('Offline save timed out')),90000);
              channel.port1.onmessage=event=>{
                if(event.data.error){clearTimeout(timer);reject(new Error(event.data.error));}
                if(event.data.result){clearTimeout(timer);resolve(event.data.result);}
              };
              registration.active.postMessage({type:'SAVE',path:documentPath,release:revision},[channel.port2]);
            });
          },{documentPath,revision:command.revision});
          console.log(JSON.stringify({passed:true,action:'save',url:page.url()}));
        } else if(command.action==='after') {
          assert.equal(new URL(page.url()).searchParams.get('r'),command.savedRevision);
          // The shipped navigation helper keeps this open reader's links pinned.
          const hrefs=await page.$$eval('a[href]',nodes=>nodes.map(node=>node.href));
          for(const href of hrefs.filter(href=>href.startsWith(base+'/Studies/') && href.endsWith('.html?r='+command.savedRevision))) {
            assert.equal(new URL(href).searchParams.get('r'),command.savedRevision);
          }
          await page.setOfflineMode(true);
          await page.goto(base+documentPath+'?r='+command.savedRevision,{waitUntil:'domcontentloaded'});
          assert.match(await page.$eval('h1',node=>node.textContent),/CI acceptance/);
          await page.setOfflineMode(false);
          console.log(JSON.stringify({passed:true,action:'after',offline:true,url:page.url()}));
        } else if(command.action==='close') break;
        else throw new Error('Unknown browser drill action');
      } catch(error) {console.log(JSON.stringify({passed:false,error:error.message}));}
    }
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
