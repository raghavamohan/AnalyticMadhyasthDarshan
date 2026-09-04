import sys, json, re
import pymupdf as fitz

DEVA_RE = re.compile(r'[ऀ-ॿ]')
LATIN_RE = re.compile(r'[A-Za-z]')

def classify(text):
    t = text.strip()
    if not t:
        return 'blank'
    deva = len(DEVA_RE.findall(t))
    latin = len(LATIN_RE.findall(t))
    if deva == 0 and latin == 0:
        return 'other'  # pure numbers/bullets/symbols
    if deva > 0 and latin == 0:
        return 'hi'
    if latin > 0 and deva == 0:
        return 'en'
    return 'mixed'  # e.g. transliteration footnotes, inline Sanskrit in English para

def clean(text):
    # strip bullet glyphs, zero-width spaces, leading numbering
    t = text.replace('​', '').strip()
    t = re.sub(r'^[•●\-\*]\s*', '', t)  # bullet chars
    return t

def is_boilerplate(text, y0, y1, page_h):
    t = text.strip()
    if not t:
        return True
    # footer/header bands
    if y0 < page_h * 0.03 or y1 > page_h * 0.97:
        return True
    if re.fullmatch(r'page[-\s]?\d+', t, re.IGNORECASE):
        return True
    if re.fullmatch(r'\d{1,4}', t):
        return True
    return False

def extract(pdf_path, book_tag, page_range=None):
    doc = fitz.open(pdf_path)
    n = len(doc)
    pages = range(n) if page_range is None else range(page_range[0]-1, page_range[1])
    units = []  # list of dict(class, text, page, y0)
    for i in pages:
        page = doc[i]
        page_h = page.rect.height
        blocks = page.get_text('blocks')
        blocks.sort(key=lambda b: (round(b[1]/5), b[0]))  # reading order: row-ish then x
        for b in blocks:
            x0, y0, x1, y1, text = b[0], b[1], b[2], b[3], b[4]
            if is_boilerplate(text, y0, y1, page_h):
                continue
            cls = classify(text)
            if cls in ('blank', 'other'):
                continue
            txt = clean(text)
            if not txt:
                continue
            units.append({'cls': cls, 'text': txt, 'page': i+1})

    # merge consecutive same-class units into groups
    groups = []
    for u in units:
        if groups and groups[-1]['cls'] == u['cls'] and groups[-1]['page'] == u['page']:
            groups[-1]['text'] += '\n' + u['text']
        elif groups and groups[-1]['cls'] == u['cls'] and u['page'] == groups[-1]['page'] + 1:
            # allow same-class continuation across a page break (paragraph split by page)
            groups[-1]['text'] += '\n' + u['text']
            groups[-1]['page_end'] = u['page']
        else:
            groups.append({'cls': u['cls'], 'text': u['text'], 'page': u['page'], 'page_end': u['page']})

    # pair hi -> en (allow hi followed by mixed then en, treat mixed as part of en side if it follows hi)
    pairs = []
    i = 0
    while i < len(groups):
        g = groups[i]
        if g['cls'] == 'hi':
            hi_text = g['text']
            hi_page = g['page']
            j = i + 1
            en_text = None
            en_page = None
            if j < len(groups) and groups[j]['cls'] in ('en', 'mixed'):
                en_text = groups[j]['text']
                en_page = groups[j]['page']
                j += 1
            pairs.append({
                'book': book_tag,
                'hi': hi_text,
                'en': en_text,
                'hi_page': hi_page,
                'en_page': en_page,
            })
            i = j
        else:
            i += 1
    return pairs

if __name__ == '__main__':
    pdf_path = sys.argv[1]
    book_tag = sys.argv[2]
    out_path = sys.argv[3]
    start = int(sys.argv[4]) if len(sys.argv) > 4 else None
    end = int(sys.argv[5]) if len(sys.argv) > 5 else None
    page_range = (start, end) if start else None
    pairs = extract(pdf_path, book_tag, page_range)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(pairs, f, ensure_ascii=False, indent=2)
    print(f'{book_tag}: {len(pairs)} pairs written to {out_path}')
