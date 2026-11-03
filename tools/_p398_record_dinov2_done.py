# -*- coding: utf-8 -*-
r"""落账：task-8（DINOv2 异质配对）收官（2026-10-12）。

    python tools\_p398_record_dinov2_done.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅ 2026-10-12（续）—— task-8（DINOv2 异质配对）收官，已写入论文**
>
> ### 结果（`outputs/analysis/dinov2_hetero/{fitted,random}/**/results.json`，我已核实）
>
> | arm（seed 42，严格冻结） | 可训（vision 侧） | ΔCG | ΔDG | R@1 |
> |---|---|---|---|---|
> | frozen（fitted head） | 0 | — | — | 0.2890 |
> | text_only | 196,608（**0**） | **−0.3913** | −0.4462 | 0.3540 |
> | **both** | 491,520（**294,912** ✅） | **−0.4099** | −0.4667 | **0.5550** |
>
> **两臂排序 `both < text_only`** → 与论文**非对比式骨干（SigLIP / BioCLIP）同向**，
> 而 CLIP/OpenCLIP 行是 text-only 最小；**且检索排序也 both 更高**（论文 CLIP 行里两个排序相反）。
>
> ### 随机头对照（我先前砍掉、后要求补回；结论：**效应不是头造出来的**）
>
> | | fitted head | **random head** |
> |---|---|---|
> | frozen CG / R@1 | 0.6769 / 0.2890 | **0.8717 / 0.0050**（≈chance 0.002） |
> | text_only ΔCG | −0.3913 | **−0.2988（= fitted 的 76%）** |
>
> **交叉验证**：random 臂 live 量测 LoRA 范数 **9.7959** vs 从 checkpoint 恢复的 **9.7878**
> → **差 0.08%，证明恢复方法与实时量测同口径**。
>
> ### 已写入论文（`empirical.tex`，`tools/_p396`；`\\logit` 编译错见 `tools/_p397`）
>
> 新段 *"A non-contrastively pre-trained vision tower, as a qualitative extension"*，
> **同时写入五条限制**：① 异质配对（**不是原生双塔模型**）② **InfoNCE 温度不同**
> （exp 14.29 vs 论文 100，**7×** → **量级不可与表并列**）③ n=1
> ④ **无单一预训练目标 ⇒ 既不确认也不否证论文分组规则** ⑤ `vision_only` **未跑**（记为未跑，不估计）。
> **禁语已核不出现在稿中**。
>
> ### B 部分
>
> - **Qwen2-VL-2B 复用核对通过**：13-seed 重算 66.47±8.32 / 87.94±5.35 / 18.03±8.78
>   vs 论文 66.5±8.3 / 87.9±5.4 / 18.0±8.8 **全部一致**
> - **LLaVA-1.5-7B 本地不可行（实测）**：bf16 权重 **13.157 GiB** vs 8 GiB 显存 = **1.64×**，
>   缺口 5.16 GiB，在激活/优化器状态之前就已超出；**未用 4-bit**（项目铁律）
>
> ### 成员自查出的三个真 bug（均已修）
>
> ① DINOv2 投影层名（`query`/`value`）与 LoRA 默认（`q_proj`/`v_proj`）不匹配 →
> **静默不注入假实验**（我已系统核查论文全部 backbone：**只有 DINOv2 不匹配**）
> ② 插桩把**已训 LoRA 清零**后才量测 → 新增字段对所有臂失效（真值由 checkpoint 恢复）
> ③ PowerShell `Get-Content -Raw | Set-Content` 往返**双重编码**报告生成器
> （5 个修复脚本，**无归档数字受影响**）
>
> ### 两条流程教训（成员自提，我采纳）
>
> - **自动续跑逻辑必须把已答应的 scope 编码进判据**，否则会在无人值守时越过范围
>   （其 watcher 曾自动起了超范围的 `vision_only`，1 分钟内被发现并杀掉、无数据落盘）
> - **禁止 `Get-Content -Raw | Set-Content` 往返**（见本轮另一条目）
>
> ### 状态（本条目落账时）
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | `main_nc` | **62** | 0 | 0 | 0 |
> | `main_springer` | **45** | 0 | 0 | 0 |
> | 投稿包 | **62** | 0 | 0 | — |
>
> **PR 核验 26/26** ｜ 提交 `8cff2d2`、`a77052c`
> **GPU**：task-7 已恢复续跑剩余 3 个 cell（`1e-4 seed999`、`3e-4 seed123/999`）
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "task-8（DINOv2 异质配对）收官" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("task-8（DINOv2 异质配对）收官", "0.4099", "0.2988", "9.7959", "1.64"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
