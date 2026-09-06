/* Device speech: short utterances and cancel/restart pause work on Android too. */
(function(root,factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AMDReaderSpeech = api;
})(typeof globalThis !== 'undefined' ? globalThis : this,() => {
  'use strict';
  function chunks(text,language) {
    let sentences = [{index:0,segment:text}];
    try { if (typeof Intl.Segmenter === 'function') sentences = [...new Intl.Segmenter(language,{granularity:'sentence'}).segment(text)]; }
    catch (_) { /* A device may return a nonstandard language tag. */ }
    const result = [];
    for (const {index,segment} of sentences) for (let start = 0; start < segment.length;) {
      let end = Math.min(start + 200,segment.length);
      if (end < segment.length) {
        const space = segment.lastIndexOf(' ',end - 1);
        if (space > start + 60) end = space + 1;
        // Never cut between the two UTF-16 code units of a character.
        if (/[\uD800-\uDBFF]/.test(segment[end - 1])) end--;
      }
      if (segment.slice(start,end).trim()) result.push({start:index + start,end:index + end});
      start = end;
    }
    return result;
  }
  function chooseVoice(voices,previous,language,languages = []) {
    const local = voices.filter(v => v.localService), normalize = s => (s || '').replace(/_/g,'-').toLowerCase();
    const lang = normalize(language), family = lang.split('-')[0];
    const preferred = local.find(v => v.voiceURI === previous);
    if (preferred) return preferred;
    const matching = local.filter(v => normalize(v.lang).split('-')[0] === family);
    const regional = languages.map(normalize).filter(l => l.split('-')[0] === family);
    return matching.find(v => v.default) || matching.find(v => normalize(v.lang) === lang) ||
      regional.map(l => matching.find(v => normalize(v.lang) === l)).find(Boolean) || matching[0] ||
      local.find(v => v.default) || local[0];
  }
  function createPlayer({synth,Utterance,onState = () => {},onChunk = () => {},onError = () => {},onFinish = () => {},
    setTimer = setTimeout,clearTimer = clearTimeout,startTimeout = 12000}) {
    let state = 'idle', plan = null, index = 0, epoch = 0, timer, utterance;
    const change = value => { state = value; onState(value); };
    function invalidate() { epoch++; clearTimer(timer); timer = undefined; utterance = null; }
    function cancel() {
      // cancel() does not necessarily clear the browser's paused flag.
      if (synth.speaking || synth.pending || synth.paused || state !== 'idle') synth.cancel();
    }
    function stop() {
      invalidate();
      try { cancel(); } catch (_) { /* UI still needs to recover from a broken engine. */ }
      plan = null; change('idle');
    }
    function fail(code) { stop(); onError(code); }
    function speak() {
      if (!plan || index >= plan.pieces.length) { stop(); onFinish(); return; }
      const run = ++epoch, piece = plan.pieces[index];
      const current = () => run === epoch;
      change('starting');
      try {
        utterance = new Utterance(plan.text.slice(piece.start,piece.end));
        utterance.voice = plan.voice; utterance.lang = plan.voice.lang; utterance.rate = plan.rate;
        utterance.onstart = () => {
          if (!current()) return;
          clearTimer(timer); timer = undefined; change('speaking'); onChunk(piece,index,plan.pieces.length);
        };
        utterance.onend = () => {
          if (!current()) return;
          invalidate(); index++; speak();
        };
        utterance.onerror = event => { if (current()) fail(event.error || 'speech-failed'); };
        timer = setTimer(() => { if (current()) fail('start-timeout'); },startTimeout);
        // Keep the first speak in the Read/Test/Resume click's user activation.
        if (synth.paused) synth.resume();
        synth.speak(utterance);
      } catch (_) { if (current()) fail('speech-failed'); }
    }
    return {
      get state() { return state; },
      play(value) { stop(); plan = {...value,pieces:chunks(value.text,value.voice.lang)}; index = 0; speak(); },
      pause() {
        if (state !== 'speaking') return;
        invalidate();
        try { cancel(); } catch (_) { fail('speech-failed'); return; }
        // Android implements native pause as stop and has no native resume.
        // Preserve the chunk so an explicit Resume can speak it again.
        change('paused');
      },
      resume() { if (state === 'paused') speak(); },
      stop,
    };
  }
  return {chunks,chooseVoice,createPlayer};
});
