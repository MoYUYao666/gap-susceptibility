"""ARACATI2017 FLS dataset — per-file mirror download from jsDelivr (6366 images + annotations)."""
import os, json, time, urllib.request, urllib.parse
import concurrent.futures as cf

REPO = 'sourajyoti-datta/Object_Detection_ARACATI2017'
OUT = 'data/aracati2017'
UA = {'User-Agent': 'Mozilla/5.0'}

req = urllib.request.Request('https://api.github.com/repos/%s/git/trees/main?recursive=1' % REPO, headers=UA)
tree = json.load(urllib.request.urlopen(req, timeout=300))['tree']
blobs = [t for t in tree if t['type'] == 'blob']
print('blobs:', len(blobs), flush=True)


def fetch(t):
    p = t['path']
    fp = os.path.join(OUT, p.replace('/', os.sep))
    if os.path.exists(fp) and os.path.getsize(fp) == t['size']:
        return 'skip'
    url = 'https://cdn.jsdelivr.net/gh/%s@main/%s' % (REPO, p.replace(' ', '%20'))
    for attempt in range(4):
        try:
            r = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(r, timeout=120) as resp:
                data = resp.read()
            if len(data) == t['size']:
                os.makedirs(os.path.dirname(fp), exist_ok=True)
                with open(fp, 'wb') as f:
                    f.write(data)
                return 'ok'
            print('  mismatch %s %d/%d' % (p, len(data), t['size']), flush=True)
        except Exception as e:
            if attempt == 3:
                return 'FAIL ' + p
        time.sleep(3 + attempt * 5)
    return 'FAIL ' + p


fails = 0
t0 = time.time()
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for i, msg in enumerate(ex.map(fetch, blobs)):
        if msg.startswith('FAIL'):
            fails += 1
            print(msg, flush=True)
        if (i + 1) % 800 == 0:
            print('  %d/%d fails=%d %.0fs' % (i + 1, len(blobs), fails, time.time() - t0), flush=True)
print('DONE %d/%d fails=%d %.0fs' % (len(blobs), len(blobs), fails, time.time() - t0), flush=True)
