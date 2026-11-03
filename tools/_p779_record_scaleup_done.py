# -*- coding: utf-8 -*-
r"""Record the completed large-scale COCO result.

    python tools/_p779_record_scaleup_done.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔬 2026-10-15 14:00 —— 规模跑完成（7 个 run）：**COCO 上没有 text-only 优势**，且冻结基线已接近天花板**
>
> ### 一、配置（可复跑：`tools/_p754_coco_scaleup.py`）
>
> COCO **train2014 10,000 唯一图 / 50,020 行** 训练；**val2014 3,000 唯一图 / 15,010 行** 评测
> （**断言不相交**）；3 epoch / batch 64 / **rank 8 / lr 1e-5 / dropout 0**；**修正检索协议**（唯一图 gallery，图↔其自身全部 caption）。
>
> ### 二、✅ 全部结果（`outputs/analysis/coco_scaleup.json`）
>
> | run | R@1 | R@5 | R@10 | i2t R@1 | t2i R@1 |
> |---|---|---|---|---|---|
> | `frozen` s42 | 0.5794 | 0.7300 | 0.7865 | 0.9157 | 0.2431 |
> | `text_only` s42 | 0.6179 | 0.7775 | 0.8339 | 0.9293 | 0.3065 |
> | `text_only` s43 | 0.6218 | 0.7791 | 0.8332 | 0.9380 | 0.3056 |
> | `text_only` s44 | 0.6174 | 0.7774 | 0.8331 | 0.9300 | 0.3047 |
> | `both` s42 | 0.6241 | 0.7778 | 0.8329 | 0.9367 | 0.3115 |
> | `both` s43 | 0.6206 | 0.7764 | 0.8316 | 0.9343 | 0.3069 |
> | `both` s44 | 0.6244 | 0.7776 | 0.8327 | 0.9370 | 0.3117 |
>
> **按臂汇总**：
>
> | arm | n | R@1 | i2t R@1 | t2i R@1 |
> |---|---|---|---|---|
> | frozen | 1 | 0.5794 | 0.9157 | 0.2431 |
> | **text_only** | 3 | **0.6190 ± 0.0024** | 0.9324 ± 0.0048 | 0.3056 ± 0.0009 |
> | **both** | 3 | **0.6230 ± 0.0021** | 0.9360 ± 0.0015 | 0.3100 ± 0.0028 |
>
> ### 三、🔴 核心结论（**与"text-only 优势"相反**）
>
> 1. **`text_only` 与 `both` 统计上不可区分**：R@1 差 **0.0040**（各自 sd ≈ 0.002）；i2t 差 0.0036（sd 0.0048 vs 0.0015，**区间重叠**）⇒ **在 COCO 上分不出适应位置的优势**；
> 2. **两者的 t2i 都优于 frozen**（0.31 vs 0.243），i2t 略优（0.936 vs 0.916）⇒ **微调确实有效，但哪个位置无关**；
> 3. **冻结基线已接近天花板**（i2t 0.9157）⇒ 在此协议下**提升空间本就很小**，"位置效应"没有可表现的余地。
>
> **⚠️ 诚实标注**：**这不证明位置效应不存在** —— 它证明的是**这套协议/指标（检索 R@1）上分不出位置差异**。
> 稿件的位置结论建立在 **gap / 对齐能量**上，而非检索精度（稿件自己也说"更小的 gap 与更好的检索不是同一目标"）。
>
> ### 四、✅ 对 Paper A 的直接价值
>
> | 稿件内容 | 本结果的判定 |
> |---|---|
> | **COCO `R@1 < 0.001`（near-random）** | 🔴 **被推翻**：冻结基线 i2t = **0.9157**、微调 **0.9360**；`R@1` 合并口径 0.58–0.62 |
> | "COCO cross-dataset validation" 支撑跨数据集泛化 | 🟡 **可支撑"微调有效"**，**但不能支撑"text-only 优于 both"** |
> | 审稿人 R1-W4 的怀疑 | ✅ **完全成立**（协议错、规模只有 1/5、train/val 同源）|
>
> ### 五、📁 产出
>
> | 文件 | 内容 |
> |---|---|
> | `outputs/scaleup_coco/*.json`（7 个） | 每个 run 的完整指标 |
> | `outputs/analysis/coco_scaleup.json` | 汇总（config + 7 runs） |
> | `tools/_p754_coco_scaleup.py` | 可复跑脚本（含 resume：已完成的 run 自动跳过） |
> | `tools/_p760_loop_measure.py` | 逐例循环的权威测量 |
>
> ### 六、⚠️ 已知局限
>
> 1. **只跑到 3 epoch / rank 8**：未做 rank 扫描，故**未测"位置×rank"交互**；
> 2. **frozen 只有 1 个 seed**（确定性，无方差）；
> 3. **i2t ≈ 0.93 偏高**：gallery 只有 3,000 图且 caption 属批量采样，与标准 5k 协议不完全可比 ⇒ **引用时必须写明 gallery 规模**；
> 4. **t2i 明显低于 i2t**（0.31 vs 0.93）：与标准 COCO 协议下两者应接近的预期不符，**原因未查明**，**引用前需先解释**。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "COCO 上没有 text-only 优势" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("COCO 上没有 text-only 优势", "0.6190", "0.6230", "0.9157", "原因未查明"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
