# -*- coding: utf-8 -*-
r"""记录 2026-10-04 下午阶段：k 修正 + 跨骨干 rank 确认 + 一次自我更正（阶段收尾）。

    python tools\_docs_20261004_pm.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **✏️ 2026-10-04 下午 —— 修 `k=0.043`（5 处清零）+ 写入跨骨干 rank 确认 + **一次自我更正****
>
> ### ① `k = 0.043` 全部清除（正文 + 图注 + 引言 + 理论，共 5 处）
>
> 依据 `docs/K043_INVESTIGATION.md` 的最终结论（both 臂，严格冻结，3 seeds/rank，$r\in[1,64]$）：
>
> | 改写前 | 改写后 |
> |---|---|
> | "$\|g_v\|$ is flat across $r\in[1,64]$, with slope $k=0.043$" | "restricted to a $10\%$ band across $r\in[1,64]$ (means $12.75$--$14.09$), where $\|g_v\|\propto\sqrt r$ would predict an eightfold change" |
>
> **理由**：$k=0.043$ 无法复现（线性拟合 0.257），且**相邻区间局部斜率 −0.20/+0.89/−0.35/+1.39/−0.40 正负交替**
> → 无可辨趋势，报斜率是把噪声当信号。
>
> 脚本 `tools/_pa_fix_k_slope.py`（正文 2 处）、`tools/_pa_fix_k_slope2.py`（其余 4 处，含 2 处图注）。
> **已验证未误伤** `empirical.tex:77` 的 MS-COCO 数值 `$-0.043$`（那是数据，不是斜率）。
>
> ### ② 跨骨干 rank 确认写入正文
>
> **CLIP 完整 rank sweep**（严格冻结，text_only）：
>
> | rank | 1 | 4 | 8 | 16 | 32 | 64 |
> |---|---|---|---|---|---|---|
> | $\Delta$CG | −0.0091 | −0.0285 | −0.0465 | −0.0598 | −0.0754 | −0.0754 |
> | $R@1$ | 0.614 | 0.618 | 0.624 | 0.628 | 0.633 | 0.639 |
>
> **单调递减**（rank 越高降间隙越多），$r{=}32$ 后饱和。**both 臂则非单调**（U 形，$r{=}64$ 转正 +0.0179）。
>
> **SigLIP 确认**（text_only，r4 vs r8，5 个配对 seed）：差 **+0.0166 ± 0.0098**，**配对 t = +3.79**，5/5 同向；
> CLIP 同口径 **+0.0192**，**t = +7.96** → **两骨干方向一致** ⇒ **「rank 效应的方向依赖训练约定」这一结论跨骨干成立**。
>
> ### ③ ⚠️ 一次自我更正（**我的误读，未写进稿件**）
>
> 我中途看到 SigLIP r4（+0.0831）高于 r8（+0.0664），而 CLIP r4（−0.0285）高于 r8（−0.0465），
> 便断言"**rank 方向依骨干反转**"。**配对检验推翻了这个说法**：
>
> - CLIP：$r4 \to r8$ 差 **+0.0192**（r8 更负）
> - SigLIP：$r4 \to r8$ 差 **+0.0166**（r8 更负）
> - **两者方向相同**——我把"更负"与"更小"误读成了不同方向。
>
> **该错误只存在于对话中，未写入任何文档或稿件**（正文当时只写了 protocol-dependent，没有 backbone）。
> **教训**：① 不用两个点下结论；② 比较"更负/更小"时要统一成同一口径再看符号。
>
> ### ④ 编译与合规
>
> NC 版 **41 页**、Springer 版 **31 页**、**0 错误 / 0 未定义引用**、cites 41 / bib 41 全匹配。
>
> ### ⑤ 打断的实验（操作者要求终止，晚上再跑）
>
> | 实验 | 断点 |
> |---|---|
> | SigLIP r4 text_only | ✅ **5/5**（已入正文） |
> | SigLIP r4 both | **1/5**（seed42 完成；seed123 为残缺目录，无 `results.json`，续跑会重跑） |
> | OpenCLIP r4 | **1/10**（seed42/text_only 完成） |
>
> **续跑命令（幂等）**：
> ```powershell
> python tools\_run_siglip_r4.py --apply          # 补 SigLIP both 剩余 4 个
> python tools\_run_remaining_steps.py --apply    # 或整链续跑（会跳过已完成的）
> ```
>
> ### ⑥ 本轮另修的脚本缺陷
>
> **`siglip_experiments.py` 的 ✅/❌ 判据会误导**：原文 `marker = "✅" if delta < 0 else ... "❌"`
> —— 把"**间隙增大**"标成失败，而本项目的核心发现恰是"**降间隙 ≠ 提检索**"
> （OpenCLIP 上 both 的间隙更大、检索却更强）。操作者据此提问，说明确会误导。
> 已改为中性报告：`[gap ↓/= /↑] ... (run completed)`。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "HANDOFF.md"
    t = io.open(p, encoding="utf-8").read()
    if "2026-10-04 下午 —— 修 `k=0.043`" in t:
        print("  已记录，跳过")
        return 0
    anchor = "> **🔧 2026-10-04 上午"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("5 处清零", "+3.79", "自我更正", "run completed"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
