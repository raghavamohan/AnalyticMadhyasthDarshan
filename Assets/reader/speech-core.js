/* Device speech: complete sentences with cancel/restart pause for Android. */
(function(root,factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.AMDReaderSpeech = api;
})(typeof globalThis !== 'undefined' ? globalThis : this,() => {
  'use strict';
  function chunks(text,language,passageEnds = []) {
    let segmenter;
    // Voice engines sometimes return en_IN or tags that are not BCP 47.
    for (const locale of [(language || 'en').replace(/_/g,'-'),'en']) {
      try { segmenter = new Intl.Segmenter(locale,{granularity:'sentence'}); break; }
      catch (_) { /* Retry a valid locale, then use punctuation on older browsers. */ }
    }
    const result = [];
    // A heading/list item without terminal punctuation must not absorb the
    // following passage. Keep original UTF-16 offsets for DOM word highlighting.
    const ends = [...new Set(passageEnds.filter(n => Number.isInteger(n) && n > 0 && n < text.length))].sort((a,b) => a - b);
    let blockStart = 0;
    for (const blockEnd of [...ends,text.length]) {
      // Markdown soft line wraps are whitespace, not passage boundaries.
      const source = text.slice(blockStart,blockEnd).replace(/[\r\n]/g,' '), spans = [];
      if (segmenter) {
        for (const s of segmenter.segment(source)) spans.push({start:s.index,end:s.index + s.segment.length});
      } else {
        let start = 0;
        for (const match of source.matchAll(/[.!?।॥]+["'”’»\)\]]*(?:\s+|$)/g)) {
          const end = match.index + match[0].length;
          spans.push({start,end}); start = end;
        }
        if (start < source.length) spans.push({start,end:source.length});
      }
      let pending;
      for (const span of spans) {
        if (!pending) pending = {...span}; else pending.end = span.end;
        const sentence = source.slice(pending.start,pending.end);
        // ICU can treat honorifics and author initials as entire sentences.
        const abbreviation = /\b(?:Dr|Mr|Mrs|Ms|Prof|Shri|Smt|e\.g|i\.e)\.\s*$/u.test(sentence);
        const initials = /^\s*(?:(?:Dr|Mr|Mrs|Ms|Prof)\.\s+|(?:Shri|Smt)\s+)?(?:[A-Z]\.\s*)+$/u.test(sentence);
        if (abbreviation || initials) continue;
        if (sentence.trim()) result.push({start:blockStart + pending.start,end:blockStart + pending.end});
        pending = null;
      }
      if (pending && source.slice(pending.start,pending.end).trim()) result.push({start:blockStart + pending.start,end:blockStart + pending.end});
      blockStart = blockEnd;
    }
    return result;
  }
  function sentenceStart(text,offset,language) {
    const at = Math.max(0,Math.min(offset,text.length));
    const piece = chunks(text,language).find(p => at < p.end && text.slice(at,p.end).trim());
    return piece ? piece.start + (text.slice(piece.start,piece.end).match(/^\s*/)?.[0].length || 0) : at;
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
  function createPlayer({synth,Utterance,onState = () => {},onChunk = () => {},onWord = () => {},onError = () => {},onFinish = () => {},
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
      // Do not silently split or truncate an exceptional over-limit sentence.
      if (piece.end - piece.start > 32767) { fail('text-too-long'); return; }
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
        utterance.onboundary = event => {
          if (!current() || state !== 'speaking' || event.name !== 'word') return;
          const at = event.charIndex, text = plan.text.slice(piece.start,piece.end);
          if (!Number.isInteger(at) || at < 0 || at >= text.length) return;
          let word;
          try { word = [...new Intl.Segmenter(plan.voice.lang,{granularity:'word'}).segment(text)]
            .find(s => s.isWordLike && s.index <= at && s.index + s.segment.length > at); } catch (_) {}
          if (!word) {
            const match = /\S+/g; let token;
            while ((token = match.exec(text))) if (token.index <= at && token.index + token[0].length > at) {
              word = {index:token.index,segment:token[0]}; break;
            }
          }
          if (word) onWord({start:piece.start + word.index,end:piece.start + word.index + word.segment.length});
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
      play(value) { stop(); plan = {...value,pieces:chunks(value.text,value.language || value.voice.lang,value.passageEnds)}; index = 0; speak(); },
      pause() {
        if (state !== 'speaking') return;
        invalidate();
        try { cancel(); } catch (_) { fail('speech-failed'); return; }
        // Android implements native pause as stop and has no native resume.
        // Preserve the complete sentence so Resume never starts mid-sentence.
        change('paused');
      },
      resume() { if (state === 'paused') speak(); },
      stop,
    };
  }
  return {chunks,sentenceStart,chooseVoice,createPlayer};
});
