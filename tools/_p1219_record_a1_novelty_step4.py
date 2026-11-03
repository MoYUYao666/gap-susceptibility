# -*- coding: utf-8 -*-
r"""Record A1 novelty step 4: SigLIP path repaired, three-architecture replication written into the paper.

    python tools/_p1219_record_a1_novelty_step4.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

APPEND = """

---

# 第 4 步（2026-10-18 13:40）：修好 SigLIP，跨模型复现补齐到三个骨干

**根因**：SigLIP 的文本塔必须按训练时的 `max_length=64` 做 padding。用默认 `padding=True`（按最长样本）时，
pooled 输出不是训练时的那个位置 ⇒ zero-shot 基线塌到 **1.86%**（500 图探针甚至 0%）；改成
`padding="max_length", truncation=True, max_length=64` 后基线恢复 **72.8%/73.3%**。

**三骨干结果（ImageNet-5k，1000 类，冻结模型）**：

| 模型 | frozen CG / top-1 | 类收缩 a=0.5：CG / top-1 | 变化 | 回程反例（λ=0.5 vs λ=2）|
|---|---|---|---|---|
| CLIP ViT-B/32 | 0.855 / 59.1% | 0.897 / 78.1% | **+19.0** | ΔCG 0.028 → 32.7 点 |
| OpenCLIP laion2B | 0.791 / 62.4% | 1.187 / 81.8% | **+19.4** | ΔCG 0.066 → 27.1 点 |
| SigLIP base-p16-224 | 1.116 / 73.3% | 1.168 / 88.3% | **+15.0** | ΔCG 0.197 → 27.1 点 |

**结论（已写入正文 5.2 节）**：类收缩的"**gap 更大、准确率更高**"方向反转在**三个架构上都复现**（+19.0/+19.4/+15.0）；
回程分支的塌缩也在三者上出现，但 SigLIP/OpenCLIP 需要更大的 ΔCG 才显现（都是 27.1 点，ΔCG 0.197 vs 0.066）。

**⚠️ 为后续复用记录**：SigLIP 文本塔必须 `padding="max_length", max_length=64`；否则 zero-shot 基线会假性塌陷。
"""

ENT = """> **🧪 2026-10-18 13:40 —— A1 第 4 步：SigLIP 修好，跨模型复现补齐到三骨干**
>
> 根因：SigLIP 文本塔需 `padding="max_length", max_length=64`（默认 padding 使基线假塌到 1.86%）。修好后：
>
> | 模型 | frozen CG / top-1 | 类收缩 a=0.5 | 变化 | 回程反例 |
> |---|---|---|---|---|
> | CLIP B/32 | 0.855 / 59.1% | 0.897 / 78.1% | **+19.0** | ΔCG 0.028 → 32.7 点 |
> | OpenCLIP laion2B | 0.791 / 62.4% | 1.187 / 81.8% | **+19.4** | ΔCG 0.066 → 27.1 点 |
> | SigLIP base-p16 | 1.116 / 73.3% | 1.168 / 88.3% | **+15.0** | ΔCG 0.197 → 27.1 点 |
>
> **"gap 更大、准确率更高"的方向反转在三个架构上全部复现**；回程塌缩三者皆有（都 27.1 点，SigLIP 需更大 ΔCG）。
> 已写入 A1 §5.2；A1 编译 **45 页**、0/0/0。归档 `a1_matched_gap_crossmodel.json`（3 模型）；脚本 `_p1214`（已修）/`_p1217`（诊断）/`_p1218b`（入稿）。
> ⚠️ 复用提醒：SigLIP 必须 `padding="max_length", max_length=64`。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    d = io.open(DOC, encoding="utf-8").read()
    if "第 4 步（2026-10-18" not in d:
        io.open(DOC, "w", encoding="utf-8", newline="").write(d.rstrip("\n") + APPEND)
        print("  doc updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "A1 第 4 步" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("69. 🧪 **A1 第 4 步：SigLIP 修好、跨模型复现补齐三骨干（2026-10-18 13:40）** —— SigLIP 文本塔须 "
           "`padding=max_length/64`（否则基线假塌 1.86%）；修好后 SigLIP frozen 73.3%、类收缩 88.3%（+15.0）。"
           "三骨干方向反转：CLIP +19.0 / OpenCLIP +19.4 / SigLIP +15.0；回程塌缩三者皆有（均 27.1 点）。"
           "已写入 A1 §5.2，编译 45 页 0/0/0。\n")
    if "A1 第 4 步" not in m:
        anchor = "68. 🧪 **A1 新颖性第 3 步"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
