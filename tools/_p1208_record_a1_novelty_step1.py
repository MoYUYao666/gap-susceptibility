# -*- coding: utf-8 -*-
"""Record the A1 novelty step-1 result in the handover docs."""
from __future__ import annotations

import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

ENT = """> **🔬 2026-10-18 12:35 —— A1 新颖性升级第 1 步：一阶定律的"外推预测"边界（诚实结果）**
>
> 起因：A1 摘要自认 bias-field 的 `r=1.000` 是"**自洽、非独立验证**"。本轮检验：换成**只用聚合量**的闭式分支后，
> 定律能否跨基准预测 τ(λ)。结论：**形状可迁移、水平不可迁移 ⇒ 目前还不是可预测定律**。
>
> ### 一、两条分支的性质（ImageNet-5k，CLIP ViT-B/32）
>
> | 分支 | MAE | Pearson r | 说明 |
> |---|---|---|---|
> | 逐图反转条件（exact）| **0.0013** | 1.0000 | **近乎同义反复**：它反演的就是定义实测 τ 的同一批逐图边距 |
> | 闭式高斯（Gauss）| **0.1153** | 0.9865 | 形状对、**水平系统性偏低**（top-1 平均差 16.3 点）|
>
> margin–bias 独立性成立（Pearson **0.066**，n=50 000 对）⇒ 偏差来源是"用单一 σ_b 代替真实边距场"，不是独立性被破坏。
>
> ### 二、单常数标定 + 跨四基准冻结检验
>
> 在 ImageNet 上拟合单常数 `σ_b,eff = k·√2·σ_m`：**k=0.550**，误差 **0.1153 → 0.0171**（6.7×）。
> 把 k **冻结**，在四个无关基准上预测（各自 gap 方向，冻结 CLIP，无训练）：
>
> | 基准 | 图像 | 类 | **MAE(k=0.55)** | r | 该基准最优 k |
> |---|---|---|---|---|---|
> | rare_species | 1 000 | 50 | **0.0789** | 0.961 | 0.640 |
> | inat_wild | 718 | 48 | **0.1021** | 0.933 | 0.360 |
> | DTD | 1 880 | 47 | **0.1199** | 0.975 | 0.980 |
> | Food-101 | 25 250 | 101 | **0.1043** | 0.986 | 0.940 |
>
> **判定：形状可迁移（r=0.93–0.99），水平不可迁移（最优 k 在 0.36–0.98 间变化）**；且 |λ|≥2 时实测 τ 可为负而模型饱和在 0 以上
> ⇒ 缺的是**逐对相关性结构**，不是更好的常数。
>
> ### 三、对 A1 新颖性策略的影响
>
> **不要把新颖性押在"预测定律"上**（本轮已证不可行）；应押在：
> 1. **可识别性命题**（top-1 只依赖类相对序；gap 是一阶矩量 ⇒ 非充分统计量）+ 构造性反例（同协议 `v1_both_r2` gap +0.1138/R@1 0.584 vs `v1_full_ft` gap +0.1112/R@1 0.181，ΔCG=0.0026、ΔR@1=0.403）；
> 2. **本轮的量化边界结果**：一阶定律跨基准"保形不保水平"，缺的是边距–偏置联合结构 —— 这本身是有价值的新结果。
>
> **归档**：`outputs/analysis/a1_closed_form_{validation,calibration}.json`、`a1_crossbenchmark_closed_form.json`；
> 说明 `docs/A1_NOVELTY_STEP1_2026-10-18.md`；脚本 `_p1205`–`_p1207`。
> ⚠️ 工具细节：torch 在 `D:\Anaconda\envs\pytorch`（系统 python 无 torch）；四基准数据均在本地 `data/`。
>

"""


def main() -> None:
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 新颖性升级第 1 步" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff entry added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("66. 🔬 **A1 新颖性升级第 1 步（2026-10-18 12:35）** —— 一阶定律外推检验：exact 分支 MAE **0.0013**（近乎同义反复），"
           "闭式高斯 MAE 0.1153/r=0.9865（top-1 差 16.3 点）；单常数 k=0.550 把误差降到 0.0171，但冻结后跨四基准"
           "（rare_species/inat/DTD/Food-101）MAE **0.079–0.120**、各自最优 k **0.36–0.98** ⇒ **保形不保水平**。"
           "归档 `outputs/analysis/a1_closed_form_*.json` + `a1_crossbenchmark_closed_form.json`；说明 `docs/A1_NOVELTY_STEP1_2026-10-18.md`。\n")
    if "A1 新颖性升级第 1 步" not in m:
        anchor = "65. ✅ **A1 本地工作副本修复"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")


if __name__ == "__main__":
    main()
