"""Stable asset closures; release identity belongs to navigation, not asset bytes."""
import html
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from _common import site_base_url
from _build_inputs import file_hash
import hashlib

ASSET_SUFFIXES = {'.css', '.js', '.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.avif', '.ico', '.woff', '.woff2', '.ttf'}
CSS_URL = re.compile(r'url\(\s*([\"\x27]?)([^)\"\x27]+)\1\s*\)', re.I)
IMPORT_URL = re.compile(r'(importScripts\(\s*[\"\x27])([^\"\x27]+)([\"\x27]\s*\))')


def is_asset(path: str) -> bool:
    from pathlib import PurePosixPath
    return not path.startswith('/References/') and PurePosixPath(path).suffix.lower() in ASSET_SUFFIXES


def asset_record_key(path: str, sha: str) -> str:
    return f'site/assets/{path.lstrip("/")}/{sha}.json'


def asset_url(value: str, path: str, hashes: dict) -> str:
    origin = site_base_url().rstrip('/')
    resolved = urlsplit(urljoin(origin + path, value))
    if resolved.netloc != urlsplit(origin).netloc or resolved.path not in hashes or value.startswith('#'):
        return value
    original = urlsplit(value)
    query = dict(parse_qsl(original.query, keep_blank_values=True))
    query.pop('r', None)
    query['v'] = hashes[resolved.path]
    return urlunsplit((original.scheme, original.netloc, original.path, urlencode(query), original.fragment))


def compile_assets(bodies: dict[str, bytes]) -> dict[str, str]:
    """Hash leaves first, then CSS imports and font/image references."""
    hashes, visiting = {}, set()
    origin = site_base_url().rstrip('/')

    def compile_one(path):
        if path in hashes:
            return
        if path in visiting:
            raise ValueError(f'Cyclic CSS dependency: {path}')
        visiting.add(path)
        if path.endswith('.css'):
            text = bodies[path].decode('utf-8')
            for match in CSS_URL.finditer(text):
                target = urlsplit(urljoin(origin + path, match[2]))
                if target.netloc == urlsplit(origin).netloc and target.path in bodies and is_asset(target.path):
                    compile_one(target.path)
            bodies[path] = CSS_URL.sub(lambda m: 'url("' + asset_url(m[2], path, hashes) + '")', text).encode()
        elif path.endswith('.js'):
            text = bodies[path].decode('utf-8')
            for match in IMPORT_URL.finditer(text):
                target = urlsplit(urljoin(origin + path, match[2]))
                if target.netloc == urlsplit(origin).netloc and target.path in bodies and is_asset(target.path):
                    compile_one(target.path)
            bodies[path] = IMPORT_URL.sub(lambda m: m[1] + asset_url(m[2], path, hashes) + m[3], text).encode()
        hashes[path] = hashlib.sha256(bodies[path]).hexdigest()
        visiting.remove(path)

    for path in bodies:
        if is_asset(path):
            compile_one(path)
    return hashes


# Every installed handler uses the page's explicit release URL. Asset fetches
# carrying their own content hash retain that identity. The live-dashboard link
# intentionally opens the separately verified publication revision.
CLIENT = r'''<script>(()=>{const r=new URL(location.href).searchParams.get('r');if(!/^[a-f0-9]{64}$/.test(r||''))return;window.AMD_RELEASE=r;const pin=u=>{if(u.origin===location.origin&&!u.pathname.startsWith('/api/')&&!u.pathname.startsWith('/References/')&&!/^[a-f0-9]{64}$/.test(u.searchParams.get('v')||''))u.searchParams.set('r',r);return u;};const original=window.fetch.bind(window);window.fetch=(input,init)=>{const method=init?.method||(input instanceof Request?input.method:'GET');let u=new URL(input instanceof Request?input.url:input,location.href);if(method==='GET'&&/\.(json|html|pdf|md|css|js|txt)$/.test(u.pathname)){u=pin(u);input=input instanceof Request?new Request(u,input):u;}return original(input,init);};const link=a=>{if(!a?.href||a.hasAttribute?.('data-publication-live')||a.getAttribute('href').startsWith('#'))return;const u=new URL(a.href,location.href);if(u.pathname.endsWith('/')||/\.(html|pdf|md|pptx|docx|json|txt)$/.test(u.pathname)){pin(u);if(a.href!==u.href)a.href=u.href;}};const update=n=>{if(n.nodeType!==1)return;if(n.matches('a[href]'))link(n);n.querySelectorAll('a[href]').forEach(link);};for(const event of ['pointerdown','click','auxclick','contextmenu'])document.addEventListener(event,e=>link(e.target.closest?.('a[href]')),true);document.addEventListener('DOMContentLoaded',()=>{update(document.documentElement);new MutationObserver(ms=>ms.forEach(m=>{if(m.type==='attributes')link(m.target);else m.addedNodes.forEach(update);})).observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['href']});});})();</script>'''


def compile_html(data: bytes, path: str, hashes: dict) -> bytes:
    text = data.decode('utf-8')
    def tag(match):
        value = match[0]
        if re.search(r'\brel=[\"\x27]canonical[\"\x27]', value, re.I):
            return value
        value = re.sub(r'\b(href|src)=("|\x27)([^"\x27]*)\2',
                       lambda m: f'{m[1]}={m[2]}{html.escape(asset_url(html.unescape(m[3]), path, hashes), quote=True)}{m[2]}', value)
        return value
    text = re.sub(r'<(?:a|link|script|img|source)\b[^>]*>', tag, text, flags=re.I)
    # The lazy Mermaid loader assigns a literal asset URL inside inline JS.
    # Rewrite only complete quoted local asset URLs, leaving arbitrary code alone.
    text = re.sub(r'([\"\x27])((?:/|\.\./)+Assets/[^\"\x27\s]+)\1',
                  lambda m: m[1] + asset_url(m[2], path, hashes) + m[1], text)
    text = re.sub(r'(<style\b[^>]*>)([\s\S]*?)(</style>)',
                  lambda m: m[1] + CSS_URL.sub(lambda u: 'url("' + asset_url(u[2], path, hashes) + '")', m[2]) + m[3], text, flags=re.I)
    return re.sub(r'<head\b[^>]*>', lambda m: m[0] + CLIENT, text, count=1, flags=re.I).encode('utf-8')
