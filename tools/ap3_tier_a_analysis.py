"""(Tier A summary analysis) Aggregate the experimental results produced by the battery into paper-ready JSON artifacts in one pass.

Sections:
  A5  policy_multiseed : ΔE of 5 allocation policies × multiple seeds, mean/std, Welch test against uniform, budget and trainable parameter count
  A2  gradmask         : ΔE of image/text pathway gradient masking vs reference vs language-only, plus gradient-norm evidence (whether masking really takes effect)
  A6  projector_asym   : ΔE and trainable parameters of projector-only / high-projector-low-LLM / low-projector-high-LLM
  A7  alpha_sweep      : ΔE of LoRA alpha=32 vs default (2r) at r5/r6
  A10 grad_norm_vs_rank: mean ‖g_vision‖ per rank under the reference protocol (measuring gradient saturation) + masking-effectiveness check
Output: outputs/tier_a_analysis.json (re-runnable; whatever data has landed is what gets summarized)
"""
import glob
import json
import math
import os
import re
from collections import defaultdict

import numpy as np
from scipy import stats

EXP = 'paper3/scripts/outputs/experiments'
OUT = 'outputs/tier_a_analysis.json'
POLICIES = ['uniformv1', 'exp', 'greedy', 'expnorm', 'deepavoid', 'uniform']
POLICY_RANKS = {'uniformv1': [4, 4, 4], 'uniform': [4, 4, 4], 'exp': [9, 1, 6], 'greedy': [16, 1, 1],
                'expnorm': [11, 1, 4], 'deepavoid': [4, 6, 1]}


def load():
    recs = []
    for p in glob.glob(os.path.join(EXP, 'verify_r*.json')):
        base = os.path.basename(p)
        try:
            d = json.load(open(p, encoding='utf-8'))
        except Exception:
            continue
        de = d.get('delta_E')
        cfg = d.get('block_config')
        if not cfg:
            mm = re.search(r'_bc([a-z]+)', base)
            cfg = mm.group(1) if mm else 'uniform'
        gm = d.get('grad_mask')
        if not gm:
            mm = re.search(r'_gm(image|text)', base)
            gm = mm.group(1) if mm else 'none'
        # alpha: newer JSON writes the "effective alpha" (=2r or 16), which cannot be used to tell whether an alpha ablation was run
        # → only trust the explicit tag _a<digits> in the filename (old runs lack the field, new runs always go by the tag)
        mm = re.search(r'_a(\d+)', base)
        alpha = float(mm.group(1)) if mm else None
        targets = d.get('attn_targets')
        if not targets:
            mm = re.search(r'_t(qkvo|q|qv|qo|none)', base)
            targets = mm.group(1) if mm else 'qkvo'
        pr = d.get('proj_rank')
        if pr is None:
            mm = re.search(r'_pr(\d+)', base)
            pr = int(mm.group(1)) if mm else None
        lang = bool(d.get('lang_only')) or '_lang' in base
        proj = bool(d.get('target_proj')) or '_proj' in base
        recs.append({'file': base, 'rank': int(d.get('rank', 0)), 'seed': int(d.get('seed', 0)),
                     'epochs': int(d.get('epochs', 0)), 'cfg': cfg, 'grad_mask': gm, 'alpha': alpha,
                     'targets': targets, 'proj_rank': pr, 'lang_only': lang, 'target_proj': proj,
                     'batch_size': int(d.get('batch_size', 1)),
                     'lr': float(d.get('lr', 5e-5)), 'warmup': bool(d.get('warmup', False)),
                     'dtype': d.get('compute_dtype', 'float16'), 'opt': d.get('opt', 'adamw'),
                     'images_dir': bool(d.get('images_dir')) or '_imgs' in base,
                     'data_path': bool(d.get('data_path')) or '_cap' in base,
                     'is_variant': bool(re.search(r'_(tf457|e10)\b', base)),
                     # the per-epoch *_partial.json written in the cloud (to avoid losing a whole round to OOM) is not a complete run and never enters the statistics
                     'partial': bool(d.get('partial')) or '_partial' in base,
                     'delta_E': None if de is None else float(de),
                     'E': d.get('E'), 'grad_norms': d.get('grad_norms'), 'trainable': d.get('trainable')})
    return recs


def ref(recs):
    """Strict reference-protocol records (3 epochs, fp16, adamw, lr 5e-5, no warmup, batch=1, no intervention tag at all)."""
    return [r for r in recs if r['epochs'] == 3 and r['grad_mask'] == 'none' and r['alpha'] is None
            and r['targets'] == 'qkvo' and r['proj_rank'] is None and not r['lang_only']
            and not r['target_proj'] and r['batch_size'] == 1 and abs(r['lr'] - 5e-5) < 1e-12
            and not r['warmup'] and r['dtype'] == 'float16' and r['opt'] == 'adamw'
            and not r['images_dir'] and not r['data_path'] and not r['is_variant']
            and not r['partial']]


def ok(x):
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def sec_policies(recs):
    # baseline: uniformv1 = all LLM layers r4 + vision r1 (same convention as vision r1 of each policy)
    base = [r for r in ref(recs) if r['cfg'] == 'uniformv1' and r['rank'] == 4 and ok(r['delta_E'])]
    base_label = 'uniformv1'
    if not base:  # fallback: if uniformv1 has not finished running, use uniform (vision r4) as the reference and label it as such
        base = [r for r in ref(recs) if r['cfg'] == 'uniform' and r['rank'] == 4 and ok(r['delta_E'])]
        base_label = 'uniform(vision r4)'
    out = {'baseline': base_label,
           'baseline_stats': {'n': len(base), 'seeds': [r['seed'] for r in base],
                              'mean': round(float(np.mean([r['delta_E'] for r in base])), 2) if base else None,
                              'values': [round(r['delta_E'], 2) for r in base]},
           'policies': {}}
    b = [r['delta_E'] for r in base]
    for cfg in POLICIES:
        rs = [r for r in ref(recs) if r['cfg'] == cfg and ok(r['delta_E'])]
        if cfg in ('uniform', 'uniformv1'):
            rs = [r for r in rs if r['rank'] == 4]
        if not rs:
            continue
        vals = [r['delta_E'] for r in rs]
        ent = {'n': len(vals), 'seeds': [r['seed'] for r in rs], 'values': [round(v, 2) for v in vals],
               'mean': round(float(np.mean(vals)), 2),
               'std': round(float(np.std(vals, ddof=1)), 2) if len(vals) > 1 else None,
               'rank_vector': POLICY_RANKS[cfg],
               'budget_rank_layers': sum(POLICY_RANKS[cfg]) * 8 if cfg != 'uniform' else 4 * 32,
               'trainable': rs[0]['trainable']}
        if cfg != 'uniform' and len(vals) > 1 and len(b) > 1:
            t, p = stats.ttest_ind(vals, b, equal_var=False)
            ent['welch_vs_uniform'] = {'t': round(float(t), 3), 'p': round(float(p), 5)}
        out['policies'][cfg] = ent
    return out


def sec_gradmask(recs):
    refset = ref(recs)
    out = {}
    for rank in (5, 6):
        entry = {}
        for cond, sel in (('reference', lambda r: any(r['file'] == x['file'] for x in refset)),
                          ('gradmask_image', lambda r: r['grad_mask'] == 'image'),
                          ('gradmask_text', lambda r: r['grad_mask'] == 'text'),
                          ('loss_lang_only', lambda r: r['lang_only'])):
            rs = [r for r in recs if r['epochs'] == 3 and r['rank'] == rank and sel(r) and ok(r['delta_E'])]
            if rs:
                entry[cond] = {'n': len(rs), 'mean': round(float(np.mean([r['delta_E'] for r in rs])), 2),
                               'values': [round(r['delta_E'], 2) for r in rs],
                               'grad_norms_last': (rs[0]['grad_norms'] or [None])[-1]}
        # masking-effectiveness evidence: under image masking the vision-route gradient norm should be ≈ 0
        out[f'r{rank}'] = entry
    # whether the crossing still exists (within each condition, r6 mean - r5 mean)
    cross = {}
    for cond in ('reference', 'gradmask_image', 'gradmask_text', 'loss_lang_only'):
        v5 = out.get('r5', {}).get(cond, {}).get('mean')
        v6 = out.get('r6', {}).get(cond, {}).get('mean')
        if v5 is not None and v6 is not None:
            cross[cond] = {'r5': v5, 'r6': v6, 'delta': round(v6 - v5, 2), 'crossing': bool(v6 > v5)}
    out['crossing_by_condition'] = cross
    return out


def sec_projector(recs):
    out = {'uniform': None, 'variants': {}}
    u = [r for r in ref(recs) if r['cfg'] == 'uniform' and r['rank'] == 4 and ok(r['delta_E'])]
    if u:
        out['uniform'] = {'mean': round(float(np.mean([r['delta_E'] for r in u])), 2), 'n': len(u),
                          'trainable': u[0]['trainable']}
    for name, sel in (('proj_only_r4', lambda r: r['targets'] == 'none' and r['proj_rank'] == 4),
                      ('proj_hi16_llm_lo2', lambda r: r['proj_rank'] == 16 and r['rank'] == 2),
                      ('proj_lo2_llm_hi16', lambda r: r['proj_rank'] == 2 and r['rank'] == 16),
                      ('uniform_plus_proj_r4', lambda r: r['target_proj'] and r['rank'] == 4)):
        rs = [r for r in recs if r['epochs'] == 3 and sel(r) and ok(r['delta_E'])]
        if rs:
            out['variants'][name] = {'n': len(rs), 'mean': round(float(np.mean([r['delta_E'] for r in rs])), 2),
                                     'values': [round(r['delta_E'], 2) for r in rs],
                                     'trainable': rs[0]['trainable']}
    return out


def sec_alpha(recs):
    """A7 three-axis sensitivity: alpha / attention target modules / batch size, each at r5/r6 relative to the reference protocol."""
    out = {'axes': {}, 'reference_crossing': None}

    def one(tag, sel):
        ent = {}
        for rank in (5, 6):
            rs = [r for r in recs if r['epochs'] == 3 and r['rank'] == rank and sel(r) and ok(r['delta_E'])]
            ent[f'r{rank}'] = {'n': len(rs), 'mean': round(float(np.mean([r['delta_E'] for r in rs])), 2),
                               'values': [round(r['delta_E'], 2) for r in rs]} if rs else None
        v5 = (ent.get('r5') or {}).get('mean')
        v6 = (ent.get('r6') or {}).get('mean')
        if v5 is not None and v6 is not None:
            ent['crossing'] = {'delta_r6_minus_r5': round(v6 - v5, 2), 'crossing': bool(v6 > v5)}
        out['axes'][tag] = ent
        return ent

    # reference-protocol baseline (for comparison)
    refset = {(r['rank'], r['seed']): r for r in ref(recs)}
    refc = {}
    for rank in (5, 6):
        vals = [v['delta_E'] for (rk, s), v in refset.items() if rk == rank and ok(v['delta_E'])]
        refc[f'r{rank}'] = {'n': len(vals), 'mean': round(float(np.mean(vals)), 2)} if vals else None
    if refc.get('r5') and refc.get('r6'):
        out['reference_crossing'] = {'delta_r6_minus_r5': round(refc['r6']['mean'] - refc['r5']['mean'], 2),
                                     **refc}
    one('alpha_32', lambda r: r['alpha'] == 32 and r['targets'] == 'qkvo' and r['batch_size'] == 1)
    one('targets_q', lambda r: r['targets'] == 'q' and r['alpha'] is None and r['batch_size'] == 1)
    one('targets_qv', lambda r: r['targets'] == 'qv' and r['alpha'] is None and r['batch_size'] == 1)
    one('batch_4', lambda r: r['batch_size'] == 4 and r['alpha'] is None and r['targets'] == 'qkvo')
    out['reference'] = refc
    return out


def sec_gradnorm(recs):
    by_rank = defaultdict(list)
    for r in ref(recs):
        gn = r['grad_norms']
        if not gn:
            continue
        last = gn[-1]
        by_rank[r['rank']].append({'seed': r['seed'], 'vision': last.get('vision'), 'llm': last.get('llm'),
                                   'ratio_v_over_l': (last['vision'] / last['llm']
                                                      if last.get('llm') else None), 'delta_E': r['delta_E']})
    ranks = sorted(by_rank)
    summary = {str(k): {'n': len(by_rank[k]),
                        'vision_mean': float(np.mean([x['vision'] for x in by_rank[k]])) if by_rank[k] else None,
                        'llm_mean': float(np.mean([x['llm'] for x in by_rank[k]])) if by_rank[k] else None}
               for k in ranks}
    corr = None
    if len(ranks) > 2:
        rk = np.array(ranks, dtype=float)
        vm = np.array([summary[str(k)]['vision_mean'] for k in ranks], dtype=float)
        rho, p = stats.spearmanr(rk, vm)
        corr = {'spearman_rank_vs_vision_gradnorm': round(float(rho), 3), 'p': round(float(p), 4)}
    # masking-effectiveness check: under image masking the vision gradient should be ≈ 0
    masked = [r for r in recs if r['grad_mask'] == 'image' and r['grad_norms']]
    mask_check = [{'seed': r['seed'], 'rank': r['rank'],
                   'vision': (r['grad_norms'] or [{}])[-1].get('vision'),
                   'llm': (r['grad_norms'] or [{}])[-1].get('llm')} for r in masked]
    return {'per_rank': summary, 'correlation': corr, 'per_run': {str(k): by_rank[k] for k in ranks},
            'image_mask_check': mask_check}


def main():
    recs = load()
    res = {'n_records': len(recs), 'A5_policies': sec_policies(recs), 'A2_gradmask': sec_gradmask(recs),
           'A6_projector': sec_projector(recs), 'A7_alpha': sec_alpha(recs), 'A10_gradnorm': sec_gradnorm(recs)}
    json.dump(res, open(OUT, 'w', encoding='utf-8'), indent=1)
    print('records:', len(recs), flush=True)
    print('A5:', json.dumps({k: (v['mean'] if isinstance(v, dict) and 'mean' in v else v)
                             for k, v in res['A5_policies']['policies'].items()}), flush=True)
    print('A2 crossing:', json.dumps(res['A2_gradmask']['crossing_by_condition']), flush=True)
    print('A6:', json.dumps({k: (v['mean'] if v else None) for k, v in
                             [('uniform', res['A6_projector']['uniform'])] +
                             list(res['A6_projector']['variants'].items())}), flush=True)
    print('A7:', json.dumps(res['A7_alpha']), flush=True)
    print('A10:', json.dumps(res['A10_gradnorm']['per_rank']), flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
