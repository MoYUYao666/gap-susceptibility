"""C1（Qwen2-VL-7B：投影器 vs LLM 的不对称秩分配）分析。

数据：2026-09-13 云端清盘重跑，autodl RTX 4080 SUPER（32760 MiB / torch 2.12.1+cu130）。
4 seeds {42,123,456,999} × 3 臂，3 epochs，参考协议（rank=8, uniform 块策略, qkvo 关闭）：
  ① projonly        : 投影器 r=4, attn-targets=none（LLM 不加 LoRA）
  ② projhi16_llmlo2 : 投影器 r=16 + LLM r=2
  ③ projlo2_llmhi16 : 投影器 r=2  + LLM r=16

⚠️ 协议注意（必须写进论文/局限）：Qwen 脚本的"blank image"实为 `np.random.randint` 噪声图，
按 seed 播撒 → **E0 随 seed 变化**（27008–46592，跨度 72%）。因此：
  * 臂间比较（同一 seed 内）是干净的：三臂共用同一张图、同一 E0；
  * 跨 seed 的 ΔE 绝对值不可直接平均 —— 同时报告归一化 ΔE/E0（%），并以"每 seed 的臂序"为主证据；
  * LLaVA 脚本用的是全黑图（E0 恒定 3921/3926），两架构此点协议不一致。

产出：outputs/c1_qwen_asymmetry.json
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
    'tnone_pr4_projonly': '投影器 r=4 单独（LLM 冻结）',
    'pr16_lr2_projhi16_llmlo2': '投影器 r=16 + LLM r=2',
    'pr2_lr16_projlo2_llmhi16': '投影器 r=2 + LLM r=16',
}


def load(seed, arm):
    p = os.path.join(EXP, f'qwen_cf_uniform_rank8_seed{seed}_{arm}.json')
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding='utf-8'))


def sign_test_p(k, n):
    """双侧符号检验 p（k 次成功 / n 次）。"""
    if n == 0:
        return float('nan')
    from math import comb
    tail = sum(comb(n, i) for i in range(k, n + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def block_baseline_block():
    """当前 vintage 的块策略基线（_v2）vs 旧存档：E0 指纹决定可否直接比较。"""
    print()
    print('===== 块策略基线：当前 vintage（_v2）vs 旧存档 =====')
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
    # 旧存档（若存在）
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
            print(f'  [旧存档] seed {s}: E0={e0:.0f} | ' + '  '.join(
                f'{bc} {row[bc]["delta_E"]:+.0f}' for bc in row))

    # E0 指纹检查：v2 与 C1 各臂是否同 vintage
    print()
    c1_e0 = {}
    for s in SEEDS:
        p = os.path.join(EXP, f'qwen_cf_uniform_rank8_seed{s}_tnone_pr4_projonly.json')
        if os.path.exists(p):
            c1_e0[s] = json.load(open(p, encoding='utf-8'))['E'][0]
    same = all(out['v2'][s][next(iter(out['v2'][s]))]['E0'] == c1_e0.get(s)
               for s in out['v2'] if s in c1_e0)
    print(f'  E0 指纹：v2 基线与 C1 各臂一致 = {same}'
          f'（v2 {[out["v2"][s][next(iter(out["v2"][s]))]["E0"] for s in sorted(out["v2"])]} '
          f'vs C1 {[c1_e0[s] for s in sorted(c1_e0)]}）')
    if out['archive']:
        arch_e0 = [out['archive'][s][next(iter(out['archive'][s]))]['E0'] for s in sorted(out['archive'])]
        print(f'  旧存档 E0 = {arch_e0} → 与当前 vintage 不同 → 两组不得混表')

    # 块策略效应 vs 秩分配效应（同 seed 配对）
    print()
    print('  ---- 同 seed 配对：块策略三臂 vs 秩分配三臂 ----')
    for s in sorted(out['v2']):
        if s not in c1_e0:
            continue
        row = out['v2'][s]
        proj = json.load(open(os.path.join(EXP, f'qwen_cf_uniform_rank8_seed{s}_tnone_pr4_projonly.json'),
                              encoding='utf-8'))['delta_E']
        print(f'  seed {s}: 块策略 {min(row[b]["delta_E"] for b in row):+.0f}…{max(row[b]["delta_E"] for b in row):+.0f}'
              f'（跨度 {max(row[b]["delta_E"] for b in row) - min(row[b]["delta_E"] for b in row):.0f}）'
              f' | 投影器单独 {proj:+.0f} → 差 {proj - row["uniform"]["delta_E"]:+.0f}')
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
        print('缺文件 seeds:', missing)

    print(f'纳入 {len(rows)} 条（{len({r["seed"] for r in rows})} seeds × 3 臂）\n')
    print('===== 每 seed 明细 =====')
    print(f'{"seed":>5} {"臂":<28} {"可训练参数":>10} {"E0":>8} {"ΔE":>9} {"ΔE/E0":>9}  E 轨迹')
    for s in SEEDS:
        sub = [r for r in rows if r['seed'] == s]
        if not sub:
            continue
        for r in sub:
            traj = ' -> '.join(f'{v:.0f}' for v in r['E'])
            print(f'{r["seed"]:>5} {r["label"]:<28} {str(r["trainable_params"]):>10} {r["E0"]:>8.0f} '
                  f'{r["delta_E"]:>+9.0f} {r["delta_E_pct"]:>+8.2f}%  {traj}')
        print()

    print('===== 每臂汇总 =====')
    print(f'{"臂":<28} {"n":>2} {"ΔE 均值±sd":>22} {"ΔE/E0 均值±sd":>20} {"正号次数":>9}')
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
    print('===== 主检验：每 seed 的臂序是否一致 =====')
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
    print(f'臂序 投影器单独 > 投影器r2+LLM r16 > 投影器r16+LLM r2 的 seed 数: {order_ok}/{n_seeds}'
          f'  （若完全随机，恰为此序的概率 = 1/6 每 seed → 观测到 {order_ok}/{n_seeds} 的概率 = {(1/6) ** order_ok:.4f}）')
    for (a, b), k in pair_ok.items():
        diffs = pair_diff[(a, b)]
        print(f'  {LABEL[a][:18]:<18} > {LABEL[b][:18]:<18}: {k}/{len(diffs)} seeds  '
              f'差值均值 {mean(diffs):+.0f}（全部差值同号: {"是" if k in (0, len(diffs)) else "否"}）')

    print()
    print('===== 与存档的 Qwen 块策略基线对照 =====')
    arch = sorted(glob.glob(os.path.join(EXP, 'qwen_cf_*_rank8_seed42.json')))
    arch = [p for p in arch if not any(a in os.path.basename(p) for a in ARMS)]
    for p in arch:
        d = json.load(open(p, encoding='utf-8'))
        print(f'  {os.path.basename(p):<52} E0={d["E"][0]:.0f} ΔE={d["delta_E"]:+.0f}')

    blocks = block_baseline_block()

    json.dump({
        'source': 'cloud clean rerun 2026-09-13, autodl RTX 4080 SUPER 32760MiB / torch 2.12.1+cu130',
        'protocol_note': ('Qwen 脚本的 blank image 为 np.random.randint 噪声图并按 seed 播撒，'
                          '故 E0 随 seed 变化；臂间比较干净，跨 seed 绝对值不可平均，另报 ΔE/E0。'
                          'LLaVA 脚本用 np.zeros 全黑图（E0 恒定），两架构此点协议不一致。'),
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
