"""Lightweight, transitive source fingerprints shared by PDF caches."""
import ast
import hashlib
from pathlib import Path

def script_dependencies(root: Path, names: tuple[str, ...]) -> set[str]:
    pending = list(names)
    found: set[str] = set()
    while pending:
        name = pending.pop()
        relative = "Scripts/" + name
        path = root / relative
        if relative in found or not path.is_file():
            continue
        found.add(relative)
        if path.suffix != ".py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                pending.append(node.module.split(".")[0] + ".py")
            elif isinstance(node, ast.Import):
                pending.extend(alias.name.split(".")[0] + ".py" for alias in node.names)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                # Subprocess helpers are often not imported as Python modules.
                candidate = node.value.replace("\\", "/").split("/")[-1]
                if candidate.startswith("_") and Path(candidate).suffix in {".py", ".js", ".cjs", ".mjs"}:
                    pending.append(candidate)
    return found



def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
