"""Qwen2-VL-7B 的两个 vintage 对照：noise（按 seed 播撒噪声图）vs blank（确定化全黑图）。

noise vintage：2026-09-13 14:2x，autodl RTX 4080 SUPER 32GB，驱动 580.142
blank vintage：2026-09-13 16:5x，autodl RTX 4080（非 SUPER）32GB，驱动 595.71.05
→ 两套 vintage 在**图像协议与设备上同时不同**，因此：
   * 每个 vintage 内部的臂间比较是干净的（同种 seed 内共用一张图、同一台设备）；
   * vintage 之间只能比"每 seed 的臂序/符号"，不能比 ΔE 绝对值。

产出：outputs/c1_qwen_vintages.json
"""
import json
import math
import os
from statistics import mean, pstdev

try:
    from scipy import stats
    HAVE_SCIPY = True
except Exception:  # noqa: BLE001
    HAVE_SCIPY = False

EXP = 'paper3/scripts/outputs/experiments'
OUT = 'outputs/c1_qwen_vintages.json'
SEEDS = (42, 123, 456, 999)
# 每个臂有两个 vintage 的文件名后缀（--tag 追加在 pr/lr 之后，所以位置不同）
ARMS = {
    'projonly': {'label': 'projector r=4 only (LLM frozen)',
                 'noise': 'tnone_pr4_projonly',
                 'blank': 'tnone_pr4_blankimg_projonly'},
    'prhi16_llmlo2': {'label': 'projector r=16 + LLM r=2',
                      'noise': 'pr16_lr2_projhi16_llmlo2',
                      'blank': 'pr16_lr2_blankimg_projhi16_llmlo2'},
    'prlo2_llmhi16': {'label': 'projector r=2 + LLM r=16',
                      'noise': 'pr2_lr16_projlo2_llmhi16',
                      'blank': 'pr2_lr16_blankimg_projlo2_llmhi16'},
}
BLOCK_CFGS = ('uniform', 'theory', 'violation')


def welch(a, b):
    if len(a) < 2 or len(b) < 2:
        return None, None
    va, vb = pstdev(a) ** 2 * len(a) / (len(a) - 1), pstdev(b) ** 2 * len(b) / (len(b) - 1)
    se = math.sqrt(va / len(a) + vb / len(b))
    if se == 0:
        return None, None
    t = (mean(a) - mean(b)) / se
    if HAVE_SCIPY:
        df = (va / len(a) + vb / len(b)) ** 2 / (
            (va / len(a)) ** 2 / (len(a) - 1) + (vb / len(b)) ** 2 / (len(b) - 1))
        p = 2 * stats.t.sf(abs(t), df)
    else:
        p = float('nan')
    return t, p


def load(path):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else None


def vintage(which):
    """which in {'noise','blank'}"""
    out = {}
    for s in SEEDS:
        row = {}
        for k, meta in ARMS.items():
            p = os.path.join(EXP, f'qwen_cf_uniform_rank8_seed{s}_{meta[which]}.json')
            d = load(p)
            if d:
                row[k] = {'E0': d['E'][0], 'delta_E': d['delta_E'], 'E': d['E'],
                          'file': os.path.basename(p), 'trainable': d.get('trainable_params')}
        if row:
            out[s] = row
    return out


def report(name, v, note=''):
    print(f'===== {name} =====   {note}')
    e0s = sorted({round(r[k]['E0']) for r in v.values() for k in r})
    print(f'  E0 取值集合（应只有 1 个 → 图与 seed 无关）: {e0s}')
    print(f'  {"seed":>5} ' + ' '.join(f'{k:>16}' for k in ARMS))
    for s in sorted(v):
        print(f'  {s:>5} ' + ' '.join(f'{v[s][k]["delta_E"]:>+16.0f}' if k in v[s] else f'{"-":>16}'
                                     for k in ARMS))
    print(f'  {"均值":>5} ' + ' '.join(
        f'{mean([v[s][k]["delta_E"] for s in v if k in v[s]]):>+16.0f}' for k in ARMS))
    print(f'  {"sd":>5} ' + ' '.join(
        f'{pstdev([v[s][k]["delta_E"] for s in v if k in v[s]]):>16.0f}' for k in ARMS))
    print(f'  {"正号":>5} ' + ' '.join(
        f'{sum(1 for s in v if k in v[s] and v[s][k]["delta_E"] > 0)}/{len([s for s in v if k in v[s]])}'
        .rjust(16) for k in ARMS))
    # 臂序一致性
    order_ok = 0
    n = 0
    detail = []
    for s in sorted(v):
        if len(v[s]) < 3:
            continue
        n += 1
        vals = {k: v[s][k]['delta_E'] for k in ARMS}
        ok = vals['projonly'] > vals['prlo2_llmhi16'] > vals['prhi16_llmlo2']
        order_ok += ok
        detail.append(f'{s}:' + ('ok' if ok else 'NO'))
    print(f'  臂序 projonly > pr2/lr16 > pr16/lr2 一致的 seed 数: {order_ok}/{n}  [{" ".join(detail)}]')
    tests = {}
    for k in ('prhi16_llmlo2', 'prlo2_llmhi16'):
        a = [v[s]['projonly']['delta_E'] for s in v if 'projonly' in v[s] and k in v[s]]
        b = [v[s][k]['delta_E'] for s in v if 'projonly' in v[s] and k in v[s]]
        t, p = welch(a, b)
        tests[k] = {'t': None if t is None else round(t, 3),
                    'p': None if p is None or math.isnan(p) else round(p, 6),
                    'n': [len(a), len(b)], 'mean_a': round(mean(a), 1), 'mean_b': round(mean(b), 1)}
        print(f'  Welch projonly vs {k}: Δ={mean(a) - mean(b):+.0f}  t={t if t is None else round(t, 2)}  p={p if p is None or math.isnan(p) else f"{p:.2e}"}')
    return {'E0_set': e0s, 'rows': {str(s): {k: v[s][k]['delta_E'] for k in v[s]} for s in v},
            'mean': {k: mean([v[s][k]['delta_E'] for s in v if k in v[s]]) for k in ARMS},
            'sd': {k: pstdev([v[s][k]['delta_E'] for s in v if k in v[s]]) for k in ARMS},
            'n_positive': {k: sum(1 for s in v if k in v[s] and v[s][k]['delta_E'] > 0) for k in ARMS},
            'order_ok': order_ok, 'n_seeds': n, 'welch_vs_projonly': tests}


def main():
    noise = vintage('noise')
    blank = vintage('blank')
    a = report('noise vintage (RTX 4080 SUPER, 噪声图)', noise)
    print()
    b = report('blank vintage (RTX 4080, 全黑图)', blank)
    print()
    print('===== 跨 vintage：每 seed 的臂序是否一致 =====')
    both = sorted(set(noise) & set(blank))
    for s in both:
        on = {k: noise[s][k]['delta_E'] for k in ARMS if k in noise[s]}
        ob = {k: blank[s][k]['delta_E'] for k in ARMS if k in blank[s]}
        if len(on) < 3 or len(ob) < 3:
            continue
        rn = sorted(on, key=lambda k: -on[k])
        rb = sorted(ob, key=lambda k: -ob[k])
        print(f'  seed {s}: noise 序 {rn}')
        print(f'           blank 序 {rb}   {"一致" if rn == rb else "不一致"}')
        print(f'           noise ΔE {[on[k] for k in rn]}')
        print(f'           blank ΔE {[ob[k] for k in rb]}')

    print()
    print('===== 块策略：blank vs noise(v2) vs 旧存档 的符号 =====')
    block = {'blank': {}, 'noise_v2': {}, 'archive': {}}
    for s in (42, 123, 456):
        for bc in BLOCK_CFGS:
            for tag, pat in (('blank', f'qwen_cf_{bc}_rank8_seed{s}_blankimg_v3.json'),
                             ('noise_v2', f'qwen_cf_{bc}_rank8_seed{s}_v2.json'),
                             ('archive', f'qwen_cf_{bc}_rank8_seed{s}.json')):
                d = load(os.path.join(EXP, pat))
                if d:
                    block[tag].setdefault(s, {})[bc] = d['delta_E']
    for tag in ('archive', 'noise_v2', 'blank'):
        print(f'  [{tag}]')
        for s in sorted(block[tag]):
            row = block[tag][s]
            print(f'    seed {s}: ' + '  '.join(f'{bc} {row[bc]:+.0f}' for bc in BLOCK_CFGS if bc in row)
                  + f'   → 符号 {sorted({"+" if row[bc] > 0 else "-" for bc in row if bc in row})}')
    # 符号稳定性判定
    signs = {tag: sorted({('+' if v > 0 else '-') for s in block[tag] for v in block[tag][s].values()})
             for tag in block}
    print(f'  各 vintage 出现的符号集合: {signs}')

    json.dump({'provenance': {
        'noise_vintage': 'autodl RTX 4080 SUPER 32760MiB, driver 580.142 (seeded noise image per seed)',
        'blank_vintage': 'autodl RTX 4080 (non-SUPER) 32760MiB, driver 595.71.05 (deterministic black image)',
        'caveat': '两套 vintage 在图像协议与设备上同时不同；vintage 内臂间比较干净，跨 vintage 只比臂序/符号。',
    }, 'noise': a, 'blank': b, 'block_signs': block, 'sign_sets': signs},
        open(OUT, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f'\nDONE -> {OUT}')


if __name__ == '__main__':
    main()
