"""(A9) 用"对实测 ΔE 的预测力"选定对齐能量 E 的实例化(局限 7 / 13 的操作性收口)。

思路: 论文的分配律要求先给定 E; 不同 E 实例化会重排 |Γ_k|(成对族 vs 信息论族在 CLIP 上
完全反向; 解码器侧 4 种池化变体使 LLM 层序翻转)。与其把"哪个 E 正确"留作开放问题,
本脚本用**已有实测 ΔE**做留出预测检验: 对每个候选 E 实例化的 |Γ_k|, 用三种风险泛函
预测各分配策略的 ΔE, 再看哪个实例化的预测与实测排序最一致。

候选 E 实例化(全部来自本地归档 JSON):
  i1 adapter 子空间块耦合 (outputs/llava_granularity_bootstrap_v2.json :: block_mean_gdot 的 llm_*)
  i2 全参数化层剖面聚合到三层块 (同文件的 llm_layer_gdot_full)
  i3..i6 四种解码器池化变体 (outputs/llava_e_pooling_ablation_v2.json :: gamma[*])
风险泛函:
  P1 Σ_k |Γ_k| r_k        (Corollary 2 线性风险目标)
  P2 Σ_k |Γ_k| (r_k - r_max)^2  (容量分散×耦合)
  P3 max_k |Γ_k| r_k      (最差块损伤)
实测策略(LLaVA, 参考协议, 多种子取均值):
  uniform 4/4/4, exp 9/1/6, greedy 16/1/1, expnorm 9/2/5, deepavoid 9/6/1
输出: outputs/e_family_selection.json
"""
import glob
import json
import os
import re

import numpy as np
from scipy import stats

EXP = 'paper3/scripts/outputs/experiments'
OUT = 'outputs/e_family_selection.json'
BLOCKS = ['llm_shallow', 'llm_mid', 'llm_deep']
POLICY_RANKS = {
    'uniform': {'llm_shallow': 4, 'llm_mid': 4, 'llm_deep': 4},
    'exp': {'llm_shallow': 9, 'llm_mid': 1, 'llm_deep': 6},
    'greedy': {'llm_shallow': 16, 'llm_mid': 1, 'llm_deep': 1},
    'expnorm': {'llm_shallow': 11, 'llm_mid': 1, 'llm_deep': 4},
    'deepavoid': {'llm_shallow': 4, 'llm_mid': 6, 'llm_deep': 1},
}


def measured_policies():
    """从实验目录读取各策略的 ΔE(多种子取均值)。"""
    got = {k: [] for k in POLICY_RANKS}
    for p in glob.glob(os.path.join(EXP, 'verify_r*.json')):
        base = os.path.basename(p)
        d = json.load(open(p, encoding='utf-8'))
        if d.get('partial') or '_partial' in base:
            continue  # 云端逐 epoch 落盘的中间态, 不是完整 run
        # 旧 JSON 无 block_config 字段 → 从文件名标签 _bc<name> 推断
        cfg = d.get('block_config')
        if not cfg:
            mm = re.search(r'_bc([a-z]+)', base)
            cfg = mm.group(1) if mm else 'uniform'
        if cfg not in POLICY_RANKS:
            continue
        if cfg == 'uniform' and int(d.get('rank', 0)) != 4:
            continue  # 只取 uniform 策略基线(全层 r=4), 排除 rank 扫描运行
        if d.get('target_proj') or '_proj' in base:
            continue  # 投影器探查单独报告, 不属块重分配策略
        # 仅参考协议: 3 epochs, fp16, adamw, lr 5e-5, 无 warmup/imgs/lang/mask/alpha 等
        if (d.get('epochs') != 3 or d.get('compute_dtype') != 'float16' or d.get('opt') != 'adamw'
                or abs(d.get('lr', 5e-5) - 5e-5) > 1e-12 or d.get('warmup')
                or d.get('grad_mask', 'none') != 'none' or d.get('attn_targets', 'qkvo') != 'qkvo'
                or d.get('proj_rank') is not None or d.get('batch_size', 1) != 1
                or d.get('lang_only') or d.get('data_offset', 0) != 0):
            continue
        de = d.get('delta_E')
        if de is None or (isinstance(de, float) and np.isnan(de)):
            continue
        got[cfg].append((int(d.get('seed', 0)), float(de), base))
    return {k: {'seeds': [s for s, _, _ in v], 'mean': float(np.mean([d for _, d, _ in v])),
                'values': [d for _, d, _ in v], 'files': [f for _, _, f in v]}
            for k, v in got.items() if v}


def instantiation_gammas():
    inst = {}
    g = json.load(open('outputs/llava_granularity_bootstrap_v2.json', encoding='utf-8'))
    bm = g.get('block_mean_gdot', {})
    if all(b in bm for b in BLOCKS):
        inst['adapter_subspace_blocks'] = {b: abs(bm[b]) for b in BLOCKS}
    lay = g.get('llm_layer_gdot_full', {})
    if lay:
        agg = {}
        for b, rng in (('llm_shallow', range(0, 8)), ('llm_mid', range(8, 24)), ('llm_deep', range(24, 32))):
            vals = [abs(lay[str(i)]) for i in rng if str(i) in lay] or [abs(lay[i]) for i in rng if i in lay]
            agg[b] = float(np.mean(vals)) if vals else None
        if all(agg.get(b) is not None for b in BLOCKS):
            inst['fullparam_layer_profile'] = agg
    try:
        pool = json.load(open('outputs/llava_e_pooling_ablation_v2.json', encoding='utf-8'))
        for var, v in pool.get('gamma', {}).items():
            gm = v.get('gamma', {})
            if all(b in gm for b in BLOCKS):
                inst['pooling:' + var] = {b: abs(gm[b]) for b in BLOCKS}
    except FileNotFoundError:
        pass
    return inst


def predictors(gam, ranks):
    g = np.array([gam[b] for b in BLOCKS], dtype=float)
    r = np.array([ranks[b] for b in BLOCKS], dtype=float)
    return {'P1_linear': float((g * r).sum()),
            'P2_dispersion': float((g * (r - r.max()) ** 2).sum()),
            'P3_worstblock': float((g * r).max())}


def main():
    meas = measured_policies()
    inst = instantiation_gammas()
    rows = {}
    for name, gam in inst.items():
        preds = {p: predictors(gam, POLICY_RANKS[p]) for p in meas}
        rows[name] = {'gamma': {k: round(v, 3) for k, v in gam.items()}, 'pred': preds}
    # 与实测 ΔE 的排序相关(策略级)
    pol = sorted(meas)
    y = np.array([meas[p]['mean'] for p in pol])
    res = {}
    for name, d in rows.items():
        res[name] = {}
        for pk in ('P1_linear', 'P2_dispersion', 'P3_worstblock'):
            x = np.array([d['pred'][p][pk] for p in pol])
            if len(x) > 2 and np.std(x) > 0:
                rho, pv = stats.spearmanr(x, y)
                pr, pp = stats.pearsonr(x, y)
                res[name][pk] = {'spearman': round(float(rho), 3), 'p': round(float(pv), 4),
                                 'pearson': round(float(pr), 3), 'pearson_p': round(float(pp), 4)}
            else:
                res[name][pk] = None
    # 选出最佳实例化(以 |Spearman| 最大者为准, 期望正相关: 预测风险越大 ΔE 越大)
    best, best_rho = None, -2
    for name, d in res.items():
        for pk, v in d.items():
            if v and abs(v['spearman']) > best_rho:
                best, best_rho = (name, pk, v), abs(v['spearman'])
    json.dump({'measured_policies': meas, 'policies': pol,
               'instantiations': rows, 'correlations': res,
               'best_predictor': None if best is None else {'instantiation': best[0], 'predictor': best[1],
                                                            **best[2]},
               'note': '正 Spearman 表示该 E 实例化的风险泛函与实测 ΔE 同序(预测力越强越应作为分配 E)'},
              open(OUT, 'w', encoding='utf-8'), indent=1)
    print('measured:', {k: round(v['mean'], 1) for k, v in meas.items()}, flush=True)
    for name, d in res.items():
        print('%-28s %s' % (name, {k: (v['spearman'] if v else None) for k, v in d.items()}), flush=True)
    print('best:', best, flush=True)
    print('DONE ->', OUT, flush=True)


if __name__ == '__main__':
    main()
