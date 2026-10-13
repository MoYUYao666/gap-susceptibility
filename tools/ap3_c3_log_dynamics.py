"""Parse training dynamics from the cloud per-cell logs: per-epoch avg_loss / gradient norm / runtime, and test "whether the gradient norm diverges before E".

Input: paper3/scripts/outputs/logs/c3_r*_s*.log (per-cell tee logs of run_all_clean.sh, UTF-8; already committed together with the results)
Output: outputs/c3_log_dynamics.json
"""
import glob
import json
import math
import os
import re

LOG_DIR = 'paper3/scripts/outputs/logs'
OUT = 'outputs/c3_log_dynamics.json'

RE_EPOCH = re.compile(
    r'Epoch (\d+): avg_loss=([\d.]+|nan) \((\d+)/(\d+) valid\) \| \|\|g\|\| vis=([\d.eE+-]+) proj=([\d.eE+-]+) llm=([\d.eE+-]+)')
# lines after the NaN have no gradient segment: Epoch 8: avg_loss=0.0000 (0/16 valid)
RE_EPOCH_NAN = re.compile(r'Epoch (\d+): avg_loss=([\d.]+|nan) \((\d+)/(\d+) valid\)\s*$', re.M)
RE_E = re.compile(r'E\((\d+)\) = ([\d.]+|nan)')
RE_TIME = re.compile(r'Training time: (\d+)s')
RE_VRAM = re.compile(r'Model loaded\. VRAM: ([\d.]+) GB')


def parse(p):
    txt = open(p, encoding='utf-8', errors='replace').read()
    rec = {'file': os.path.basename(p), 'epochs': [], 'E': [], 'train_seconds': None, 'vram_loaded': None}
    m = RE_TIME.search(txt)
    if m:
        rec['train_seconds'] = int(m.group(1))
    m = RE_VRAM.search(txt)
    if m:
        rec['vram_loaded'] = float(m.group(1))
    for m in RE_EPOCH.finditer(txt):
        rec['epochs'].append({
            'epoch': int(m.group(1)),
            'avg_loss': float(m.group(2)) if m.group(2) != 'nan' else float('nan'),
            'valid': int(m.group(3)), 'total': int(m.group(4)),
            'g_vis': float(m.group(5)), 'g_proj': float(m.group(6)), 'g_llm': float(m.group(7)),
        })
    for m in RE_EPOCH_NAN.finditer(txt):
        rec['epochs'].append({
            'epoch': int(m.group(1)),
            'avg_loss': float(m.group(2)) if m.group(2) != 'nan' else float('nan'),
            'valid': int(m.group(3)), 'total': int(m.group(4)),
            'g_vis': None, 'g_proj': None, 'g_llm': None,
        })
    rec['epochs'].sort(key=lambda e: e['epoch'])
    E = {}
    for m in RE_E.finditer(txt):
        E[int(m.group(1))] = float(m.group(2)) if m.group(2) != 'nan' else float('nan')
    rec['E'] = [E.get(i, None) for i in range(0, 11)]
    return rec


def isnan(v):
    return isinstance(v, float) and math.isnan(v)


def main():
    files = sorted(glob.glob(os.path.join(LOG_DIR, 'c3_r*_s*.log')))
    print(f'parsing {len(files)} logs\n')
    recs = [parse(p) for p in files]
    for r in recs:
        m = re.search(r'c3_r(\d+)_s(\d+)', r['file'])
        r['rank'], r['seed'] = int(m.group(1)), int(m.group(2))

    print(f'{"cel":<12} {"train s":>6} {"valid epochs":>9} {"first 0/16":>9} {"loss trajectory (valid part)":<46}')
    for r in sorted(recs, key=lambda x: (x['rank'], x['seed'])):
        zero = next((e['epoch'] for e in r['epochs'] if e['valid'] == 0), None)
        los = ' '.join(f'{e["avg_loss"]:.2f}' for e in r['epochs'] if e['valid'] > 0)
        print(f'r{r["rank"]}_s{r["seed"]:<8} {str(r["train_seconds"]):>6} '
              f'{sum(1 for e in r["epochs"] if e["valid"] > 0):>9} {str(zero):>9} {los:<46}')

    print()
    print('===== ⭐ loss decreases vs E increases: the two metrics point in opposite directions within the valid epochs =====')
    print(f'{"cel":<12} {"loss first→last":>16} {"change":>9} {"E first→peak":>16} {"peak/first":>9}')
    for r in sorted(recs, key=lambda x: (x['rank'], x['seed']))[:6]:
        eff = [e for e in r['epochs'] if e['valid'] > 0]
        if not eff:
            continue
        l0, l1 = eff[0]['avg_loss'], eff[-1]['avg_loss']
        Ev = [v for v in r['E'] if v is not None and not isnan(v)]
        if len(Ev) < 2:
            continue
        print(f'r{r["rank"]}_s{r["seed"]:<8} {f"{l0:.2f} -> {l1:.2f}":>16} '
              f'{(l1 - l0) / l0 * 100:>+8.1f}% {f"{Ev[1]:.0f} -> {max(Ev):.0f}":>16} '
              f'{max(Ev) / Ev[1]:>8.2f}x')

    print()
    print('===== gradient-norm trend: does it rise monotonically before divergence? =====')
    print(f'{"rank":>4} {"‖g‖llm first→last (valid)":>26} {"slope (per epoch)":>15} {"‖g‖vis first→last":>20} {"slope":>10}')
    per_rank = {}
    for rank in (4, 5, 6):
        sub = [r for r in recs if r['rank'] == rank]
        firsts, lasts, slopes_l, slopes_v, firstv, lastv = [], [], [], [], [], []
        for r in sub:
            eff = [e for e in r['epochs'] if e['valid'] > 0]
            if len(eff) < 3:
                continue
            xs = [e['epoch'] for e in eff]
            gl = [e['g_llm'] for e in eff]
            gv = [e['g_vis'] for e in eff]
            n = len(xs)
            mx, my = sum(xs) / n, sum(gl) / n
            den = sum((x - mx) ** 2 for x in xs)
            sl = sum((x - mx) * (y - my) for x, y in zip(xs, gl)) / den
            mxv, myv = mx, sum(gv) / n
            slv = sum((x - mxv) * (y - myv) for x, y in zip(xs, gv)) / den
            firsts.append(gl[0]); lasts.append(gl[-1]); slopes_l.append(sl)
            firstv.append(gv[0]); lastv.append(gv[-1]); slopes_v.append(slv)
        per_rank[rank] = {'g_llm_first_mean': sum(firsts) / len(firsts), 'g_llm_last_mean': sum(lasts) / len(lasts),
                          'g_llm_slope_mean': sum(slopes_l) / len(slopes_l),
                          'g_vis_first_mean': sum(firstv) / len(firstv), 'g_vis_last_mean': sum(lastv) / len(lastv),
                          'g_vis_slope_mean': sum(slopes_v) / len(slopes_v)}
        print(f'{rank:>4} {firsts and f"{sum(firsts)/len(firsts):.1f} -> {sum(lasts)/len(lasts):.1f}":>26} '
              f'{sum(slopes_l)/len(slopes_l):>+15.3f} '
              f'{f"{sum(firstv)/len(firstv):.1f} -> {sum(lastv)/len(lastv):.1f}":>20} '
              f'{sum(slopes_v)/len(slopes_v):>+10.3f}')

    print()
    print('===== mechanism of the E divergence: relation between avg_loss and E =====')
    for r in sorted(recs, key=lambda x: (x['rank'], x['seed']))[:3]:
        eff = [e for e in r['epochs'] if e['valid'] > 0]
        los = ' '.join(f'{e["avg_loss"]:.2f}' for e in eff)
        Es = ' '.join('nan' if isnan(v) or v is None else f'{v:.0f}' for v in r['E'])
        print(f'  r{r["rank"]}_s{r["seed"]}:')
        print(f'    avg_loss: {los}')
        print(f'    E       : {Es}')

    ok = [r for r in recs if r['train_seconds']]
    print()
    print(f'training time: {min(r["train_seconds"] for r in ok)}–{max(r["train_seconds"] for r in ok)} s '
          f'(median {sorted(r["train_seconds"] for r in ok)[len(ok)//2]} s, 10 epochs)')

    print()
    print('===== per-rank summary for the paper tables =====')
    # the divergence slope has outputs/c3_epoch_budget.json as its single source (to avoid computing it in two places)
    budget = json.load(open('outputs/c3_epoch_budget.json', encoding='utf-8')) if os.path.exists('outputs/c3_epoch_budget.json') else {'per_rank': {}}
    print(f'{"rank":>4} {"n":>2} {"collapse epoch(mean±sd)":>20} {"divergence slope(budget)":>18} '
          f'{"min E":>7} {"minE@ep":>8} {"loss drop":>10} {"E peak/first":>10} {"0/16 after collapse":>11}')

    def mean(v):
        return sum(v) / len(v)

    def sd(v):
        return (sum((x - mean(v)) ** 2 for x in v) / len(v)) ** 0.5

    for rank in (4, 5, 6):
        sub = [r for r in recs if r['rank'] == rank]
        cols = []
        for r in sub:
            eff = [e for e in r['epochs'] if e['valid'] > 0]
            Ev = [v for v in r['E'] if v is not None and not isnan(v)]
            zero = next((e['epoch'] for e in r['epochs'] if e['valid'] == 0), None)
            cols.append({
                'nan_idx': next((i for i, v in enumerate(r['E']) if v is not None and isnan(v)), None),
                'loss_drop': ((eff[-1]['avg_loss'] - eff[0]['avg_loss']) / eff[0]['avg_loss'] * 100) if eff else None,
                'peak_ratio': (max(Ev) / Ev[1]) if len(Ev) > 1 else None,
                'minE': min(Ev) if Ev else None,
                'minE_ep': Ev.index(min(Ev)) if Ev else None,
                'zero_epoch': zero,
            })
        nb = [c['nan_idx'] for c in cols if c['nan_idx'] is not None]
        loss = [c['loss_drop'] for c in cols if c['loss_drop'] is not None]
        pk = [c['peak_ratio'] for c in cols if c['peak_ratio'] is not None]
        mn = [c['minE'] for c in cols if c['minE'] is not None]
        mep = [c['minE_ep'] for c in cols if c['minE_ep'] is not None]
        z = [c['zero_epoch'] for c in cols if c['zero_epoch'] is not None]
        b = budget['per_rank'].get(str(rank), budget['per_rank'].get(rank, {}))
        per_rank[rank].update({
            'nan_epoch_mean': mean(nb), 'nan_epoch_sd': sd(nb),
            'nan_epoch_values': sorted(nb),
            'loss_drop_pct_mean': mean(loss), 'peak_ratio_mean': mean(pk),
            'minE_mean': mean(mn), 'minE_epoch_mean': mean(mep),
            'zero_valid_epoch_mean': mean(z) if z else None,
            'slope_mean_from_budget': b.get('slope_mean'),
        })
        print(f'{rank:>4} {len(nb):>2} {mean(nb):>12.2f} ± {sd(nb):<6.2f} '
              f'{str(b.get("slope_mean"))[:18]:>18} {mean(mn):>7.0f} {mean(mep):>8.2f} '
              f'{mean(loss):>9.1f}% {mean(pk):>10.2f} {mean(z) if z else float("nan"):>11.1f}')

    json.dump({'source': 'cloud per-cell logs 2026-09-13', 'cells': recs, 'per_rank': per_rank},
              open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'\nDONE -> {OUT}')


if __name__ == '__main__':
    main()
