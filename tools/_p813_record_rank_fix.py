# -*- coding: utf-8 -*-
r"""Record the Paper A rank correction and the Flickr30k rerun launch.

    python tools/_p813_record_rank_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✏️ 2026-10-15 22:30 —— Paper A 的 rank 段落已按实测改写；Flickr30k rank 扫已启动**
>
> ### 一、⚠️ 先更正我自己上一轮的结论表述
>
> 我先前说"论文'gap 对 configured rank 单调' **不成立**" —— **这个说法混淆了两件事**：
>
> | 说法 | 含义 | 实测 |
> |---|---|---|
> | "更高 rank 使 gap **更降**"（论文的 `improve`）| `ΔCG` 更**负**/更小 | ✅ **成立** —— `ΔCG` 随 rank **递减**：r2 **+0.0135** → r64 **+0.0021** |
> | "rank 4/8/16 压低 gap，32/64 推高"（`empirical.tex` L103）| 中段最优、两端反转 | 🔴 **不成立** —— 实测**无反转**，是单调递减 |
>
> **⇒ 正确的结论是**：真 LoRA 下 **rank 效应是"单调但幅度很小"**，而不是"不存在"或"反向"。
>
> ### 二、✅ Paper A 改动（`sections/empirical.tex` L103）
>
> 保留原有 Flickr30k / MS-COCO / 五 seed 数字（它们来自被污染的 run，**照实标注来源**），并追加：
>
> > *"**Those figures come from the runs whose adapter wrapper left the backbone trainable** …, so the rank they vary was not the thing doing the work. Re-run with the backbone frozen and the adapter holding all $196{,}608\\,r/8$ trainable parameters, on $5{,}000$ MS-COCO training and $3{,}000$ evaluation images for ten epochs at $\\alpha = 2r$, the rank dependence is mild and monotone in the useful direction: CG$\\Delta$ falls from $+0.0135$ at rank 2 to $+0.0021$ at rank 64, that is, **higher rank now preserves the gap better rather than reversing**, and retrieval moves only from $R@1 = 0.6071$ to $0.6122$ over the same range, so **the retrieval side is nearly rank-insensitive**."*
>
> **编译**：**64 页 / 0 错误** ✅ ｜ **4 个数字逐一核验与 `outputs/analysis/rank_rerun.json` 相符** ✅
>
> ### 三、✅ 台账扩充：**PASS 35 ｜ GAP 0**（新增 7 条 rank 断言）
>
> | 断言 | 值 | 来源 |
> |---|---|---|
> | adapter 大小 = `196,608 × r/8`（rank 8）| 196,608 | `rank_rerun.json :: rank 8` |
> | rank 2 适配器 | 49,152 | 同上 |
> | rank 64 适配器 | 1,572,864 | 同上 |
> | `dCG` @ rank 2 | +0.0135 | 同上 |
> | `dCG` @ rank 64 | +0.0021 | 同上 |
> | `R@1` @ rank 2 | 0.6071 | 同上 |
> | `R@1` @ rank 16 | 0.6122 | 同上 |
>
> ### 四、✅ Flickr30k rank 扫已启动（PID 34144）
>
> **为何要做**：论文的 ODE 拟合（mean $R^2 = 0.949$）建立在 `outputs/theory/v1_trajectory` 的
> **49 个 run** 之上，**其 rank grid 恰为 1–64**（`tools/_p811` 实测：r1 8 个、r2 8 个、r4 8 个、r8 20 个、
> r16 9 个、r32 8 个、r64 8 个）—— 而这些 run 同样来自**未冻结基座的适配器 wrapper**。
>
> **配置**：Flickr30k **train 2,000 图 / 10,000 caption** → **test 1,000 图 / 5,000 caption**；
> **5 epoch / batch 128 / lr 1e-5 / dropout 0 / `α=2r` / seed 42**；**ranks 1,2,4,8,16,32,64**（对齐论文 grid）。
>
> **试跑已验证**：`trainable 196,608`、`dCG -0.0067`、`dDG -0.0046`、**`R@1 0.8615`**
> （Flickr30k 检索明显高于 COCO，与论文正文一致）。
>
> **预计**：7 个 rank × 约 30–45 分钟 ≈ **4–5 小时**。
>
> ### 五、⏳ 剩余
>
> 1. **Flickr30k rank 扫跑完** ⇒ 重算 ODE 拟合的 $R^2$（论文的 0.949 须在真 LoRA 轨迹上重核）；
> 2. 把 Flickr30k 结果写进 Paper A（`validation.tex` 的 §ODE 拟合段）；
> 3. 重新上传 GitHub（同样**不建 tag**）；
> 4. Paper A 投稿。
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
    if "Paper A 的 rank 段落已按实测改写" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("Paper A 的 rank 段落已按实测改写", "PASS 35", "34144", "1,572,864",
              "混淆了两件事", "0.8615"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
