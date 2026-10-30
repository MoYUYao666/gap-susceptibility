# -*- coding: utf-8 -*-
r"""落账：选项 B（按归档改正 ODE 数字）完成（2026-10-07）。

    python tools\_docs_ode_correction.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **🛠️ 2026-10-07 深夜 —— 选项 B 完成：按归档**改正 ODE 数字**（操作者决定）**
>
> **交付件**：`paper合/`（NC **50 页** / Springer **37 页**，0 错误、0 未定义引用）；
> 台账 `outputs/analysis/ode_ledger.json`（`tools/_p1_ledger.py`）。
>
> ### 改了什么（**逐 run 口径**，与正文 `±` 表一致）
>
> | 项 | 原 | 现 | 依据 |
> |---|---|---|---|
> | LoRA 总 R² | 0.986（0.978–0.997） | **0.949**（0.814–0.977） | 55 runs |
> | Flickr30k LoRA | 0.985 ± 0.008（81 runs） | **0.953 ± 0.014**（**43** runs） | 台账 |
> | MS-COCO LoRA | 0.971 ± 0.007（81 runs） | **0.903 ± 0.054**（**6** runs） | 台账 |
> | 逐秩 R² | 0.975–0.991 | **0.937–0.964**（14 格全部对齐台账） | 台账 |
> | 实验总数 | 162（81/数据集） | **55**（43+6） | 归档 |
>
> ### **未改**（**能复现，正文原本正确**）
>
> | 项 | 正文 | 实测 | 结论 |
> |---|---|---|---|
> | OpenCLIP BitFit | 0.943 ± 0.041 | **0.9428** | ✅ 正确 |
> | CLIP BitFit 边界 | 0.30–0.84 | **0.298–0.843** | ✅ 正确 |
>
> ### 新增 limitation（**关键：只改数字不说明原因不可接受**）
>
> `discussion.tex` Limitations 新增第四、五条：
> 1. **α、β 是逐 run 拟合的**，不是从梯度预测的；梯度流恒等式**另有直接验证**，
>    故 R² 衡量"函数形式是否足够"，**不等于**"系数可事先算出"；
> 2. 本文分析的轨迹是**原 rank sweep 的子集**：**55 条 LoRA run 已归档**（43 Flickr30k、6 COCO），
>    每配置 3 seeds，而原 sweep 为 5 seeds；补充表另有说明。
>
> ### 措辞收紧
>
> 摘要与结论的 `predicts trajectories` → **`reproduces trajectories`**（拟合口径下更准确）。
> 摘要因增补涨到 255 词 → **压回 241 词**（限 250）。
>
> ### ⚠️ 两项**故意未动**（改了会构成编造）
>
> | 项 | 原因 |
> |---|---|
> | `supplement` 的 **COCO 逐配置表**（14 行，81 runs） | 本地归档仅 **3 配置 × 3 seeds = 9 runs** → **无法复现**；已在 limitation 中说明该表源自更大的 run 集 |
> | `26 configurations` 的表述 | 本地按（数据集×位置×秩）计为 **18** → **待核**，本轮只改 R² |
>
> ### 校验
>
> 一致性校验器 `tools/_pa_ode_consistency.py`（**自动按语境分类**）：
> **需处理 0 处**；`0.986` 剩 1 处 = **他人工作**（Liu et al.）；`0.984` 剩 2 处 = **COCO 表**；
> `162` 剩 3 处 = **arXiv 编号 `2604.16256`**（2）+ COCO 表（1）。
> 新值在位：0.949×8、0.953×4、0.903×3、`55 archived`×3；逐秩 **14/14** 命中。
>
> ### ⏳ 另一项实验仍在跑
>
> `tools/_p2_alpha_from_gradients.py`（从梯度预测 α）**11/90 epoch**，约 3.5 min/epoch
> → **预计还需约 4.5 小时**。该实验**不依赖归档完整性**，结论独立成立。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "选项 B 完成：按归档" in h:
        print("  已记录，跳过")
        return 0
    anchor = "> **🔬 2026-10-07 —— 拟合 vs 预测核查"
    i = h.find(anchor)
    assert i > 0, "未找到 HANDOFF 锚点"
    io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ENT + "\n" + h[i:])
    h2 = io.open(hp, encoding="utf-8").read()
    for k in ("0.949", "43", "OpenCLIP BitFit", "逐 run 拟合", "2604.16256", "4.5 小时"):
        assert k in h2, f"HANDOFF 断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")

    fp = REPO / "文件地图.md"
    t = io.open(fp, encoding="utf-8").read()
    old = ("0a. 🔴 **Paper A 归档完整性问题（2026-10-07 发现）**")
    if old in t and "已于同日按选项 B 处置" not in t:
        t = t.replace(old, ("0a. ✅ **Paper A 归档完整性问题 —— 已于同日按选项 B 处置**（操作者决定）\n"
                            "   **已按归档改正正文 ODE 数字**：LoRA R² **0.986 → 0.949**、"
                            "Flickr30k **0.985 → 0.953**（81→**43** runs）、COCO **0.971 → 0.903**（81→**6** runs）、"
                            "逐秩 0.975–0.991 → **0.937–0.964**；**并新增 limitation** 说明"
                            "（α/β 为逐 run 拟合、分析集为原 sweep 子集）。\n"
                            "   **未动**：OpenCLIP BitFit 0.943 与 CLIP BitFit 0.30–0.84（**实测可复现**）；"
                            "**COCO 逐配置表**（本地仅 3 配置×3 seed，无法复现 → 仅在 limitation 说明）。\n"
                            "   脚本 `tools/_pa_align_ode_numbers{,2,3}.py`、`_pa_ode_limitation{,2}.py`；"
                            "校验 `tools/_pa_ode_consistency.py`（需处理 0 处）。\n"
                            "   ~~原记：正文称 162 runs 而归档仅 96；复现不出 0.985–0.986~~\n"
                            "   正文现 **NC 50 页 / Springer 37 页**，0 错误、0 未定义引用。\n"), 1)
        io.open(fp, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(fp, encoding="utf-8").read()
        assert "已于同日按选项 B 处置" in t2 and "原记：" in t2
        print(f"  ✅ 文件地图.md 待办 0a 已更新（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
