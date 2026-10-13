"""C2 (Γ cost) / C4 (batch axis) / C5 (device ceiling) analysis + cross-device comparison.

Data: 2026-09-13 cloud clean rerun (autodl RTX 4080 SUPER 32760 MiB, driver 580.142,
torch 2.12.1+cu130, transformers 5.16.1) + the same model card on the previous instance (files ending in _v1).

Output: outputs/c2c4_cloud_summary.json
"""
import glob
import json
import os
from statistics import mean, median, pstdev

OUT = 'outputs/c2c4_cloud_summary.json'
EXP = 'paper3/scripts/outputs/experiments'


def load(p):
    return json.load(open(p, encoding='utf-8'))


def cost_block():
    """C2: 8 probes (2 single runs + 6 repeats), summarized by model as medians."""
    print('===== C2 Γ cost probes (8 files) =====')
    groups = {'llava': [], 'qwen': []}
    rows = []
    for p in sorted(glob.glob('outputs/gamma_cost_*.json')):
        d = load(p)
        arch = d['arch']
        groups[arch].append(d)
        rows.append({'file': os.path.basename(p), 'arch': arch, 'gpu': d['gpu'],
                     'torch': d['torch'],
                     'gamma_total': d['gamma_total_seconds'],
                     'gamma_fwd': d['gamma_forward_seconds'],
                     'gamma_bwd': d['gamma_backward_seconds'],
                     'gamma_peak': d['gamma_peak_vram_gb'],
                     'train_step': d['train_step_seconds'],
                     'train_peak': d['train_step_peak_vram_gb'],
                     'ratio': d['gamma_over_train_step_time'],
                     'trainable_float': d['n_trainable_float_params'],
                     'vram_after_load': d['vram_after_load_gb']})
    print(f'{"file":<48} {"Γ total":>7} {"Γ peak":>7} {"train step":>8} {"step peak":>7} {"ratio":>6}')
    for r in rows:
        print(f'{r["file"]:<48} {r["gamma_total"]:>7.3f} {r["gamma_peak"]:>7.2f} '
              f'{r["train_step"]:>8.3f} {r["train_peak"]:>7.2f} {r["ratio"]:>6.3f}')
    summary = {}
    for arch, ds in groups.items():
        if not ds:
            continue
        summary[arch] = {
            'n': len(ds),
            'gpu': ds[0]['gpu'], 'torch': ds[0]['torch'],
            'trainable_float': ds[0]['n_trainable_float_params'],
            'gamma_total_median': median(d['gamma_total_seconds'] for d in ds),
            'gamma_total_range': [min(d['gamma_total_seconds'] for d in ds),
                                  max(d['gamma_total_seconds'] for d in ds)],
            'gamma_peak_median': median(d['gamma_peak_vram_gb'] for d in ds),
            'train_step_median': median(d['train_step_seconds'] for d in ds),
            'train_peak_median': median(d['train_step_peak_vram_gb'] for d in ds),
            'ratio_median': median(d['gamma_over_train_step_time'] for d in ds),
            'ratio_values': [d['gamma_over_train_step_time'] for d in ds],
        }
    print()
    for arch, s in summary.items():
        print(f'{arch:>6}: n={s["n"]}  Γ median {s["gamma_total_median"]:.3f}s '
              f'(range {s["gamma_total_range"][0]:.3f}-{s["gamma_total_range"][1]:.3f})  '
              f'Γ/train step median {s["ratio_median"]:.3f} (values {[round(v, 3) for v in s["ratio_values"]]})')
    return rows, summary


def batch_block():
    """C4: cloud batch=2 vs local batch=2 + interpretation of C5 having no artifacts."""
    print()
    print('===== C4 batch=2 (3 epochs, r=5/6, seed 42): cloud vs local =====')
    out = {}
    for r in (5, 6):
        loc = os.path.join(EXP, f'verify_r{r}_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2.json')
        cld = os.path.join(EXP, f'verify_r{r}_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2_cloud.json')
        a, b = load(loc), load(cld)
        out[r] = {'local': {'E': a['E'], 'delta_E': a['delta_E']},
                  'cloud': {'E': b['E'], 'delta_E': b['delta_E']}}
        print(f'  r={r}: local ΔE {a["delta_E"]:+.1f}  E0={a["E"][0]:.0f} | '
              f'cloud ΔE {b["delta_E"]:+.1f}  E0={b["E"][0]:.0f}')
        print(f'        local {[round(v, 1) for v in a["E"]]}')
        print(f'        cloud {[round(v, 1) for v in b["E"]]}')
        print(f'        sign agreement: {"yes" if (a["delta_E"] > 0) == (b["delta_E"] > 0) else "no"}; '
              f'E0 offset {b["E"][0] - a["E"][0]:+.0f}') 
    print()
    print('===== C5 device ceiling =====')
    for tag in ('b4', 'b8', 'b16', 'b32'):
        hits = glob.glob(os.path.join(EXP, f'*_e3_bcuniform_{tag}.json'))
        parts = glob.glob(os.path.join(EXP, f'verify_r6_s42_{tag}_partial.json'))
        print(f'  batch={tag[1:]:>2}: {len(hits)} complete results, {len(parts)} per-epoch intermediates'
              f'{"  -> not even the first epoch finished (OOM very early)" if not hits and not parts else ""}')
    return out


def main():
    rows, summary = cost_block()
    c4 = batch_block()
    json.dump({
        'source': 'cloud clean rerun 2026-09-13 + previous instance (same model card)',
        'c2_probes': rows, 'c2_summary': summary,
        'c4': {str(k): v for k, v in c4.items()},
        'c5_note': ('batch 4/8 (r=6, s=42, 3 epochs) produced no JSON at all on the 32760 MiB card, '
                    'not even per-epoch intermediates -> it crashes within the first epoch; '
                    'batch 2 can complete 3 epochs; batch 1 is the reference protocol.'),
    }, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'\nDONE -> {OUT}')


if __name__ == '__main__':
    main()
