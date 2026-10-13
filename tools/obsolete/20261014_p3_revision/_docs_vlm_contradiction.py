# -*- coding: utf-8 -*-
r"""落账：解码器 VLM 的多种子结果**推翻了论文的单 seed 排序**（2026-10-10）。

    python tools\_docs_vlm_contradiction.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴 2026-10-10 —— 解码器 VLM 的 3-seed 结果**推翻了论文基于单 seed 的排序**（待操作者定处置）**
>
> ### 一、跑完了：bf16、3 seed、9/9 成功
>
> `tools/_p156_vlm_bf16_seeds.py`｜配置 `400 样本 / 3 epoch / batch 2`（bf16）｜
> 输出 `outputs/vlm_seeds_bf16/`｜结论 `outputs/analysis/vlm_bf16_seeds_verdict.json`
>
> | 臂 | n | CG 跨度（mean ± sd） | 逐 seed |
> |---|---|---|---|
> | `text_only` | 3 | **0.2053 ± 0.1505** | 0.110 / 0.127 / **0.379** |
> | `vision_only` | 3 | **0.3421 ± 0.0644** | 0.415 / 0.319 / 0.293 |
> | `both` | 3 | **0.3595 ± 0.2352** | 0.224 / 0.224 / **0.631** |
>
> | 比较 | 效应量 | 判定 |
> |---|---|---|
> | `text_only` vs `vision_only` | **0.84 sd** | 🔴 不显著 |
> | `vision_only` vs `both` | **0.07 sd** | 🔴 不显著 |
>
> ### 二、论文现在的主张（**`discussion.tex`**）
>
> > *"adapting the vision tower alone is again **the least effective choice**, moving the gap by
> > $11\\%$ where the other two arms move it by $74\\%$ and $84\\%$ … on this model the
> > **both-position arm reduces the gap most**"*
>
> **出处**：`supplement.tex` 的 `tab:vlm`（论文自己标注 **four-bit quantisation, one seed**）
>
> ### 三、**两条主张都不成立**（3-seed 实测）
>
> | 论文主张 | 实测 |
> |---|---|
> | `vision_only` 最差（11% vs 74%/84%） | ❌ `vision_only` 排**中间**（CG 0.342） |
> | `both` 减得最多 | ❌ `both` 排**最差**（CG 0.360） |
> | 三臂差异显著 | ❌ 全部不显著（0.84 / 0.07 sd） |
>
> **根因**：**单 seed + 巨大种子波动**（`both` 0.224 → 0.631，**2.8 倍**；`text_only` 0.110 → 0.379，**3.4 倍**）。
> **排序随 seed 数量改变**：1 seed → `both` 最好；2 seed → `both` 仍好；**3 seed → `both` 最差**。
>
> ### 四、附带查出论文一处**不准确的表述**
>
> 论文写：*"at bfloat16 the vision-only arm had **not completed a single epoch after $27$ minutes**
> … whereas at four-bit the same arm completes three epochs in $5.4$ minutes"*。
>
> **实测：bf16 下 `vision_only` 三 epoch 只要 216–328 s（batch 2）** → **bf16 是可行的**，
> 那句是 **batch 4 的 OOM 重试**结果，但写在 batch 4 语境里会让读者理解成"bf16 不可行"。
>
> ### 五、连带发现（**更重要**）
>
> **4-bit 路径不可逐位复现**（`bitsandbytes` NF4）：
>
> | 精度 | 同 seed 两次 | 可复现 |
> |---|---|---|
> | **bf16** | `0.110064` / `0.110064` | ✅ 是 |
> | **4-bit** | 0.3041 / 0.4073 | ❌ 否 |
>
> **所以论文 `tab:vlm` 的 4-bit 单 seed 数字，本身不可被任何人逐位重放。**
>
> ### 六、待操作者定（**两个选项**）
>
> | 选项 | 做法 | 代价 |
> |---|---|---|
> | **A（我建议）** | **把 `tab:vlm` 换成 3-seed bf16 的结果**；正文改为"**在解码器 VLM 上三臂差异不显著**，故**位置排序不迁移**"，并**如实写明 4-bit 不可复现** | 该节结论从"支持"变"不确定"，但**站得住** |
> | **B** | **删掉解码器 VLM 这一节**（连同正文那句），把 scope 收回到双塔编码器 | 失去"跨架构"的卖点；但**limitation 已写了只覆盖双塔**，收回去是自洽的 |
>
> **我不建议**保留现有单 seed 排序——**因为 3 seed 就翻转了，审稿人一问就散。**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "推翻了论文基于单 seed 的排序" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("推翻了论文基于单 seed 的排序", "0.2053", "0.3595", "0.84 sd",
              "0.224 → 0.631", "216–328 s", "逐位重放", "待操作者定"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
