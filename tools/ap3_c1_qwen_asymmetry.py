"""C1 (Qwen2-VL-7B: asymmetric rank allocation between projector and LLM) analysis.

Data: cloud clean rerun 2026-09-13, autodl RTX 4080 SUPER (32760 MiB / torch 2.12.1+cu130).
4 seeds {42,123,456,999} × 3 arms, 3 epochs, reference protocol (rank=8, uniform block policy, qkvo off):
  ① projonly        : projector r=4, attn-targets=none (no LoRA on the LLM)
  ② projhi16_llmlo2 : projector r=16 + LLM r=2
  ③ projlo2_llmhi16 : projector r=2  + LLM r=16

⚠️ Protocol caveat (must go into the paper/limitations): the Qwen script's "blank image" is actually an `np.random.randint` noise image,
seeded by seed → **E0 varies with seed** (27008–46592, a 72% span). Therefore:
  * comparisons between arms (within the same seed) are clean: all three arms share the same image and the same E0;
  * cross-seed absolute ΔE cannot be averaged directly — also report the normalized ΔE/E0 (%), and treat "per-seed arm ordering" as the primary evidence;
  * the LLaVA script uses an all-black image (E0 constant 3921/3926), so the two architectures differ in protocol on this point.

Output: outputs/c1_qwen_asymmetry.json
"""
import glob
import json
import math
import os
from statistics import mean, pstdev

OUT = 'outputs/c1_qwen_asymmetry.json'
EXP = 'paper3/scripts/outputs/experiments'
SEEDS = (42, 123, 456, 999)
ARMS = ('tnone_pr4_projonly', 'pr16_lr2_projhi16_llmlo2', 'pr2_lr16_projlo2_llmhi16')
LABEL = {
    'tnone_pr4_projonly': 'projector r=4 only (LLM frozen)',
    'pr16_lr2_projhi16_llmlo2': 'projector r=16 + LLM r=2',
    'pr2_lr16_projlo2_llmhi16': 'projector r=2 + LLM r=16',
}


def load(seed, arm):
    p = os.path.join(EXP, f'qwen_cf_uniform_rank8_seed{seed}_{arm}.json')
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding='utf-8'))


def sign_test_p(k, n):
    """Two-sided sign test p (k successes / n trials)."""
    if n == 0:
        return float('nan')
    from math import comb
    tail = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def block_baseline_block():
    """Block-policy baseline of the current vintage (_v2) vs the old archive: the E0 fingerprint decides comparability."""
    print()
    print('===== Block-policy baseline: current vintage (_v2) vs old archive =====')
    out = {'v2': {}, 'archive': {}}
    for s in (42, 123, 456):
        row = {}
        for bc in ('uniform', 'theory', 'violation'):
            p = os.path.join(EXP, f'qwen_cf_{bc}_rank8_seed{s}_v2.json')
            if not os.path.exists(p):
                continue
            d = json.load(open(p, encoding='utf-8'))
            row[bc] = {'E0': d['E'][0], 'delta_E': d['delta_E'], 'E': d['E']}
        if row:
            out['v2'][s] = row
            e0 = next(iter(row.values()))['E0']
            print(f'  seed {s}: E0={e0:.0f} | ' + '  '.join(
                f'{bc} {row[bc]["delta_E"]:+.0f}' for bc in row))
    # Old archive (if present)
    for s in (42, 123, 456):
        row = {}
        for bc in ('uniform', 'theory', 'violation'):
            p = os.path.join(EXP, f'qwen_cf_{bc}_rank8_seed{s}.json')
            if os.path.exists(p):
                d = json.load(open(p, encoding='utf-8'))
                row[bc] = {'E0': d['E'][0], 'delta_E': d['delta_E']}
        if row:
            out['archive'][s] = row
            e0 = next(iter(row.values()))['E0']
            print(f'  [old archive] seed {s}: E0={e0:.0f} | ' + '  '.join(
                f'{bc} {row[bc]["delta_E"]:+.0f}' for bc in row))

    # E0 fingerprint check: are v2 and the C1 arms the same vintage?
    print()
    c1_e0 = {}
    for s in SEEDS:
        p = os.path.join(EXP, f'qwen_cf_uniform_rank8_seed{s}_tnone_pr4_projonly.json')
        if os.path.exists(p):
            c1_e0[s] = json.load(open(p, encoding='utf-8'))['E'][0]
    same = all(out['v2'][s][next(iter(out['v2'][s]))]['E0'] == c1_e0.get(s)
               for s in out['v2'] if s in c1_e0)
    print(f'  E0 fingerprint: v2 baseline matches the C1 arms = {same}'
          f' (v2 {[out["v2"][s][next(iter(out["v2"][s]))]["E0"] for s in sorted(out["v2"])]} '
          f'vs C1 {[c1_e0[s] for s in sorted(c1_e0)]})')
    if out['archive']:
        arch_e0 = [out['archive'][s][next(iter(out['archive'][s]))]['E0'] for s in sorted(out['archive'])]
        print(f'  old archive E0 = {arch_e0} → different vintage from the current one → the two groups must not be tabulated together')

    # Block-policy effect vs rank-allocation effect (paired by seed)
    print()
    print('  ---- Paired by seed: block-policy arms vs rank-allocation arms ----')
    for s in sorted(out['v2']):
        if s not in c1_e0:
            continue
        row = out['v2'][s]
        proj = json.load(open(os.path.join(EXP, f'qwen_cf_uniform_rank8_seed{s}_tnone_pr4_projonly.json'),
                              encoding='utf-8'))['delta_E']
        print(f'  seed {s}: block policy {min(row[b]["delta_E"] for b in row):+.0f}…{max(row[b]["delta_E"] for b in row):+.0f}'
              f' (span {max(row[b]["delta_E"] for b in row) - min(row[b]["delta_E"] for b in row):.0f})'
              f' | projector only {proj:+.0f} → diff {proj - row["uniform"]["delta_E"]:+.0f}')
    return out


def main():
    rows = []
    missing = []
    for s in SEEDS:
        d0 = load(s, 'tnone_pr4_projonly')
        if d0 is None:
            missing.append(s)
            continue
        e0 = d0['E'][0]
        for arm in ARMS:
            d = load(s, arm)
            if d is None:
                continue
            de = d['delta_E']
            rows.append({
                'seed': s, 'arm': arm, 'label': LABEL[arm],
                'trainable_params': d.get('trainable_params'),
                'proj_rank': d.get('proj_rank'), 'llm_rank': d.get('llm_rank'),
                'E0': e0, 'E': d['E'], 'delta_E': de,
                'delta_E_pct': (de / e0 * 100.0) if e0 else float('nan'),
            })
    if missing:
        print('missing files, seeds:', missing)

    print(f'included {len(rows)} rows ({len({r["seed"] for r in rows})} seeds × 3 arms)\n')
    print('===== Per-seed detail =====')
    print(f'{"seed":>5} {"arm":<28} {"trainable":>10} {"E0":>8} {"ΔE":>9} {"ΔE/E0":>9}  E trajectory')
    for s in SEEDS:
        sub = [r for r in rows if r['seed'] == s]
        if not sub:
            continue
        for r in sub:
            traj = ' -> '.join(f'{v:.0f}' for v in r['E'])
            print(f'{r["seed"]:>5} {r["label"]:<28} {str(r["trainable_params"]):>10} {r["E0"]:>8.0f} '
                  f'{r["delta_E"]:>+9.0f} {r["delta_E_pct"]:>+8.2f}%  {traj}')
        print()

    print('===== Per-arm summary =====')
    print(f'{"arm":<28} {"n":>2} {"ΔE mean±sd":>22} {"ΔE/E0 mean±sd":>20} {"n positive":>9}')
    summ = {}
    for arm in ARMS:
        sub = [r for r in rows if r['arm'] == arm]
        de = [r['delta_E'] for r in sub]
        pc = [r['delta_E_pct'] for r in sub]
        pos = sum(1 for v in de if v > 0)
        summ[arm] = {'n': len(sub), 'delta_E_mean': mean(de), 'delta_E_sd': pstdev(de),
                     'pct_mean': mean(pc), 'pct_sd': pstdev(pc), 'n_positive': pos,
                     'delta_E': de, 'pct': pc}
        print(f'{LABEL[arm]:<28} {len(sub):>2} {mean(de):>+12.0f} ± {pstdev(de):<8.0f} '
              f'{mean(pc):>+11.2f}% ± {pstdev(pc):<6.2f}% {pos:>6}/{len(sub)}')

    print()
    print('===== Main test: is the arm ordering consistent across seeds =====')
    order_ok = 0
    pair_ok = {('tnone_pr4_projonly', 'pr16_lr2_projhi16_llmlo2'): 0,
               ('tnone_pr4_projonly', 'pr2_lr16_projlo2_llmhi16'): 0,
               ('pr2_lr16_projlo2_llmhi16', 'pr16_lr2_projhi16_llmlo2'): 0}
    pair_diff = {k: [] for k in pair_ok}
    for s in SEEDS:
        sub = {r['arm']: r for r in rows if r['seed'] == s}
        if len(sub) < 3:
            continue
        vals = {a: sub[a]['delta_E'] for a in ARMS}
        if vals['tnone_pr4_projonly'] > vals['pr2_lr16_projlo2_llmhi16'] > vals['pr16_lr2_projhi16_llmlo2']:
            order_ok += 1
        for (a, b) in pair_ok:
            if vals[a] > vals[b]:
                pair_ok[(a, b)] += 1
            pair_diff[(a, b)].append(vals[a] - vals[b])
    n_seeds = len({r['seed'] for r in rows})
    print(f'seeds with order projector-only > projector r2+LLM r16 > projector r16+LLM r2: {order_ok}/{n_seeds}'
          f'  (if fully random, the probability of exactly this order = 1/6 per seed → probability of observing {order_ok}/{n_seeds} = {(1/6) ** order_ok:.4f})')
    for (a, b), k in pair_ok.items():
        diffs = pair_diff[(a, b)]
        print(f'  {LABEL[a][:18]:<18} > {LABEL[b][:18]:<18}: {k}/{len(diffs)} seeds  '
              f'mean diff {mean(diffs):+.0f} (all diffs same sign: {"yes" if k in (0, len(diffs)) else "no"})')

    print()
    print('===== Against the archived Qwen block-policy baseline =====')
    arch = sorted(glob.glob(os.path.join(EXP, 'qwen_cf_*_rank8_seed42.json')))
    arch = [p for p in arch if not any(a in os.path.basename(p) for a in ARMS)]
    for p in arch:
        d = json.load(open(p, encoding='utf-8'))
        print(f'  {os.path.basename(p):<52} E0={d["E"][0]:.0f} ΔE={d["delta_E"]:+.0f}')

    blocks = block_baseline_block()

    json.dump({
        'source': 'cloud clean rerun 2026-09-13, autodl RTX 4080 SUPER 32760MiB / torch 2.12.1+cu130',
        'protocol_note': ('The Qwen script uses an np.random.randint noise image, seeded by seed, so E0 varies with seed; '
                          'arm comparisons are clean but cross-seed absolute values cannot be averaged, so ΔE/E0 is also '
                          'reported. The LLaVA script uses a np.zeros black image (constant E0): the protocols differ here.'),
        'rows': rows,
        'summary': summ,
        'block_baseline': blocks,
        'per_seed_order_consistent': order_ok,
        'n_seeds': n_seeds,
        'pairwise': {f'{a}|{b}': {'n_a_gt_b': k, 'n': len(pair_diff[(a, b)]),
                                  'mean_diff': mean(pair_diff[(a, b)]) if pair_diff[(a, b)] else None}
                     for (a, b), k in pair_ok.items()},
    }, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'\nDONE -> {OUT}')


if __name__ == '__main__':
    main()
