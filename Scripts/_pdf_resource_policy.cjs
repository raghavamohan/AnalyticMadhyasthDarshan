const fs = require('node:fs');
const path = require('node:path');
const { fileURLToPath } = require('node:url');

function inside(file, root) {
  const relative = path.relative(root, file);
  return relative === '' || (!relative.startsWith('..' + path.sep) && relative !== '..' && !path.isAbsolute(relative));
}

// Only the input document, its local figures and vendored math fonts may load.
// Resolve symlinks before the containment check; never grant the whole checkout.
function allowedPdfResource(url, type, inputPath, fontDir) {
  try {
    if (!url.startsWith('file:')) return false;
    const file = fs.realpathSync(fileURLToPath(url));
    const input = fs.realpathSync(inputPath);
    if (file === input && type === 'document') return true;
    const ext = path.extname(file).toLowerCase();
    if (type === 'image' && ['.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp'].includes(ext)) {
      return inside(file, path.dirname(input));
    }
    return type === 'font' && ['.woff', '.woff2', '.ttf'].includes(ext)
      && inside(file, fs.realpathSync(fontDir));
  } catch {
    return false;
  }
}

module.exports = { allowedPdfResource };
