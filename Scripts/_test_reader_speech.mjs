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
  const synth = engine(), time = clock(), states = [], errors = [], played = [], words = [];
  let finished = 0;
  const player = S.createPlayer({synth,Utterance,...time,onState:s => states.push(s),onError:e => errors.push(e),
    onChunk:(p,i) => played.push(i),onWord:p => words.push(p),onFinish:() => finished++});
  return {synth,time,states,errors,played,words,player,get finished() { return finished; }};
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
  setAttribute(name,value) { this[name] = value; }
  removeAttribute(name) { delete this[name]; }
  scrollIntoView() { this.revealed = true; }
  focus() { this.focused = true; }
}
function integration() {
  const time = clock(), synth = Object.assign(new Node(),engine());
  let available = [], nativeSelection = null;
  synth.getVoices = () => available;
  const ids = [...fs.readFileSync(new URL('_study_reader.py',import.meta.url),'utf8').matchAll(/id="([a-z-]+)"/g)].map(m => m[1]);
  const nodes = new Map(ids.map(id => [id,new Node(id)]));
  for (const id of ['reader-read','reader-read-stop']) nodes.set(id,new Node(id));
  nodes.get('listen-speed').value = '1';
  const main = new Node('main');
  function passage(id,text,tag = 'p') {
    const node = new Node(), textNode = {textContent:text,length:text.length,parentElement:{closest:() => null}};
    node.matches = selector => selector.split(',').includes(tag);
    return {id,heading:'section',subheading:'subsection',text,node,textNode};
  }
  const heading = passage('heading','Section heading','h3');
  const first = passage('p-1','The selected paragraph is preserved on a phone.');
  const second = passage('p-2','This clicked paragraph is read without selecting text.');
  const long = passage('p-long','Long prose '.repeat(650));
  const passages = [heading,first,second,long];
  main.contains = n => passages.some(p => p.node === n || p.textNode === n);
  const document = new Node();
  Object.assign(document,{readyState:'loading',currentScript:{dataset:{}},documentElement:{lang:'en',hasAttribute:() => false},
    getElementById:id => nodes.get(id) || null,
    querySelector:selector => selector === 'h1' ? {textContent:'Test study'} : {content:'abc',getBoundingClientRect:() => ({bottom:0})},
    querySelectorAll:() => ['notes-new','selection-note','selection-highlight'].map(id => nodes.get(id)),
    createElement:() => new Node(),
    createRange:() => ({setStart() {},setEnd() {},getBoundingClientRect:() => ({height:0})}),
    createTreeWalker:root => { let seen = false; return {nextNode:() => seen ? null : (seen = true,passages.find(p => p.node === root).textNode)}; },
  });
  const window = Object.assign(new Node(),{speechSynthesis:synth,SpeechSynthesisUtterance:Utterance,
    AMDReaderSpeech:{...S,createPlayer:options => S.createPlayer({...options,...time})},
    AMDNotes:{...C,openStore:() => new Promise(() => {})},getSelection:() => nativeSelection});
  const sandbox = {window,document,location:{pathname:'/Studies/Test/Test.html'},navigator:{languages:['en-IN']},
    getSelection:window.getSelection,NodeFilter:{SHOW_TEXT:4,FILTER_REJECT:2,FILTER_ACCEPT:1},
    setTimeout:time.setTimer,clearTimeout:time.clearTimer,console};
  vm.runInNewContext(fs.readFileSync(new URL('../Assets/reader/study-tools.js',import.meta.url),'utf8'),sandbox);
  let place = 'p-1', changePlace = () => {}, tab = null;
  const context = {main,tools:nodes.get('reader-tools'),wide:{matches:false},passages,
    headings:[{id:'subsection',text:'1.1 Current subsection'}],
    currentPlace:() => ({anchor:place}),onPlaceChange:listener => { changePlace = listener; },
    selectTab:name => { tab = name; },openPanel:() => { nativeSelection = null; nodes.get('reader-tools').open = true; }};
  window.AMDStudyTools(context); // Deliberately never awaits IndexedDB.
  function select(start,end,p = first) {
    const textNode = p.textNode;
    nativeSelection = {rangeCount:1,isCollapsed:false,anchorNode:textNode,getRangeAt:() => ({
      commonAncestorContainer:p.node,startContainer:textNode,endContainer:textNode,startOffset:start,endOffset:end,
      intersectsNode:n => n === p.node || n === textNode,
    })};
  }
  return {time,synth,nodes,main,document,first,second,long,select,
    voices(value) { available = value; synth.fire('voiceschanged'); },
    place(value) { place = value; changePlace(); },
    get tab() { return tab; },get nativeSelection() { return nativeSelection; }};
}
{
  const f = integration(), {time,synth,nodes,main,document,first,second,select} = f;
  assert.equal(nodes.get('listen-test').disabled,true);
  assert.equal(nodes.get('selection-note').disabled,true);
  assert.equal(synth.spoken.length,0,'initialization never plays audio');
  assert.equal(nodes.get('listen-selection-preview').textContent,first.text);
  assert.match(nodes.get('listen-selection-label').textContent,/Read from here/);
  f.voices([hindi,remote,english]);
  assert.equal(nodes.get('listen-voice').value,'en');
  assert.equal(nodes.get('listen-voice').children.length,2,'remote voices stay excluded');
  assert.equal(nodes.get('listen-test').disabled,false,'Listen works before notes storage opens');
  assert.equal(nodes.get('listen-start').disabled,false,'current paragraph needs no native selection');
  nodes.get('reader-tab-listen').fire('click');
  assert.equal(synth.spoken.length,0,'opening Listen never starts audio');
  f.place('p-2');
  assert.equal(nodes.get('listen-selection-preview').textContent,second.text);
  assert.equal(nodes.get('listen-selection-section').textContent,'1.1 Current subsection');
  nodes.get('listen-start').fire('click');
  assert.equal(synth.spoken.at(-1).text.trim(),second.text,'Read paragraph starts synchronously');
  synth.spoken.at(-1).onstart();
  f.place('p-1');
  assert.equal(nodes.get('listen-selection-preview').textContent,second.text,'scrolling cannot relabel the paragraph being spoken');
  assert.equal(nodes.get('listen-start').textContent,'Pause');
  nodes.get('listen-start').fire('click');
  assert.equal(nodes.get('listen-resume').disabled,false);
  assert.equal(nodes.get('listen-start').textContent,'Resume');
  nodes.get('listen-start').fire('click');
  assert.equal(synth.spoken.at(-1).text.trim(),second.text);
  nodes.get('listen-stop').fire('click');
  assert.equal(nodes.get('listen-selection-preview').textContent,first.text,'stopping restores the current reading target');
  const beforeTest = synth.spoken.length;
  nodes.get('listen-test').fire('click'); assert.equal(synth.spoken.length,beforeTest + 1);
  assert.equal(nodes.get('listen-pause').disabled,true,'starting is not yet speaking');
  time.flush(); assert.match(nodes.get('listen-status').textContent,/did not start/);
  assert.equal(nodes.get('listen-test').disabled,false);
  select(0,12); document.fire('selectionchange'); time.flush();
  assert.equal(nodes.get('listen-selection-preview').textContent,first.text.slice(0,12));
  f.place('p-2');
  assert.equal(nodes.get('listen-selection-preview').textContent,first.text.slice(0,12),'selected text takes precedence over reading position');
  // Capture the final drag-handle adjustment before the debounce or dialog focus.
  select(0,first.text.length);
  document.fire('selectionchange');
  document.fire('pointerdown',{target:nodes.get('selection-listen')});
  const beforeRead = synth.spoken.length;
  nodes.get('selection-listen').fire('click');
  assert.equal(synth.spoken.length,beforeRead + 1,'floating Read speaks in the same click, without another Read tap');
  assert.equal(synth.spoken.at(-1).text,first.text);
  assert.equal(f.tab,'listen');
  assert.equal(nodes.get('listen-stop').revealed,true,'direct Read brings playback controls into view');
  assert.equal(nodes.get('listen-stop').focused,true,'keyboard focus follows the selected-text action into Listen');
  synth.spoken.at(-1).onstart();
  document.fire('selectionchange'); time.flush();
  assert.equal(f.nativeSelection,null);
  assert.equal(nodes.get('listen-selection-preview').textContent,first.text);
  assert.equal(nodes.get('listen-start').disabled,false,'the primary control remains available to pause');
  assert.equal(nodes.get('listen-start').textContent,'Pause');
  document.fire('pointerdown',{target:nodes.get('listen-start')});
  assert.equal(nodes.get('reader-selection-tools').hidden,true,'playback controls do not reopen the floating selection toolbar');
  assert.equal(nodes.get('listen-pause').disabled,false);
  synth.fire('voiceschanged'); assert.match(nodes.get('listen-status').textContent,/Reading 1/);
  nodes.get('listen-stop').fire('click');
  select(0,12); document.fire('selectionchange'); time.flush();
  assert.equal(nodes.get('reader-selection-tools').hidden,true,'native range updates behind an open mobile drawer do not reveal floating controls');
  main.fire('pointerdown');
  assert.equal(nodes.get('listen-start').disabled,false);
  assert.match(nodes.get('listen-selection-label').textContent,/Read from here/);
  assert.equal(nodes.get('listen-selection-preview').textContent,second.text);
  assert.equal(nodes.get('listen-test').disabled,false);
  f.place('heading');
  assert.equal(nodes.get('listen-selection-preview').textContent,first.text,'a heading offers its following prose paragraph');
  f.place('p-long');
  assert.equal(nodes.get('listen-start').disabled,false,'continuous reading accepts long paragraphs');
  assert.equal(nodes.get('listen-selection-hint').hidden,true);
  select(0,f.long.text.length,f.long); document.fire('selectionchange'); time.flush();
  assert.equal(nodes.get('listen-start').disabled,true);
  assert.match(nodes.get('listen-selection-hint').textContent,/Select up to 6,000/);
}
{
  const f = integration();
  f.select(0,f.first.text.length); f.document.fire('selectionchange'); f.time.flush();
  f.nodes.get('selection-listen').fire('click');
  assert.equal(f.tab,'listen');
  assert.equal(f.synth.spoken.length,0);
  assert.match(f.nodes.get('listen-status').textContent,/No device voices/);
  f.voices([english]);
  assert.equal(f.synth.spoken.length,0,'late voices never cause deferred autoplay');
  f.nodes.get('listen-start').fire('click');
  assert.equal(f.synth.spoken.at(-1).text,f.first.text);
}
{
  const f = fixture(); f.player.play(plan);
  const u = f.synth.spoken[0]; u.onstart();
  u.onboundary({name:'word',charIndex:4,charLength:0});
  assert.equal(plan.text.slice(f.words[0].start,f.words[0].end),'sentence');
  u.onboundary({name:'sentence',charIndex:0});
  u.onboundary({name:'word',charIndex:999});
  assert.equal(f.words.length,1);
  f.player.pause(); u.onboundary({name:'word',charIndex:0});
  assert.equal(f.words.length,1,'late boundaries cannot paint after pause');
  f.player.resume(); const next = f.synth.spoken.at(-1); next.onstart(); next.onend();
  const last = f.synth.spoken.at(-1); last.onstart(); last.onboundary({name:'word',charIndex:0});
  assert.equal(plan.text.slice(f.words.at(-1).start,f.words.at(-1).end),'Another','word offsets include the chunk offset');
  f.player.stop(); last.onboundary({name:'word',charIndex:0}); assert.equal(f.words.length,2);
}
{
  const f = integration(); f.voices([english]); f.place('p-2');
  f.nodes.get('reader-read').fire('click');
  assert.equal(f.tab,null,'top-bar Read keeps the document visible');
  let u = f.synth.spoken.at(-1); u.onstart();
  assert.equal(f.nodes.get('reader-read').textContent,'Pause');
  f.nodes.get('reader-read').fire('click');
  assert.equal(f.nodes.get('reader-read').textContent,'Resume');
  f.nodes.get('reader-read').fire('click');
  let heard = '', count = 0;
  while (f.nodes.get('reader-read').textContent !== 'Read' && count++ < 100) {
    u = f.synth.spoken.at(-1); heard += u.text; u.onstart(); u.onend();
  }
  assert.equal(heard.trimEnd(),(f.second.text + '\n' + f.long.text).trimEnd(),'continues through a paragraph longer than 6,000 characters to the end');
  assert.equal(f.nodes.get('reader-read-stop').hidden,true);
  f.nodes.get('reader-read').fire('click'); u = f.synth.spoken.at(-1); u.onstart();
  f.nodes.get('reader-read-stop').fire('click');
  const countBefore = f.synth.spoken.length; u.onend();
  assert.equal(f.synth.spoken.length,countBefore,'Stop prevents queued continuation');
}
console.log('Reader speech: continuous reading, toolbar controls, word boundaries, selection, mobile pause/resume and errors passed.');
