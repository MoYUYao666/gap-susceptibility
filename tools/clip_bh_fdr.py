"""BH-FDR 校正: 相变章节全部报告的 p 值族(局限 12)。输出 outputs/bh_fdr_correction.json"""
import json
import numpy as np

# 名称, p 值, 来源(论文 tab:phase 讨论)
tests = [
    ('sharegpt_r5_eq0', 0.92, 'ShareGPT r=5 sign test (n=3)'),
    ('llava_r5_eq0', 0.37, 'LLaVA r=5 sign test (n=3)'),
    ('llava_r6_eq0', 0.17, 'LLaVA r=6 sign test (n=3)'),
    ('sharegpt_r6_eq0', 0.013, 'ShareGPT r=6 sign test (n=3)'),
    ('sharegpt_welch_56', 0.011, 'ShareGPT Welch t across r=5..6'),
    ('llava_pooled_45_vs_67', 0.0014, 'LLaVA pooled r{4,5} vs r{6,7} t'),
    ('binomial_ordering', 0.031, 'ordering DeltaE(6)>DeltaE(5) in 6 configs, 2^-5'),
]
ps = np.array([t[1] for t in tests])
names = [t[0] for t in tests]
m = len(ps)
idx = np.argsort(ps)
out = []
for rank, i in enumerate(idx, 1):
    p = ps[i]
    q = p * m / rank
    out.append({'name': names[i], 'p': round(float(p), 4), 'rank': rank,
                'bh_q': round(float(min(q, 1.0)), 4),
                'survives_005': float(q) <= 0.05, 'survives_010': float(q) <= 0.10})
json.dump({'tests': tests, 'bh_fdr': out,
           'summary': 'FDR<=0.05: ' + ', '.join([o['name'] for o in out if o['survives_005']]) +
                      ' | FDR<=0.10: ' + ', '.join([o['name'] for o in out if o['survives_010']])},
          open('outputs/bh_fdr_correction.json', 'w', encoding='utf-8'), indent=1)
print(json.dumps(out, indent=1))
