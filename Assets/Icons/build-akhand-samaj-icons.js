/* Build the Akhand Samaj icon family — ordered-square mark (C) and
   16px-first cut (D). SVG masters, PNG exports, compact mark, watermark,
   site favicon, and preview sheet. */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const {
  missingChromeMessage,
  puppeteerLaunchOptions,
  resolveChromeExecutable,
} = require('../../Scripts/_chrome.js');
const puppeteer = require('puppeteer');

const OUT = process.argv[2];
if (!OUT) {
  console.error('usage: node build-akhand-samaj-icons.js <out-dir>');
  process.exit(1);
}
fs.mkdirSync(OUT, { recursive: true });
const ROOT = path.resolve(OUT, '..', '..');

const COL = {
  navy: '#1A5276',
  lightblue: '#B8DAF3',
  goldPale: '#E8BD92',
  gold: '#D5A477',
  amber: '#C18A5A',
  copper: '#A66E42',
  brownLight: '#C58E5D',
  brownMid: '#B77B48',
  brownDeep: '#A36A39',
  brown: '#8B5E34',
  ivory: '#F7F4EF',
  charcoal: '#2A241C',
};

const DARK_GOALS = [COL.goldPale, COL.gold, COL.amber, COL.copper];
const LIGHT_GOALS = [COL.brownLight, COL.brownMid, COL.brownDeep, COL.brown];
const GOALS = ['resolution', 'prosperity', 'fearlessness', 'coexistence'];

const DESC = 'A central atma nucleus inside an ordered rounded square whose four mid-side joints are resolution, prosperity, fearlessness, and coexistence — the public evidence of an undivided society.';

/* C = large mark. D = optically heavier 16–48 px cut of the same figure.
   Joints are clockwise from the top: resolution, prosperity, fearlessness,
   coexistence. */
const CUTS = {
  c: {
    x: 155,
    size: 690,
    rx: 120,
    stroke: 44,
    jointR: 44,
    atmaR: 92,
    atmaRing: 8,
    joints: [
      [500, 155],
      [845, 500],
      [500, 845],
      [155, 500],
    ],
  },
  d: {
    x: 118,
    size: 764,
    rx: 168,
    stroke: 88,
    jointR: 56,
    atmaR: 188,
    atmaRing: 0,
    joints: [
      [500, 118],
      [882, 500],
      [500, 882],
      [118, 500],
    ],
  },
};

function svgWrap(title, desc, body, viewBox = '0 0 1000 1000') {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="${viewBox}" role="img" aria-labelledby="t d">
  <title id="t">${title}</title>
  <desc id="d">${desc}</desc>
  ${body}
</svg>
`;
}

function orderedSquare(cut, colors) {
  const g = CUTS[cut];
  const parts = [];
  parts.push(`<rect x="${g.x}" y="${g.x}" width="${g.size}" height="${g.size}" rx="${g.rx}" fill="none" stroke="${colors.square}" stroke-width="${g.stroke}"/>`);
  g.joints.forEach(([x, y], i) => {
    parts.push(`<circle cx="${x}" cy="${y}" r="${g.jointR}" fill="${colors.goals[i]}"/>`);
  });
  parts.push(`<circle cx="500" cy="500" r="${g.atmaR}" fill="${colors.atma}"/>`);
  if (g.atmaRing && colors.atmaRing) {
    parts.push(`<circle cx="500" cy="500" r="${g.atmaR}" fill="none" stroke="${colors.atmaRing}" stroke-width="${g.atmaRing}"/>`);
  }
  return parts.join('\n  ');
}

function framed(inner, opts) {
  const body = [];
  if (opts.fullBleed) {
    body.push(`<rect width="1000" height="1000" fill="${opts.bg}"/>`);
    body.push(`<rect x="18" y="18" width="964" height="964" fill="none" stroke="${COL.ivory}" stroke-width="3" opacity="0.16"/>`);
  } else {
    body.push(`<rect x="20" y="20" width="960" height="960" rx="${opts.frameRx || 190}" fill="${opts.bg}"/>`);
    body.push(`<rect x="38" y="38" width="924" height="924" rx="${(opts.frameRx || 190) - 16}" fill="none" stroke="${COL.ivory}" stroke-width="3" opacity="0.16"/>`);
  }
  body.push(inner);
  return body.join('\n  ');
}

const lightC = {
  square: COL.navy,
  goals: LIGHT_GOALS,
  atma: COL.brown,
  atmaRing: COL.ivory,
};
const darkC = {
  square: COL.ivory,
  goals: DARK_GOALS,
  atma: COL.gold,
  atmaRing: COL.ivory,
};
const monoC = {
  square: COL.navy,
  goals: [COL.navy, COL.navy, COL.navy, COL.navy],
  atma: COL.navy,
  atmaRing: null,
};
const reversedC = {
  square: COL.ivory,
  goals: [COL.ivory, COL.ivory, COL.ivory, COL.ivory],
  atma: COL.ivory,
  atmaRing: null,
};
const darkD = {
  square: COL.ivory,
  goals: DARK_GOALS,
  atma: COL.gold,
  atmaRing: null,
};

const variants = {
  'akhand-samaj-badge': svgWrap(
    'Akhand Samaj badge',
    'A rounded navy field containing the ordered-square Akhand Samaj emblem. ' + DESC,
    framed(orderedSquare('c', darkC), { bg: COL.navy }),
  ),
  'akhand-samaj-symbol-light': svgWrap(
    'Akhand Samaj symbol for light backgrounds',
    DESC,
    orderedSquare('c', lightC),
  ),
  'akhand-samaj-symbol-dark': svgWrap(
    'Akhand Samaj symbol for dark backgrounds',
    DESC,
    orderedSquare('c', darkC),
  ),
  'akhand-samaj-monochrome': svgWrap(
    'Akhand Samaj monochrome mark',
    'Single-ink navy version for one-colour reproduction. ' + DESC,
    orderedSquare('c', monoC),
  ),
  'akhand-samaj-reversed': svgWrap(
    'Akhand Samaj reversed mark',
    'One-colour ivory version for dark fields. ' + DESC,
    orderedSquare('c', reversedC),
  ),
  'akhand-samaj-watermark-blue': svgWrap(
    'Akhand Samaj monochrome blue watermark',
    'Full-strength navy source for document watermarks. ' + DESC,
    orderedSquare('c', monoC),
  ),
};

function tiledD(title, desc) {
  return svgWrap(
    title,
    desc,
    framed(orderedSquare('d', darkD), { bg: COL.navy, frameRx: 190 }),
  );
}

const COMPACT = tiledD(
  'Compact Akhand Samaj icon',
  'Sixteen-pixel-first cut of the ordered square for placements around 48–96 px. ' + DESC,
);
const FAVICON = tiledD(
  'Akhand Samaj favicon',
  'Small-scale site mark: atma, rounded square, and four mid-side goal joints. ' + DESC,
);
const APP = svgWrap(
  'Akhand Samaj app icon',
  'Full-bleed app and touch icon. ' + DESC,
  framed(orderedSquare('c', darkC), { bg: COL.navy, fullBleed: true }),
);

for (const [name, svg] of Object.entries(variants)) {
  fs.writeFileSync(path.join(OUT, name + '.svg'), svg);
}
fs.writeFileSync(path.join(OUT, 'akhand-samaj-compact.svg'), COMPACT);
fs.writeFileSync(path.join(OUT, 'akhand-samaj-favicon.svg'), FAVICON);
fs.writeFileSync(path.join(OUT, 'akhand-samaj-app-icon.svg'), APP);

(async () => {
  const executablePath = resolveChromeExecutable();
  if (!executablePath) {
    throw new Error(missingChromeMessage());
  }
  const browser = await puppeteer.launch({
    ...puppeteerLaunchOptions(executablePath),
    args: ['--no-sandbox'],
  });
  const page = await browser.newPage();

  async function raster(svg, outPng, px, bg, opacity = 1) {
    await page.setViewport({ width: px, height: px, deviceScaleFactor: 1 });
    const html = `<!doctype html><meta charset="utf-8"><style>*{margin:0;padding:0}html,body{width:${px}px;height:${px}px;background:${bg || 'transparent'}}.art{width:${px}px;height:${px}px;opacity:${opacity}}svg{display:block;width:${px}px;height:${px}px}</style><div class="art">${svg}</div>`;
    await page.setContent(html, { waitUntil: 'load' });
    await page.screenshot({ path: outPng, omitBackground: !bg });
  }

  for (const [name, svg] of Object.entries(variants)) {
    await raster(svg, path.join(OUT, name + '.png'), 1000);
  }
  await raster(COMPACT, path.join(OUT, 'akhand-samaj-compact.png'), 512);
  await raster(FAVICON, path.join(OUT, 'akhand-samaj-favicon.png'), 512);
  await raster(FAVICON, path.join(OUT, 'akhand-samaj-favicon-16.png'), 16);
  await raster(FAVICON, path.join(OUT, 'akhand-samaj-favicon-32.png'), 32);
  await raster(FAVICON, path.join(OUT, 'akhand-samaj-favicon-48.png'), 48);
  await raster(APP, path.join(OUT, 'akhand-samaj-app-icon.png'), 1024);
  await raster(APP, path.join(OUT, 'akhand-samaj-apple-touch-icon.png'), 180);
  await raster(
    variants['akhand-samaj-watermark-blue'],
    path.join(OUT, 'akhand-samaj-watermark-blue-10.png'),
    1000,
    null,
    0.10,
  );

  const tile = (label, bg, inner, w) => `<div style="display:flex;flex-direction:column;gap:10px;align-items:center">
    <div style="width:${w}px;height:${w}px;border-radius:26px;background:${bg};display:flex;align-items:center;justify-content:center;box-shadow:0 1px 3px rgba(0,0,0,.12)">${inner}</div>
    <div style="font:400 22px/1.2 Cambria,Georgia,serif;color:${COL.charcoal}">${label}</div></div>`;
  const scaled = (svg, w, scale = 0.84) => svg.replace('<svg ', `<svg width="${Math.round(w * scale)}" height="${Math.round(w * scale)}" `);
  const preview = `<!doctype html><meta charset="utf-8"><body style="margin:0;background:#EFE7DA;padding:56px;font-family:Calibri,Arial,sans-serif">
    <div style="font:400 46px/1.1 Cambria,Georgia,serif;color:${COL.navy};margin-bottom:6px">Akhand Samaj icon family</div>
    <div style="font:400 22px/1.4 Calibri,Arial,sans-serif;color:#5B5346;margin-bottom:16px">Atma inside an ordered square · four human goals at the mid-sides</div>
    <div style="font:400 16px/1.35 Calibri,Arial,sans-serif;color:#756C60;margin-bottom:8px">Joints, clockwise from the top:</div>
    <div style="display:flex;align-items:center;gap:10px;font:400 18px/1.35 Calibri,Arial,sans-serif;color:#6B6255;margin-bottom:38px">
      ${GOALS.map((goal, i) => `<span style="display:inline-flex;align-items:center;gap:6px"><i style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${LIGHT_GOALS[i]}"></i>${goal}</span>`).join('<span style="opacity:.45">·</span>')}
    </div>
    <div style="display:flex;gap:34px;flex-wrap:wrap;align-items:flex-start">
      ${tile('Framed badge', COL.ivory, scaled(variants['akhand-samaj-badge'], 260), 260)}
      ${tile('Light symbol', COL.ivory, scaled(variants['akhand-samaj-symbol-light'], 260), 260)}
      ${tile('Dark symbol', COL.charcoal, scaled(variants['akhand-samaj-symbol-dark'], 260), 260)}
      ${tile('Monochrome', COL.ivory, scaled(variants['akhand-samaj-monochrome'], 260), 260)}
      ${tile('Reversed', COL.navy, scaled(variants['akhand-samaj-reversed'], 260), 260)}
    </div>
    <div style="display:flex;gap:34px;flex-wrap:wrap;align-items:flex-start;margin-top:40px">
      ${tile('Compact', COL.ivory, scaled(COMPACT, 180, 0.90), 180)}
      ${tile('48 px', COL.ivory, scaled(COMPACT, 120, 0.40), 120)}
      ${tile('Favicon', COL.ivory, scaled(FAVICON, 180, 0.90), 180)}
      ${tile('App icon', COL.ivory, scaled(APP, 180, 0.90), 180)}
      ${tile('Watermark 10%', '#FFFFFF', `<div style="opacity:.10">${scaled(variants['akhand-samaj-watermark-blue'], 200)}</div>`, 200)}
    </div>
  </body>`;

  await page.setViewport({ width: 1500, height: 1080, deviceScaleFactor: 2 });
  await page.setContent(preview, { waitUntil: 'load' });
  const height = await page.evaluate(() => document.body.scrollHeight);
  await page.setViewport({ width: 1500, height, deviceScaleFactor: 2 });
  await page.screenshot({ path: path.join(OUT, 'akhand-samaj-icon-family-preview.png') });
  await browser.close();
  execFileSync('magick', [
    path.join(OUT, 'akhand-samaj-favicon-16.png'),
    path.join(OUT, 'akhand-samaj-favicon-32.png'),
    path.join(OUT, 'akhand-samaj-favicon-48.png'),
    path.join(OUT, 'akhand-samaj-favicon.ico'),
  ], { stdio: 'inherit' });
  fs.copyFileSync(path.join(OUT, 'akhand-samaj-favicon.ico'), path.join(ROOT, 'favicon.ico'));
  fs.copyFileSync(path.join(OUT, 'akhand-samaj-apple-touch-icon.png'), path.join(ROOT, 'apple-touch-icon.png'));
  console.log('Akhand Samaj icon family built.');
})();
