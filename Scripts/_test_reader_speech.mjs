/* Regressions for mobile speech engines and native-selection event ordering. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const S = require('../Assets/reader/speech-core.js');
const C = require('../Assets/reader/notes-core.js');
const english = {voiceURI:'en',name:'English',lang:'en-IN',localService:true,default:true};
const hindi = {voiceURI:'hi',name:'Hindi',lang:'hi-IN',localService:true};
const remote = {...english,voiceURI:'remote',localService:false};

function clock() {
  let id = 0; const timers = new Map();
  return {setTimer(fn) { timers.set(++id,fn); return id; },clearTimer(key) { timers.delete(key); },
    flush() { const pending = [...timers.values()]; timers.clear(); pending.forEach(fn => fn()); },timers};
}
class Utterance { constructor(text) { this.text = text; } }
function engine() {
  return {speaking:false,pending:false,paused:false,spoken:[],calls:[],
    cancel() { this.calls.push('cancel'); this.speaking = this.pending = false; },
    pause() { throw Error('Android has no usable native pause/resume pair'); },
    resume() { this.calls.push('resume'); this.paused = false; },
    speak(u) { this.calls.push('speak'); this.pending = true; this.spoken.push(u); },
  };
}
function fixture() {
  const synth = engine(), time = clock(), states = [], errors = [], played = [];
  let finished = 0;
  const player = S.createPlayer({synth,Utterance,...time,onState:s => states.push(s),onError:e => errors.push(e),
    onChunk:(p,i) => played.push(i),onFinish:() => finished++});
  return {synth,time,states,errors,played,player,get finished() { return finished; }};
}
const plan = {text:'One sentence. Another sentence.',voice:english,rate:1.25};

// Long paragraphs remain intact, bounded, and aligned to the original text.
for (const text of ['A '.repeat(1600),'पाठ और अर्थ। '.repeat(80),'x'.repeat(199) + '😀'.repeat(220),'word '.repeat(40) + ' tail.']) {
  const pieces = S.chunks(text,'en-IN');
  assert.equal(pieces.map(p => text.slice(p.start,p.end)).join('').trim(),text.trim());
  for (const p of pieces) {
    assert.ok(p.end - p.start <= 200);
    assert.doesNotMatch(text.slice(p.start,p.end),/^[\uDC00-\uDFFF]|[\uD800-\uDBFF]$/u);
  }
}
assert.ok(S.chunks('A long selection. Another part.','invalid_voice_tag').length);
assert.equal(S.chooseVoice([hindi,remote,english],'','en',['en-IN']),english);
assert.equal(S.chooseVoice([hindi,english],'hi','en'),hindi);
assert.equal(S.chooseVoice([remote],'remote','en'),undefined);

{
  const f = fixture();
  f.player.play(plan);
  assert.deepEqual(f.synth.calls,['speak'],'first speech is synchronous without unnecessary cancel');
  assert.equal(f.player.state,'starting');
  const first = f.synth.spoken[0]; assert.equal(first.rate,1.25); assert.equal(first.voice,english);
  first.onstart(); assert.equal(f.player.state,'speaking'); assert.equal(f.time.timers.size,0);
  f.player.pause(); assert.equal(f.player.state,'paused');
  first.onend(); first.onerror({error:'interrupted'});
  assert.equal(f.synth.spoken.length,1); assert.equal(f.errors.length,0);
  f.player.resume(); const repeated = f.synth.spoken.at(-1);
  assert.equal(repeated.text,first.text,'Resume restarts the paused chunk on Android');
  first.onstart(); assert.equal(f.player.state,'starting','late old callbacks cannot change a resumed run');
  repeated.onstart(); repeated.onend();
  const last = f.synth.spoken.at(-1); assert.equal(last.text,'Another sentence.');
  last.onstart(); last.onend();
  assert.equal(f.player.state,'idle'); assert.equal(f.finished,1); assert.equal(f.time.timers.size,0);
}
{
  const f = fixture(); f.synth.paused = true; f.player.play(plan);
  assert.deepEqual(f.synth.calls,['cancel','resume','speak']);
  const old = f.synth.spoken[0]; f.time.flush();
  assert.equal(f.player.state,'idle'); assert.deepEqual(f.errors,['start-timeout']);
  old.onstart(); old.onend(); assert.equal(f.player.state,'idle'); assert.equal(f.synth.spoken.length,1);
  f.player.play(plan); assert.equal(f.player.state,'starting','a stalled engine can be retried');
  f.player.stop(); f.time.flush(); assert.equal(f.errors.length,1);
}
{
  const f = fixture(); f.player.play(plan); const first = f.synth.spoken[0]; first.onstart();
  f.synth.speak = () => { throw Error('engine failure on second chunk'); };
  first.onend(); assert.equal(f.player.state,'idle'); assert.deepEqual(f.errors,['speech-failed']);
  first.onend(); assert.equal(f.errors.length,1);
}
{
  const f = fixture(); f.player.play(plan); f.synth.spoken[0].onerror({error:'voice-unavailable'});
  assert.equal(f.player.state,'idle'); assert.deepEqual(f.errors,['voice-unavailable']);
}

// Run the actual DOM integration with storage held pending. A phone can emit
// selectionchange after pointerup, then collapse selection as the dialog opens.
class Node {
  constructor(id = '') { this.id = id; this.listeners = {}; this.children = []; this.value = ''; this.hidden = false; this.disabled = false; this.textContent = ''; this.dataset = {}; }
  addEventListener(name,fn) { (this.listeners[name] ||= []).push(fn); }
  fire(name,event = {}) { for (const fn of this.listeners[name] || []) fn({target:this,...event}); }
  after() {}
  append(node) { this.children.push(node); if (!this.value) this.value = node.value; }
  replaceChildren() { this.children = []; this.value = ''; }
  closest() { return this.id ? this : null; }
}
{
  const time = clock(), synth = Object.assign(new Node(),engine());
  let available = [], nativeSelection = null;
  synth.getVoices = () => available;
  const ids = [...fs.readFileSync(new URL('_study_reader.py',import.meta.url),'utf8').matchAll(/id="([a-z-]+)"/g)].map(m => m[1]);
  const nodes = new Map(ids.map(id => [id,new Node(id)]));
  nodes.get('listen-speed').value = '1';
  const main = new Node('main'), paragraph = new Node();
  const textNode = {textContent:'The selected paragraph is preserved on a phone.',length:47,parentElement:{closest:() => null}};
  textNode.length = textNode.textContent.length;
  paragraph.matches = () => false;
  main.contains = n => n === paragraph || n === textNode;
  const document = new Node();
  Object.assign(document,{readyState:'loading',currentScript:{dataset:{}},documentElement:{lang:'en',hasAttribute:() => false},
    getElementById:id => nodes.get(id) || null,
    querySelector:selector => selector === 'h1' ? {textContent:'Test study'} : {content:'abc'},
    querySelectorAll:() => ['notes-new','selection-note','selection-highlight'].map(id => nodes.get(id)),
    createElement:() => new Node(),
    createTreeWalker:() => { let seen = false; return {nextNode:() => seen ? null : (seen = true,textNode)}; },
  });
  const window = Object.assign(new Node(),{speechSynthesis:synth,SpeechSynthesisUtterance:Utterance,
    AMDReaderSpeech:{...S,createPlayer:options => S.createPlayer({...options,...time})},
    AMDNotes:{...C,openStore:() => new Promise(() => {})},getSelection:() => nativeSelection});
  const sandbox = {window,document,location:{pathname:'/Studies/Test/Test.html'},navigator:{languages:['en-IN']},
    getSelection:window.getSelection,NodeFilter:{SHOW_TEXT:4,FILTER_REJECT:2,FILTER_ACCEPT:1},
    setTimeout:time.setTimer,clearTimeout:time.clearTimer,console};
  vm.runInNewContext(fs.readFileSync(new URL('../Assets/reader/study-tools.js',import.meta.url),'utf8'),sandbox);
  const context = {main,tools:nodes.get('reader-tools'),wide:{matches:false},passages:[{id:'p-1',heading:'section',text:textNode.textContent,node:paragraph}],selectTab:() => {},openPanel:() => { nativeSelection = null; nodes.get('reader-tools').open = true; }};
  window.AMDStudyTools(context); // Deliberately never awaits IndexedDB.
  assert.equal(nodes.get('listen-test').disabled,true);
  assert.equal(nodes.get('selection-note').disabled,true);
  assert.equal(synth.spoken.length,0,'initialization never plays audio');
  available = [hindi,remote,english]; synth.fire('voiceschanged');
  assert.equal(nodes.get('listen-voice').value,'en');
  assert.equal(nodes.get('listen-voice').children.length,2,'remote voices stay excluded');
  assert.equal(nodes.get('listen-test').disabled,false,'Listen works before notes storage opens');
  nodes.get('listen-test').fire('click'); assert.equal(synth.spoken.length,1);
  assert.equal(nodes.get('listen-pause').disabled,true,'starting is not yet speaking');
  time.flush(); assert.match(nodes.get('listen-status').textContent,/did not start/);
  assert.equal(nodes.get('listen-test').disabled,false);
  function select(start,end) {
    nativeSelection = {rangeCount:1,isCollapsed:false,anchorNode:textNode,getRangeAt:() => ({
      commonAncestorContainer:paragraph,startContainer:textNode,endContainer:textNode,startOffset:start,endOffset:end,intersectsNode:() => true,
    })};
  }
  select(0,12); document.fire('selectionchange'); time.flush();
  assert.equal(nodes.get('listen-selection-preview').textContent,textNode.textContent.slice(0,12));
  // Capture the final drag-handle adjustment before the debounce or dialog focus.
  select(0,textNode.length);
  document.fire('selectionchange');
  document.fire('pointerdown',{target:nodes.get('selection-listen')});
  nodes.get('selection-listen').fire('click');
  document.fire('selectionchange'); time.flush();
  assert.equal(nativeSelection,null);
  assert.equal(nodes.get('listen-selection-preview').textContent,textNode.textContent);
  assert.equal(nodes.get('listen-start').disabled,false);
  document.fire('pointerdown',{target:nodes.get('listen-start')});
  assert.equal(nodes.get('reader-selection-tools').hidden,true,'playback controls do not reopen the floating selection toolbar');
  nodes.get('listen-start').fire('click');
  assert.equal(synth.spoken.at(-1).text,textNode.textContent);
  synth.spoken.at(-1).onstart(); assert.equal(nodes.get('listen-pause').disabled,false);
  synth.fire('voiceschanged'); assert.match(nodes.get('listen-status').textContent,/Reading 1/);
  nodes.get('listen-stop').fire('click');
  select(0,12); document.fire('selectionchange'); time.flush();
  assert.equal(nodes.get('reader-selection-tools').hidden,true,'native range updates behind an open mobile drawer do not reveal floating controls');
  main.fire('pointerdown');
  assert.equal(nodes.get('listen-start').disabled,true);
  assert.match(nodes.get('listen-selection-label').textContent,/No passage/);
  assert.equal(nodes.get('listen-test').disabled,false);
}
console.log('Reader speech: mobile selection, delayed storage/voices, chunking, pause/resume, stalls and errors passed.');
