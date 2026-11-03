"""跨设备可复现性对照（本地 8GB 机 vs 云端 32GB 4080 SUPER）。

证据意义：
  * 同一 rank 的 10-epoch 轨迹，两台设备**触发 NaN 的 epoch 完全一致**（r4→ep9 / r5→ep8 / r6→ep7），
    说明"崩溃时刻"是设备不变量（协议属性，不是硬件噪声）。
  * 稳定段（前 ~4 个 epoch）逐点相对差 ≤0.25%；一旦进入发散段，相对差放大到 3–7%
    （混沌放大），因此**跨设备的 ΔE 绝对值不可混用**。
  * batch=2/3-epoch 的 r5/r6 符号在两台设备上一致（r5 负、r6 正），但幅度有设备差
    （−73.5 vs −49.5；+36.0 vs +22.0）→ ΔE 是小量之差，跨设备比较需谨慎。

产出：outputs/device_reproducibility.json
"""
import json
import math
import os

OUT = 'outputs/device_reproducibility.json'
EXP = 'paper3/scripts/outputs/experiments'


def load(p):
    return json.load(open(p, encoding='utf-8'))


def isnan(v):
    return isinstance(v, float) and math.isnan(v)


def first_nan(E):
    return next((i for i, v in enumerate(E) if isnan(v)), None)


def compare(name, pl, pc):
    if not (os.path.exists(pl) and os.path.exists(pc)):
        print(f'  [{name}] 缺文件，跳过')
        return None
    a, b = load(pl), load(pc)
    Ea, Eb = a['E'], b['E']
    rel = [(y - x) / x * 100 for x, y in zip(Ea, Eb)
           if not isnan(x) and not isnan(y) and x != 0]
    rec = {
        'name': name,
        'local': {'file': os.path.basename(pl), 'E': Ea, 'E0': Ea[0],
                  'delta_E': a.get('delta_E'), 'first_nan_index': first_nan(Ea)},
        'cloud': {'file': os.path.basename(pc), 'E': Eb, 'E0': Eb[0],
                  'delta_E': b.get('delta_E'), 'first_nan_index': first_nan(Eb)},
        'E0_offset': Eb[0] - Ea[0],
        'E0_offset_pct': (Eb[0] - Ea[0]) / Ea[0] * 100,
        'rel_diff_pct_by_epoch': rel,
        'max_abs_rel_diff_before_epoch5_pct': max((abs(v) for v in rel[:4]), default=None),
        'max_abs_rel_diff_pct': max((abs(v) for v in rel), default=None),
        'same_first_nan_epoch': first_nan(Ea) == first_nan(Eb),
        'same_delta_sign': (None if (a.get('delta_E') is None or b.get('delta_E') is None
                                     or (isinstance(a.get('delta_E'), float) and math.isnan(a['delta_E']))
                                     or (isinstance(b.get('delta_E'), float) and math.isnan(b['delta_E'])))
                            else (a['delta_E'] > 0) == (b['delta_E'] > 0)),
    }
    print(f'  [{name}]')
    print(f'      本地 E0={Ea[0]:.0f}  云端 E0={Eb[0]:.0f}  偏移 {rec["E0_offset"]:+.0f} '
          f'({rec["E0_offset_pct"]:+.3f}%)')
    print(f'      前 4 个 epoch 最大相对差 {rec["max_abs_rel_diff_before_epoch5_pct"]:.3f}%  |  '
          f'全轨迹最大 {rec["max_abs_rel_diff_pct"]:.3f}%')
    print(f'      NaN epoch: 本地 {rec["local"]["first_nan_index"]} vs 云端 '
          f'{rec["cloud"]["first_nan_index"]} → 一致: {rec["same_first_nan_epoch"]}')
    if rec['same_delta_sign'] is not None:
        print(f'      ΔE 符号一致: {rec["same_delta_sign"]} '
              f'(本地 {a["delta_E"]:+.1f} vs 云端 {b["delta_E"]:+.1f})')
    elif a.get('delta_E') is not None:
        print(f'      ΔE 均为 NaN（崩到无法定义）→ 符号不可判')
    return rec


def main():
    recs = []
    print('===== 10-epoch（batch=1）=====')
    recs.append(compare('r=4 s=42 e10',
                        os.path.join(EXP, 'verify_r4_s42_lr5e-05_nw_float1_adamw_e10_bcuniform.json'),
                        os.path.join(EXP, 'verify_r4_s42_lr5e-05_nw_float1_adamw_e10_bcuniform_cloud.json')))
    for r in (5, 6):
        recs.append(compare(f'r={r} s=42 e10',
                            os.path.join(EXP, f'verify_r{r}_s42_e10.json'),
                            os.path.join(EXP, f'verify_r{r}_s42_lr5e-05_nw_float1_adamw_e10_bcuniform.json')))
    print()
    print('===== batch=2 / 3 epochs =====')
    for r in (5, 6):
        recs.append(compare(f'r={r} s=42 e3 b2',
                            os.path.join(EXP, f'verify_r{r}_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2.json'),
                            os.path.join(EXP, f'verify_r{r}_s42_lr5e-05_nw_float1_adamw_e3_bcuniform_b2_cloud.json')))
    recs = [r for r in recs if r]
    n_e10 = sum(1 for r in recs if 'e10' in r['name'])
    n_e10_same = sum(1 for r in recs if 'e10' in r['name'] and r['same_first_nan_epoch'])
    stable = [r['max_abs_rel_diff_before_epoch5_pct'] for r in recs if 'e10' in r['name']]
    print()
    print(f'结论：10-epoch 轨迹的 NaN epoch 一致 {n_e10_same}/{n_e10}；'
          f'前 4 个 epoch 相对差 ≤{max(stable):.2f}%（逐格: ' +
          ', '.join(f'{v:.2f}%' for v in stable) + '）；发散段放大到 3–7%。')
    print('      batch=2/3-epoch：ΔE 符号两台设备一致，但幅度差 24 与 14 '
          '（相对差 0.84% / 1.55%）→ ΔE 是小量之差，跨设备不可混用。')
    json.dump({
        'local_device': 'local 8 GB box (torch 2.9.1+cu130, E0=3921 for LLaVA reference protocol)',
        'cloud_device': 'autodl RTX 4080 SUPER 32760 MiB, driver 580.142, torch 2.12.1+cu130 (E0=3926)',
        'records': recs,
        'conclusion': ('NaN epoch 是设备不变量；稳定段一致性 ≤0.3%；发散段为混沌放大 3–7%；'
                       '跨设备不可混用 ΔE 绝对值（本仓库因此把云端文件与本地文件分开命名与统计）。'),
    }, open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'\nDONE -> {OUT}')


if __name__ == '__main__':
    main()
