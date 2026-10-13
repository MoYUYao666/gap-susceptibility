import re, os, time, urllib.request, urllib.parse, json

papers = [
    ('Paper 1', 'paper/references.bib'),
    ('Paper A', 'paper合/references.bib'),
    ('Paper 3', 'paper3/paper_ieee/references.bib'),
]

def query_arxiv(title):
    q = urllib.parse.quote('ti:"%s"' % title)
    try:
        resp = urllib.request.urlopen(
            'http://export.arxiv.org/api/query?search_query=%s&max_results=2' % q, timeout=15)
        xml = resp.read().decode('utf-8', errors='ignore')
        titles = re.findall(r'<title>(.*?)</title>', xml, re.S)
        return len(titles) > 1  # first is feed title
    except Exception:
        return None

results = {}
for label, bib in papers:
    src = open(bib, encoding='utf-8').read()
    entries = re.findall(r'@\w+\{([^,]+),([^@]*?)\n\}', src, re.S)
    n_found = n_miss = n_err = 0
    missing = []
    for key, body in entries:
        tm = re.search(r'title\s*=\s*[{"](.+?)[}"]\s*,', body, re.S)
        if not tm:
            continue
        title = ' '.join(tm.group(1).split())
        ok = query_arxiv(title)
        time.sleep(3)
        if ok is True:
            n_found += 1
        elif ok is False:
            n_miss += 1
            missing.append(key)
        else:
            n_err += 1
    results[label] = {'found': n_found, 'missing': n_miss, 'error': n_err, 'missing_keys': missing}
    print('%s: found=%d missing=%d error=%d' % (label, n_found, n_miss, n_err))
    if missing:
        print('  missing: %s' % missing)

with open('citation_verify_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print('results saved to citation_verify_results.json')
