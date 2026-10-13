"""L3 threshold calibration: sensitivity/specificity statistical test of the τ tripwire.
Aggregates (tau_meas, top1 retention) cells over the full matrix (domain × model × λ) — 5 domains:
domain matrix (imagenet5k/dtd/food101 × 4 models) + marine (4 models) + sonar (balanced/full × 3 models).
Outputs outputs/threshold_calibration.json: per-cell list + for each cutoff (0.5/0.6/0.7/0.8/0.9) the
sensitivity/specificity/precision (under the two baselines "healthy = retention ≥96%" and "≥83%"), bootstrap 95% CI.
"""
import json
import itertools
import numpy as np

CELLS = []  # (domain, model, lambda, tau, ret)

def add_rows(domain, model, sigma, top1_0, rows):
    for r in rows:
        lam = r['lambda']
        top1 = r.get('top1')
        tau = r.get('tau_meas')
        if top1 is None or tau is None or abs(lam) < 1e-9:
            continue
        CELLS.append(dict(domain=domain, model=model, sigma_m=sigma,
                          lam=lam, tau=tau, ret=top1 / top1_0))

# domain matrix (frozen models, data files)
DM = json.load(open('outputs/domain_matrix.json', encoding='utf-8'))
for dom in ['imagenet5k', 'dtd', 'food101']:
    for mk, m in DM[dom].items():
        add_rows(dom, mk, m['sigma_m'], m['top1_0'], m['rows'])

# marine (fish-67, 4 model families) — ocean_gap_surgery.json is a flat row list {model, side, lam, CG, top1, tau}
GS = json.load(open('outputs/ocean_gap_surgery.json', encoding='utf-8'))
base = {r['model']: r['top1'] for r in GS if r['side'] == 'image' and abs(r['lam']) < 1e-9}
for r in GS:
    if r['side'] != 'image' or abs(r['lam']) < 1e-9:
        continue
    CELLS.append(dict(domain='marine-67', model=r['model'], sigma_m=None,
                      lam=r['lam'], tau=r['tau'], ret=r['top1'] / base[r['model']]))

# sonar (balanced 650 / full 2617, frozen + fine-tuned)
for proto, cols in [('sonar-balanced', ['clip_frozen', 'sonar_ft', 'clip_flickrft']),
                    ('sonar-full', ['clip_frozen', 'sonar_ft_full', 'clip_flickrft'])]:
    P = json.load(open(f'outputs/sonar_protocol{"_full" if "full" in proto else ""}.json',
                       encoding='utf-8'))
    for mk in cols:
        if mk not in P:
            continue
        add_rows(proto, mk, P[mk]['sigma_m'], P[mk]['top1_0'], P[mk]['rows'])

# sonar frozen/fine-tuned already present; marine 2×2 discrimination (clip family among the 4 models) already in ocean_gap_surgery? skip duplicates.

X = np.array([c['tau'] for c in CELLS])
R = np.array([c['ret'] for c in CELLS])
N = len(CELLS)

def stats(cut, thr):
    # healthy = R >= thr; tripwire = X >= cut
    healthy = R >= thr
    flagged = X >= cut
    tp = np.mean(flagged & healthy)
    fn = np.mean((~flagged) & healthy)
    fp = np.mean(flagged & ~healthy)
    tn = np.mean((~flagged) & ~healthy)
    sens = tp / max(tp + fn, 1e-12)
    spec = tn / max(tn + fp, 1e-12)
    prec = tp / max(tp + fp, 1e-12)
    return dict(sensitivity=round(float(sens), 3), specificity=round(float(spec), 3),
                precision=round(float(prec), 3))

rng = np.random.default_rng(42)
def boot(cut, thr, n=2000):
    idx = rng.integers(0, N, (n, N))
    Xb = X[idx]; Rb = R[idx]
    hb = Rb >= thr; fb = Xb >= cut
    tp = (fb & hb).sum(1); fn = ((~fb) & hb).sum(1)
    fp = (fb & ~hb).sum(1); tn = ((~fb) & ~hb).sum(1)
    sn = tp / (tp + fn + 1e-12)
    sp = tn / (tn + fp + 1e-12)
    return dict(sens_lo=float(np.percentile(sn, 2.5)), sens_hi=float(np.percentile(sn, 97.5)),
                spec_lo=float(np.percentile(sp, 2.5)), spec_hi=float(np.percentile(sp, 97.5)))

OUT = dict(n_points=N, cells=CELLS, cutoffs={})
for thr, tname in [(0.96, 'ret_ge_0.96'), (0.83, 'ret_ge_0.83')]:
    row = {}
    for cut in [0.5, 0.6, 0.7, 0.8, 0.9]:
        st = stats(cut, thr)
        b = boot(cut, thr)
        row[str(cut)] = {**st, **{k: round(v, 3) for k, v in b.items()}}
    OUT['cutoffs'][tname] = row

json.dump(OUT, open('outputs/threshold_calibration.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f'n_points={N}')
for tname, row in OUT['cutoffs'].items():
    print(tname)
    for cut, st in row.items():
        print(f"  cut={cut}: sens={st['sensitivity']} [{st['sens_lo']},{st['sens_hi']}] "
              f"spec={st['specificity']} [{st['spec_lo']},{st['spec_hi']}] prec={st['precision']}")
