# -*- coding: utf-8 -*-
r"""落账：DINOv2 审计完成 + 编号重号已消解（2026-10-12）。

    python tools\_p392_record_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""**审计交付**：`docs/DINOV2_AUDIT.md`（47.8 KB，9 节）｜脚本 `tools/_p357`(rev-2)、`_p357a`、
`_p360_gallery_noise`、`_p361_protocol_facts`、`_p362_clip_api_check`、`_p363_logit_scale_provenance`、
`_p364_pristine_clip_provenance`、`_p365_lora_update_norms`、`_p366_gallery_noise_fix`、
`_p367_r1_discrepancies`、`_p368_checkpoint_epochs`、`_p369_reproduce_clip_arm_r1`、
`_p370_vision_only_checkpoint_identity`

**一、−0.3913 的判定：数字可靠，问题在「不可比」**

| 假设 | 判定 | 关键数字（我已独立复核归档） |
|---|---|---|
| 归一化错配导致 −0.39 | **不成立** | frozen CG 0.6769→0.6785（**+0.24%**）；成对 ΔCG 只变 ≤0.0025 |
| −0.39 是噪声 | **不成立** | 抽样 sd(ΔCG) = **0.0003–0.0007**（四臂 × 12 次）；归档被独立复现到 **0.0002–0.0004** |
| 头+文本侧联合漂移 | ΔCG **100% 来自文本侧**（构造性）；**头的作用未定**（随机头对照未跑，头 656,384 参数 > 适配器） | — |

**真正缺陷**：异质配对、无随机头对照、**损失温度差 7×**、初始 R@1 只有论文骨干一半（0.289 vs 0.577）、n=1。

**二、折算到论文量级（核心答案）**

| 量 | 抽样 sd（四臂 × 12 draws，`gallery_noise/results_corrected.json`） | vs 论文臂间差异 |
|---|---|---|
| **ΔCG** | **0.00045–0.00070** | 臂间间隔 **0.0207/0.0364** 的 **1.5%–3%** → **低 1–2 个数量级，ΔCG 排序稳健** ✅ |
| **R@1** | **0.00550–0.00777**（极差 0.017–0.025） | 与单 run 同量级 → "text_only 检索最差"（0.069）稳；**"both > vision_only"（0.013）只 1.7–2.4σ ⇒ 边缘** |

**三、比 DINOv2 更重要的发现：归档单 run R@1 复现不出**

用**论文自己的 loader + 论文自己的指标函数**（未改一行）复评归档 checkpoint：

| 臂 | 复评（4 次） | 归档 | 差 |
|---|---|---|---|
| text_only | 0.6198 | 0.6180 | +0.0017 |
| both | 0.6925 | 0.6890 | +0.0035 |
| **vision_only** | **0.6790**（0.682/0.675/0.681/0.678） | **0.7000** | **−0.0210** 🔴 |

且 `vision_only/seed42` 的 **0.7000 是该组 5 个 seed（0.671–0.700，均值 0.6800）中最高的单次抽样**
（我已核 `outputs/strict_freeze/vision_only/seed*/results.json`）。
→ **归档的 run 级 R@1 是单次随机抽样，偏移可达 ~0.02**——**这是 R1.1/R3.1 的机制解释**。
成因**未定**（已排除 seed、权重 epoch、指标代码）。

**四、我据此更正了自己的一处分类错误**

我先前把 `tab:position_strict` 的**全部 6 格** R@1 差异都归入"抽样噪声"。
**错**：最大那格 **OpenCLIP r4 text_only（0.643 vs 0.6366 = 0.0064）是 provenance 混用**
（R@1 取自 rank-8 树、ΔCG 取自 rank-4 树）——**这正是我自己的 `_p325` 查明的**，
我却在改 caption 时把它一并归为噪声。**已分开写**（`tools/_p389`）：
- **5 格 ≤0.0022** → 抽样噪声（符合审计预期 |Δ|≈0.004）
- **1 格 0.0064** → provenance 混用，**须改稿而非改口径**

**五、并入稿件的三条**

1. `tab:position_strict` caption：区分 provenance 与噪声；**并记录 `vision_only` 那格复现不出**
   （0.675–0.682 vs 归档 0.700，为 5 seed 中最高抽样）
2. `discussion.tex` Twelfth limitation：补**"both vs vision_only 的 0.013 不成立为排序、
   应报为未决"**（1.7–2.4σ 单次 / ~1.5σ 对论文自身 seed-sd）
3. **不改论文数字**——问题在"该列应读作一次抽样"而非数值错误

**六、编号重号已消解（审计指出的真问题）**

隔离并行开发使 `_p360`–`_p370` 段相撞（**11 个编号各有两个不同脚本**）→ 违反
"每个数字必须能指名**唯一**产出脚本"。**已把我的 11 个重命名到 `_p380`–`_p390`**，
并**同步脚本内自指与产出 JSON 的 `script` 字段**（脚本内改 9 个、JSON 改 3 个）：

| 旧（我的） | 新 |
|---|---|
| `_p360_eval_paths` | `_p380_eval_paths` |
| `_p361_record_gallery_noise` | `_p381_record_gallery_noise` |
| `_p362_verify_bioclip_initcg` | `_p382_verify_bioclip_initcg` |
| `_p363_gallery_noise_cg` | `_p383_gallery_noise_cg` |
| `_p364_record_gallery_verdict` | `_p384_record_gallery_verdict` |
| `_p365_fix_caption_and_limitation` | `_p385_fix_caption_and_limitation` |
| `_p366_verify_logit_scale` | `_p386_verify_logit_scale` |
| `_p367_logit_scale_in_archive` | `_p387_logit_scale_in_archive` |
| `_p368_record_logit_scale` | `_p388_record_logit_scale` |
| `_p369_update_noise_numbers` | `_p389_update_noise_numbers` |
| `_p370_record_a1_submitted` | `_p390_record_a1_submitted` |

**保留队友的** `_p360_gallery_noise`、`_p361_protocol_facts`、`_p362_clip_api_check`、
`_p363_logit_scale_provenance`、`_p364_pristine_clip_provenance`、`_p365_lora_update_norms`、
`_p366_gallery_noise_fix`、`_p367_r1_discrepancies`、`_p368_checkpoint_epochs`、
`_p369_reproduce_clip_arm_r1`、`_p370_vision_only_checkpoint_identity`。

**遗留**：`_p1*`/`_p3*`/`_p4*`/`_p20*` 等**更早会话**的历史重号仍在（不在本次范围），
已记入待办。
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
    if "DINOv2 审计完成" in t and "_p380_eval_paths" in t:
        print("  已记录")
        return 0
    ent = ("> **🔬 2026-10-12（续）—— DINOv2 审计完成（`docs/DINOV2_AUDIT.md`，47.8 KB）："
           "数字可靠但**不可比**；并查出归档 R@1 复现不出的一格**\n>\n")
    for line in ENT.splitlines():
        ent += "> " + line + "\n" if line.strip() else ">\n"
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ent + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("DINOv2 审计完成", "-0.0210", "_p380_eval_paths", "0.00045–0.00070"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
