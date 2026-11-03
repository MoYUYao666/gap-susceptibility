import re, json, time, urllib.request, urllib.parse

papers = [
    ('Paper 1', 'paper/references.bib'),
    ('Paper A', 'paper合/references.bib'),
    ('Paper 3', 'paper3/paper_ieee/references.bib'),
]

# 从 citation_verify_results.json 取未找到条目
results = json.load(open('citation_verify_results.json', encoding='utf-8'))

# 已知正常（无需查）：自家 under review
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

# 对全部"未找到"条目做 DBLP 验证
all_missing = set()
for label, r in results.items():
    for k in r.get('missing_keys', []):
        if k not in OWN:
            all_missing.add(k)

print('=== DBLP 二次验证（%d 条未找到条目）===' % len(all_missing))
final_missing = []
for key in sorted(all_missing):
    # 找该 key 的 title（可能多篇 bib 都有）
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
        print('  [双查无] %-24s %s' % (key, title[:55]))
        final_missing.append(key)
    else:
        print('  [查询失败] %-24s' % key)

print('\n=== 最终高危清单（arXiv+DBLP 均查无）===')
print(final_missing if final_missing else '无')
json.dump({'high_risk': final_missing}, open('citation_high_risk.json', 'w', encoding='utf-8'), ensure_ascii=False)
