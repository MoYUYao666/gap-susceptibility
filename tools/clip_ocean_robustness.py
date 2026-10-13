"""Strengthen ⑦+⑧: multi-seed (subset sampling robustness) and multi-template (3/7 sets, same as A1).
⑦: rebuild the fish subset with seed∈{1,42,99} (≤24 images per class sampled), rerun the λ surgery τ/top1, report mean±sd.
⑧: on the seed42 subset, τ/top1 at key λ points for the 3tpl/7tpl template sets (d̂ fixed to the default template protocol).
Output: outputs/ocean_multiseed.json + ocean_multitemplate.json
"""
import os, sys, json, importlib.util
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from datasets import load_dataset
from scipy import stats

spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
ocm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocm)

TEMPLATE = 'a photo of a {}'
FISH = ['Actinopterygii', 'Chondrichthyes', 'Coelacanthi']
MIN_PER_CLASS = 8
MAX_PER_CLASS = 24
TPL_SETS = {
    '3tpl': ['a photo of a {}', 'a photo of the {}', 'a photo of a {} in a photo'],
    '7tpl': ['a photo of a {}', 'a photo of the {}', 'a photo of a {} in a photo',
             'a {} in a photo', 'a photo of one {}', 'an image of a {}', 'a close-up of a {}'],
}


def build_subset(ds, seed):
    idx_fish = [i for i, r in enumerate(ds) if r['class'] in FISH]
    sub = ds.select(idx_fish)
    import collections
    per = collections.defaultdict(list)
    for i, r in enumerate(sub):
        per[r['sciName']].append(idx_fish[i])
    keep = {c: v for c, v in per.items() if len(v) >= MIN_PER_CLASS}
    rng = np.random.RandomState(seed)
    chosen = []
    for c, v in sorted(keep.items()):
        v = sorted(v)
        if len(v) > MAX_PER_CLASS:
            v = [v[i] for i in rng.choice(len(v), MAX_PER_CLASS, replace=False)]
        chosen.extend((c, j) for j in v)
    classes = sorted(set(c for c, _ in chosen))
    return classes, [j for _, j in chosen]


def run_surgery(tag, ds, idx, texts, labels, lams):
    tf, base = ocm.embed(tag, ds, idx, texts)
    gap = tf.mean(0) - base.mean(0)
    gnorm = gap.norm().item()
    dH = gap / gnorm
    S0 = (base @ tf.T).cpu().numpy()
    topk5 = np.argsort(-S0, axis=1)[:, :5]
    res = {'gap_norm': round(gnorm, 4)}
    for l in lams:
        with torch.no_grad():
            sh = F.normalize(base + l * gnorm * dH, dim=-1)
        Sl = (sh @ tf.T).cpu().numpy()
        top1 = float((Sl.argmax(1) == labels).mean() * 100)
        taus = []
        for i in range(len(S0)):
            r1, r2 = S0[i][topk5[i]], Sl[i][topk5[i]]
            if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                continue
            t, _ = stats.kendalltau(r1, r2)
            if np.isfinite(t):
                taus.append(t)
        res[str(l)] = {'top1': round(top1, 3), 'tau': round(float(np.mean(taus)), 4)}
    return res


def main_seed():
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    out = {}
    for tag in ['bioclip', 'oceanclip']:
        out[tag] = {}
        print('== %s ==' % tag, flush=True)
        for seed in [1, 42, 99]:
            classes, idx = build_subset(ds, seed)
            texts = [ocm.TEMPLATE.format(c) for c in classes]
            labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
            r = run_surgery(tag, ds, idx, texts, labels, [0.0, 0.5, 1.0, 2.0])
            r['n_classes'] = len(classes)
            r['n_images'] = len(idx)
            out[tag]['seed%d' % seed] = r
            print('  seed%d: %d classes/%d images top1@0=%.2f tau@1=%.4f top1@1=%.2f' %
                  (seed, len(classes), len(idx), r['0.0']['top1'], r['1.0']['tau'], r['1.0']['top1']), flush=True)
            json.dump(out, open('outputs/ocean_multiseed.json', 'w', encoding='utf-8'), indent=1)


def main_tpl():
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open('outputs/ocean_subset.json', encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    out = {}
    for tag in ['bioclip', 'oceanclip']:
        print('== %s ==' % tag, flush=True)
        # d̂ fixed: default template protocol
        tf0, base = ocm.embed(tag, ds, idx, [ocm.TEMPLATE.format(c) for c in classes])
        gap = tf0.mean(0) - base.mean(0)
        gnorm = gap.norm().item()
        dH = gap / gnorm
        out[tag] = {'gap_norm': round(gnorm, 4)}
        for name, tpls in TPL_SETS.items():
            texts = [t.format(c) for t in tpls for c in classes]
            tf, _ = ocm.embed(tag, ds, idx, texts)
            tf = tf.view(len(tpls), len(classes), -1).mean(0)
            tf = F.normalize(tf, dim=-1)
            S0 = (base @ tf.T).cpu().numpy()
            topk5 = np.argsort(-S0, axis=1)[:, :5]
            rows = {}
            for l in [0.0, 0.25, 0.5, 1.0, 2.0]:
                with torch.no_grad():
                    sh = F.normalize(base + l * gnorm * dH, dim=-1)
                Sl = (sh @ tf.T).cpu().numpy()
                top1 = float((Sl.argmax(1) == labels).mean() * 100)
                taus = []
                for i in range(len(S0)):
                    r1, r2 = S0[i][topk5[i]], Sl[i][topk5[i]]
                    if np.std(r1) < 1e-12 or np.std(r2) < 1e-12:
                        continue
                    t, _ = stats.kendalltau(r1, r2)
                    if np.isfinite(t):
                        taus.append(t)
                rows[str(l)] = {'top1': round(top1, 3), 'tau': round(float(np.mean(taus)), 4)}
            out[tag][name] = rows
            print('  %s: tpl@1.0 top1=%.2f tau=%.4f' % (name, rows['1.0']['top1'], rows['1.0']['tau']), flush=True)
            json.dump(out, open('outputs/ocean_multitemplate.json', 'w', encoding='utf-8'), indent=1)
    print('DONE', flush=True)


if __name__ == '__main__':
    main_seed()
    main_tpl()
