"""riku-1825 FLS 数据集经 jsDelivr 逐文件镜像下载(绕过 GitHub 大包 TLS 中断)。
清单: GitHub API tree(images + 标注);URL: cdn.jsdelivr.net/gh/<repo>@main/<path>
8 并发 + 重试;输出 data/second_sonar/riku1825/<path>
"""
import json
import os
import urllib.request
import concurrent.futures as cf
import time

REPO = 'riku-1825/Forward_Looking_Under_Water_Mines_And_Debris_Sonar_dataset'
OUT = 'data/second_sonar/riku1825'
API = 'https://api.github.com/repos/%s/git/trees/main?recursive=1' % REPO
UA = {'User-Agent': 'Mozilla/5.0'}

req = urllib.request.Request(API, headers=UA)
tree = json.load(urllib.request.urlopen(req, timeout=60))['tree']
blobs = [t for t in tree if t['type'] == 'blob']
print('blobs to fetch:', len(blobs), flush=True)


def fetch(t):
    p = t['path']
    fp = os.path.join(OUT, p.replace('/', os.sep))
    if os.path.exists(fp) and os.path.getsize(fp) == t['size']:
        return 'skip ' + p
    url = 'https://cdn.jsdelivr.net/gh/%s@main/%s' % (REPO, p)
    for attempt in range(4):
        try:
            r = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(r, timeout=90) as resp:
                data = resp.read()
            if len(data) == t['size']:
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                with open(fp, 'wb') as f:
                    f.write(data)
                return 'ok ' + p
            print('  size mismatch %s (%d/%d) attempt %d' % (p, len(data), t['size'], attempt), flush=True)
        except Exception as e:
            if attempt == 3:
                return 'FAIL %s %s' % (p, str(e)[:60])
        time.sleep(2 + attempt * 2)
    return 'FAIL ' + p


fails = 0
done = 0
t0 = time.time()
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for msg in ex.map(fetch, blobs):
        done += 1
        if msg.startswith('FAIL'):
            fails += 1
            print(msg, flush=True)
        if done % 200 == 0:
            print('  %d/%d  fails=%d  %.0fs' % (done, len(blobs), fails, time.time() - t0), flush=True)
print('DONE %d/%d fails=%d  %.0fs' % (done, len(blobs), fails, time.time() - t0), flush=True)
