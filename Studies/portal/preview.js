/* Untrusted drafts render in an opaque sandbox. No navigation, image downloads,
 * network fetches or parent DOM access are available to draft content. */
(() => {
  'use strict';
  const target = document.getElementById('preview');
  const md = markdownit({html:true, typographer:true, linkify:false}).disable('strikethrough');
  // This author-content contract is exercised against _safe_study_html.py.
  const tags = ['p','br','hr','h1','h2','h3','h4','h5','h6','blockquote','ul','ol','li','pre','code','em','strong','b','i','s','del','sub','sup','a','img','table','thead','tbody','tfoot','tr','th','td','caption','div','span','dl','dt','dd'];
  const attributes = {a:['href','title'], img:['src','alt','title','width','height'], ol:['start'], td:['colspan','rowspan','style'], th:['colspan','rowspan','scope','style'], code:['class']};
  DOMPurify.addHook('uponSanitizeAttribute', (node,data) => {
    if (!attributes[node.nodeName.toLowerCase()]?.includes(data.attrName)) data.keepAttr = false;
    if (data.attrName === 'style') {
      const align = data.attrValue.match(/^\s*text-align\s*:\s*(left|right|center|justify)\s*;?\s*$/i);
      if (!align) data.keepAttr = false;
    }
    if (data.attrName === 'class' && !/^language-(mermaid|text|python|json|javascript|bash)$/.test(data.attrValue)) data.keepAttr = false;
    if (['href','src'].includes(data.attrName) && !safeUrl(data.attrValue)) data.keepAttr = false;
  });
  function safeUrl(value) {
    const clean = value.replace(/[\u0000-\u0020]/g,'');
    return !clean.startsWith('//') && (!/^[a-z][a-z0-9+.-]*:/i.test(clean) || /^(https?:|mailto:)/i.test(clean));
  }
  function protect(source) {
    const codes = [], math = [];
    const nonce = crypto.randomUUID().replace(/-/g,'');
    let text = source.replace(/^```[\s\S]*?^```[^\n]*$/gm, code => `\uE000C${nonce}${codes.push(code)-1}\uE001`)
      .replace(/(`+)(?:(?!\1).)+?\1/g, code => `\uE000C${nonce}${codes.push(code)-1}\uE001`);
    const stash = (all,tex,display) => `\uE000M${nonce}${math.push({tex,display})-1}\uE001`;
    text = text.replace(/\$\$([\s\S]+?)\$\$/g,(all,tex) => stash(all,tex,true))
      .replace(/(?<!\\)\$(?!\$)((?:\\.|[^$\\])+?)(?<!\\)\$(?!\$)/g,(all,tex) => stash(all,tex,false));
    text = text.replace(new RegExp(`\uE000C${nonce}(\\d+)\uE001`,'g'), (_,i) => codes[+i]);
    return {text,math,pattern:new RegExp(`\uE000M${nonce}(\\d+)\uE001`,'g')};
  }
  let latest = 0, chain = Promise.resolve(), mermaidPromise;
  const diagramLibrary = () => mermaidPromise || (mermaidPromise = new Promise((resolve,reject) => {
    const script = document.createElement('script'); script.src = '../../Assets/Mermaid/mermaid.min.js?v=581ed7d74bd9048d';
    script.onload = () => resolve(window.mermaid); script.onerror = () => { mermaidPromise = null; reject(new Error('Diagram renderer could not load.')); };
    document.head.append(script);
  }));
  async function render(data) {
    if (data.id !== latest) return;
    const warnings = [];
    if (data.content.length > 500000) throw new Error('Preview supports up to 500,000 characters. Preview a section at a time; your complete draft is still saved.');
    const protectedText = protect(data.content.replace(/\r\n?/g,'\n'));
    // Inert parsing strips images before inserting any nodes into the live DOM.
    const fragment = DOMPurify.sanitize(md.render(protectedText.text), {ALLOWED_TAGS:tags,
      ALLOWED_ATTR:[...new Set(Object.values(attributes).flat())], ALLOW_DATA_ATTR:false, ALLOW_ARIA_ATTR:false,
      FORBID_CONTENTS:['script','style','iframe','object','embed','svg','math','template'], RETURN_DOM_FRAGMENT:true});
    for (const image of fragment.querySelectorAll('img')) {
      const placeholder = document.createElement('p'); placeholder.className = 'image-placeholder';
      placeholder.textContent = 'Figure: ' + (image.getAttribute('alt') || 'No description') + ' — ' + (image.getAttribute('src') || 'Invalid image URL');
      image.replaceWith(placeholder);
    }
    for (const link of fragment.querySelectorAll('a')) { link.title = link.getAttribute('href') || ''; link.removeAttribute('href'); }
    const walker = document.createTreeWalker(fragment, NodeFilter.SHOW_TEXT), texts = [];
    while (walker.nextNode()) texts.push(walker.currentNode);
    let count = 0;
    for (const node of texts) {
      const text = node.textContent, parts = [], pattern = protectedText.pattern;
      pattern.lastIndex = 0; let last = 0, match;
      while ((match = pattern.exec(text))) {
        parts.push(document.createTextNode(text.slice(last,match.index)));
        const expression = protectedText.math[+match[1]], span = document.createElement('span');
        if (++count > 2000) throw new Error('Too many equations for one preview. Preview a section at a time.');
        katex.render(expression.tex.trim(),span,{displayMode:expression.display, throwOnError:false, strict:'ignore', trust:false, maxExpand:1000, maxSize:20});
        if (span.querySelector('.katex-error')) warnings.push('An equation could not render; its source is shown in red.');
        parts.push(span); last = pattern.lastIndex;
      }
      if (parts.length) { parts.push(document.createTextNode(text.slice(last))); node.replaceWith(...parts); }
    }
    target.replaceChildren(fragment);
    for (const table of target.querySelectorAll('table')) { const wrap = document.createElement('div'); wrap.className = 'table-scroll'; table.before(wrap); wrap.append(table); }
    const diagrams = [...target.querySelectorAll('code.language-mermaid')];
    if (diagrams.length > 20) warnings.push('Only the first 20 diagrams are rendered in this preview.');
    if (diagrams.length) {
      const library = await diagramLibrary();
      library.initialize({startOnLoad:false, securityLevel:'strict', maxTextSize:50000, maxEdges:500, suppressErrorRendering:true});
      for (const [index,code] of diagrams.slice(0,20).entries()) {
        if (data.id !== latest) return;
        try {
          const result = await library.render('preview-diagram-' + data.id + '-' + index, code.textContent);
          const box = document.createElement('div'); box.className = 'mermaid'; box.innerHTML = result.svg;
          code.parentElement.replaceWith(box);
        } catch (_) { warnings.push(`Diagram ${index + 1} could not render. Check its Mermaid syntax; the source remains visible.`); }
      }
    }
    parent.postMessage({type:'preview-result',id:data.id,message:[...new Set(warnings)].join(' ') || 'Preview ready.'}, '*');
  }
  addEventListener('message', event => {
    if (event.source !== parent || event.data?.type !== 'preview' || typeof event.data.content !== 'string' || !Number.isInteger(event.data.id)) return;
    latest = event.data.id;
    chain = chain.catch(() => {}).then(() => render(event.data)).catch(error => {
      if (event.data.id !== latest) return;
      target.textContent = error.message;
      parent.postMessage({type:'preview-result', id:event.data.id, message:error.message}, '*');
    });
  });
})();
