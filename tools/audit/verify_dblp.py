import re, json, time, urllib.request, urllib.parse

papers = [
    ('Paper 1', 'paper/references.bib'),
    ('Paper A', 'paper合/references.bib'),
    ('Paper 3', 'paper3/paper_ieee/references.bib'),
]

# Take the not-found entries from citation_verify_results.json
results = json.load(open('citation_verify_results.json', encoding='utf-8'))

# Known OK (no lookup needed): our own under-review papers
OWN = {'wan2026protect', 'wan2026gap'}

def query_dblp(title):
    q = urllib.parse.quote(title)
    try:
        resp = urllib.request.urlopen(
            'https://dblp.org/search/publ/api?q=%s&format=json&h=5' % q, timeout=15)
        data = json.loads(resp.read().decode('utf-8', errors='ignore'))
        hits = data.get('result', {}).get('hits', {}).get('hit', [])
        return len(hits) > 0
    except Exception:
        return None

missing_by_paper = {}
for label, bib in papers:
    src = open(bib, encoding='utf-8').read()
    entries = re.findall(r'@\w+\{([^,]+),([^@]*?)\n\}', src, re.S)
    entry_titles = {}
    for key, body in entries:
        tm = re.search(r'title\s*=\s*[{"](.+?)[}"]\s*,', body, re.S)
        if tm:
            entry_titles[key] = ' '.join(tm.group(1).split())
    missing_by_paper[label] = entry_titles

# Run DBLP verification on all "not found" entries
all_missing = set()
for label, r in results.items():
    for k in r.get('missing_keys', []):
        if k not in OWN:
            all_missing.add(k)

print('=== DBLP second-pass verification (%d not-found entries) ===' % len(all_missing))
final_missing = []
for key in sorted(all_missing):
    # find the title for this key (several bib files may have it)
    title = None
    for label in missing_by_paper:
        if key in missing_by_paper[label]:
            title = missing_by_paper[label][key]
            break
    if not title:
        continue
    ok = query_dblp(title)
    time.sleep(1.5)
    if ok is True:
        print('  [DBLP✓] %-24s %s' % (key, title[:55]))
    elif ok is False:
        print('  [both missing] %-24s %s' % (key, title[:55]))
        final_missing.append(key)
    else:
        print('  [query failed] %-24s' % key)

print('\n=== Final high-risk list (found in neither arXiv nor DBLP) ===')
print(final_missing if final_missing else 'none')
json.dump({'high_risk': final_missing}, open('citation_high_risk.json', 'w', encoding='utf-8'), ensure_ascii=False)
