"""Keep the curated website visual registry aligned with study lifecycle changes."""
from pathlib import Path
import json
from _common import BASE
from _theme_icons import load_study_visuals


def sync_study_visuals(rows: list[dict], *, root: Path = BASE) -> None:
    """Preserve curated associations; use the neutral learning mark for new studies."""
    from _common import write_text_lf

    path = root / "Assets/Theme/study-visuals.json"
    data = json.loads(path.read_bytes()) if path.is_file() else {"studies": []}
    existing = data.get("studies")
    if not isinstance(existing, list):
        raise ValueError("study-visuals.json: missing studies array")
    by_slug = {}
    for item in existing:
        if not isinstance(item, dict) or not item.get("slug") or not item.get("icon") or item["slug"] in by_slug:
            raise ValueError("study-visuals.json: invalid or duplicate study assignment")
        by_slug[item["slug"]] = item
    current = {row["slug"]: row for row in rows}
    # Keep the approved kit's order and custom fields. Removed studies must not
    # leave assignments that fail the exact catalog-coverage gate.
    kept = [item for item in existing if item["slug"] in current]
    for row in rows:
        if row["slug"] not in by_slug:
            kept.append({"slug": row["slug"], "title": row["title"], "icon": "learning", "theme": "", "illustration": ""})
    data["studies"] = kept
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_lf(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    load_study_visuals.cache_clear()


def rename_study_visual(old_slug: str, new_slug: str, *, root: Path = BASE) -> None:
    """Carry an existing curated association through a catalog slug rename."""
    from _common import write_text_lf

    path = root / "Assets/Theme/study-visuals.json"
    if not path.is_file() or old_slug == new_slug:
        return
    data = json.loads(path.read_bytes())
    studies = data["studies"]
    if any(row["slug"] == new_slug for row in studies):
        raise ValueError(f"A visual assignment already exists for {new_slug}")
    for row in studies:
        if row["slug"] == old_slug:
            row["slug"] = new_slug
    write_text_lf(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    load_study_visuals.cache_clear()


