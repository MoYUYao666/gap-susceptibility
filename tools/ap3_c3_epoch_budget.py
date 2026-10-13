"""C3 (protocol unification: 10-epoch budget) analysis.

Data source: cloud clean rerun on 2026-09-13, autodl RTX 4080 SUPER (32760 MiB, driver 580.142,
torch 2.12.1+cu130, transformers 5.16.1). 15 cells = rank {4,5,6} × seed {42,123,456,789,1024},
batch=1 (same batch size as the paper's reference protocol), 10 epochs per cell.

Output: outputs/c3_epoch_budget.json
  * per cell: at which index of E the first NaN value appears (= after which epoch it blew up), the minimum of E and its epoch,
    exponential growth-rate fit of the divergence segment
  * per rank: mean±sd of the above quantities
  * monotonicity between rank and "number of epochs to collapse" (Spearman + permutation test)

Conventions:
  - read cloud files only. The r=4,s=42 cell has the same name locally and in the cloud; the cloud version carries the `_cloud` suffix, which is preferred here.
  - the absolute level of E differs across devices (cloud E0=3926, local 8GB machine E0=3921, +0.13%), so this script only uses
    device-invariant quantities such as "collapse epoch / relative growth" and never mixes ΔE across devices; the epoch-3 prefix is only used for a same-sign check.
"""
import json
import math
import os
import random
from statistics import mean, pstdev

OUT = 'outputs/c3_epoch_budget.json'
EXP = 'paper3/scripts/outputs/experiments'
RANKS = (4, 5, 6)
SEEDS = (42, 123, 456, 789, 1024)
# E0 of the cloud clean rerun (used for the provenance self-check: the corresponding value on the local 8GB machine is 3921)
CLOUD_E0_EXPECTED = 3926.0
E0_TOL = 2.0


def resolve(rank, seed, tag='_lr5e-05_nw_float1_adamw_e10_bcuniform'):
    """Cloud first: on a name conflict the cloud file carries the _cloud suffix."""
    base = f'verify_r{rank}_s{seed}{tag}'
    for suffix in ('_cloud.json', '.json'):
        p = os.path.join(EXP, base + suffix)
        if os.path.exists(p):
            return p, ('_cloud' if suffix == '_cloud.json' else 'canonical')
    return None, None


def isnan(v):
    return isinstance(v, float) and math.isnan(v)


def growth_rate(E):
    """Least-squares slope of log(E) ~ epoch over the divergence segment (all valid values after the minimum)."""
    valid = [(i, v) for i, v in enumerate(E) if not isnan(v) and v > 0]
    if len(valid) < 3:
        return None, None
    i_min = min(valid, key=lambda t: t[1])[0]
    seg = [(i, v) for i, v in valid if i >= i_min]
    if len(seg) < 3:
        return None, None
    xs = [i for i, _ in seg]
    ys = [math.log(v) for _, v in seg]
    n = len(xs)
    mx, my = mean(xs), mean(ys)
    den = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den
    yhat = [my + slope * (x - mx) for x in xs]
    ss_res = sum((y - yh) ** 2 for y, yh in zip(ys, yhat))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    return slope, r2


def spearman(a, b):
    """Spearman correlation with average ranks for ties."""
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                rk[order[k]] = avg
            i = j + 1
        return rk
    ra, rb = ranks(a), ranks(b)
    ma, mb = mean(ra), mean(rb)
    num = sum((p - ma) * (q - mb) for p, q in zip(ra, rb))
    den = math.sqrt(sum((p - ma) ** 2 for p in ra) * sum((q - mb) ** 2 for q in rb))
    return num / den if den else float('nan')


def main():
    cells = []
    prov_notes = []
    for r in RANKS:
        for s in SEEDS:
            p, how = resolve(r, s)
            if p is None:
                prov_notes.append(f'MISSING r={r} s={s}')
                continue
            d = json.load(open(p, encoding='utf-8'))
            E = d['E']
            e0 = E[0]
            if abs(e0 - CLOUD_E0_EXPECTED) > E0_TOL:
                prov_notes.append(f'{os.path.basename(p)} has E0={e0} deviating from the cloud value {CLOUD_E0_EXPECTED} → not included')
                continue
            nan_idx = next((i for i, v in enumerate(E) if isnan(v)), None)
            valid = [(i, v) for i, v in enumerate(E) if not isnan(v)]
            i_min, e_min = min(valid, key=lambda t: t[1])
            slope, r2 = growth_rate(E)
            cells.append({
                'rank': r, 'seed': s, 'file': os.path.basename(p), 'resolved_as': how,
                'E': E, 'E0': e0,
                'first_nan_index': nan_idx,                 # index of E; NaN appears after the nan_idx-th epoch
                'epochs_completed_valid': (nan_idx - 1) if nan_idx else len(E) - 1,
                'epochs_to_blowup': nan_idx,                # how many epochs it can still run from E0 before collapsing
                'E_min': e_min, 'E_min_epoch': i_min,
                'E_last_valid': valid[-1][1], 'E_last_valid_epoch': valid[-1][0],
                'growth_slope': slope, 'growth_r2': r2,
            })

    print(f'included {len(cells)} cells (provenance self-check: E0={CLOUD_E0_EXPECTED}±{E0_TOL})')
    for note in prov_notes:
        print('  note:', note)

    print()
    for r in RANKS:
        sub = [c for c in cells if c['rank'] == r]
        print(f'===== rank {r} (n={len(sub)}) =====')
        for c in sub:
            traj = ' -> '.join('nan' if isnan(v) else f'{v:.0f}' for v in c['E'])
            print(f'  seed {c["seed"]:>4}: {traj}')
        nb = sorted(c['epochs_to_blowup'] for c in sub)
        sl = [c['growth_slope'] for c in sub if c['growth_slope'] is not None]
        print(f'  collapse moment (E index, larger = later): {nb}')
        print(f'  E minimum = {mean(c["E_min"] for c in sub):.1f} @ epoch '
              f'{mean(c["E_min_epoch"] for c in sub):.2f} (the optimum is always extremely early)')
        print(f'  divergence-segment log(E) slope = {mean(sl):.4f} ± {pstdev(sl):.4f} (n={len(sl)})')
        print()

    print('===== main conclusion =====')
    per_rank = {}
    print(f'{"rank":>4} {"n":>3} {"collapse epoch(mean±sd)":>24} {"divergence slope(mean±sd)":>24} {"E_min(mean)":>12}')
    for r in RANKS:
        sub = [c for c in cells if c['rank'] == r]
        nb = [c['epochs_to_blowup'] for c in sub]
        sl = [c['growth_slope'] for c in sub if c['growth_slope'] is not None]
        emin = [c['E_min'] for c in sub]
        per_rank[r] = {'n': len(sub), 'blowup_mean': mean(nb), 'blowup_sd': pstdev(nb),
                       'blowup_values': sorted(nb), 'slope_mean': mean(sl), 'slope_sd': pstdev(sl),
                       'E_min_mean': mean(emin),
                       'E_min_epoch_mean': mean([c['E_min_epoch'] for c in sub])}
        print(f'{r:>4} {len(sub):>3} {mean(nb):>13.2f} ± {pstdev(nb):<8.2f} '
              f'{mean(sl):>13.4f} ± {pstdev(sl):<7.4f} {mean(emin):>12.1f}')

    xs = [c['rank'] for c in cells]
    ys = [c['epochs_to_blowup'] for c in cells]
    rho = spearman(xs, ys)
    rnd = random.Random(20260913)
    perm = list(ys)
    ge = 0
    N = 200000
    for _ in range(N):
        rnd.shuffle(perm)
        if abs(spearman(xs, perm)) >= abs(rho) - 1e-12:
            ge += 1
    p_perm = (ge + 1) / (N + 1)
    print()
    print(f'rank vs "collapse moment": Spearman rho = {rho:.4f}, permutation test p = {p_perm:.2e} ({N} reshuffles, two-sided)')
    print('  group details: ' + '; '.join(
        f'r{r}: ' + ','.join(str(c['epochs_to_blowup']) for c in cells if c['rank'] == r) for r in RANKS))
    print(f'all {len(cells)} cells diverge to NaN within 10 epochs: '
          f'{"yes" if all(c["first_nan_index"] is not None for c in cells) else "no"}')

    print()
    print('===== bridge: epoch-3 prefix of the cloud 10-epoch trajectory vs the local 3-epoch reference =====')
    local_ref = {5: -34.7, 6: 69.9}
    e3 = {}
    for r in RANKS:
        pre = [c['E'][3] - c['E'][0] for c in cells if c['rank'] == r]
        e3[r] = pre
        s = f'  r={r}: cloud epoch-3 prefix ΔE = {mean(pre):+.1f} ± {pstdev(pre):.1f} (n={len(pre)})'
        if r in local_ref:
            s += (f'; local ten-seed 3-epoch reference = {local_ref[r]:+.1f} → '
                  + ('same sign OK' if (mean(pre) > 0) == (local_ref[r] > 0) else 'opposite sign !!'))
        print(s)

    json.dump({
        'source': 'cloud clean rerun 2026-09-13, autodl RTX 4080 SUPER 32760MiB / torch 2.12.1+cu130',
        'protocol': {'epochs': 10, 'batch_size': 1, 'num_samples': 20},
        'provenance_notes': prov_notes,
        'cells': cells,
        'per_rank': per_rank,
        'trend': {'spearman_rho': rho, 'p_permutation': p_perm, 'n_permutations': N},
        'epoch3_prefix': {str(r): e3[r] for r in RANKS},
    }, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'\nDONE -> {OUT}')


if __name__ == '__main__':
    main()
