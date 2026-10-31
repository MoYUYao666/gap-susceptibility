"""按论文口径(仅 LoRA rank sweep 配置, 排除 frozen/full-FT)重算 tab:generalization 两行。"""
import json
import numpy as np
from collections import defaultdict

for label, f in [('Flickr30k', 'outputs/theory/v1_trajectory/v1_all_results.json'),
                 ('COCO', 'outputs/theory/v1_coco/v1_all_results.json')]:
    d = json.load(open(f, encoding='utf-8'))
    rs = d if isinstance(d, list) else d.get('all_results', d.get('results', []))
    names = sorted(set(str(r.get('name', '')) for r in rs))
    print('===', label, 'distinct names:', names)
    peft = [r for r in rs if not any(t in str(r.get('name', '')).lower() for t in ('frozen', 'full_ft', 'fullft'))]
    print('   LoRA-only runs n =', len(peft), ' configs =', len(set(str(r.get('name')) for r in peft)))
    a = [r['alpha'] for r in peft if r.get('alpha') is not None]
    b = [r['beta'] for r in peft if r.get('beta') is not None]
    r2 = [r['r_squared'] for r in peft if r.get('r_squared') is not None]
    print('   alpha %.4f | beta %.4f | R2 %.4f  sd(pop)=%.4f sd(sample)=%.4f' % (
        np.mean(a), np.mean(b), np.mean(r2), np.std(r2), np.std(r2, ddof=1)))
    # config 级(每配置先平均)
    byc = defaultdict(list)
    for r in peft:
        byc[str(r.get('name'))].append(r)
    cr2 = [np.mean([x['r_squared'] for x in v]) for v in byc.values()]
    cb = [np.mean([x['beta'] for x in v]) for v in byc.values()]
    ca = [np.mean([x['alpha'] for x in v]) for v in byc.values()]
    print('   config-level (n=%d): alpha %.4f | beta %.4f | R2 %.4f ± %.4f(pop) %.4f(sample)' % (
        len(byc), np.mean(ca), np.mean(cb), np.mean(cr2), np.std(cr2), np.std(cr2, ddof=1)))
