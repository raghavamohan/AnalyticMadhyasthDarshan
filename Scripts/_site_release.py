"""Build immutable website/PDF releases without modifying authoring files."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from _common import BASE, site_base_url
from _publication_inventory import public_studies

ROOT_PUBLIC = {"index.html", "404.html", "robots.txt", "sitemap.xml", "llms.txt", "llms-full.txt", "reader-sw.js", "webmcp.js", "LICENSE", "LICENSE-CODE"}
ROOT_PUBLIC.update({"api-docs.html", "catalog-all.json"})
MIME = {'.html':'text/html; charset=utf-8', '.css':'text/css; charset=utf-8', '.js':'text/javascript; charset=utf-8',
        '.json':'application/json', '.txt':'text/plain; charset=utf-8', '.md':'text/markdown; charset=utf-8',
        '.xml':'application/xml', '.pdf':'application/pdf', '.svg':'image/svg+xml', '.png':'image/png',
        '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.webp':'image/webp', '.gif':'image/gif', '.ico':'image/x-icon',
        '.woff':'font/woff', '.woff2':'font/woff2', '.ttf':'font/ttf',
        '.pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
STATIC_SUFFIXES = {".html", ".css", ".js", ".json", ".txt", ".md", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".pdf", ".pptx", ".docx"}
INTERNAL_STUDIES = {"proposal-registry.json", "companion-artifacts.json", "README.md"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def safe_path(path: str) -> bool:
    return (path.startswith("/") and not path.startswith("//") and "\\" not in path
            and not any(p in {".", ".."} for p in path.split("/")) and "?" not in path and "#" not in path)


def eligible_static(name: str, studies: set[tuple[str, str]]) -> bool:
    path = PurePosixPath(name)
    if name in ROOT_PUBLIC:
        return True
    if path.suffix.lower() not in STATIC_SUFFIXES or not safe_path("/" + name):
        return False
    if any(part.startswith(".") for part in path.parts):
        return path.parts[0] == ".well-known" and len(path.parts) >= 2
    if path.parts[0] in {"Assets", "openapi"}:
        return True
    if path.parts[0] == "References":
        return path.name not in {"r2-artifacts.json", "NOT-DOWNLOADED.md", "MANIFEST.md"}
    if path.parts[0] == "Studies" and len(path.parts) == 2:
        return path.name not in INTERNAL_STUDIES
    if name.startswith(("Studies/assets/", "Studies/search-data/", "Studies/portal/")):
        return "test" not in path.name.lower()
    return (len(path.parts) >= 3 and (path.parts[0], path.parts[1]) in studies
            and not path.name.startswith("Research-Template-"))


def static_sources(root: Path = BASE) -> dict[str, Path]:
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode("utf-8").split("\0")
    studies = public_studies()
    found = {}
    for name in names:
        if not name or not eligible_static(name, studies):
            continue
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Unsafe public file: {name}")
        if path.is_file():
            found["/" + name] = path
    return found


def pin_url(value: str, path: str, revision: str, available: set[str]) -> str:
    if not value or value.startswith(("#", "data:", "mailto:", "javascript:")):
        return value
    origin = site_base_url().rstrip("/")
    absolute = urlsplit(urljoin(origin + path, value))
    if absolute.netloc != urlsplit(origin).netloc or absolute.path not in available:
        return value
    # Reference delivery has its own rights/storage manifest and lifetime.
    if absolute.path.startswith("/References/"):
        return value
    query = dict(parse_qsl(absolute.query, keep_blank_values=True))
    query["r"] = revision
    original = urlsplit(value)
    return urlunsplit((original.scheme, original.netloc, original.path, urlencode(query), original.fragment))


def pin_html(data: bytes, path: str, revision: str, available: set[str]) -> bytes:
    text = data.decode("utf-8")
    def replace(match: re.Match) -> str:
        tag = match.group(0)
        if re.search(r'\brel=[\"\']canonical[\"\']', tag, re.I):
            return tag
        return re.sub(r'\b(href|src)=("|\')([^"\']*)\2',
                      lambda m: f'{m[1]}={m[2]}{html.escape(pin_url(html.unescape(m[3]), path, revision, available), quote=True)}{m[2]}', tag)
    text = re.sub(r'<(?:a|link|script|img|source)\b[^>]*>', replace, text, flags=re.I)
    # Dynamic catalog/search fetches must use the same revision as their page.
    client = '''<script>(()=>{const r=REV;window.AMD_RELEASE=r;const original=window.fetch.bind(window);window.fetch=(input,init)=>{const method=init?.method||(input instanceof Request?input.method:'GET');const u=new URL(input instanceof Request?input.url:input,location.href);if(method==='GET'&&u.origin===location.origin&&!u.pathname.startsWith('/api/')&&!u.pathname.startsWith('/References/')&&/\\.(json|html|pdf|css|js)$/.test(u.pathname)) {u.searchParams.set('r',r);input=input instanceof Request?new Request(u,input):u;}return original(input,init);};})();</script>'''.replace("REV", json.dumps(revision))
    # Dynamic card/download links and middle-clicks also keep the reader's release.
    links = '''<script>(()=>{const r=REV;const pin=a=>{if(!a?.href)return;const u=new URL(a.href,location.href);if(u.origin===location.origin&&!u.pathname.startsWith('/References/')&&!u.pathname.startsWith('/api/')&&!a.getAttribute('href').startsWith('#')&&/\\.(html|pdf)$/.test(u.pathname)){u.searchParams.set('r',r);if(a.href!==u.href)a.href=u.href;}};const update=n=>{if(n.nodeType!==1)return;if(n.matches('a[href]'))pin(n);n.querySelectorAll('a[href]').forEach(pin);};document.addEventListener('DOMContentLoaded',()=>{update(document.documentElement);new MutationObserver(ms=>ms.forEach(m=>{if(m.type==='attributes')pin(m.target);else m.addedNodes.forEach(update);})).observe(document.body,{subtree:true,childList:true,attributes:true,attributeFilter:['href']});});})();</script>'''.replace('REV', json.dumps(revision))
    return re.sub(r'<head\b[^>]*>', lambda m: m[0] + client + links, text, count=1, flags=re.I).encode("utf-8")


def build(output: Path, artifact_root: Path | None, *, root: Path = BASE, source_sha: str | None = None) -> dict:
    from _generated_pdf_inventory import generated_pdf_specs
    from _publish_generated_pdfs import verify_artifacts
    source_sha = source_sha or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if not re.fullmatch(r"[a-f0-9]{40}", source_sha):
        raise ValueError("Release source must be a full Git SHA")
    files = static_sources(root)
    pdfs = verify_artifacts(generated_pdf_specs(), artifact_root) if artifact_root else []
    for pdf in pdfs:
        files["/" + pdf.spec.key] = pdf.path
    # Also bind the release to the toolchain and actual compiled bytes, so a
    # renderer rebuild of one source commit has a distinct immutable revision.
    inputs = {path: digest(file.read_bytes()) for path, file in files.items()}
    revision = digest(encode({"source": source_sha, "inputs": inputs, "builder": digest(Path(__file__).read_bytes())}))
    available = set(files)
    bodies = {path: file.read_bytes() for path, file in files.items()}
    for path, body in list(bodies.items()):
        if path.endswith(".html") and not path.startswith("/References/"):
            bodies[path] = pin_html(body, path, revision, available)
        elif path.endswith('.css'):
            css = body.decode('utf-8')
            css = re.sub(r'url\(\s*([\"\']?)([^)\"\']+)\1\s*\)',
                lambda m: 'url("' + pin_url(m[2],path,revision,available) + '")', css)
            bodies[path] = css.encode('utf-8')
    # Saved-reader checksums describe the deployed copies, including release
    # links. Never modify the canonical offline manifest in Git.
    offline_path = "/Studies/offline-manifest.json"
    if offline_path in bodies:
        offline = json.loads(bodies[offline_path])
        for doc in offline.get("documents", []):
            for resource in doc.get("resources", []):
                key = urlsplit(resource["url"]).path
                if key in bodies:
                    resource["sha256"] = digest(bodies[key])
                    resource["bytes"] = len(bodies[key])
                    resource["url"] = pin_url(resource["url"], offline_path, revision, available)
            doc["bytes"] = sum(resource["bytes"] for resource in doc.get("resources", []))
            doc["htmlSha"] = digest(bodies[doc["path"]])
            doc["librarySha"] = digest(bodies["/Studies/notebook.html"])
        bodies[offline_path] = encode(offline)
    output.mkdir(parents=True, exist_ok=True)
    records = {}
    for path, body in sorted(bodies.items()):
        target = output / "assets" / path.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
        checksum = digest(body)
        records[path] = {"sha256": checksum, "bytes": len(body), "key": f"site/objects/{checksum}",
                         "type": MIME.get(PurePosixPath(path).suffix.lower(), "application/octet-stream"),
                         "archive": not path.startswith("/References/")}
        if len(body) > 25 * 1024 * 1024 and not records[path]["archive"]:
            # Large git-retained references remain static deployment assets;
            # they must never enter the generated-PDF R2 bucket.
            parts = []
            for index, start in enumerate(range(0, len(body), 16 * 1024 * 1024)):
                part = f"/__reference-parts/{checksum}/{index}"
                part_file = output / "assets" / part.lstrip("/")
                part_file.parent.mkdir(parents=True, exist_ok=True)
                part_file.write_bytes(body[start:start + 16 * 1024 * 1024])
                parts.append(part)
            records[path]["parts"] = parts
    studies = {}
    for path in ("/Studies/catalog-topical.json", "/Studies/catalog-formal.json", "/Studies/catalog-applied.json"):
        for row in json.loads(bodies.get(path, b"[]")):
            studies[row["slug"]] = {"status": row["status"], "updated": row.get("updated"),
                                    "sourceSha256": inputs.get("/" + ("Applications" if "applied" in path else "Studies") + f'/{row["slug"]}/{row["slug"]}.md')}
    manifest = {"schema": 1, "revision": revision, "sourceSha": source_sha, "files": records, "studies": studies,
                "pdfs": {"/" + p.spec.key: {"sourceSha256": p.source_sha256, "sha256": p.sha256, "kind": p.spec.kind} for p in pdfs}}
    (output / "release.json").write_bytes(encode(manifest))
    return manifest


def validate_bundle(root: Path) -> dict:
    manifest = json.loads((root / "release.json").read_bytes())
    if (manifest.get("schema") != 1 or not re.fullmatch(r"[a-f0-9]{64}", manifest.get("revision", ""))
            or not re.fullmatch(r"[a-f0-9]{40}", manifest.get("sourceSha", ""))):
        raise ValueError("Invalid release manifest")
    for path, record in manifest["files"].items():
        if not safe_path(path):
            raise ValueError(f"Unsafe release path: {path}")
        file = root / "assets" / path.lstrip("/")
        if file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Unsafe release file: {path}")
        body = file.read_bytes()
        if (digest(body), len(body), f'site/objects/{digest(body)}') != (record["sha256"], record["bytes"], record["key"]):
            raise ValueError(f"Release checksum mismatch: {path}")
        if record['archive'] != (not path.startswith('/References/')):
            raise ValueError(f'Reference storage policy mismatch: {path}')
        if 'parts' in record:
            if not path.startswith('/References/') or len(body) <= 25 * 1024 * 1024:
                raise ValueError(f'Unexpected segmented asset: {path}')
            expected = [f'/__reference-parts/{digest(body)}/{i}' for i in range((len(body) + 16*1024*1024-1)//(16*1024*1024))]
            if record['parts'] != expected:
                raise ValueError(f'Invalid asset segment inventory: {path}')
            for index, part in enumerate(expected):
                segment = root / 'assets' / part.lstrip('/')
                if segment.is_symlink() or not segment.resolve().is_relative_to(root.resolve()) or segment.read_bytes() != body[index*16*1024*1024:(index+1)*16*1024*1024]:
                    raise ValueError(f'Invalid asset segment: {part}')
    for path, pdf in manifest.get('pdfs', {}).items():
        if path not in manifest['files'] or pdf['sha256'] != manifest['files'][path]['sha256']:
            raise ValueError(f'PDF inventory mismatch: {path}')
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    release = validate_bundle(args.output_root) if args.verify else build(args.output_root, args.artifact_root)
    print(f'Release {release["revision"]}: {len(release["files"])} public files from {release["sourceSha"]}')
