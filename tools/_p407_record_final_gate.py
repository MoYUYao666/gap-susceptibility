# -*- coding: utf-8 -*-
r"""落账：最终门禁 + 本轮最好的一处流程改进（2026-10-12）。

    python tools\_p407_record_final_gate.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **🏁 2026-10-12 —— 全部工作面收官；最终门禁 `tools/_p406_final_gate.py` 全绿**
>
> ### 门禁结果（`outputs/analysis/final_gate.json`）
>
> | # | 项 | 结果 |
> |---|---|---|
> | 1 | **PR 意见核验**（`_p290`） | **26/26 通过** |
> | 2 | `main_nc` | ✅ **63 页** ｜ 错 0 ｜ 未定义 0 ｜ Overfull 0 |
> | 2 | `main_springer` | ✅ **45 页** ｜ 错 0 ｜ 未定义 0 ｜ Overfull 0 |
> | 3 | 投稿包同步（`_p190`） | ✅ |
> | 4 | 编码损伤扫描（`_p394`） | ✅ 干净 **449** 个（唯一"可疑"是扫描脚本自身，假阳性） |
> | 5 | 交付件存在性 | ✅ **21/21** |
> | 6 | 稿件禁语检查 | ✅ 全部 8 项通过 |
> | 7 | GPU | ✅ **已全部释放**（运行中 `tools/*.py` = 0） |
>
> ### 本轮最好的一处流程改进（成员 causal-hardener 自提，我采纳并推广）
>
> 我核出它报告里的全称否定 *"No interior minimum"* **不成立**（逐点序列里 `3e-07` 的 −0.0069
> 低于两侧）。它的处置**超出我的要求**：**把"无 X"从人工断言改成机器穷举**——
> `tools/_p264_fullft_tables.py` 现在**逐点枚举内部极小值**，写入
> `pr_fullft_verdict.json::shape.interior_minima_functional_regime` 与表 T7，并附
> `interior_minima_note = "computed point by point; a universal 'no interior minimum' claim is only
> valid when this list is empty"`。
> **并自查出同型问题**：§5.3 的"归档不含任何版本记录"也是全称否定 →
> 改为**写明检索范围**（`outputs/` 按文件名 `env|version|meta|fingerprint` 递归 **0 命中**；
> 13 个 full-FT 归档 JSON 按 `torch|cudnn|version|fingerprint|transformers` **0 命中**），
> 结论限定在该范围内，成因仍 **undetermined**。
>
> ### ⭐ 建议立为项目规则
>
> > **凡要写全称否定（"无 X" / "不存在 X" / "从未 X"），必须先产出机器穷举产物**
> > （列表 / 计数 / 扫描范围与命中数），**且只有当该产物为空时才允许写**。
> > 人工"我看过了"不构成依据。
>
> **依据（本阶段同类错误三次）**：
> ① 我写"88 of 94 无归档" → 实际**有**（`monitor_dg_check2.json::rules.R1`，我当时只搜了英文词，而 key 是中文）
> ② 我写"`tab:position_strict` 2 格 R@1 在归档中无来源" → 实际是**评测抽样差异**（且另一格是 provenance 混用）
> ③ 成员写"No interior minimum" → 实际**有一处**（`3e-07`）
> **三次都因"未穷举就下全称否定"**。
>
> ### 我本阶段自己的第 13 个错（同类）
>
> `_p406` 的禁语检查把 `related_work.tex` 里的 `$R^2=0.986$` 误报为违规——
> **那是 `\cite{liu2026tpc}` 的他人数值**（"Per-sample cosine distances … predict … ($R^2=0.986$)
> \cite{liu2026tpc}"），**正确引用**。已把判据限定为**仅查我们自己的 `main*.tex`**。
> 另：`_p405` 用 `interior_minima` 当检查串，而 T7 里写的是英文散文
> "*interior minimum exists (checked point by point, not asserted)…*" → **假阴性**。
> **又是"检查串太窄/太宽"**——与上一条同源。
>
> ### 全部交付件（21 项，门禁已核存在）
>
> **报告**：`docs/PR_STATS_FIX.md`｜`PR_CAUSAL_FIX.md`｜`PR_FAIRNESS_FIX.md`｜`PR_FAIRNESS_FIX2.md`
> ｜`PR_FAIRNESS_FIX3.md`｜`PR_WRITING_FIX.md`｜`PR_MORE_MODELS.md`｜`DINOV2_AUDIT.md`
> **归档**：`pr_stats_hardened.json`｜`pr_relative_perturbation.json`｜`pr_fullft_lr_sweep_full.json`
> ｜`pr_peft_lr_sweep.json`｜`pr_adapter_init_check.json`｜`dinov2_hetero/fitted/both/seed42/results.json`
> ｜`dinov2_hetero/random/text_only/seed42/results.json`｜`gallery_noise_cg.json`｜`final_gate.json`
> **投稿包**：`SUBMISSION/README.md`｜`A1_NeuralNetworks/README.md`｜`_old/README.md`
> **交接**：`HANDOFF.md`｜`文件地图.md`
>
> ### 稿件与投稿
>
> - **`paper合`（Paper A）**：NC **63 页** / Springer **45 页**，0 错 0 未定义 0 Overfull；
>   PR 对 P1 的全部意见已改入；**从未投稿**
> - **A1**：✅ **已投 Neural Networks `NEUNET-D-26-09426`**（Article；Section/Category =
>   **Mathematical and Computational Analysis**；12 October 2026）
> - **P3** `PRLETTERS-D-26-02378` 在审｜**综述** `PRLETTERS-D-26-02402` 在审｜**A23** `26-0663` Received
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
    if "最终门禁 `tools/_p406_final_gate.py` 全绿" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("最终门禁", "interior_minima_note", "NEUNET-D-26-09426", "449", "21/21"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
