"""Stable reader anchors, shared by generated HTML and the passage index.

The hash and selection rules preserve Phase 2's browser-created bookmark IDs.
Anchors are now present before JavaScript, including for shared search links.
"""
import re
import unicodedata

from bs4 import BeautifulSoup

PASSAGES = "h2[id],h3[id],h4[id],p,li,table,pre,.mermaid"


def clean_text(value: str) -> str:
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", value).strip())


def passage_key(value: str) -> str:
    a, b = 2166136261, 2246822519
    for character in clean_text(value):
        a = ((a ^ ord(character)) * 16777619) & 0xFFFFFFFF
        b = ((b ^ ord(character)) * 3266489917) & 0xFFFFFFFF
    return f"reader-p-{a:08x}{b:08x}"


def search_text(node) -> str:
    """Read math once, without its duplicate visual rendering or LaTeX annotation."""
    if node.select_one('.katex'):
        node = BeautifulSoup(str(node), 'html.parser')
        for duplicate in node.select('.katex-html, annotation'):
            duplicate.decompose()
    return clean_text(node.get_text())


def annotate_passages(fragment: str) -> str:
    soup = BeautifulSoup(fragment, "html.parser")
    used = {node["id"] for node in soup.select("[id]")}
    section = ""
    counts: dict[str, int] = {}
    for node in soup.select(PASSAGES):
        parents = list(node.parents)
        if any(set(parent.get("class", [])) & {"study-toc", "study-reading-key"} for parent in parents):
            continue
        if any(parent.name in {"li", "table", "pre"} or "mermaid" in parent.get("class", []) for parent in parents):
            continue
        if node.name == "h2":
            section = node["id"]
        text = clean_text(node.get_text())
        if not text and (image := node.find("img")):
            text = clean_text(image.get("alt", ""))
        if not text:
            continue
        if not node.get("id"):
            key = passage_key(section + "\n" + text)
            counts[key] = counts.get(key, 0) + 1
            identifier = key + (f"-{counts[key]}" if counts[key] > 1 else "")
            while identifier in used:
                identifier += "-p"
            node["id"] = identifier
            used.add(identifier)
        node["data-reader-passage"] = ""
        node["data-reader-heading"] = section
    return str(soup)
