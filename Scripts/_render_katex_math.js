/**
 * Render $...$ and $$...$$ LaTeX in study HTML via KaTeX (stdin → stdout).
 * Used by _convert_to_pdf.py before glossary tooltips mutate inline text.
 */
const katex = require('katex');

const SKIP_TAGS =
  /<(pre|code|script|style|textarea|svg)(?:\s[^>]*)?>[\s\S]*?<\/\1>/gi;

function renderTex(tex, displayMode) {
  try {
    return katex.renderToString(tex.trim(), {
      displayMode,
      throwOnError: false,
      strict: 'ignore',
    });
  } catch {
    return null;
  }
}

function renderMathSegment(segment) {
  let out = segment;

  out = out.replace(/\$\$([\s\S]+?)\$\$/g, (match, tex) => {
    const rendered = renderTex(tex, true);
    return rendered ?? match;
  });

  out = out.replace(/(?<!\\)\$(?!\$)((?:\\.|[^$\\])+?)(?<!\\)\$(?!\$)/g, (match, tex) => {
    const rendered = renderTex(tex, false);
    return rendered ?? match;
  });

  return out;
}

function renderMathInHtml(html) {
  const preserved = [];
  const stripped = html.replace(SKIP_TAGS, (block) => {
    const token = `\x00KATEX_SKIP_${preserved.length}\x00`;
    preserved.push(block);
    return token;
  });

  const rendered = renderMathSegment(stripped);

  return rendered.replace(/\x00KATEX_SKIP_(\d+)\x00/g, (_, index) => preserved[Number(index)]);
}

let html = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (chunk) => {
  html += chunk;
});
process.stdin.on('end', () => {
  process.stdout.write(renderMathInHtml(html));
});
