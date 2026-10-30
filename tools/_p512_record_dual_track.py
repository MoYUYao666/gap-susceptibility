# -*- coding: utf-8 -*-
r"""落账：双轨（7 页合规版 + 完整版备份）+ 分工（2026-10-13 16:20）。

    python tools\_p512_record_dual_track.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📐 2026-10-13 16:20 —— 操作者裁决"双轨"；篇幅标定完成；experiments 已压 8,165 字符**
>
> ### 一、操作者裁决（2026-10-13 12:48）
>
> > **"先做第 1 项，同时准备第 2 项备份"** ⇒ **① 做到 7 页（证据移入 Supplementary）** +
> > **② 同时保留 11-12 页完整版**。
>
> ### 二、🔴 篇幅标定（`tools/_p509`，可重跑）——**这是必须让操作者知道的事实**
>
> | 配置 | 页数 |
> |---|---|
> | **IEEEtran `[journal]`**（当前） | **11 页**（压缩后） |
> | **`elsarticle[final,3p,twocolumn]`**（PRL 自己的类） | **14 页** |
>
> **⇒ 换格式不是解法** —— **PRL 自己的类反而更多页**（elsarticle 3p 的版心更宽但行距/字号不同）。
>
> | 量 | 值 |
> |---|---|
> | 参与编译 tex 字符 | **64,844**（压缩前 **73,009**） |
> | 实测 | **≈ 6,084 字符/页**（用压缩前的 73,009 / 12 页标定） |
> | **≤7 页预算** | **≈ 41,264 字符** |
> | **仍需删** | **23,580 字符（现量的 36%）** |
>
> **⚠️ 关键张力**：**原投稿是 11 页却进了外审并拿到 Revise** ⇒ 7 页在实践中可能未严格执行；
> **但 Guide 写明是 Mandatory Submission Requirements**。**⇒ 双轨并行，由操作者/编辑选。**
>
> ### 三、✅ 完整版已**冻结**
>
> - **`main_full.tex`** + **`sections_full/`**（7 个 tex 的副本）
> - **编译：13 页 / 0 错 / 0 未定义** ✅
> - **⇒ 后续删减只动 `sections/`，完整版不受影响**；两份构建相互独立。
>
> ### 四、✅ experiments 已压（`tools/_p511`）：36,021 → **27,856**（≈5.92 → 4.58 页）
>
> 移出 6 块到 `supplementary/`（12,600 → **23,972** 字符），**正文留要点句 + 关键数字**：
>
> | 块 | 移出字符 | 正文留 |
> |---|---|---|
> | Comparison with Prior Work | 899 | 168 |
> | Rank Scaling and $\\Gamma$ Evolution | 1,736 | 356 |
> | Second-Dataset (ShareGPT) | 2,566 | 146 |
> | Sample Size Robustness | 1,234 | 170 |
> | 解码器 VLM（Counterfactual 内） | 2,572 | 760 |
> | 下游检验（Counterfactual 内） | 1,973 | 1,215 |
> | **合计** | **10,980** | **2,815**（净省 **8,165**） |
>
> **⚠️ 移出时**保留在正文的关键数字**（审稿人点名要的）**：
> $R@1 = 0.7241$ vs $0.6927$、分层相关 $-0.374$ / $+0.172$ / $+0.478$、配对 $21/21$ 与 $18/18$、
> 持有真实图时的 $-135$…$-271$ 与 $-260 \\to +179$、逐 rank $\\Delta E$ 值。
>
> ### 五、🔴 我又踩了同一个坑（第 30 个错，同型第 4 次）
>
> `_p511` 里我**混用了原始字符串与普通字符串**，`\\n` 写成 `\\n`（字面）⇒ **7 个 `! Undefined control sequence`**；
> 另有一处 `\\textbf{...}(Supplementary Section~S7).}` **括号位置错** ⇒ `! Too many }'s`。
> **已用 `tools/_p503`（修正判据：字面 `\\n` = `\\n` 后不跟字母）一次清完 ⇒ 全稿字面 `\\n` = 0。**
> **⇒ 教训：本脚本的修正判据是对的；错在我写脚本时混用了字符串类型。**
>
> ### 六、分工（避免写冲突）
>
> | 谁 | 范围 |
> |---|---|
> | **`writing-hardener`**（共享任务 **`task-12`**） | **`theory.tex`（15,143→≈6,500）**、**`introduction.tex`（5,048→≈2,400）**、**`discussion.tex`（5,742→≈2,500）**、**`conclusion.tex`（3,043→≈1,200）** |
> | **Lead（我）** | **`experiments.tex`**（27,856 → 目标更低）、`related_work.tex`、`supplementary/`、`main.tex` |
>
> **并已把两条红线写进 task-12**：
> ① **禁止 `r"..."` 原始字符串拼 LaTeX**（已出事 4 次）；
> ② **禁止宽泛正则批量替换**（`_p501` 把 `\\newtheorem` 吃成 `ewtheorem`）。
> **验证要求**：编译 0 错 / 0 未定义、`_p497` 矛盾扫描"需处理 0 处"、`_p503` 字面 `\\n` = 0。
>
> ### 七、状态
>
> - **P3 合规版**：**11 页** / 0 错 / 0 未定义（目标 ≤7 页，**仍需删 23,580 字符**）
> - **P3 完整版**：**13 页** / 0 错 / 0 未定义（**已冻结**）
> - **累计修订**：42 处
> - **剩余**：① 继续压缩（我与 `writing-hardener` 并行）② **33 条回复信正式文本** ③ 修订包重新生成
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
    if "操作者裁决" in t and "双轨" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("双轨", "41,264", "main_full.tex", "8,165", "task-12"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
