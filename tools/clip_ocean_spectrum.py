"""Supplementary experiment B: marine-domain task-sensitivity spectrum (matching A1's NCC < zero-shot < retrieval).
On the fish-67 subset, image side λ grid {0,0.5,1,2}, three probes:
  NCC  = nearest class centroid classification accuracy (centroids built only from frozen embeddings, frozen unchanged)
  top1 = zero-shot classification accuracy
  R1   = retrieval R@1 (i2t+t2i average; t2i is the non-degenerate probe)
Output: outputs/ocean_spectrum.json
"""
import os, sys, json, importlib.util
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn.functional as F
from scipy import stats
from datasets import load_dataset

spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
ocm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocm)

LAMS = [0.0, 0.5, 1.0, 2.0]
OUT = 'outputs/ocean_spectrum.json'


def main():
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    sub = json.load(open('outputs/ocean_subset.json', encoding='utf-8'))
    classes = sub['classes']
    idx = sub['subset_idx']
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    texts = [ocm.TEMPLATE.format(c) for c in classes]
    res = {}
    for tag in ['bioclip', 'oceanclip']:
        print('== %s ==' % tag, flush=True)
        tf, base = ocm.embed(tag, ds, idx, texts)
        gap = tf.mean(0) - base.mean(0)
        gnorm = gap.norm().item()
        dH = gap / gnorm
        # class centroids (frozen embeddings)
        centroids = torch.zeros(len(classes), base.shape[1], device='cuda')
        for c in range(len(classes)):
            cc = base[labels == c]
            centroids[c] = F.normalize(cc.mean(0), dim=-1)
        rows = []
        for l in LAMS:
            with torch.no_grad():
                sh = F.normalize(base + l * gnorm * dH, dim=-1)
            S = (sh @ tf.T).cpu().numpy()
            top1 = float((S.argmax(1) == labels).mean() * 100)
            # retrieval R@1: i2t (argmax over texts, same as top1) + t2i (argmax over images per text)
            sims = torch.tensor(S)
            i2t = (sims.argmax(1).cpu().numpy() == labels).mean()
            t2i = np.zeros(len(classes))
            for c in range(len(classes)):
                cand = np.where(labels == c)[0]
                if len(cand) == 0:
                    continue
                g = sims[:, c].argmax().item()
                t2i[c] = 1.0 if labels[g] == c else 0.0
            r1 = float((i2t + t2i[t2i > -1].mean()) / 2)
            # NCC centroid classification
            Sn = (sh @ centroids.T).cpu().numpy()
            ncc = float((Sn.argmax(1) == labels).mean() * 100)
            cg = (sh.mean(0) - tf.mean(0)).norm().item()
            rows.append({'lambda': l, 'NCC': round(ncc, 3), 'top1': round(top1, 3),
                         'R1': round(r1, 4), 'CG': round(cg, 4)})
            print('  λ=%.1f NCC=%.2f top1=%.2f R1=%.4f CG=%.4f' % (l, ncc, top1, r1, cg), flush=True)
        res[tag] = {'gap_norm': round(gnorm, 4), 'rows': rows}
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
