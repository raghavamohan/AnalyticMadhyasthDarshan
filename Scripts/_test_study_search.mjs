import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const S = require('../Assets/reader/search.js');
const R = require('../Assets/reader/reader-features.js');

assert.deepEqual(S.terms('time TIME "duration of activity"'), ['time','duration of activity']);
assert.throws(() => S.terms('"unfinished'), /Close the quotation/);
assert.throws(() => S.terms('x'.repeat(201)), /200/);
assert.deepEqual(S.terms(' "" '), []);
assert.deepEqual(S.match('Time is timeless; time.',S.terms('time')), [[0,4],[18,22]]);
assert.deepEqual(S.match('duration\n  of activity',S.terms('"duration of activity"')), [[0,22]]);
assert.deepEqual(S.match('jīvan and satta',S.terms('jivan satta')), [[0,5],[10,15]]);
assert.deepEqual(S.match('jīvan alone',S.terms('jivan satta')), []);
assert.deepEqual(S.match('cafe\u0301',S.terms('café')), [[0,5]]);
assert.equal(S.fold('ज्ञान जीवन शिव शव'), 'ज्ञान जीवन शिव शव');
assert.deepEqual(S.match('शिव शव',S.terms('शव')), [[4,6]]);
assert.deepEqual(S.match('ज्ञान अज्ञान',S.terms('ज्ञान')), [[0,5]]);
assert.deepEqual(S.match('x [a+b] x',S.terms('[a+b]')), [[2,7]]);
assert.deepEqual(S.match('time duration',S.terms('time "time duration"')), [[0,13]]);
assert.equal(S.search([{id:'one',text:'Time passes.'},{id:'two',text:'A duration.'}],S.terms('time duration')).length,0);
assert.match(S.excerpt('x'.repeat(400) + ' time',[[401,405]]), /^…/);
const link = new URL(S.passageURL('/Applications/A/A.html?old=1',{id:'reader-p-one',heading:'section'},'"time"','12345678901234567890'));
assert.equal(link.origin,'https://analyticmadhyasthdarshan.org');
assert.equal(link.hash,'#reader-p-one');
assert.equal(link.searchParams.get('find'),'"time"');
assert.equal(link.searchParams.get('pv'),'1234567890123456');
assert.equal(link.searchParams.get('old'),null);
for (const url of ['https://evil.example/Studies/A/A.html','//evil.example/Studies/A/A.html','javascript:alert(1)','/Studies/../private.html']) {
  assert.throws(() => S.passageURL(url,{id:'passage'}));
}
assert.equal(R.safeURL('javascript:alert(1)','https://example.org'),null);
assert.equal(R.safeURL('data:text/html,hi','https://example.org'),null);
assert.equal(R.safeURL('../source.pdf#page=7','https://example.org/Studies/A/A.html'),'https://example.org/Studies/source.pdf#page=7');
assert.equal(R.cited('MVD, pp. 3–7','MVD'),true);
assert.equal(R.cited('AMVD, p. 4','MVD'),false);
assert.equal(R.cited('(A+B, p. 4)','A+B'),true);
console.log('Passage query, Unicode offsets and source URL checks passed');
