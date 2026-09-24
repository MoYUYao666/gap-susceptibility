"""C2（Γ 成本）/ C4（batch 轴）/ C5（设备上限）分析 + 跨设备对照。

数据：2026-09-13 云端清盘重跑（autodl RTX 4080 SUPER 32760 MiB，驱动 580.142，
torch 2.12.1+cu130，transformers 5.16.1）+ 上一实例的同型号卡（文件以 _v1 结尾）。

产出：outputs/c2c4_cloud_summary.json
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
    """C2：8 份探针（2 单次 + 6 重复），按模型汇总中位数。"""
    print('===== C2 Γ 成本探针（8 份）=====')
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
    print(f'{"文件":<48} {"Γ合计":>7} {"Γ峰值":>7} {"训练步":>8} {"步峰值":>7} {"比值":>6}')
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
        print(f'{arch:>6}: n={s["n"]}  Γ 中位数 {s["gamma_total_median"]:.3f}s '
              f'(范围 {s["gamma_total_range"][0]:.3f}-{s["gamma_total_range"][1]:.3f})  '
              f'Γ/训练步 中位数 {s["ratio_median"]:.3f} (值 {[round(v, 3) for v in s["ratio_values"]]})')
    return rows, summary


def batch_block():
    """C4：云端 batch=2 vs 本地 batch=2 + C5 无产物的解读。"""
    print()
    print('===== C4 batch=2（3 epochs, r=5/6, seed 42）：云端 vs 本地 =====')
    out = {}
    for r in (5, 6):
        loc = os.path.join(EXP, f'verify_r{r}_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2.json')
        cld = os.path.join(EXP, f'verify_r{r}_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2_cloud.json')
        a, b = load(loc), load(cld)
        out[r] = {'local': {'E': a['E'], 'delta_E': a['delta_E']},
                  'cloud': {'E': b['E'], 'delta_E': b['delta_E']}}
        print(f'  r={r}: 本地 ΔE {a["delta_E"]:+.1f}  E0={a["E"][0]:.0f} | '
              f'云端 ΔE {b["delta_E"]:+.1f}  E0={b["E"][0]:.0f}')
        print(f'        本地 {[round(v, 1) for v in a["E"]]}')
        print(f'        云端 {[round(v, 1) for v in b["E"]]}')
        print(f'        符号一致: {"是" if (a["delta_E"] > 0) == (b["delta_E"] > 0) else "否"}；'
              f'E0 偏移 {b["E"][0] - a["E"][0]:+.0f}') 
    print()
    print('===== C5 设备上限 =====')
    for tag in ('b4', 'b8', 'b16', 'b32'):
        hits = glob.glob(os.path.join(EXP, f'*_e3_bcuniform_{tag}.json'))
        parts = glob.glob(os.path.join(EXP, f'verify_r6_s42_{tag}_partial.json'))
        print(f'  batch={tag[1:]:>2}: 完整结果 {len(hits)} 个，逐 epoch 中间态 {len(parts)} 个'
              f'{"  → 首个 epoch 都没跑完（OOM 很早）" if not hits and not parts else ""}')
    return out


def main():
    rows, summary = cost_block()
    c4 = batch_block()
    json.dump({
        'source': 'cloud clean rerun 2026-09-13 + previous instance (same model card)',
        'c2_probes': rows, 'c2_summary': summary,
        'c4': {str(k): v for k, v in c4.items()},
        'c5_note': ('batch 4/8（r=6, s=42, 3 epochs）在 32760 MiB 的卡上未产生任何 JSON、'
                    '连逐 epoch 中间态都没有 → 在第一个 epoch 内即崩溃；'
                    'batch 2 可完成 3 epochs；batch 1 为参考协议。'),
    }, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'\nDONE -> {OUT}')


if __name__ == '__main__':
    main()
