"""FathomNet shipboard-class subset v2: parallel queries + concurrent downloads, 20 images per class."""
import os, json, time, urllib.request, urllib.parse
import concurrent.futures as cf
import numpy as np

CONCEPTS = ['Actinopterygii', 'Gadiformes', 'Squaliformes', 'Octopoda',
            'Decapoda', 'crab', 'sea star', '55-gallon drum']
N_EACH = 20
OUTDIR = 'data/fathomnet8'
API = 'https://database.fathomnet.org/api/images/query/concept/'
UA = {'User-Agent': 'Mozilla/5.0'}
os.makedirs(OUTDIR, exist_ok=True)
rng = np.random.default_rng(42)


def query(c):
    try:
        d = json.load(urllib.request.urlopen(
            urllib.request.Request(API + urllib.parse.quote(c), headers=UA), timeout=300))
        return c, [i for i in d if i.get('url')]
    except Exception as e:
        print('QUERY FAIL', c, str(e)[:60], flush=True)
        return c, []


def dl(concept, im):
    fp = os.path.join(OUTDIR, concept.replace('/', '_'),
                      '%s_%s.png' % (im['uuid'][:8], str(abs(hash(im['url']))) [:6]))
    if os.path.exists(fp):
        return concept, True
    try:
        data = urllib.request.urlopen(urllib.request.Request(im['url'], headers=UA), timeout=120).read()
        if len(data) > 2000:
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            open(fp, 'wb').write(data)
            return concept, True
    except Exception as e:
        pass
    return concept, False


meta = {}
with cf.ThreadPoolExecutor(max_workers=4) as ex:
    for c, imgs in ex.map(query, CONCEPTS):
        print('%s: %d' % (c, len(imgs)), flush=True)
        if len(imgs) < 12:
            continue
        if len(imgs) > N_EACH:
            sel = rng.choice(len(imgs), N_EACH, replace=False)
            imgs = [imgs[int(i)] for i in sel]
        meta[c] = imgs
json.dump(meta, open(os.path.join(OUTDIR, 'meta.json'), 'w', encoding='utf-8'), indent=1)
print('meta done', {c: len(v) for c, v in meta.items()}, flush=True)
t0 = time.time()
ok = collections_counter = {}
alljobs = [(c, im) for c, ims in meta.items() for im in ims]
done = 0
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for c, good in ex.map(lambda x: dl(*x), alljobs):
        done += 1
        if done % 40 == 0:
            print('  %d/%d %.0fs' % (done, len(alljobs), time.time() - t0), flush=True)
print('DONE %.0fs' % (time.time() - t0), flush=True)
