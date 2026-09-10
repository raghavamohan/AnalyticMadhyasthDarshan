// Authoring inputs are committed before the draft PR is created. Generated
// DOCX/notes/PDF outputs remain the responsibility of shared CI preparation.
function invalid(message) {
  const error = new Error(message);
  error.status = 400;
  throw error;
}

export function validateAssetFilename(name) {
  if (typeof name !== 'string' || name.length > 120 ||
      !/^[A-Za-z0-9][A-Za-z0-9_-]*\.(svg|png|jpg|jpeg|webp|gif)$/i.test(name)) {
    invalid('Figure filenames must use letters, numbers, underscores or hyphens and end in .svg, .png, .jpg, .jpeg, .webp or .gif.');
  }
  return name;
}

function encodedAsset(file) {
  if (!file || typeof file !== 'object') invalid('Invalid figure attachment.');
  validateAssetFilename(file.fileName);
  const encoded = String(file.contentBase64 || '');
  if (!encoded || encoded.length > 2800000 || encoded.length % 4 || !/^[A-Za-z0-9+/]+={0,2}$/.test(encoded)) {
    invalid('Each figure must contain valid base64 data and be at most 2 MB.');
  }
  const bytes = Uint8Array.from(atob(encoded), c => c.charCodeAt(0));
  if (bytes.length > 2 * 1024 * 1024) invalid('Each figure must be at most 2 MB.');
  const head = String.fromCharCode(...bytes.slice(0, 16));
  const ext = file.fileName.split('.').pop().toLowerCase();
  if (ext === 'svg') {
    let text;
    try { text = new TextDecoder('utf-8', {fatal: true}).decode(bytes); }
    catch { invalid('SVG figures must be UTF-8.'); }
    if (!/<svg(?:\s|>)/i.test(text) || /<!DOCTYPE|<!ENTITY|<\s*(?:script|foreignObject|iframe|object|embed)\b|\bon[a-z]+\s*=|(?:javascript|vbscript)\s*:|(?:href|src)\s*=\s*["']\s*(?:https?:|\/\/|file:|data:text\/html)/i.test(text)) {
      invalid('Use a static SVG with local figure dependencies and no scripts or external content.');
    }
  } else if (!({png: head.startsWith('\x89PNG\r\n\x1a\n'), jpg: head.startsWith('\xff\xd8\xff'),
    jpeg: head.startsWith('\xff\xd8\xff'), gif: /^GIF8[79]a/.test(head),
    webp: head.startsWith('RIFF') && head.slice(8, 12) === 'WEBP'})[ext]) {
    invalid('The figure bytes do not match its filename extension.');
  }
  return encoded;
}

export function buildSupplementaryFiles(data, artifact) {
  const assets = data.assets === undefined ? [] : data.assets;
  if (!Array.isArray(assets) || assets.length > 20) invalid('Attach at most 20 figures.');
  const directory = artifact.filePath.slice(0, artifact.filePath.lastIndexOf('/'));
  const files = assets.map(file => ({...file, encodedContent: encodedAsset(file),
    filePath: `${directory}/${file.fileName}`}));
  if (data.presenter) {
    if (artifact.artifactType !== 'presentation') invalid('Attach presenter Markdown to a presentation upload.');
    const file = data.presenter;
    if (!/^Presenters-Companion-[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.md$/.test(file.fileName || '') || file.fileName.length > 120) {
      invalid('Use a Presenters-Companion-Topic.md filename.');
    }
    const content = String(file.content || '').replace(/\r\n?/g, '\n');
    if (!content.trim() || new TextEncoder().encode(content).length > 2 * 1024 * 1024) invalid('Presenter Markdown must contain text and be at most 2 MB.');
    files.push({...file, filePath: `${directory}/${file.fileName}`,
      encodedContent: btoa(unescape(encodeURIComponent(content.endsWith('\n') ? content : content + '\n')))});
  }
  const seen = new Set([artifact.filePath.toLowerCase()]);
  let total = 0;
  for (const file of files) {
    if (seen.has(file.filePath.toLowerCase())) invalid('Each attachment must have a unique filename.');
    seen.add(file.filePath.toLowerCase());
    total += file.encodedContent.length;
  }
  if (total > 4 * 1024 * 1024) invalid('Attachments must total at most 3 MB before encoding.');
  return files;
}

export function submissionFileOperations(githubRequest, assertSourceVersion) {
  const get = (name, ref, env) => githubRequest(`/contents/${name}?ref=${encodeURIComponent(ref)}`, 'GET', null, env);
  const decode = file => JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(file.content.replace(/\s/g, '')), c => c.charCodeAt(0))));
  async function checkSupplementaryVersion(file, ref, env) {
    let existing;
    try { existing = await get(file.filePath, ref, env); }
    catch (error) { if (error.status !== 404) throw error; }
    if (existing) assertSourceVersion(file.sourceSha, existing.sha);
    else if (file.sourceSha) invalid(`The attachment ${file.fileName} was removed; refresh before submitting.`);
    file.sha = existing?.sha;
  }
  async function putSupplementaryFile(file, branch, env) {
    await githubRequest(`/contents/${file.filePath}`, 'PUT', {
      message: `Update ${file.fileName} with study submission`, branch,
      content: file.encodedContent, sha: file.sha,
    }, env);
  }
  async function presenterRegistration(artifact, data, ref, env, write = false) {
    const directory = artifact.filePath.slice(0, artifact.filePath.lastIndexOf('/'));
    const name = artifact.artifactType === 'presenter' ? artifact.fileName : data.presenter.fileName;
    const deckName = artifact.artifactType === 'presenter' ? data.deckFileName : artifact.fileName;
    if (!/^[A-Za-z0-9][A-Za-z0-9-]*\.pptx$/i.test(deckName || '')) invalid('Select the presentation owned by these presenter notes.');
    const deckSource = `${directory}/${deckName}`;
    const deckFile = await get('Scripts/presentation-pipeline.json', ref, env);
    const deck = decode(deckFile).decks.find(row => row.source === deckSource);
    const manifestFile = await get('Scripts/companion-pipeline.json', ref, env);
    const manifest = decode(manifestFile);
    if (manifest.schema !== 1 || !Array.isArray(manifest.companions)) invalid('Invalid presenter ownership manifest.');
    const markdown = `${directory}/${name}`;
    const owner = manifest.companions.find(row => row.markdown === markdown || (deck && row.deck === deck.id));
    if (owner && (owner.markdown !== markdown || owner.deck !== deck?.id)) invalid('That deck or presenter document already belongs to another companion.');
    if (!deck && artifact.artifactType !== 'presentation') invalid('Select an existing registered presentation in this study.');
    if (write && !owner) {
      if (!deck) invalid('Register the presentation before its presenter companion.');
      manifest.companions.push({markdown, deck: deck.id});
      await githubRequest('/contents/Scripts/companion-pipeline.json', 'PUT', {
        message: `Register ${name} presenter ownership`, branch: ref, sha: manifestFile.sha,
        content: btoa(unescape(encodeURIComponent(JSON.stringify(manifest, null, 2) + '\n'))),
      }, env);
    }
  }
  return {checkSupplementaryVersion, putSupplementaryFile,
    checkPresenterRegistration: (artifact, data, ref, env) => presenterRegistration(artifact, data, ref, env),
    ensurePresenterManifested: (artifact, data, ref, env) => presenterRegistration(artifact, data, ref, env, true)};
}
