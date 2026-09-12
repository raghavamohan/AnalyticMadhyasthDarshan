/* Export browser-verified PNGs for slide authoring and inspect the specimen. */
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const chrome = require('../../Scripts/_chrome.js');
const puppeteer = require('../../Scripts/node_modules/puppeteer');
const OUT = __dirname;
(async()=>{
  const browser=await puppeteer.launch({executablePath:chrome.resolveChromeExecutable(),headless:true});
  try {
    const page=await browser.newPage();
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    fs.mkdirSync(path.join(OUT,'png'),{recursive:true});
    await page.setViewport({width:512,height:512,deviceScaleFactor:1});
    for(const file of fs.readdirSync(path.join(OUT,'icons')).filter(n=>n.endsWith('.svg')&&n!=='sprite.svg')) {
      const source=fs.readFileSync(path.join(OUT,'icons',file),'utf8');
      await page.setContent(`<style>html,body{margin:0;background:transparent}svg{width:512px;height:512px;display:block}</style>${source}`);
      await page.screenshot({path:path.join(OUT,'png',file.replace('.svg','.png')),omitBackground:true});
    }
    for(const name of ['jeevan','akhand-samaj']) for(const size of [16,32,48]) {
      await page.setViewport({width:size,height:size,deviceScaleFactor:1});
      const source=fs.readFileSync(path.join(OUT,'icons',`${name}-compact.svg`),'utf8');
      await page.setContent(`<style>html,body{margin:0;background:transparent}svg{width:${size}px;height:${size}px;display:block}</style>${source}`);
      await page.screenshot({path:path.join(OUT,'png',`${name}-${size}.png`),omitBackground:true});
    }
    await page.setViewport({width:1200,height:900,deviceScaleFactor:1});
    await page.goto(pathToFileURL(path.join(OUT,'preview.html')).href,{waitUntil:'load'});
    const broken=await page.evaluate(()=>Array.from(document.images).filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src));
    if(broken.length) throw new Error('Broken specimen images: '+broken.join(', '));
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw new Error('Desktop overflow');
    await page.click('#motion-toggle');
    if(await page.$eval('.amd-wait .faculty',n=>getComputedStyle(n).animationName)!=='none') throw new Error('Pause does not stop motion');
    for(const id of ['identity','symbols','website','slides','motion','images']) {
      const el=await page.$('#'+id);
      await el.screenshot({path:path.join(OUT,`preview-${id}.png`)});
    }
    await page.click('#motion-toggle');
    await page.emulateMediaFeatures([{name:'prefers-reduced-motion',value:'reduce'}]);
    const reduced=await page.$$eval('.amd-wait .faculty,.amd-wait .goal',ns=>ns.every(n=>getComputedStyle(n).animationName==='none'));
    if(!reduced) throw new Error('Reduced motion not respected');
    await page.setViewport({width:390,height:844,deviceScaleFactor:1});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw new Error('Mobile overflow');
    await page.screenshot({path:path.join(OUT,'preview-mobile.png'),fullPage:true});
    if(errors.length) throw new Error(errors.join('\n'));
    console.log('PNG exports complete. Desktop/mobile layout, images, pause and reduced motion passed.');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
