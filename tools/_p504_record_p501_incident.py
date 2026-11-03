# -*- coding: utf-8 -*-
r"""落账：`_p501` 事故（判据过宽吃命令）+ 全稿矛盾扫描 + 13 页（2026-10-13 14:10）。

    python tools\_p504_record_p501_incident.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴 2026-10-13 14:10 —— 我的 `_p501` 事故（判据过宽吃掉了 LaTeX 命令）；并完成**全稿矛盾扫描**（12 处新矛盾全部修完）**
>
> ### 一、🔴 事故：`_p501` 的正则判据过宽
>
> **意图**：把 Python 原始字符串造成的**字面 `\\n`**（反斜杠+n）换成真换行。
> **实际**：判据 `re.sub(r"\\\\n[ \\t]*(?=\\r?\\n)", "", text)` **同时匹配了合法的 LaTeX 命令**
> —— 任何"整行以 `\\n` 开头"的行（如 `\\newtheorem{...}`），其 `\\n` 被删 ⇒
>
> ```
> \\newtheorem{theorem}{Theorem}[section]   →   （空行）ewtheorem{theorem}{Theorem}[section]
> ```
>
> **⇒ 10 处 `\\newtheorem` 断头**（`main.tex` 5 + `supplementary.tex` 5），**编译错误 10 → 13**。
> **已用 `edit` 工具逐处字面替换修复**，现 **13 页 / 0 错 / 0 未定义 / 全稿 0 断头**。
>
> **⇒ 我的第 29 个错。教训：判据过宽的正则替换比不做更危险。**
> **本阶段同型已第 3 次**（`_p433` 21 处、`_p435`、本次 `_p501`）。
>
> ### 二、✅ 修正后的判据（`tools/_p503`）
>
> **字面 `\\n` 的特征：`\\` + `n` 后面**不是字母**。**
> - ✅ 可替换：`\\n(?![A-Za-z])` —— 后跟空白/行尾/非字母
> - ❌ 绝不动：`\\n[A-Za-z]+` —— `\\newtheorem` / `\\newcommand` / `\\not` / `\\nabla` / `\\neq` …
>
> **实测**：**全稿字面 `\\n` = 0 ｜ 合法 `\\n`-命令 = 10**（`\\newtheorem` ×10）。
> **并加了硬断言**：替换后**合法命令数量必须不变**，否则 `AssertionError` 中止。
> **⇒ 这补上了原脚本最缺的一道闸。**
>
> ### 三、🔴 本轮最重要的发现：**"改了正文没改别处"是系统性的，不是偶发**
>
> 我做了一次**全稿穷举扫描**（`tools/_p497`，判据：10 条"已修订结论 ⇔ 旧主张特征串"），**抓出 12 处真矛盾**：
>
> | 文件:行 | 旧主张 | 处置 |
> |---|---|---|
> | `conclusion.tex:7` | *"reduces allocation uncertainty by **$30\\times$**"* | ✅ 删（重写该段） |
> | `conclusion.tex:7` | *"**190 runs** (181 sweep…)"* | ✅ 删 |
> | `conclusion.tex:7` | *"**sharp** alignment phase transition … robust across sample sizes 16 to 256"* | ✅ 降级 |
> | `conclusion.tex` | *"the **unique** scalar satisfying the five requirements **forced**"* | ✅ 改为**需 R3′** |
> | `conclusion.tex` | *"a **theoretical guarantee** rather than an empirical heuristic"* | ✅ 改为"结构刻画" |
> | `conclusion.tex` | $\n$ **文本粘连**（我的正则只匹配句首所致） | ✅ 整段重写 |
> | `introduction.tex:18` | *"confirms an alignment **phase transition at $r_c$**"* | ✅ 改为 bracketed + 协议归属 |
> | `introduction.tex:18` | *"demonstrating **architecture-dependent** diagnostic capability"* | ✅ 改为"无法证实该预测" |
> | `introduction.tex:18` | *"**190 runs** (181 sweep…)"* | ✅ 删 |
> | `related_work.tex:21` | *"Our **alignment phase transition at** …"* | ✅ 改为 bracketing |
> | `theory.tex:230` | *"The critical rank $r_c$ is **architecture-dependent**"* | ✅ 改为"未能验证该预测" |
> | `experiments.tex:149` | **`Finding 2: Architecture-dependent behavior`** | ✅ 改为"未能复现的架构差异"（**54 token 下 Qwen 的 real 也转负 ⇒ token 预算伪影**） |
>
> **⚠️ 根因**：本轮我改了 `experiments` / `theory` / `appendix` / `main`（摘要），
> **`introduction` / `related_work` / `conclusion` / `discussion` 四处从未更新**。
> **⇒ 摘要那次也是同型。四节全部中招 ⇒ 这是"系统性遗漏"，不是手误。**
>
> **⇒ 新增流程规则（本阶段第 4 条）**：
> > **改任何实质结论时，必须同时跑一次"同型主张扫描"**（把旧主张的特征串穷举，
> > 检查全稿每个文件），**并区分"允许语境"（撤回/否定/转折句）与真矛盾**。
> > 依据：**结论不是只写在一处的；它被复述在摘要、引言、相关工作、讨论、结论里。**
>
> **并核出我自己判据的 2 处**假阳性**（已修判据）：`discussion` 的 *"not that it admits exactly one
> unconditionally"*（否定式）、`conclusion` 的 *"beats … but reverses at another"*（转折式）。
>
> ### 四、✅ 现状（扫描全清）
>
> - **矛盾扫描**：**0 处需处理**（19 处命中**全部在撤回/否定语境**）
> - **编译**：`main.pdf` = **13 页 / 0 错误 / 0 未定义 / 0 断头命令**
> - **字面 `\\n`**：全稿 **0**
>
> ### 五、页数现状与下一步
>
> | 节 | 总字符 | 散文 | 环境 |
> |---|---|---|---|
> | experiments | 38,224 | **30,459** | 7,765 |
> | theory | 15,167 | 11,190 | 3,977 |
> | discussion | 5,744 | 5,744 | 0 |
> | introduction | 5,051 | 3,223 | 1,828 |
> | related_work | 3,361 | 3,361 | 0 |
> | conclusion | 3,045 | 3,045 | 0 |
> | **合计** | **79,112** | **62,051** | 17,061 |
>
> **PRL 硬约束：双栏 ≤7 页**，`appendix` 已移入 `supplementary/`（14→13 页），
> **3 个 proof 已移入补充**；**7 张表/图保留在正文**（审稿阶段必须可见）。
> **⇒ 仍需从 13 页压到 ≤7 页**：主要从 `experiments`（30,459 散文字符）下手，
> **但修矛盾 > 压页数**（本轮 12 处矛盾若提交会直接暴露"我们自己撤回过的主张"）。
>
> ### 六、状态
>
> - **P3 稿件**：**13 页** / 0 错 / 0 未定义；**累计修 27 处 + 本轮 12 处矛盾 = 39 处**
> - **摘要**：243 词 ≤ 250 ✅
> - **剩余**：① **压到 ≤7 页**（进行中）② **33 条回复信正式文本** ③ 修订包重新生成
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
    if "_p501" in t and "判据过宽" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("_p501", "判据过宽", "系统性遗漏", "Finding 2: Architecture-dependent", "同型主张扫描"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
