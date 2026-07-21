/* Build the Jeevan icon family (concept A) — writes SVGs, rasterizes PNGs,
   assembles favicon.ico and the low-opacity watermark and the preview sheet. */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const puppeteer = require('puppeteer');

const OUT = process.argv[2];
if (!OUT) { console.error('usage: node build_icons.js <out-dir>'); process.exit(1); }
fs.mkdirSync(OUT, { recursive: true });

const COL = {
  navy: '#1A5276', lightblue: '#B8DAF3', gold: '#D5A477',
  brown: '#8B5E34', ivory: '#F7F4EF', charcoal: '#2A241C',
};

/* ---- geometry in a 1000x1000 space ---------------------------------- */
const C = 500, R = 290, nodeR = 60, atmaR = 90, arcW = 33;
const N = [500, 210], E = [790, 500], S = [500, 790], W = [210, 500];
const arc = (a, b) => `M${a[0]} ${a[1]} A${R} ${R} 0 0 1 ${b[0]} ${b[1]}`;
// projection (gold/brown): N->E and S->W ; reflection (blue): E->S and W->N
const PROJ = [arc(N, E), arc(S, W)];
const REFL = [arc(E, S), arc(W, N)];

function marker(id, fill) {
  return `<marker id="${id}" markerWidth="44" markerHeight="44" refX="37" refY="22" orient="auto" markerUnits="userSpaceOnUse"><path d="M6 6 L40 22 L6 38 Z" fill="${fill}"/></marker>`;
}

/* Build one variant of the full mark.
   opts: frame, frameRx, bg, field, guide, proj, refl, node, atma, atmaRing,
         heads(bool), reflOpacity, projOpacity */
function mark(id, opts) {
  const o = Object.assign({
    size: 1000, frame: false, frameRx: 190, bg: null,
    field: null, guide: null, heads: true,
    reflOpacity: 1, projOpacity: 1, atmaRing: null,
  }, opts);
  let defs = '';
  if (o.heads) defs = `<defs>${marker(id + '-p', o.proj)}${marker(id + '-r', o.refl)}</defs>`;
  const body = [];
  if (o.frame) {
    body.push(`<rect x="20" y="20" width="960" height="960" rx="${o.frameRx}" fill="${o.bg}"/>`);
    body.push(`<rect x="38" y="38" width="924" height="924" rx="${o.frameRx - 16}" fill="none" stroke="${COL.ivory}" stroke-width="3" opacity="0.16"/>`);
  }
  if (o.field) {
    body.push(`<circle cx="${C}" cy="${C}" r="430" fill="none" stroke="${o.field}" stroke-width="5" opacity="0.16"/>`);
    body.push(`<circle cx="${C}" cy="${C}" r="360" fill="none" stroke="${o.field}" stroke-width="5" opacity="0.10"/>`);
  }
  if (o.guide)
    body.push(`<circle cx="${C}" cy="${C}" r="${R}" fill="none" stroke="${o.guide}" stroke-width="6" opacity="0.28"/>`);
  const pe = o.heads ? ` marker-end="url(#${id}-p)"` : '';
  const re = o.heads ? ` marker-end="url(#${id}-r)"` : '';
  for (const d of PROJ)
    body.push(`<path d="${d}" fill="none" stroke="${o.proj}" stroke-width="${arcW}" stroke-linecap="round" opacity="${o.projOpacity}"${pe}/>`);
  for (const d of REFL)
    body.push(`<path d="${d}" fill="none" stroke="${o.refl}" stroke-width="${arcW}" stroke-linecap="round" opacity="${o.reflOpacity}"${re}/>`);
  for (const p of [N, E, S, W])
    body.push(`<circle cx="${p[0]}" cy="${p[1]}" r="${nodeR}" fill="${o.node}"/>`);
  body.push(`<circle cx="${C}" cy="${C}" r="${atmaR}" fill="${o.atma}"/>`);
  if (o.atmaRing)
    body.push(`<circle cx="${C}" cy="${C}" r="${atmaR}" fill="none" stroke="${o.atmaRing}" stroke-width="9"/>`);
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" role="img" aria-labelledby="t d">
  <title id="t">${o.title}</title>
  <desc id="d">${o.desc}</desc>
  ${defs}
  ${body.join('\n  ')}
</svg>
`;
}

const DESC = 'The jeevan unit: a central atma nucleus, four faculty nodes (mun, vritti, chitta and buddhi) on one orbit, and projection and reflection as a single continuous cycle.';

const variants = {
  'jeevan-badge': mark('bd', {
    frame: true, bg: COL.navy, field: COL.ivory, guide: COL.ivory,
    proj: COL.gold, refl: COL.lightblue, node: COL.ivory, atma: COL.gold, atmaRing: COL.ivory,
    title: 'Jeevan badge — saturated within satta', desc: 'A rounded navy field, representing saturation within satta. ' + DESC,
  }),
  'jeevan-symbol-light': mark('sl', {
    guide: COL.charcoal, proj: COL.brown, refl: COL.navy, node: COL.navy, atma: COL.brown,
    title: 'Jeevan symbol for light backgrounds', desc: DESC,
  }),
  'jeevan-symbol-dark': mark('sd', {
    guide: COL.ivory, proj: COL.gold, refl: COL.lightblue, node: COL.ivory, atma: COL.gold,
    title: 'Jeevan symbol for dark backgrounds', desc: DESC,
  }),
  'jeevan-monochrome': mark('mo', {
    guide: COL.navy, heads: false, reflOpacity: 0.55,
    proj: COL.navy, refl: COL.navy, node: COL.navy, atma: COL.navy,
    title: 'Jeevan monochrome mark', desc: 'Single-ink navy version for one-colour reproduction. ' + DESC,
  }),
  'jeevan-reversed': mark('rv', {
    guide: COL.ivory, heads: false, reflOpacity: 0.6,
    proj: COL.ivory, refl: COL.ivory, node: COL.ivory, atma: COL.ivory,
    title: 'Jeevan reversed mark', desc: 'One-colour ivory mark for dark fields. ' + DESC,
  }),
  'jeevan-watermark-blue': mark('wm', {
    guide: COL.navy, heads: false,
    proj: COL.navy, refl: COL.navy, node: COL.navy, atma: COL.navy,
    title: 'Jeevan monochrome blue watermark', desc: 'Full-strength navy source for document watermarks. ' + DESC,
  }),
};

/* simplified favicon (512) — two-tone loop + nucleus, safe below 48px */
const FAV = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-labelledby="t d">
  <title id="t">Jeevan favicon</title>
  <desc id="d">A compact navy tile with a gold projection arc, a light-blue reflection arc, and an ivory atma nucleus.</desc>
  <rect x="12" y="12" width="488" height="488" rx="104" fill="${COL.navy}"/>
  <path d="M48 256 A208 208 0 0 1 464 256" fill="none" stroke="${COL.gold}" stroke-width="56" stroke-linecap="round"/>
  <path d="M464 256 A208 208 0 0 1 48 256" fill="none" stroke="${COL.lightblue}" stroke-width="56" stroke-linecap="round"/>
  <circle cx="256" cy="256" r="76" fill="${COL.ivory}"/>
</svg>
`;

/* app icon (full-bleed square navy, no rounding — iOS masks it) */
const APP = mark('ap', {
  size: 1000, frame: true, frameRx: 0, bg: COL.navy, field: COL.ivory, guide: COL.ivory,
  proj: COL.gold, refl: COL.lightblue, node: COL.ivory, atma: COL.gold, atmaRing: COL.ivory,
  title: 'Jeevan app icon', desc: DESC,
}).replace('rx="0"', 'rx="0"');

/* write SVGs */
for (const [name, svg] of Object.entries(variants)) fs.writeFileSync(path.join(OUT, name + '.svg'), svg);
fs.writeFileSync(path.join(OUT, 'jeevan-favicon.svg'), FAV);

/* ---- rasterize ------------------------------------------------------ */
(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
  const page = await browser.newPage();

  async function raster(svg, outPng, px, bg) {
    await page.setViewport({ width: px, height: px, deviceScaleFactor: 1 });
    const html = `<!doctype html><meta charset="utf8"><style>*{margin:0;padding:0}html,body{background:${bg || 'transparent'}}svg{display:block;width:${px}px;height:${px}px}</style>${svg}`;
    await page.setContent(html, { waitUntil: 'load' });
    await page.screenshot({ path: outPng, omitBackground: !bg });
  }

  await raster(variants['jeevan-badge'], path.join(OUT, 'jeevan-badge.png'), 1000);
  await raster(variants['jeevan-symbol-light'], path.join(OUT, 'jeevan-symbol-light.png'), 1000);
  await raster(variants['jeevan-symbol-dark'], path.join(OUT, 'jeevan-symbol-dark.png'), 1000);
  await raster(variants['jeevan-monochrome'], path.join(OUT, 'jeevan-monochrome.png'), 1000);
  await raster(variants['jeevan-reversed'], path.join(OUT, 'jeevan-reversed.png'), 1000);
  await raster(variants['jeevan-watermark-blue'], path.join(OUT, 'jeevan-watermark-blue.png'), 1000);
  await raster(FAV, path.join(OUT, 'jeevan-favicon.png'), 512);
  await raster(FAV, path.join(OUT, 'favicon-16.png'), 16);
  await raster(FAV, path.join(OUT, 'favicon-32.png'), 32);
  await raster(FAV, path.join(OUT, 'favicon-48.png'), 48);
  await raster(APP, path.join(OUT, 'apple-touch-icon.png'), 180);

  /* preview sheet */
  const tile = (label, bg, inner, w) => `<div style="display:flex;flex-direction:column;gap:10px;align-items:center">
    <div style="width:${w}px;height:${w}px;border-radius:26px;background:${bg};display:flex;align-items:center;justify-content:center;box-shadow:0 1px 3px rgba(0,0,0,.12)">${inner}</div>
    <div style="font:400 22px/1.2 Cambria,Georgia,serif;color:#2A241C">${label}</div></div>`;
  const scaled = (svg, w) => svg.replace('<svg ', `<svg width="${Math.round(w*0.78)}" height="${Math.round(w*0.78)}" `);
  const preview = `<!doctype html><meta charset="utf8"><body style="margin:0;background:#EFE7DA;padding:56px;font-family:Calibri,Arial,sans-serif">
    <div style="font:400 46px/1.1 Cambria,Georgia,serif;color:#1A5276;margin-bottom:6px">Jeevan icon family</div>
    <div style="font:400 22px/1.4 Calibri,Arial,sans-serif;color:#5b5346;margin-bottom:40px">Atma nucleus · four faculties · projection and reflection cycle · saturated in satta</div>
    <div style="display:flex;gap:34px;flex-wrap:wrap;align-items:flex-start">
      ${tile('Framed badge', '#F7F4EF', scaled(variants['jeevan-badge'],260), 260)}
      ${tile('Light symbol', '#F7F4EF', scaled(variants['jeevan-symbol-light'],260), 260)}
      ${tile('Dark symbol', '#2A241C', scaled(variants['jeevan-symbol-dark'],260), 260)}
      ${tile('Monochrome', '#F7F4EF', scaled(variants['jeevan-monochrome'],260), 260)}
      ${tile('Reversed', '#1A5276', scaled(variants['jeevan-reversed'],260), 260)}
    </div>
    <div style="display:flex;gap:34px;flex-wrap:wrap;align-items:flex-start;margin-top:40px">
      ${tile('Favicon', '#F7F4EF', scaled(FAV,180), 180)}
      ${tile('48 px', '#F7F4EF', scaled(FAV,120), 120)}
      ${tile('App icon', '#F7F4EF', scaled(APP,180), 180)}
      ${tile('Watermark 9%', '#FFFFFF', `<div style="opacity:.09">${scaled(variants['jeevan-watermark-blue'],200)}</div>`, 200)}
    </div>
  </body>`;
  await page.setViewport({ width: 1500, height: 1080, deviceScaleFactor: 2 });
  await page.setContent(preview, { waitUntil: 'load' });
  const h = await page.evaluate(() => document.body.scrollHeight);
  await page.setViewport({ width: 1500, height: h, deviceScaleFactor: 2 });
  await page.screenshot({ path: path.join(OUT, 'jeevan-icon-family-preview.png') });

  await browser.close();

  /* favicon.ico from the three PNG sizes + 10% watermark */
  execSync(`magick "${path.join(OUT, 'favicon-16.png')}" "${path.join(OUT, 'favicon-32.png')}" "${path.join(OUT, 'favicon-48.png')}" "${path.join(OUT, 'favicon.ico')}"`, { stdio: 'inherit' });
  execSync(`magick "${path.join(OUT, 'jeevan-watermark-blue.png')}" -channel A -evaluate multiply 0.10 +channel "${path.join(OUT, 'jeevan-watermark-blue-10.png')}"`, { stdio: 'inherit' });

  console.log('done');
})();
