"""补强实验 ④: rare-species 单来源"海洋动物"扩展类集（鱼+鲸豚+鳍足类+海鸟+珊瑚+海参）。
同一协议（margins 全量分析: m_c/σ_m/margins/精确预测/实测 τ/top1/逐类 Pearson）在更大 N 上复验,
并把 N-sweep 延伸到 N≈120（跨类群, 比 67 类鱼更代表"海洋视觉"）。
输出: outputs/ocean_subset_fauna.json + outputs/ocean_fauna_margins.json
"""
import os, sys, json, importlib.util
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
from datasets import load_dataset

# 复用 clip_ocean_margins 的 embed / analyze（open_clip 模型路径）
spec = importlib.util.spec_from_file_location('ocm', 'tools/clip_ocean_margins.py')
ocm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ocm)

MIN_PER_CLASS = 8
MAX_PER_CLASS = 24
SEED = 42
OUT_SUB = 'outputs/ocean_subset_fauna.json'
OUT = 'outputs/ocean_fauna_margins.json'
FISH = ['Actinopterygii', 'Chondrichthyes', 'Coelacanthi']
PINNIPEDIA = {'Otariidae', 'Phocidae', 'Odobenidae'}
SEABIRDS = {'Procellariiformes', 'Sphenisciformes'}


def marine_mask(r):
    c, o, f = r['class'], r['order'], r['family']
    return (c in FISH or
            (c == 'Mammalia' and o == 'Cetacea') or
            (c == 'Mammalia' and f in PINNIPEDIA) or
            (c == 'Aves' and o in SEABIRDS) or
            (c == 'Anthozoa' and o == 'Scleractinia') or
            c == 'Holothuroidea')


def build():
    ds = load_dataset('parquet', data_files=sorted(
        os.path.join('data/rare-species/data', f) for f in os.listdir('data/rare-species/data')), split='train')
    idx = [i for i, r in enumerate(ds) if marine_mask(r)]
    print('海洋动物行数', len(idx), flush=True)
    sub = ds.select(idx)
    import collections
    per = collections.defaultdict(list)
    for i, r in enumerate(sub):
        per[r['sciName']].append(idx[i])
    keep = {c: v for c, v in per.items() if len(v) >= MIN_PER_CLASS}
    print('≥8 图类目: %d' % len(keep), flush=True)
    rng = np.random.RandomState(SEED)
    chosen = []
    for c, v in sorted(keep.items()):
        v = sorted(v)
        if len(v) > MAX_PER_CLASS:
            v = [v[i] for i in rng.choice(len(v), MAX_PER_CLASS, replace=False)]
        chosen.extend((c, j) for j in v)
    classes = sorted(set(c for c, _ in chosen))
    out = {'classes': classes, 'class_counts': {c: sum(1 for cc, _ in chosen if cc == c) for c in classes},
           'n_images': len(chosen), 'subset_idx': [j for _, j in chosen],
           'groups': {}}
    from collections import Counter
    grp = Counter()
    for j in sorted(set(j for _, j in chosen)):
        r = ds[j]
        if r['class'] in FISH:
            grp['fish'] += 1
        elif r['class'] == 'Mammalia':
            grp['marine_mammal'] += 1
        elif r['class'] == 'Aves':
            grp['seabird'] += 1
        elif r['class'] == 'Anthozoa':
            grp['coral'] += 1
        else:
            grp['other_marine'] += 1
    out['groups'] = dict(grp)
    json.dump(out, open(OUT_SUB, 'w', encoding='utf-8'), indent=1)
    return ds, out


def main():
    ds, sub = build()
    classes = sub['classes']
    idx = sub['subset_idx']
    texts = [ocm.TEMPLATE.format(c) for c in classes]
    labels = np.array([classes.index(r['sciName']) for r in ds.select(idx)])
    print('类目 %d / 图像 %d / 分组 %s' % (len(classes), len(idx), sub['groups']), flush=True)
    res = {}
    for tag in ['bioclip', 'oceanclip']:
        print('== %s ==' % tag, flush=True)
        tf, base = ocm.embed(tag, ds, idx, texts)
        gap = tf.mean(0) - base.mean(0)
        gnorm = gap.norm().item()
        dH = gap / gnorm
        m_c = (dH @ tf.T).cpu().numpy()
        res[tag] = ocm.analyze(tf, base, labels, m_c, gnorm, dH)
        json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
        a = res[tag]
        print('  %s: gap=%.4f sigma_m=%.4f mean_m=%.4f | tau_pred(1)=%.4f tau_meas(1)=%.4f | top1 0→1: %.2f→%.2f'
              % (tag, a['gap_norm'], a['sigma_m'], a['mean_m'],
                 a['predicted_tau_exact']['1.0'], a['measured']['1.0']['tau'],
                 a['measured']['0.0']['top1'], a['measured']['1.0']['top1']), flush=True)
        bp = a['bias_field_pearson'].get('1.0', {})
        if bp:
            print('   bias pearson@1: %.4f (p=%.2g, n=%d)' % (bp['pearson'], bp['p'], bp['n']), flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
