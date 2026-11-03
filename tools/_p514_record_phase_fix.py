# -*- coding: utf-8 -*-
r"""落账：修 phase-transition 节内的旧主张 + 扫描判据补全（2026-10-13 17:00）。

    python tools\_p514_record_phase_fix.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴 2026-10-13 17:00 —— `Alignment Phase Transition` 节内**三处旧主张**（扫描器漏抓）+ experiments 已压至 27,856**
>
> ### 一、🔴 三处与已修订结论**直接冲突**的主张（我的扫描器**没抓到**）
>
> | 位置 | 旧主张 | 冲突对象 |
> |---|---|---|
> | `experiments.tex` **Finding 1** | *"LLaVA exhibits a **sharp phase transition** at $r_c\\in[5,6]$"* + *"**establishing** $r_c\\in[5,6]$ as a **statistically supported** transition"* | **同节稍后已改为** *"bracketed … **not a sharply localised one**"* |
> | **Finding 3** | *"This **explains** why the transition appears in LLaVA but not Qwen-VL: **architectural differences** … determine the critical threshold"* | **Finding 2 已撤回**架构依赖（54 token 下 Qwen 的 real 也转负） |
> | **图注** `fig:phase_transition` | *"critical rank $r_c \\in [5, 6]$ where $\\Delta E$ flips sign"* | 同上 |
>
> **⚠️ 扫描器漏抓的原因**：我用的是特征串 `sharp alignment phase transition` / `phase transition at`，
> 而这两处写的是 **`sharp phase transition`**（无 "alignment"）与 **`appears in LLaVA but not`**
> ⇒ **判据不全**。**已把 3 条新特征串补进 `_p497` 的规则表。**
> **⇒ 教训：特征串扫描的完备性取决于"旧主张有多少种措辞"，而措辞是随写作变化的。**
> **⇒ 与本轮"改了正文没改别处"同源 —— 扫描只能覆盖你想到的措辞。**
>
> ### 二、✅ 已修（`tools/_p513`）
>
> - **Finding 1** → 改为 *"the crossing, and how far we can localise it"*：
>   保留 ShareGPT $t=4.81$ / $p=0.011$、池化 LLaVA $t=4.65$ / $p=0.0014$、6/6 配置一致性 $p=2^{-5}\\approx0.031$，
>   **并明确：*"What we cannot do is place $r_c$ on a rank"*** ——
>   **三 seed 的 MDE 大于实测效应**、**精确置换 $p=0.100$** ⇒ *"the crossing is **bracketed**, and its location
>   is a property of the measurement protocol rather than a constant of the model."*
> - **Finding 3** → 改为 *"a mechanism we can state only as a hypothesis"*：
>   *"we were unable to confirm that prediction: the apparent difference … tracked the visual token budget
>   rather than the architecture (Finding 2). We therefore state the mechanism as a hypothesis consistent
>   with the data rather than as the explanation of it."*
> - **图注** → *"a crossing bracketed by those two ranks rather than a sharp threshold"*
>
> ### 三、✅ experiments 已压缩（`tools/_p511`）
>
> **36,021 → 27,856 字符**（≈5.92 → **4.58 页**）；移出 6 块到 `supplementary/`（12,600 → 23,972）。
> **正文保留的关键数字**（审稿人点名要的）：$R@1$ 两组对照、分层相关、配对检验、持有真实图的结果、逐 rank $\\Delta E$。
>
> ### 四、✅ 验证全绿
>
> | 检查 | 结果 |
> |---|---|
> | 编译 | **11 页 / 0 错误 / 0 未定义** |
> | `_p497` 矛盾扫描 | **需处理 0 处**（17 处命中**全在撤回/否定语境**；判据已加 3 条） |
> | `_p503` 字面 `\\n` | **全稿 0**（合法 `\\n`-命令 26 个未触碰） |
> | 完整版 `main_full` | **13 页 / 0 错 / 0 未定义** |
>
> ### 五、状态与剩余
>
> - **合规版**：**11 页**（目标 ≤7，**仍需删 ~23,580 字符**）
> - **完整版**：**13 页**（已冻结）
> - **`writing-hardener` 正在做 `task-12`**：压 `theory`（15,143→≈6,500）、`introduction`（5,048→≈2,400）、
>   `discussion`（5,742→≈2,500）、`conclusion`（3,043→≈1,200）
> - **剩余**：① 压缩收尾 ② **33 条回复信正式文本** ③ 修订包重新生成
> - **累计修订**：44 处
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
    if "扫描器漏抓" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("扫描器漏抓", "how far we can localise it", "only as a hypothesis",
              "bracketed by those two ranks", "累计修订"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
