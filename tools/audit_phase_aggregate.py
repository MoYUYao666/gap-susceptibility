"""Aggregate ΔE = E[-1] - E[0] with the correct structure (the E list), cross-checking the paper's phase table and counterfactual numbers."""
import json
import math
from collections import defaultdict

PAPER = {  # rank: (mean, std) paper tab:phase
    4: (-105, 21), 5: (-21, 26), 6: (62, 42), 7: (192, 44),
    8: (311, 49), 16: (1572, 67), 20: (2860, 234),
}


def de_of(rec):
    E = rec.get('E')
    if not isinstance(E, list) or len(E) < 2:
        return None
    a, b = E[0], E[-1]
    if a is None or b is None:
        return None
    if isinstance(a, float) and math.isnan(a):
        return None
    if isinstance(b, float) and math.isnan(b):
        return float('nan')
    return float(b) - float(a)


def aggregate(records, label):
    by_rank = defaultdict(list)
    for r in records:
        by_rank[r.get('rank')].append(de_of(r))
    print('===', label)
    for rk in sorted(by_rank, key=lambda x: (x is None, x)):
        vals = by_rank[rk]
        ok = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
        nans = sum(1 for v in vals if isinstance(v, float) and math.isnan(v))
        if not ok:
            print('   rank=%-3s n=%d all-NaN nan=%d' % (rk, len(vals), nans))
            continue
        m = sum(ok) / len(ok)
        sd = (sum((x - m) ** 2 for x in ok) / len(ok)) ** 0.5
        tag = ''
        if rk in PAPER:
            pm, ps = PAPER[rk]
            tag = '  [paper %+d±%d]' % (pm, ps)
        print('   rank=%-3s n=%d mean=%+.1f std=%.1f nan=%d%s' % (rk, len(ok), m, sd, nans, tag))


d = json.load(open('paper3/scripts/outputs/experiments/E2_results.json', encoding='utf-8'))
for k in d:
    aggregate(d[k], 'E2_results.json:' + k)

a = json.load(open('paper3/scripts/outputs/experiments/all_results.json', encoding='utf-8'))
print()
for k in a:
    vals = [de_of(r) for r in a[k]]
    ok = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
    nans = sum(1 for v in vals if isinstance(v, float) and math.isnan(v))
    if ok:
        m = sum(ok) / len(ok)
        sd = (sum((x - m) ** 2 for x in ok) / len(ok)) ** 0.5
        print('=== counterfactual %-14s n=%d mean=%+.1f std=%.1f nan=%d' % (k, len(ok), m, sd, nans))
    else:
        print('=== counterfactual %-14s n=%d all-NaN nan=%d' % (k, len(vals), nans))
