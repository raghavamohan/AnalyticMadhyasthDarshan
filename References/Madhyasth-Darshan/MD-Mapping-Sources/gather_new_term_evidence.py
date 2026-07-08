import json, re, sys

DEVA_TOKEN = re.compile(r'[ऀ-ॿ]+')
MAX_PER_TERM = 4
MAX_CHARS = 350

def tokenize(text):
    return DEVA_TOKEN.findall(text)

def load_pairs(path, book_tag):
    data = json.load(open(path, encoding='utf-8'))
    out = []
    for p in data:
        if not p.get('en'):
            continue
        out.append({
            'hi_tokens': tokenize(p['hi']),
            'hi_text': p['hi'],
            'en_text': p['en'],
            'hi_page': p['hi_page'],
            'en_page': p['en_page'],
            'book': book_tag,
        })
    return out

def trim(t):
    t = t.strip()
    return t[:MAX_CHARS] + '…' if len(t) > MAX_CHARS else t

def main():
    candidates = json.load(open(sys.argv[1], encoding='utf-8'))  # [[token, freq], ...]
    mvd = load_pairs(sys.argv[2], 'MVD')
    sb = load_pairs(sys.argv[3], 'SB')
    all_pairs = mvd + sb
    out_path = sys.argv[4]

    results = []
    for token, freq in candidates:
        hits = [p for p in all_pairs if token in p['hi_tokens']]
        hits.sort(key=lambda p: len(p['hi_text']))  # shortest/most focused first
        # prefer MVD hits first (priority source), then SB
        hits.sort(key=lambda p: 0 if p['book'] == 'MVD' else 1)
        sample = hits[:MAX_PER_TERM]
        results.append({
            'token': token,
            'total_occurrences': freq,
            'evidence': [
                {'book': h['book'], 'hi_page': h['hi_page'], 'en_page': h['en_page'],
                 'hi': trim(h['hi_text']), 'en': trim(h['en_text'])}
                for h in sample
            ],
        })

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=1)
    print(f'{len(results)} candidate tokens with evidence written', file=sys.stderr)

if __name__ == '__main__':
    main()
