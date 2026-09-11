/* Shared identity and symbol kit. Source SVG geometry; deterministic UTF-8/LF. */
const fs = require('fs');
const path = require('path');
const OUT = __dirname;
const ROOT = path.resolve(OUT, '../..');
const NAVY = '#1A5276', GOLD = '#B47B46';
function write(name, body) {
  const dest = path.join(OUT, name);
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  const data = body.replace(/\r\n/g, '\n');
  if (!fs.existsSync(dest) || fs.readFileSync(dest, 'utf8') !== data) fs.writeFileSync(dest, data);
}
const esc = s => s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const p = d => `<path d="${d}"/>`;
const c = (x,y,r,extra='') => `<circle cx="${x}" cy="${y}" r="${r}" ${extra}/>`;
const accent = body => `<g stroke="var(--amd-accent,${GOLD})">${body}</g>`;
const fill = (x,y,r) => c(x,y,r,`fill="var(--amd-accent,${GOLD})" stroke="none"`);
const icons = {
  resolution: p('M3 12s3-6 9-6 9 6 9 6-3 6-9 6-9-6-9-6Z') + fill(12,12,2.5),
  prosperity: p('M3 14h18c-1 5-4 7-9 7s-8-2-9-7ZM12 14V7') + accent(p('M12 10C6 10 6 5 6 4c5 0 6 3 6 6ZM12 8c0-4 3-6 6-6 0 4-2 6-6 6Z')),
  fearlessness: c(6,6,2.5)+c(18,6,2.5)+p('M2 20v-5c0-3 2-4 4-4s4 1 4 4v5M14 20v-5c0-3 2-4 4-4s4 1 4 4v5')+accent(p('M8 14c3 3 5 3 8 0')),
  coexistence: c(8,12,6)+accent(c(16,12,6)),
  learning: p('M12 6C9 3 5 3 2 4v15c4-1 7 0 10 2 3-2 6-3 10-2V4c-3-1-7-1-10 2ZM12 6v15')+accent(p('M5 8h3M16 8h3M5 12h3M16 12h3')),
  wisdom: c(12,12,9)+accent(p('m16 8-2.5 5.5L8 16l2.5-5.5Z')),
  science: p('M9 3h6M10 3v7L4 19c-1 1 0 2 1 2h14c1 0 2-1 1-2l-6-9V3')+accent(p('M7 15h10')),
  justice: p('M12 3v18M7 21h10M3 7h18M6 7l-4 8h8ZM18 7l-4 8h8Z')+fill(12,6,2),
  relationships: p('M10 15 8 17a4 4 0 0 1-6-6l4-4a4 4 0 0 1 6 0M14 9l2-2a4 4 0 0 1 6 6l-4 4a4 4 0 0 1-6 0')+accent(p('m8 12 8 0')),
  family: c(12,5,2.5)+c(4,10,2)+c(20,10,2)+p('M7 15v-2c0-3 2-4 5-4s5 1 5 4v2M1 21v-4c0-2 1-3 3-3s3 1 3 3v4M17 21v-4c0-2 1-3 3-3s3 1 3 3v4')+accent(p('M9 21v-4h6v4')),
  ecology: p('M12 22V10M12 14C4 14 3 8 3 5c6 0 9 4 9 9Z')+accent(p('M12 10c0-6 4-8 9-8 0 5-3 8-9 8Z')),
  health: p('M12 21 3 12C-2 5 7-1 12 6c5-7 14-1 9 6Z')+accent(p('M3 12h5l2-4 4 8 2-4h5')),
  work: p('M14 3a6 6 0 0 0-7 8l-5 5a3 3 0 0 0 4 4l6-6a6 6 0 0 0 8-7l-4 4-4-4Z'),
  model: c(5,5,2)+c(19,5,2)+c(5,19,2)+c(19,19,2)+p('M7 5h10M5 7v10M19 7v10M7 19h10')+accent(p('m7 7 10 10m0-10L7 17')),
  time: c(12,12,9)+accent(p('M12 6v6l4 3')),
  language: p('M3 3h18v14H9l-6 4ZM7 7h10M7 11h7'),
  art: p('M14 3 3 14l-1 8 8-1L21 10ZM14 3l7 7M3 14l7 7')+accent(p('m5 18 2 2')),
  choice: p('M12 22V12M12 12 5 5M12 12l7-7M2 5h6M5 2v6M16 5h6M19 2v6'),
  continuity: p('M4 8a9 9 0 0 1 15-2l2 2M21 3v5h-5M20 16a9 9 0 0 1-15 2l-2-2M3 21v-5h5'),
  search: c(10,10,7)+p('m15 15 7 7'),
  download: p('M12 2v13m-5-5 5 5 5-5M3 17v5h18v-5'),
  slides: p('M2 3h20v14H2ZM12 17v5M8 22h8')+accent(p('m10 7 5 3-5 3Z')),
  discussion: p('M2 3h16v12H7l-5 4ZM18 7h4v15l-5-4h-6v-3'),
  audio: p('M3 9h4l5-5v16l-5-5H3Z M16 8c3 2 3 6 0 8M19 5c5 4 5 10 0 14'),
  pause: p('M8 4v16M16 4v16'),
  close: p('m5 5 14 14M19 5 5 19'),
  menu: p('M3 5h18M3 12h18M3 19h18'),
  external: p('M14 3h7v7M21 3l-11 11M10 3H3v18h18v-7'),
  saved: p('m4 12 5 5L20 6'),
  moon: p('M20 15A9 9 0 0 1 9 3a9 9 0 1 0 11 12Z'),
  sun: c(12,12,4)+p('M12 1v2M12 21v2M1 12h2M21 12h2M4 4l2 2M18 18l2 2M20 4l-2 2M6 18l-2 2'),
  notes: p('M4 2h12l4 4v16H4ZM15 2v5h5M8 11h8M8 15h8M8 19h5'),
};
function markBody(name, compact=false) {
  if (name === 'jeevan') return [34,54,74,94].map(r=>`<circle class="faculty" cx="120" cy="120" r="${r}" fill="none" stroke="var(--amd-icon,${NAVY})" stroke-width="${compact?8:4.5}"/>`).join('')+fill(120,120,compact?17:13);
  return [0,90,180,270].map((a,i)=>`<path class="goal" d="M120 36H163Q204 36 204 77V120" transform="rotate(${a} 120 120)" fill="none" stroke="var(--amd-${i%2?'accent':'icon'},${i%2?GOLD:NAVY})" stroke-width="${compact?20:15}"/>`).join('')+fill(120,120,compact?22:18);
}
function svg(name, mode='light', compact=false, cls='') {
  const isMark=['jeevan','akhand-samaj'].includes(name);
  const colors=mode==='dark'?['#F7F4EF','#D5A477']:mode==='mono'?[NAVY,NAVY]:[NAVY,GOLD];
  const body=isMark?markBody(name,compact):`<g fill="none" stroke="var(--amd-icon,${NAVY})" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${icons[name]}</g>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${isMark?'240 240':'24 24'}" role="img" aria-label="${esc(name.replace(/-/g,' '))}" class="${cls}" style="--amd-icon:${colors[0]};--amd-accent:${colors[1]}">${body}</svg>`;
}
const names=['jeevan','akhand-samaj',...Object.keys(icons)];
for(const name of names) for(const mode of ['light','dark','mono']) write(`icons/${name}-${mode}.svg`,svg(name,mode));
for(const name of names.slice(0,2)) write(`icons/${name}-compact.svg`,svg(name,'light',true));
write('icons/sprite.svg',`<svg xmlns="http://www.w3.org/2000/svg"><defs>${Object.entries(icons).map(([name,body])=>`<symbol id="${name}" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">${body.replace(/var\(--amd-accent,#[A-Fa-f0-9]+\)/g,'currentColor')}</g></symbol>`).join('')}</defs></svg>`);

const specific={
 'The-Ontology-of-Coexistence':['coexistence','jeevan'], 'Nature-Of-Time':['time','jeevan'],
 'Why-Humans-Are-Not-Just-Material':['jeevan','jeevan'], 'Philosophy-Of-Mind-And-Jeevan':['jeevan','jeevan'],
 'Chitta-Brain-And-Memory':['resolution','jeevan'], 'The-Epistemology-of-Coexistence':['resolution','jeevan'],
 'Methodology-And-Hermeneutics':['wisdom','jeevan'], 'Axiology-Value-Theory':['justice','akhand-samaj'],
 'Ethics-And-Morals-In-Human-Beings':['justice','akhand-samaj'], 'Human-Behavior-And-Society':['relationships','akhand-samaj'],
 'Family-Relationships-And-Values':['family','akhand-samaj'], 'Education-And-Sanskar':['learning','akhand-samaj'],
 'Prosperity-Economics-And-Right-Use':['prosperity','akhand-samaj'], 'Governance-Justice-And-Undivided-Society':['justice','akhand-samaj'],
 'Nature-Ecology-And-Right-Use':['ecology','akhand-samaj'], 'Aesthetics':['art','jeevan'],
 'Spiritual-Practice-And-Realization':['jeevan','jeevan'], 'Science-Technology-And-Human-Purpose':['science','akhand-samaj'],
 'How-Undivided-Society-Is-Established':['akhand-samaj','akhand-samaj'], 'Death-Continuity-And-Rebirth':['continuity','jeevan'],
 'Language-Meaning-And-Definition':['language','jeevan'], 'Work-Action-And-Karma':['work','akhand-samaj'],
 'Free-Will-Choice-And-Agency':['choice','jeevan'], 'Health-Body-And-Restraint':['health','akhand-samaj'],
 'God-Divinity-And-The-Sacred':['coexistence','jeevan'], 'A-State-Dynamic-Model-Of-Coexistence':['model','jeevan'],
 'How-To-Form-Self-Sustaining-Organizations':['family','akhand-samaj'],
};
const rows=['topical','formal','applied'].flatMap(t=>JSON.parse(fs.readFileSync(path.join(ROOT,`Studies/catalog-${t}.json`),'utf8')));
const assignments=rows.map(row=>{
 if(!specific[row.slug]) throw new Error(`Assign a visual explicitly: ${row.slug}`);
 const [icon,theme]=specific[row.slug];
 return {slug:row.slug,title:row.title,icon,theme,illustration:theme==='jeevan'?'inner-life.svg':'community-courtyard.png'};
});
write('study-visuals.json',JSON.stringify({status:'approved-for-use',note:'Navigation associations, not an exhaustive philosophical classification. Approved asset kit; website and deck integration is separate.',studies:assignments},null,2)+'\n');

const text=(x,y,s,size=22)=>`<text x="${x}" y="${y}" font-family="Calibri,Segoe UI,sans-serif" font-size="${size}" fill="${NAVY}">${esc(s)}</text>`;
write('illustrations/inner-life.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 480" role="img" aria-label="Jeevan: atma at the centre, followed outward by buddhi, citta, vritti and mun"><rect width="800" height="480" fill="#F7F4EF"/><g transform="translate(60 70) scale(1.4)">${markBody('jeevan')}</g>${text(425,85,'Jeevan',36)}${['Atma · centre','Buddhi · first orbit','Citta · second orbit','Vritti · third orbit','Mun · outermost orbit'].map((s,i)=>text(425,151+i*48,s)).join('')}${text(65,444,'One conscious unit · five integral faculties',20)}</svg>`);
write('illustrations/shared-goals.svg',`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 480" role="img" aria-label="Akhand Samaj: resolution, prosperity, fearlessness and coexistence"><rect width="800" height="480" fill="#F7F4EF"/><g transform="translate(60 70) scale(1.4)">${markBody('akhand-samaj')}</g>${text(425,85,'Akhand Samaj',36)}${['Resolution','Prosperity','Fearlessness','Coexistence'].map((s,i)=>text(425,155+i*53,s)).join('')}${text(65,444,'Four human goals · one undivided society',20)}</svg>`);

const specimen=(name,title,desc)=>`<article class="identity"><div class="identity-art">${svg(name)}</div><h3>${title}</h3><p>${desc}</p><div class="cuts"><span class="amd-dark">${svg(name,'dark')}</span><span>${svg(name,'mono')}</span><span class="smallcut">${svg(name,'light',true)}<small>32 px</small></span></div></article>`;
const topicNames=['resolution','prosperity','fearlessness','coexistence','learning','wisdom','science','justice','relationships','family','ecology','health','work','model','time','language','art','choice','continuity'];
const utilityNames=Object.keys(icons).filter(n=>!topicNames.includes(n));
const tile=n=>`<div class="symbol">${svg(n)}<span>${n}</span></div>`;
const ui=(n,label)=>`<span class="sample-action">${svg(n,'light',false,'amd-icon')}${label}</span>`;
const cardRow=(n,title,sub)=>`<article class="study-card">${svg(n,'light',false,'amd-mark')}<div><h4>${title}</h4><p>${sub}</p><div class="actions">${ui('learning','Read')}${ui('slides','Slides')}${ui('discussion','Discuss')}</div></div></article>`;
const imagePath='illustrations/community-courtyard.png';
const haveImage=fs.existsSync(path.join(OUT,imagePath));
const community=haveImage?`<img src="${imagePath}" alt="People studying together, repairing a useful object and tending a garden."/>`:`<img src="illustrations/shared-goals.svg" alt="The four human goals of Akhand Samaj."/>`;
const slides=`<div class="slide cover amd-dark"><div><p class="eyebrow">MADHYASTH DARSHAN · JEEVAN</p><h3>Knowledge, knower<br>and human conduct</h3><p>Understanding and its expression in living</p><small>AnalyticMadhyasthDarshan.org</small></div>${svg('jeevan','dark')}</div><div class="slide content-slide"><p class="eyebrow">AKHAND SAMAJ · HUMAN GOALS</p><h3>Four goals in human living</h3><div class="goal-row">${['resolution','prosperity','fearlessness','coexistence'].map(n=>`<div>${svg(n)}<h4>${n[0].toUpperCase()+n.slice(1)}</h4></div>`).join('')}</div><footer>${svg('akhand-samaj','light',false,'amd-icon')} AnalyticMadhyasthDarshan.org <span>Style specimen</span></footer></div>`;
write('preview.html',`<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Shared visual theme — Madhyasth Darshan</title><link rel="stylesheet" href="tokens.css"><style>
*{box-sizing:border-box}body{margin:0;background:var(--amd-paper);color:var(--amd-ink);font:18px/1.55 var(--amd-sans)}main{max-width:1160px;margin:auto;padding:48px 28px}h1,h2,h3,h4{font-family:var(--amd-serif);line-height:1.15;font-weight:600}h1{font-size:54px;margin:12px 0 16px}h2{font-size:34px;margin:0 0 14px}h3{font-size:26px}h4{font-size:22px;margin:0 0 10px}p{color:var(--amd-muted)}.eyebrow{font-size:13px;letter-spacing:.14em;color:var(--amd-gold-text);font-weight:600}.lede{max-width:760px;font-size:21px}section{padding:42px 0;border-top:1px solid var(--amd-line);margin-top:32px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:36px}.identity{padding:28px;background:white;border-radius:14px}.identity-art{height:220px;display:flex;justify-content:center}.identity-art svg{width:230px}.identity p{min-height:60px}.cuts{display:flex;gap:20px;align-items:center}.cuts>span{width:88px;height:88px;display:flex;align-items:center;justify-content:center;border-radius:12px}.cuts svg{width:80px;height:80px}.cuts .smallcut{flex-direction:column}.smallcut svg{width:32px;height:32px}.smallcut small{font-size:12px;margin-top:6px}.palette{display:flex;gap:18px;flex-wrap:wrap;margin:22px 0}.swatch{display:flex;align-items:center;gap:9px;font-size:14px}.swatch i{display:block;width:32px;height:32px;border-radius:50%;border:1px solid #bbb}.symbol-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:28px 12px;margin-top:30px}.symbol{display:flex;flex-direction:column;align-items:center;gap:12px;font-size:14px;text-align:center}.symbol svg{width:44px;height:44px}.utility .symbol svg{width:24px;height:24px}.web-example{border:1px solid var(--amd-line);background:white;border-radius:16px;overflow:hidden}.web-nav{padding:20px 28px;display:flex;align-items:center;gap:12px;font-size:16px;border-bottom:1px solid var(--amd-line)}.web-nav svg{width:38px;height:38px}.web-nav span:last-child{margin-left:auto}.web-hero{display:grid;grid-template-columns:1fr 1fr;align-items:center;padding:30px;gap:22px;background:var(--amd-paper)}.web-hero h3{font-size:38px;margin:12px 0}.web-hero img{width:100%;display:block}.sample-action{display:inline-flex;align-items:center;gap:6px;color:var(--amd-navy);font-size:15px}.actions{display:flex;gap:22px;flex-wrap:wrap}.studies{padding:25px 30px}.study-card{display:flex;gap:18px;padding:24px 0;border-top:1px solid var(--amd-line)}.study-card p{margin:8px 0 15px;font-size:16px}.study-card .amd-mark{width:56px;height:56px}.slide{aspect-ratio:16/9;padding:38px;position:relative;margin:20px 0}.cover{display:grid;grid-template-columns:1.5fr 1fr;align-items:center}.cover h3{font-size:40px;color:var(--amd-paper);margin:25px 0}.cover svg{width:100%}.cover p{color:#e2ebf0}.cover .eyebrow{color:#d5a477}.cover small{display:block;margin-top:40px;font-size:13px}.content-slide{background:white}.content-slide h3{font-size:36px;margin:16px 0 44px}.goal-row{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}.goal-row svg{width:58px;height:58px;margin-bottom:15px}.goal-row h4{font-size:22px}.content-slide footer{position:absolute;bottom:24px;left:38px;right:38px;display:flex;align-items:center;gap:10px;font-size:13px;color:var(--amd-muted)}footer span{margin-left:auto}.motion-examples{display:flex;flex-wrap:wrap;gap:40px;background:white;padding:28px;border-radius:12px}.motion-examples .amd-wait{min-width:250px}button{font:inherit;cursor:pointer;border:1px solid var(--amd-navy);background:transparent;color:var(--amd-navy);padding:9px 16px;border-radius:6px}button:focus-visible{outline:3px solid var(--amd-gold);outline-offset:3px}.motion-control{display:flex;gap:15px;align-items:center;margin:20px 0}.image-pair img{width:100%;display:block}.hero-image{width:100%;display:block;margin-top:22px}.note{font-size:15px}.links{display:flex;gap:25px;flex-wrap:wrap}a{color:var(--amd-navy)}.review-table{width:100%;border-collapse:collapse;font-size:16px}.review-table td,.review-table th{text-align:left;padding:14px;border-bottom:1px solid var(--amd-line);vertical-align:top}.review-table th{color:var(--amd-navy)}
@media(max-width:740px){main{padding:26px 18px}h1{font-size:39px}.pair,.web-hero{grid-template-columns:1fr}.symbol-grid{grid-template-columns:repeat(4,1fr)}.slide{padding:22px;aspect-ratio:auto;min-height:300px}.cover h3{font-size:26px}.content-slide h3{font-size:26px}.goal-row{grid-template-columns:repeat(2,1fr);padding-bottom:55px}.goal-row h4{font-size:18px}.content-slide footer{left:22px;right:22px}.cover small{margin-top:20px}.web-nav{padding:15px}.web-hero h3{font-size:30px}.web-hero,.studies{padding:20px}.review-table{font-size:14px}.review-table td,.review-table th{padding:8px}.web-nav span:last-child{display:none}}
</style></head><body><main>
<p class="eyebrow">MADHYASTH DARSHAN · SHARED VISUAL THEME</p><h1>Understanding.<br>Expressed in living.</h1><p class="lede">One family for the study website, teaching decks and waiting states. Jeevan J1 and the continuous Akhand Samaj bond, now with a golden nucleus.</p><div class="links"><a href="#identity">Identity</a><a href="#symbols">Icons</a><a href="#website">Website</a><a href="#slides">Presentations</a><a href="#motion">Motion</a><a href="#images">Images</a></div>
<section id="identity"><h2>The two identity marks</h2><div class="pair">${specimen('jeevan','Jeevan · J1','Atma at the centre; buddhi, citta, vritti and mun in four successive orbits.')}${specimen('akhand-samaj','Akhand Samaj · A1 + nucleus','Four equal connected sections for the human goals, with your requested golden centre.')}</div><div class="palette">${[['Navy',NAVY],['Gold',GOLD],['Pale gold','#D5A477'],['Ivory','#F7F4EF'],['Ink','#2A241C']].map(([n,col])=>`<span class="swatch"><i style="background:${col}"></i>${n} ${col}</span>`).join('')}</div><p class="note">The Akhand Samaj centre is an identity element, not a fifth human goal. Goal labels remain necessary in explanatory uses.</p></section>
<section id="symbols"><h2>A shared vocabulary of icons</h2><p>Rounded linework and restrained gold accents. Topic icons retain labels; interface icons describe familiar actions.</p><div class="symbol-grid">${topicNames.map(tile).join('')}</div><h3>Reading and interface actions</h3><div class="symbol-grid utility">${utilityNames.map(tile).join('')}</div></section>
<section id="website"><h2>Website application</h2><p>Visible identity in the header, a quiet human illustration, and subject icons beside the study titles. This is a layout specimen.</p><div class="web-example"><div class="web-nav">${svg('akhand-samaj')}<strong>Studies of Madhyasth Darshan</strong><span>${ui('search','Search')}</span></div><div class="web-hero"><div><p class="eyebrow">AN OPEN COMPARATIVE INQUIRY</p><h3>The human question.<br>A shared world.</h3><p>Explore existence, knowledge, value and human participation.</p><div class="actions">${ui('learning','Start reading')}${ui('discussion','Join the discussion')}</div></div>${community}</div><div class="studies">${cardRow('jeevan','Why Humans Are Not Just Material','The body, the knower and the human question.')}${cardRow('resolution','The Epistemology of Coexistence','Knowledge, understanding and evidence in living.')}${cardRow('akhand-samaj','How Undivided Society Is Established','Resolution, prosperity, fearlessness and coexistence.')}</div></div></section>
<section id="slides"><h2>Presentation application</h2><p>Retain Cambria titles, Calibri text and the existing deck grids. Use the identity once per cover or section, and topic icons where they clarify the subject.</p>${slides}<p class="note">These are visual specimens, not modified teaching slides. Existing content, citations, comparison colours and speaker notes remain authoritative.</p></section>
<section id="motion"><h2>Waiting, with continuity</h2><p>A steady nucleus and gentle changes in line opacity. No spinning atom or implied progress percentage.</p><div class="motion-control"><button id="motion-toggle" aria-pressed="false">Pause motion</button><span id="motion-label" aria-live="polite">Motion follows your system preference.</span></div><div class="motion-examples"><div class="amd-wait">${svg('jeevan','light',true)}<span>Loading studies…</span></div><div class="amd-wait">${svg('akhand-samaj','light',true)}<span>Loading discussion…</span></div></div><p class="note">Reduced-motion settings show static marks. Each real loading state needs task-specific text, completion handling and an error path.</p></section>
<section id="images"><h2>Images that belong to the same family</h2><p>Use labelled compositions for concepts and editorial scenes for everyday participation. Keep the two purposes distinct.</p><div class="pair image-pair"><img src="illustrations/inner-life.svg" alt="Jeevan and its five integral faculties."><img src="illustrations/shared-goals.svg" alt="Akhand Samaj and its four human goals."></div>${haveImage?`<img class="hero-image" src="${imagePath}" alt="People studying together, repairing a useful object and tending a garden."><p class="note">AI-generated editorial illustration; not a photograph or documentary evidence.</p>`:''}</section>
<section><h2>What changes across the collection</h2><table class="review-table"><thead><tr><th>Current pattern</th><th>Shared treatment</th></tr></thead><tbody><tr><td>Different atom-like motifs in decks and assets</td><td>J1 with four rings; A1 with four sections and a centre</td></tr><tr><td>Handshake, cycle and gear reused for unrelated concepts</td><td>Eye for understanding, compass for discernment, flask for scientific inquiry; always labelled</td></tr><tr><td>Shield used for fearlessness</td><td>Equal people in mutual confidence; reserve shields for protection/security</td></tr><tr><td>Mostly typographic website and social images</td><td>Visible identity, study-topic icons and a consistent editorial illustration</td></tr><tr><td>Waiting conveyed chiefly through text/disabled controls</td><td>Small branded motion beside the existing status text</td></tr></tbody></table><p class="note">Review covers 8 decks / 192 slides at contact-sheet level, with selected icon-bearing slides examined at full size, plus the local website and loading-state sources.</p><div class="links"><a href="README.md">Theme guide</a><a href="review.md">Detailed review</a><a href="study-visuals.json">Study assignments</a></div></section>
</main><script>const toggle=document.getElementById('motion-toggle');toggle.addEventListener('click',()=>{const paused=toggle.getAttribute('aria-pressed')!=='true';toggle.setAttribute('aria-pressed',String(paused));document.body.dataset.motion=paused?'paused':'running';toggle.textContent=paused?'Resume motion':'Pause motion';document.getElementById('motion-label').textContent=paused?'Motion paused.':'Motion follows your system preference.';});</script></body></html>`);
console.log(`Built ${names.length} symbols, ${assignments.length} study assignments and the theme specimen.`);
