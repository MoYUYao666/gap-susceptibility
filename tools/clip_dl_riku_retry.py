import json, os, time, urllib.request
import concurrent.futures as cf
REPO = 'riku-1825/Forward_Looking_Under_Water_Mines_And_Debris_Sonar_dataset'
OUT = 'data/second_sonar/riku1825'
UA = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request('https://api.github.com/repos/%s/git/trees/main?recursive=1' % REPO, headers=UA)
tree = json.load(urllib.request.urlopen(req, timeout=60))['tree']
blobs = [t for t in tree if t['type'] == 'blob']
miss = [t for t in blobs if not (os.path.exists(os.path.join(OUT, t['path'].replace('/', os.sep)))
        and os.path.getsize(os.path.join(OUT, t['path'].replace('/', os.sep))) == t['size'])]
print('retry missing:', len(miss), flush=True)


def fetch(t):
    p = t['path']
    fp = os.path.join(OUT, p.replace('/', os.sep))
    url = 'https://cdn.jsdelivr.net/gh/%s@main/%s' % (REPO, p)
    for attempt in range(6):
        try:
            r = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(r, timeout=120) as resp:
                data = resp.read()
            if len(data) == t['size']:
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                with open(fp, 'wb') as f:
                    f.write(data)
                return 'ok ' + p
            print('  mismatch %s (%d/%d)' % (p, len(data), t['size']), flush=True)
        except Exception as e:
            if attempt == 5:
                return 'FAIL ' + p
        time.sleep(10 + attempt * 10)
    return 'FAIL ' + p


with cf.ThreadPoolExecutor(max_workers=4) as ex:
    for msg in ex.map(fetch, miss):
        print(msg, flush=True)
print('retry DONE', flush=True)
