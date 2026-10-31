# -*- coding: utf-8 -*-
r"""记录 2026-10-05 凌晨阶段：OpenCLIP r4 完成 + **我在同一问题上三次快速断言的更正**。

    python tools\_docs_20261005_am.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **🔬 2026-10-05 凌晨 —— OpenCLIP r4 完成；**我在同一问题上三次快速断言、三次更正****
>
> ### ① 实验全部完成
>
> | 实验 | 结果 |
> |---|---|
> | SigLIP r4 | ✅ **10/10**（text_only 5 + both 5） |
> | OpenCLIP r4 | ✅ **10/10**（text_only 5 + both 5） |
>
> ### ② 权威分析已固化为脚本：`tools/_pa_rank_analysis.py`
>
> 因为我在这个主题上**三次凭快速阅读下结论、三次都错**（其中一次写进了正文），
> 故把分析**完全交给代码**：所有数字由脚本算出，每个断言由配对检验支撑，不再手工读。
>
> **rank 方向（r8 − r4，配对检验，全部严格冻结）**：
>
> | 骨干 | 臂 | 平均差 | t | 方向 |
> |---|---|---|---|---|
> | CLIP | text_only | −0.0192 | **−7.96** | r8 更小 |
> | CLIP | both | −0.0065 | **−2.88** | r8 更小 |
> | OpenCLIP | text_only | −0.0112 | **−5.86** | r8 更小 |
> | **OpenCLIP** | **both** | **+0.0042** | **+1.09** | r8 更大（**不显著**） |
> | SigLIP | text_only | −0.0166 | **−3.79** | r8 更小 |
> | SigLIP | both | −0.0204 | **−2.57** | r8 更小 |
>
> → **5/6 同向且显著，唯一例外不显著**。
>
> **位置排序（10 个骨干 × rank 组合）**：
>
> | 骨干 | 一致的倾向 | 组合数 |
> |---|---|---|
> | CLIP | `text_only` 的 ΔCG 更小 | **6/6** |
> | OpenCLIP | `text_only` 的 ΔCG 更小 | **2/2** |
> | **SigLIP** | **`both` 的 ΔCG 更小** | **2/2** |
>
> → **8/10 是 text_only，例外全部集中在 SigLIP** ⇒ **位置效应确实按骨干分组**。
>
> ### ③ ⚠️ 撤回：`16bb0f5` 写入正文的"rank 效应跨骨干成立"
>
> 该句写于**只有 CLIP 与 SigLIP 两个骨干**时（未做配对检验、未等 OpenCLIP）。OpenCLIP 跑完后被推翻。
>
> **已改为**（`tools/_pa_fix_crossbackbone_claim.py`）：
> "The direction is not specific to one backbone. Pairing rank 8 against rank 4 within seeds, the gap
> falls on CLIP at the text-only and both positions ($t=-8.0$ and $-2.9$) and on SigLIP likewise
> ($t=-3.8$ and $-2.6$); the exception is OpenCLIP at the both position, which moves the other way by
> $0.004$ and at $t=+1.1$ is not distinguishable from no change. **Five of six combinations therefore
> agree, and the dissenting one is the one that carries no significance.**"
>
> **设计模式①（位置）经核实与数据一致，未动**：CLIP 三臂 ΔCG 排序 `text_only < both < vision_only`，
> 检索排序 `both > vision_only > text_only`。
>
> ### ④ 三次错误断言的时间线（**供以后自查**）
>
> | # | 我说了什么 | 依据 | 错在哪 |
> |---|---|---|---|
> | 1 | "rank 方向依骨干**反转**"（CLIP 更负 vs SigLIP 更小） | 2 个点、手工读 | 把"更负"与"更小"当成不同方向 |
> | 2 | "方向**一致**，跨骨干成立" | 2 个骨干、无检验 | OpenCLIP 未跑就下概括 |
> | 3 | "OpenCLIP 在两个臂上都**与另外两个骨干相反**" | 手工比较 r4/r8 | 未做配对检验；其中 `both` 臂 t=+1.09 **不显著** |
>
> **共同根因**：**未等数据齐、未做检验、凭手工读数字下结论**。
> **对策（已执行）**：分析固化为 `tools/_pa_rank_analysis.py`，断言一律由配对检验给出。
>
> ### ⑤ 编译与合规
>
> NC 版 **41 页**、0 错误、0 未定义引用。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "HANDOFF.md"
    t = io.open(p, encoding="utf-8").read()
    if "2026-10-05 凌晨 —— OpenCLIP r4 完成" in t:
        print("  已记录，跳过")
        return 0
    anchor = "> **📮 2026-10-04 晚"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("三次快速断言", "t = +1.1", "8/10 是 text_only", "_pa_rank_analysis.py"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
