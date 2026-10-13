"""(Corrected version) Linearity of the decoder-side risk model: input = the mean |ΔE| over the 7 finite ranks of the phase table, with the full input recorded for reproducibility.
Output: outputs/llava_rank_linearity_v2.json
"""
import json
import numpy as np
from scipy import stats

RANKS = [4, 5, 6, 7, 8, 16, 20]
DE = [-105.2, -21.0, 62.3, 191.5, 311.3, 1571.5, 2859.7]  # tab:phase mean (E2_results.json)
x = np.array(RANKS, dtype=float)
y = np.abs(np.array(DE, dtype=float))

lin = stats.linregress(x, y)
log = stats.linregress(np.log(x), y)
sp = stats.spearmanr(x, y)

out = {
    'inputs': {'ranks': RANKS, 'delta_E_means': DE, 'source': 'E2_results.json (Phase table means); |dE| used to avoid the sign crossing'},
    'linear_fit': {'slope': round(float(lin.slope), 1), 'intercept': round(float(lin.intercept), 1),
                   'R2': round(float(lin.rvalue ** 2), 4), 'p': float(lin.pvalue), 'n': len(x)},
    'log_rank_fit': {'slope': round(float(log.slope), 1), 'R2': round(float(log.rvalue ** 2), 4),
                     'p': float(log.pvalue)},
    'spearman': {'rho': round(float(sp.statistic), 3), 'p': round(float(sp.pvalue), 4)},
    'note': 'supersedes outputs/llava_rank_linearity.json (that file reported slope 175.4 / R2 0.9608 / spearman 0.991 with undocumented inputs; 0.991 is also arithmetically impossible for n=7 without ties)',
}
json.dump(out, open('outputs/llava_rank_linearity_v2.json', 'w', encoding='utf-8'), indent=1)
print(json.dumps(out, indent=1))
