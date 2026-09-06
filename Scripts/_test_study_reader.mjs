import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { preferences, passageKey, cursor, state, resolvePlace, lastBefore, readingIndex } = require('../Assets/reader/reader.js');

assert.deepEqual(preferences({ fontSize: '900px', lineHeight: -1, width: 10000, sidebar: 'false' }),
  { fontSize: 18, lineHeight: 1.75, width: 68, sidebar: true });
assert.deepEqual(preferences({ fontSize: 24, lineHeight: 2, width: 56, sidebar: false }),
  { fontSize: 24, lineHeight: 2, width: 56, sidebar: false });

// Whitespace and Unicode normalization must not orphan a saved paragraph.
assert.equal(passageKey('  Time\n is duration. '), passageKey('Time is duration.'));
assert.equal(passageKey('e\u0301'), passageKey('é'));
assert.notEqual(passageKey('जीवन'), passageKey('जीवन ज्ञान'));
assert.match(passageKey('§1 <script>'), /^reader-p-[a-f0-9]{16}$/);

const place = { anchor: 'paragraph-a', heading: 'section-1', quote: 'A sufficiently long saved quotation for recovery.', label: 'First section', fraction: 0.45 };
assert.equal(cursor({ ...place, fraction: Infinity }), null);
assert.equal(cursor({ ...place, anchor: '' }), null);
assert.equal(cursor({ ...place, anchor: 'x'.repeat(401) }), null);
assert.equal(cursor({ ...place, fraction: 2 }).fraction, 1);
assert.equal(cursor({ ...place, quote: 'x'.repeat(200) }).quote.length, 160);
assert.throws(() => state({ version: 2, bookmarks: [] }));
assert.throws(() => state({ version: 1, bookmarks: null }));
const hostileName = '<img src=x onerror=alert(1)>';
const restored = state({ version: 1, position: place, bookmarks: [
  { id: 'valid-1', name: hostileName, place },
  { id: 'valid-1', name: 'duplicate', place },
  { id: '../../escape', name: 'invalid identifier', place },
  { id: 'invalid-place', place: { ...place, fraction: NaN } },
] });
assert.equal(restored.bookmarks.length, 1);
// Untrusted names remain strings; DOM rendering uses textContent.
assert.equal(restored.bookmarks[0].name, hostileName);
assert.deepEqual(restored.position, place);
assert.equal(state({ version: 1, bookmarks: Array.from({ length: 120 }, (_, i) => ({ id: 'id-' + i, name: 'n'.repeat(100), place })) }).bookmarks.length, 100);

const exact = { id: place.anchor, heading: place.heading, text: place.quote };
const section = { id: place.heading, text: 'First section' };
assert.deepEqual(resolvePlace(place, [exact], [section]), { item: exact, fraction: 0.45, changed: false });
const revised = { ...exact, id: 'changed-paragraph', text: 'New introduction. ' + place.quote };
assert.deepEqual(resolvePlace(place, [revised], [section]), { item: revised, fraction: 0, changed: true });
// Repeated quotations or a match in a different section must never guess.
assert.equal(resolvePlace(place, [revised, { ...revised, id: 'duplicate' }], [section]).item, section);
assert.equal(resolvePlace(place, [{ ...revised, heading: 'elsewhere' }], [section]).item, section);
assert.equal(resolvePlace(place, [{ ...exact, heading: 'elsewhere' }], [section]).item, section);
assert.equal(resolvePlace(place, [{ ...exact, text: 'Different text reusing an old heading ID.' }], [section]).changed, true);
assert.equal(resolvePlace({ ...place, quote: 'short' }, [revised], [section]).item, section);
assert.equal(resolvePlace(place, [], []), null);
assert.equal(resolvePlace(null, [exact], [section]), null);

const offsets = [{ top: 100 }, { top: 300 }, { top: 450 }];
assert.equal(lastBefore([], 100), -1);
assert.equal(lastBefore(offsets, 99), -1);
assert.equal(lastBefore(offsets, 100), 0);
assert.equal(lastBefore(offsets, 449.5), 1);
assert.equal(lastBefore(offsets, 900), 2);

// Real reader headings land on fractional coordinates. Rounded scroll/focus
// positions must advance from Scope through the first and subsequent sections.
const sections = [
  { id: 'scope', top: 715.7734375 },
  { id: 'first', top: 2009.109375 },
  { id: 'second', top: 32434.234375 },
];
assert.equal(readingIndex([], 100), -1);
assert.equal(readingIndex(sections, 0), -1);
for (const [index, section] of sections.entries()) {
  assert.equal(readingIndex(sections, section.top - 2.01), index - 1);
  for (const y of [section.top, Math.floor(section.top), Math.floor(section.top) - 1, Math.ceil(section.top)]) {
    const current = readingIndex(sections, y);
    assert.equal(current, index, `Identify ${section.id} at rounded position ${y}`);
    assert.equal(sections[current + 1]?.id, sections[index + 1]?.id, 'Next advances or stops at the final section');
    assert.equal(sections[current - 1]?.id, sections[index - 1]?.id, 'Previous returns without skipping a section');
  }
}
assert.equal(readingIndex(sections, 40000), 2);
console.log('Reader preference, storage validation, passage recovery and navigation tests passed.');
