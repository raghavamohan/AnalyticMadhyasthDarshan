"""Publish Agent Skills Discovery via a Cloudflare Worker.

Snippets cannot currently be created with the zone token used for Transform
Rules, so this path deploys Worker `amd-agent-skills` and a route covering
`/.well-known/agent-skills/*`. Static copies remain under
`.well-known/agent-skills/` for GitHub Pages.
"""
from __future__ import annotations

import hashlib
import json
import sys
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cloudflare_performance as cf

from _build_agent_skills_index import INDEX_PATH, MAINTAINER_INDEX_PATH, PUBLISH_ROOT

WORKER_NAME = "amd-agent-skills"
WORKER_ROUTE = f"{cf.SITE_HOST}/.well-known/agent-skills/*"
WORKER_SRC = cf.BASE / "infra" / "agent-skills-worker" / "src" / "index.js"
COMPATIBILITY_DATE = "2024-03-01"


def worker_js(index: dict, maintainer_index: dict, skills: dict[str, str]) -> str:
    body = json.dumps(index, separators=(",", ":"), ensure_ascii=False)
    maintainer_body = json.dumps(
        maintainer_index, separators=(",", ":"), ensure_ascii=False
    )
    etag = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    maintainer_etag = hashlib.sha256(maintainer_body.encode("utf-8")).hexdigest()[:16]
    skill_entries = ",\n".join(
        f"  {json.dumps(name)}: {json.dumps(text)}"
        for name, text in sorted(skills.items())
    )
    return f"""\
const INDEX = {json.dumps(body)};
const MAINTAINER_INDEX = {json.dumps(maintainer_body)};
const SKILLS = {{
{skill_entries}
}};
const INDEX_HEADERS = {{
  "content-type": {json.dumps(cf.AGENT_SKILLS_INDEX_CONTENT_TYPE)},
  "cache-control": "public, max-age=3600",
  "etag": {json.dumps(f'"{etag}"')},
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, OPTIONS"
}};
const MAINTAINER_INDEX_HEADERS = {{
  "content-type": {json.dumps(cf.AGENT_SKILLS_INDEX_CONTENT_TYPE)},
  "cache-control": "public, max-age=3600",
  "etag": {json.dumps(f'"{maintainer_etag}"')},
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, OPTIONS"
}};
const SKILL_HEADERS = {{
  "content-type": {json.dumps(cf.AUTH_MD_CONTENT_TYPE)},
  "cache-control": "public, max-age=3600",
  "access-control-allow-origin": "*",
  "access-control-allow-methods": "GET, HEAD, OPTIONS"
}};

function respond(request, body, headers) {{
  if (request.method === "OPTIONS") {{
    return new Response(null, {{ status: 204, headers }});
  }}
  if (request.method === "HEAD") {{
    return new Response(null, {{ status: 200, headers }});
  }}
  return new Response(body, {{ status: 200, headers }});
}}

export default {{
  async fetch(request) {{
    const path = new URL(request.url).pathname.replace(/\\/+$/, "") || "/";
    if (path === "/.well-known/agent-skills/index.json") {{
      return respond(request, INDEX, INDEX_HEADERS);
    }}
    if (path === "/.well-known/agent-skills/index-maintainer.json") {{
      return respond(request, MAINTAINER_INDEX, MAINTAINER_INDEX_HEADERS);
    }}
    const match = path.match(/^\\/.well-known\\/agent-skills\\/([a-z0-9-]+)\\/SKILL\\.md$/);
    if (match && Object.prototype.hasOwnProperty.call(SKILLS, match[1])) {{
      return respond(request, SKILLS[match[1]], SKILL_HEADERS);
    }}
    return new Response("Not Found", {{ status: 404 }});
  }}
}};
"""


def load_published_skills() -> dict[str, str]:
    skills: dict[str, str] = {}
    if not PUBLISH_ROOT.is_dir():
        return skills
    for skill_dir in sorted(PUBLISH_ROOT.iterdir()):
        skill_file = skill_dir / "SKILL.md"
        if skill_dir.is_dir() and skill_file.is_file():
            skills[skill_dir.name] = skill_file.read_text(encoding="utf-8")
    return skills


def multipart_put(url: str, token: str, filename: str, content: str, metadata: dict) -> dict:
    boundary = uuid.uuid4().hex
    parts = []
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"metadata\"; "
        f"filename=\"metadata.json\"\r\nContent-Type: application/json\r\n\r\n"
        f"{json.dumps(metadata)}\r\n"
    )
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{filename}\"; "
        f"filename=\"{filename}\"\r\nContent-Type: application/javascript+module\r\n\r\n"
        f"{content}\r\n"
    )
    parts.append(f"--{boundary}--\r\n")
    body = "".join(parts).encode("utf-8")
    req = Request(
        url,
        data=body,
        method="PUT",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc


def resolve_account_id(token: str) -> str:
    payload = cf._api_request("GET", "/accounts?per_page=20", token)
    accounts = (payload or {}).get("result") or []
    if not accounts:
        raise RuntimeError("CLOUDFLARE_API_TOKEN cannot list accounts.")
    return accounts[0]["id"]


def ensure_route(token: str, zone: str, script: str, pattern: str) -> None:
    payload = cf._api_request("GET", f"/zones/{zone}/workers/routes", token)
    routes = (payload or {}).get("result") or []
    for route in routes:
        if route.get("pattern") == pattern:
            if route.get("script") == script:
                print(f"Worker route already configured: {pattern}")
                return
            cf._api_request(
                "PUT",
                f"/zones/{zone}/workers/routes/{route['id']}",
                token,
                {"pattern": pattern, "script": script},
            )
            print(f"Updated worker route {pattern} -> {script}")
            return
    cf._api_request(
        "POST",
        f"/zones/{zone}/workers/routes",
        token,
        {"pattern": pattern, "script": script},
    )
    print(f"Created worker route {pattern} -> {script}")


def main() -> int:
    cf.load_repo_env()
    token = cf.cloudflare_api_token()
    if not token:
        print("CLOUDFLARE_API_TOKEN is required.", file=sys.stderr)
        return 1
    if not INDEX_PATH.is_file() or not MAINTAINER_INDEX_PATH.is_file():
        print("Run python Scripts/_build_agent_skills_index.py first.", file=sys.stderr)
        return 1
    zone = cf.resolve_zone_id(token, cf.cloudflare_zone_id())
    account = resolve_account_id(token)
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    maintainer_index = json.loads(MAINTAINER_INDEX_PATH.read_text(encoding="utf-8"))
    skills = load_published_skills()
    if not skills:
        print("No published SKILL.md files under .well-known/agent-skills/.", file=sys.stderr)
        return 1
    js = worker_js(index, maintainer_index, skills)
    WORKER_SRC.parent.mkdir(parents=True, exist_ok=True)
    WORKER_SRC.write_text(js, encoding="utf-8", newline="\n")
    print(f"Wrote {WORKER_SRC.relative_to(cf.BASE)}")
    print(f"Uploading worker {WORKER_NAME!r} to account {account}...")
    result = multipart_put(
        f"{cf.API_BASE}/accounts/{account}/workers/scripts/{WORKER_NAME}",
        token,
        "index.js",
        js,
        {"main_module": "index.js", "compatibility_date": COMPATIBILITY_DATE},
    )
    print(json.dumps(result.get("result") or result, indent=2)[:2000])
    try:
        cf._api_request(
            "POST",
            f"/accounts/{account}/workers/scripts/{WORKER_NAME}/subdomain",
            token,
            {"enabled": True, "previews_enabled": True},
        )
        print("Enabled workers.dev subdomain for the script.")
    except RuntimeError as exc:
        print(f"workers.dev subdomain enable skipped: {exc}")
    try:
        ensure_route(token, zone, WORKER_NAME, WORKER_ROUTE)
    except RuntimeError as exc:
        print(
            "Zone worker route was not created (token may lack Workers Routes Edit). "
            f"{exc}"
        )
    cf.apply_agent_skills_redirect(token, zone)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
