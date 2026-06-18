"""Extract text (with paragraph styles) from a .docx for review analysis."""
import sys
import zipfile
import defusedxml.ElementTree as ET

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def qn(tag):
    return f"{{{W}}}{tag}"


def para_text(p):
    return "".join(t.text or "" for t in p.iter(qn("t")))


def para_style(p):
    pPr = p.find(qn("pPr"))
    if pPr is None:
        return ""
    pStyle = pPr.find(qn("pStyle"))
    if pStyle is None:
        return ""
    return pStyle.get(qn("val"), "")


def main(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    body = root.find(qn("body"))
    for el in body:
        tag = el.tag.split("}")[1]
        if tag == "p":
            style = para_style(el)
            text = para_text(el)
            if not text.strip() and not style:
                print()
                continue
            prefix = f"[{style}] " if style else ""
            print(f"{prefix}{text}")
        elif tag == "tbl":
            print("--- TABLE ---")
            for row in el.iter(qn("tr")):
                cells = []
                for cell in row.findall(qn("tc")):
                    cell_text = " ".join(
                        para_text(p) for p in cell.findall(qn("p"))
                    ).strip()
                    cells.append(cell_text)
                print(" | ".join(cells))
            print("--- /TABLE ---")


if __name__ == "__main__":
    main(sys.argv[1])
