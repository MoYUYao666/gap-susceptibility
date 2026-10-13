"""(A9) Select the instantiation of the alignment energy E by its "predictive power for the measured ΔE" (operational closure of limitations 7 / 13).

Rationale: the paper's allocation law requires E to be given first; different E instantiations
reorder |Γ_k| (the pairwise family vs the information-theoretic family are on CLIP completely
opposite; the 4 decoder-side pooling variants flip the LLM layer order). Rather than leaving
"which E is correct" as an open question, this script uses the **existing measured ΔE** for a hold-out

Candidate E instantiations (all from local archived JSON):
  i1 adapter subspace block coupling (outputs/llava_granularity_bootstrap_v2.json :: llm_* of block_mean_gdot)
  i2 full-parameter layer profile aggregated into three blocks (llm_layer_gdot_full of the same file)
  i3..i6 four decoder pooling variants (outputs/llava_e_pooling_ablation_v2.json :: gamma[*])
Risk functionals:
  P1 Σ_k |Γ_k| r_k        (Corollary 2 linear risk objective)
  P2 Σ_k |Γ_k| (r_k - r_max)^2  (capacity dispersion x coupling)
  P3 max_k |Γ_k| r_k      (worst-block damage)
Measured policies (LLaVA, reference protocol, average over multiple seeds):
  uniform 4/4/4, exp 9/1/6, greedy 16/1/1, expnorm 9/2/5, deepavoid 9/6/1
Output: outputs/e_family_selection.json
"""
import glob
import json
import os
import re

import numpy as np
from scipy import stats

EXP = 'paper3/scripts/outputs/experiments'
OUT = 'outputs/e_family_selection.json'
BLOCKS = ['llm_shallow', 'llm_mid', 'llm_deep']
POLICY_RANKS = {
    'uniform': {'llm_shallow': 4, 'llm_mid': 4, 'llm_deep': 4},
    'exp': {'llm_shallow': 9, 'llm_mid': 1, 'llm_deep': 6},
    'greedy': {'llm_shallow': 16, 'llm_mid': 1, 'llm_deep': 1},
    'expnorm': {'llm_shallow': 11, 'llm_mid': 1, 'llm_deep': 4},
    'deepavoid': {'llm_shallow': 4, 'llm_mid': 6, 'llm_deep': 1},
}


def measured_policies():
    """Read the ΔE of each policy from the experiment directory (averaged over multiple seeds)."""
    got = {k: [] for k in POLICY_RANKS}
    for p in glob.glob(os.path.join(EXP, 'verify_r*.json')):
        base = os.path.basename(p)
        d = json.load(open(p, encoding='utf-8'))
        if d.get('partial') or '_partial' in base:
            continue  # intermediate state written per-epoch in the cloud, not a complete run
        # old JSON has no block_config field → infer from the filename tag _bc<name>
        cfg = d.get('block_config')
        if not cfg:
            mm = re.search(r'_bc([a-z]+)', base)
            cfg = mm.group(1) if mm else 'uniform'
        if cfg not in POLICY_RANKS:
            continue
        if cfg == 'uniform' and int(d.get('rank', 0)) != 4:
            continue  # only take the uniform policy baseline (all layers r=4), excluding rank-sweep runs
        if d.get('target_proj') or '_proj' in base:
            continue  # projector probing is reported separately, not a block reallocation policy
        # reference protocol only: 3 epochs, fp16, adamw, lr 5e-5, no warmup/imgs/lang/mask/alpha etc.
        if (d.get('epochs') != 3 or d.get('compute_dtype') != 'float16' or d.get('opt') != 'adamw'
                or abs(d.get('lr', 5e-5) - 5e-5) > 1e-12 or d.get('warmup')
                or d.get('grad_mask', 'none') != 'none' or d.get('attn_targets', 'qkvo') != 'qkvo'
                or d.get('proj_rank') is not None or d.get('batch_size', 1) != 1
                or d.get('lang_only') or d.get('data_offset', 0) != 0):
            continue
        de = d.get('delta_E')
        if de is None or (isinstance(de, float) and np.isnan(de)):
            continue
        got[cfg].append((int(d.get('seed', 0)), float(de), base))
    return {k: {'seeds': [s for s, _, _ in v], 'mean': float(np.mean([d for _, d, _ in v])),
                'values': [d for _, d, _ in v], 'files': [f for _, _, f in v]}
            for k, v in got.items() if v}


def instantiation_gammas():
    inst = {}
    g = json.load(open('outputs/llava_granularity_bootstrap_v2.json', encoding='utf-8'))
    bm = g.get('block_mean_gdot', {})
    if all(b in bm for b in BLOCKS):
        inst['adapter_subspace_blocks'] = {b: abs(bm[b]) for b in BLOCKS}
    lay = g.get('llm_layer_gdot_full', {})
    if lay:
        agg = {}
        for b, rng in (('llm_shallow', range(0, 8)), ('llm_mid', range(8, 24)), ('llm_deep', range(24, 32))):
            vals = [abs(lay[str(i)]) for i in rng if str(i) in lay] or [abs(lay[i]) for i in rng if i in lay]
            agg[b] = float(np.mean(vals)) if vals else None
        if all(agg.get(b) is not None for b in BLOCKS):
            inst['fullparam_layer_profile'] = agg
    try:
        pool = json.load(open('outputs/llava_e_pooling_ablation_v2.json', encoding='utf-8'))
        for var, v in pool.get('gamma', {}).items():
            gm = v.get('gamma', {})
            if all(b in gm for b in BLOCKS):
                inst['pooling:' + var] = {b: abs(gm[b]) for b in BLOCKS}
    except FileNotFoundError:
        pass
    return inst


def predictors(gam, ranks):
    g = np.array([gam[b] for b in BLOCKS], dtype=float)
    r = np.array([ranks[b] for b in BLOCKS], dtype=float)
    return {'P1_linear': float((g * r).sum()),
            'P2_dispersion': float((g * (r - r.max()) ** 2).sum()),
            'P3_worstblock': float((g * r).max())}


def main():
    meas = measured_policies()
    inst = instantiation_gammas()
    rows = {}
    for name, gam in inst.items():
        preds = {p: predictors(gam, POLICY_RANKS[p]) for p in meas}
        rows[name] = {'gamma': {k: round(v, 3) for k, v in gam.items()}, 'pred': preds}
    # ranking correlation with the measured ΔE (policy level)
    pol = sorted(meas)
    y = np.array([meas[p]['mean'] for p in pol])
    res = {}
    for name, d in rows.items():
        res[name] = {}
        for pk in ('P1_linear', 'P2_dispersion', 'P3_worstblock'):
            x = np.array([d['pred'][p][pk] for p in pol])
            if len(x) > 2 and np.std(x) > 0:
                rho, pv = stats.spearmanr(x, y)
                pr, pp = stats.pearsonr(x, y)
                res[name][pk] = {'spearman': round(float(rho), 3), 'p': round(float(pv), 4),
                                 'pearson': round(float(pr), 3), 'pearson_p': round(float(pp), 4)}
            else:
                res[name][pk] = None
    # select the best instantiation (the one with the largest |Spearman|, expecting a positive correlation: the larger the predicted risk, the larger ΔE)
    best, best_rho = None, -2
    for name, d in res.items():
        for pk, v in d.items():
            if v and abs(v['spearman']) > best_rho:
                best, best_rho = (name, pk, v), abs(v['spearman'])
    json.dump({'measured_policies': meas, 'policies': pol,
               'instantiations': rows, 'correlations': res,
               'best_predictor': None if best is None else {'instantiation': best[0], 'predictor': best[1],
                                                            **best[2]},
               'note': 'A positive Spearman means the risk functional of this E instantiation has the same order as the measured ΔE (the stronger the predictive power, the more it should serve as the allocation E)'},
              open(OUT, 'w', encoding='utf-8'), indent=1)
    print('measured:', {k: round(v['mean'], 1) for k, v in meas.items()}, flush=True)
    for name, d in res.items():
        print('%-28s %s' % (name, {k: (v['spearman'] if v else None) for k, v in d.items()}), flush=True)
    print('best:', best, flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
