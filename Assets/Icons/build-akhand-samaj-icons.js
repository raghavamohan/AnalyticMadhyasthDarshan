/* Build the Akhand Samaj icon family — SVG masters, PNG exports,
   compact mark, watermark, and preview sheet. */
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const puppeteer = require('puppeteer');

const OUT = process.argv[2];
if (!OUT) {
  console.error('usage: node build-akhand-samaj-icons.js <out-dir>');
  process.exit(1);
}
fs.mkdirSync(OUT, { recursive: true });

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

const C = 500;
const ATMA_R = 64;
const FACULTIES = [
  { name: 'buddhi', r: 125, width: 25 },
  { name: 'chitta', r: 180, width: 22 },
  { name: 'vritti', r: 235, width: 20 },
  { name: 'mun', r: 290, width: 18 },
];
const GOAL_R = 385;
const GOAL_W = 42;
const JOINT_R = 31;
// Rotate the joint pattern 45° clockwise from 12 o'clock.
const JOINT_ANGLES = [-45, 45, 135, 225];
const CUP_R = JOINT_R + 8;
const GOALS = ['resolution', 'prosperity', 'fearlessness', 'coexistence'];

function polar(cx, cy, r, deg) {
  const a = deg * Math.PI / 180;
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
}

function arcPath(cx, cy, r, startDeg, endDeg) {
  const start = polar(cx, cy, r, startDeg);
  const end = polar(cx, cy, r, endDeg);
  const span = ((endDeg - startDeg) % 360 + 360) % 360;
  return `M${start[0].toFixed(3)} ${start[1].toFixed(3)} A${r} ${r} 0 ${span > 180 ? 1 : 0} 1 ${end[0].toFixed(3)} ${end[1].toFixed(3)}`;
}

const GOAL_ARCS = JOINT_ANGLES.map((angle, i) => {
  const next = i === JOINT_ANGLES.length - 1 ? JOINT_ANGLES[0] + 360 : JOINT_ANGLES[i + 1];
  return arcPath(C, C, GOAL_R, angle, next);
});
const JOINTS = JOINT_ANGLES.map((deg) => polar(C, C, GOAL_R, deg));

const DESC = 'Atma orders the concentric faculties of jeevan — buddhi, chitta, vritti and mun. Their harmony becomes outwardly evident as resolution, prosperity, fearlessness and coexistence, joined through relationship and complementarity.';

function mark(opts) {
  const o = Object.assign({
    frame: false,
    frameRx: 190,
    fullBleed: false,
    bg: null,
    field: null,
    faculty: [COL.ivory, COL.lightblue, COL.ivory, COL.lightblue],
    facultyOpacity: [0.98, 0.84, 0.70, 0.56],
    goals: DARK_GOALS,
    joint: COL.ivory,
    jointCore: COL.navy,
    atma: COL.gold,
    atmaRing: COL.ivory,
  }, opts);

  const body = [];
  const cupMask = `<defs><mask id="goal-cups"><rect width="1000" height="1000" fill="white"/>${JOINTS.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="${CUP_R}" fill="black"/>`).join('')}</mask></defs>`;
  if (o.frame) {
    if (o.fullBleed) {
      body.push(`<rect width="1000" height="1000" fill="${o.bg}"/>`);
      body.push('<rect x="18" y="18" width="964" height="964" fill="none" stroke="#F7F4EF" stroke-width="3" opacity="0.16"/>');
    } else {
      body.push(`<rect x="20" y="20" width="960" height="960" rx="${o.frameRx}" fill="${o.bg}"/>`);
      body.push(`<rect x="38" y="38" width="924" height="924" rx="${o.frameRx - 16}" fill="none" stroke="${COL.ivory}" stroke-width="3" opacity="0.16"/>`);
    }
  }
  if (o.field) {
    body.push(`<circle cx="${C}" cy="${C}" r="452" fill="none" stroke="${o.field}" stroke-width="5" opacity="0.12"/>`);
    body.push(`<circle cx="${C}" cy="${C}" r="337" fill="none" stroke="${o.field}" stroke-width="4" opacity="0.08"/>`);
  }

  FACULTIES.forEach((faculty, i) => {
    body.push(`<circle cx="${C}" cy="${C}" r="${faculty.r}" fill="none" stroke="${o.faculty[i]}" stroke-width="${faculty.width}" opacity="${o.facultyOpacity[i]}"/>`);
  });

  body.push('<g mask="url(#goal-cups)">');
  GOAL_ARCS.forEach((d, i) => {
    body.push(`<path d="${d}" fill="none" stroke="${o.goals[i]}" stroke-width="${GOAL_W}"/>`);
  });
  body.push('</g>');

  JOINTS.forEach(([x, y]) => {
    body.push(`<circle cx="${x}" cy="${y}" r="${JOINT_R}" fill="${o.joint}"/>`);
    body.push(`<circle cx="${x}" cy="${y}" r="10" fill="${o.jointCore}" opacity="0.82"/>`);
  });

  body.push(`<circle cx="${C}" cy="${C}" r="${ATMA_R}" fill="${o.atma}"/>`);
  if (o.atmaRing) {
    body.push(`<circle cx="${C}" cy="${C}" r="${ATMA_R}" fill="none" stroke="${o.atmaRing}" stroke-width="8"/>`);
  }

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" role="img" aria-labelledby="t d">
  <title id="t">${o.title}</title>
  <desc id="d">${o.desc}</desc>
  ${cupMask}
  ${body.join('\n  ')}
</svg>
`;
}

const variants = {
  'akhand-samaj-badge': mark({
    frame: true,
    bg: COL.navy,
    field: COL.ivory,
    title: 'Akhand Samaj badge',
    desc: 'A rounded navy field containing the Akhand Samaj emblem. ' + DESC,
  }),
  'akhand-samaj-symbol-light': mark({
    faculty: [COL.brown, COL.navy, COL.navy, COL.navy],
    facultyOpacity: [0.80, 0.72, 0.54, 0.38],
    goals: LIGHT_GOALS,
    joint: COL.navy,
    jointCore: COL.ivory,
    atma: COL.brown,
    atmaRing: COL.ivory,
    title: 'Akhand Samaj symbol for light backgrounds',
    desc: DESC,
  }),
  'akhand-samaj-symbol-dark': mark({
    title: 'Akhand Samaj symbol for dark backgrounds',
    desc: DESC,
  }),
  'akhand-samaj-monochrome': mark({
    faculty: [COL.navy, COL.navy, COL.navy, COL.navy],
    facultyOpacity: [0.86, 0.70, 0.54, 0.38],
    goals: [COL.navy, COL.navy, COL.navy, COL.navy],
    joint: COL.navy,
    jointCore: COL.ivory,
    atma: COL.navy,
    atmaRing: null,
    title: 'Akhand Samaj monochrome mark',
    desc: 'Single-ink navy version for one-colour reproduction. ' + DESC,
  }),
  'akhand-samaj-reversed': mark({
    faculty: [COL.ivory, COL.ivory, COL.ivory, COL.ivory],
    facultyOpacity: [1, 0.82, 0.64, 0.46],
    goals: [COL.ivory, COL.ivory, COL.ivory, COL.ivory],
    joint: COL.ivory,
    jointCore: COL.navy,
    atma: COL.ivory,
    atmaRing: null,
    title: 'Akhand Samaj reversed mark',
    desc: 'One-colour ivory version for dark fields. ' + DESC,
  }),
  'akhand-samaj-watermark-blue': mark({
    faculty: [COL.navy, COL.navy, COL.navy, COL.navy],
    facultyOpacity: [1, 1, 1, 1],
    goals: [COL.navy, COL.navy, COL.navy, COL.navy],
    joint: COL.navy,
    jointCore: COL.ivory,
    atma: COL.navy,
    atmaRing: null,
    title: 'Akhand Samaj monochrome blue watermark',
    desc: 'Full-strength navy source for document watermarks. ' + DESC,
  }),
};

function compactMark() {
  const cc = 256;
  const goalR = 181;
  const arc = (a, b) => arcPath(cc, cc, goalR, a, b);
  const arcs = JOINT_ANGLES.map((angle, i) => {
    const next = i === JOINT_ANGLES.length - 1 ? JOINT_ANGLES[0] + 360 : JOINT_ANGLES[i + 1];
    return [angle, next];
  });
  const joints = JOINT_ANGLES.map((deg) => polar(cc, cc, goalR, deg));
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-labelledby="t d">
  <title id="t">Compact Akhand Samaj icon</title>
  <desc id="d">Compact form retaining atma, four faculty bands, four human-goal segments and their joints.</desc>
  <defs><mask id="compact-goal-cups"><rect width="512" height="512" fill="white"/>${joints.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="21" fill="black"/>`).join('')}</mask></defs>
  <rect x="12" y="12" width="488" height="488" rx="104" fill="${COL.navy}"/>
  <circle cx="256" cy="256" r="72" fill="none" stroke="${COL.ivory}" stroke-width="13" opacity="0.95"/>
  <circle cx="256" cy="256" r="99" fill="none" stroke="${COL.lightblue}" stroke-width="11" opacity="0.82"/>
  <circle cx="256" cy="256" r="126" fill="none" stroke="${COL.ivory}" stroke-width="9" opacity="0.64"/>
  <circle cx="256" cy="256" r="151" fill="none" stroke="${COL.lightblue}" stroke-width="8" opacity="0.48"/>
  <g mask="url(#compact-goal-cups)">
  ${arcs.map(([a, b], i) => `<path d="${arc(a, b)}" fill="none" stroke="${DARK_GOALS[i]}" stroke-width="25"/>`).join('\n  ')}
  </g>
  ${joints.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="16" fill="${COL.ivory}"/>`).join('\n  ')}
  <circle cx="256" cy="256" r="41" fill="${COL.gold}" stroke="${COL.ivory}" stroke-width="6"/>
</svg>
`;
}

const COMPACT = compactMark();

function faviconMark() {
  const cc = 256;
  // Keep only a narrow optical inset inside the navy tile. The previous
  // radius made the emblem collapse to about 11 px in a 16 px browser tab.
  const goalR = 219;
  const goalW = 45;
  const cupR = 28;
  const jointR = 20;
  const facultyRings = [
    { r: 94, width: 16, color: COL.ivory, opacity: 0.96 },
    { r: 122, width: 15, color: COL.lightblue, opacity: 0.84 },
    { r: 150, width: 14, color: COL.ivory, opacity: 0.70 },
    { r: 178, width: 13, color: COL.lightblue, opacity: 0.58 },
  ];
  const arcs = JOINT_ANGLES.map((angle, i) => {
    const next = i === JOINT_ANGLES.length - 1 ? JOINT_ANGLES[0] + 360 : JOINT_ANGLES[i + 1];
    return arcPath(cc, cc, goalR, angle, next);
  });
  const joints = JOINT_ANGLES.map((deg) => polar(cc, cc, goalR, deg));
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" role="img" aria-labelledby="t d">
  <title id="t">Akhand Samaj favicon</title>
  <desc id="d">Small-scale mark with atma, four faculty bands, and the four joined human-goal segments.</desc>
  <defs><mask id="favicon-goal-cups"><rect width="512" height="512" fill="white"/>${joints.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="${cupR}" fill="black"/>`).join('')}</mask></defs>
  <rect x="12" y="12" width="488" height="488" rx="104" fill="${COL.navy}"/>
  ${facultyRings.map((ring) => `<circle cx="256" cy="256" r="${ring.r}" fill="none" stroke="${ring.color}" stroke-width="${ring.width}" opacity="${ring.opacity}"/>`).join('\n  ')}
  <g mask="url(#favicon-goal-cups)">
  ${arcs.map((d, i) => `<path d="${d}" fill="none" stroke="${DARK_GOALS[i]}" stroke-width="${goalW}"/>`).join('\n  ')}
  </g>
  ${joints.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="${jointR}" fill="${COL.ivory}"/>`).join('\n  ')}
  <circle cx="256" cy="256" r="66" fill="${COL.gold}" stroke="${COL.ivory}" stroke-width="11"/>
</svg>
`;
}

const FAVICON = faviconMark();
const APP = mark({
  frame: true,
  fullBleed: true,
  bg: COL.navy,
  field: COL.ivory,
  title: 'Akhand Samaj app icon',
  desc: 'Full-bleed app and touch icon. ' + DESC,
});

for (const [name, svg] of Object.entries(variants)) {
  fs.writeFileSync(path.join(OUT, name + '.svg'), svg);
}
fs.writeFileSync(path.join(OUT, 'akhand-samaj-compact.svg'), COMPACT);
fs.writeFileSync(path.join(OUT, 'akhand-samaj-favicon.svg'), FAVICON);
fs.writeFileSync(path.join(OUT, 'akhand-samaj-app-icon.svg'), APP);

(async () => {
  const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
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
    <div style="font:400 22px/1.4 Calibri,Arial,sans-serif;color:#5B5346;margin-bottom:16px">Atma · buddhi · chitta · vritti · mun · harmony evidenced in the four human goals</div>
    <div style="font:400 16px/1.35 Calibri,Arial,sans-serif;color:#756C60;margin-bottom:8px">Outer segments, clockwise from the right:</div>
    <div style="display:flex;align-items:center;gap:10px;font:400 18px/1.35 Calibri,Arial,sans-serif;color:#6B6255;margin-bottom:38px">
      ${GOALS.map((goal, i) => `<span style="display:inline-flex;align-items:center;gap:6px"><i style="display:inline-block;width:18px;height:6px;border-radius:6px;background:${LIGHT_GOALS[i]}"></i>${goal}</span>`).join('<span style="opacity:.45">·</span>')}
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
  console.log('Akhand Samaj icon family built.');
})();
