"""Compare generated discovery Worker bundles with their canonical inputs."""
from __future__ import annotations

import json
from pathlib import Path

import _publish_agent_skills_snippet as agent_skills
import _publish_auth_md_snippet as auth_md
import _publish_mcp_server_card as mcp


BASE = Path(__file__).resolve().parent.parent


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def check(path: Path, expected: str) -> None:
    if not path.is_file():
        fail(f"missing generated bundle {path.relative_to(BASE)}")
    actual = path.read_bytes()
    canonical = expected.replace("\r\n", "\n").encode("utf-8")
    if actual != canonical:
        fail(f"{path.relative_to(BASE)} differs byte-for-byte from canonical inputs")
    print(f"OK: {path.relative_to(BASE)} matches canonical inputs byte-for-byte.")


def main() -> None:
    agent_index = json.loads(agent_skills.INDEX_PATH.read_text(encoding="utf-8"))
    maintainer_index = json.loads(
        agent_skills.MAINTAINER_INDEX_PATH.read_text(encoding="utf-8")
    )
    check(
        agent_skills.WORKER_SRC,
        agent_skills.worker_js(
            agent_index,
            maintainer_index,
            agent_skills.load_published_skills(),
        ),
    )
    check(
        mcp.WORKER_SRC,
        mcp.worker_js(json.loads(mcp.CARD_PATH.read_text(encoding="utf-8"))),
    )
    check(
        auth_md.WORKER_SRC,
        auth_md.worker_js(auth_md.AUTH_MD_PATH.read_text(encoding="utf-8")),
    )


if __name__ == "__main__":
    main()
