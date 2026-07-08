import json, sys

MAX_PER_SOURCE = 3
MAX_CHARS = 350

def trim_text(t):
    t = t.strip()
    if len(t) > MAX_CHARS:
        t = t[:MAX_CHARS] + '…'
    return t

def dedupe_and_cap(evidence_list):
    seen = set()
    out = []
    # prefer shorter (more focused) snippets first
    for e in sorted(evidence_list, key=lambda e: len(e['hi_text'])):
        key = (e['hi_page'], e['en_page'])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            'term': e['term'],
            'hi_page': e['hi_page'],
            'en_page': e['en_page'],
            'hi': trim_text(e['hi_text']),
            'en': trim_text(e['en_text']),
        })
        if len(out) >= MAX_PER_SOURCE:
            break
    return out

def main():
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    out = []
    for row in data:
        mvd = dedupe_and_cap(row['evidence']['MVD'])
        sb = dedupe_and_cap(row['evidence']['SB'])
        out.append({
            'row': row['row'],
            'hindi_variants': row['hindi_variants'],
            'existing_english': row['existing_english'],
            'existing_transliteration': row['existing_transliteration'],
            'existing_reference': row['existing_reference'],
            'mvd_evidence_count_total': len(row['evidence']['MVD']),
            'sb_evidence_count_total': len(row['evidence']['SB']),
            'mvd': mvd,
            'sb': sb,
        })
    with open(sys.argv[2], 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f'{len(out)} rows written', file=sys.stderr)

if __name__ == '__main__':
    main()
