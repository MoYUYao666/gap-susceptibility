# -*- coding: utf-8 -*-
r"""重写 `Counterfactual Validation` 的结果段：去重复 + 撤"最坏情况保护"过度主张 + 修因果自相矛盾 + 压缩（2026-10-13）。

## 三处问题

### ① 文本重复（我的 `_p480` 锚点选错）
L329-333 残留旧版（含 *"the revised version"* 这类**投稿文本里不该出现的话**），
紧接 L333 又是新版开头 ⇒ **两版并存**。

### ② 🔴 "最坏情况保护"是过度主张（L544-559）
该段称 *"$\Gamma$ therefore removes the catastrophic tail of the distribution that random
allocation cannot avoid---a stronger guarantee than mean improvement"*。**但正文自己的数据不支持**：
- 同预算随机池（30 run）**mean +3347**；**Γ-guided mean +1478** ⇒ Γ 只比池均值好，**这不是"消除尾部"**
- **`random_03`（−1450.3）比 Γ-guided（+1477.5）更好**（差 −2928）
- Γ 的**最坏值 +3235** 与池的 **+18575** 比，**n=6 vs n=30** —— **小样本的极值比较不可靠**
- 且 `uniform` 均值 +5047 是池中较差者 ⇒ "最坏情况"叙事**建在同预算比较之上**，而那个比较已判定"不可区分"

**⇒ 只能弱化为**：*"在这 6 个种子里 Γ 的极差较小，但样本量不足以把它当作保证"*。

### ③ 因果自相矛盾（L564-566 vs L571-572）
一处写 *"we stop short of calling the relation causal"*，另一处写 *"establishes $\Gamma$ as a
**causal factor** in alignment degradation"* ⇒ **同节内直接冲突**。

    python tools\_p505_rewrite_counterfactual.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

# ① 重复段：从 "We therefore do not read the ratio" 之后的旧版开头，到新版 p=0.0055 说明结束
DUP_START = "The capacity-matched comparison we ran does not support the stronger reading"
DUP_END = "$p = 0.0055$)."

DUP_NEW = (
    "The capacity-matched comparison we ran does not support the stronger reading either,\n"
    "and we report the failure in full below.")
# ② "最坏情况保护"段
WC_START = "\\textbf{Worst-case protection.} The three groups exhibit fundamentally"
WC_END = "avoid---a stronger guarantee than mean improvement."
WC_NEW = (
    r"\textbf{What we can and cannot say about the tail.} Within the six $\Gamma$-guided runs"
    "\n"
    r"we report, the spread is narrower than in the thirty-run random pool and every run"
    "\n"
    r"improves alignment, whereas the pool contains a run at $+18{,}575$. We deliberately"
    "\n"
    r"stop there. Comparing a six-run sample against a thirty-run pool makes an extreme-value"
    "\n"
    r"argument unreliable, the pool's \emph{mean} is not worse than the rule's, and two of the"
    "\n"
    r"ten random allocations beat it outright. A claim that the rule removes a catastrophic"
    "\n"
    r"tail is therefore not something our design can support, and we do not make it."
)
# ③ 因果句
CAUSAL_OLD = ("This monotonic dose-response relationship---higher forced rank $\\to$ worse\n"
              "outcome---establishes $\\Gamma$ as a causal factor in alignment degradation,\n"
              "not merely a correlated biomarker.")
CAUSAL_NEW = ("This monotonic dose-response relationship---higher forced rank $\\to$ worse\n"
              "outcome---is consistent with $\\Gamma$ locating where damage occurs. We stop at\n"
              "consistency: the capacity-matched control shows that the ordering alone does not\n"
              "determine the outcome, since the reversed allocation performs like the predicted\n"
              "one, so we do not claim causation.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()

    i = t.find(DUP_START)
    j = t.find(DUP_END, i)
    k = t.find(WC_START)
    m = t.find(WC_END, k)
    c = t.count(CAUSAL_OLD)
    print(f"  ① 重复段 i={i}, j={j}（{j + len(DUP_END) - i if i >= 0 and j >= 0 else -1} 字符）")
    print(f"  ② 最坏情况段 k={k}, m={m}（{m + len(WC_END) - k if k >= 0 and m >= 0 else -1} 字符）")
    print(f"  ③ 因果句命中 {c}")
    if i < 0 or j < 0 or k < 0 or m < 0 or c != 1:
        print("  🔴 锚点不全")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p505")
    if not bak.exists():
        shutil.copy2(EX, bak)

    # 从后往前替换，避免位移
    t = t[:k] + WC_NEW + t[m + len(WC_END):]
    t = t.replace(CAUSAL_OLD, CAUSAL_NEW)
    i = t.find(DUP_START)
    j = t.find(DUP_END, i)
    t = t[:i] + DUP_NEW + t[j + len(DUP_END):]
    io.open(EX, "w", encoding="utf-8", newline="").write(t)

    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "重复段已除（'In a capacity-matched comparison' 只 1 次）":
            t2.count("In a capacity-matched comparison") == 1,
        "删掉'report both in the revised version'": "in the revised version" not in t2,
        "删掉'removes the catastrophic tail'": "removes the catastrophic tail" not in t2,
        "含'tail 主张设计不支持'": "not something our design can support" in t2,
        "因果句已弱化": "establishes $\\Gamma$ as a causal factor" not in t2,
        "含'do not claim causation'": "do not claim causation" in t2,
        "字符数减少": len(t2) < len(io.open(bak, encoding="utf-8", errors="replace").read()),
    }
    old_len = len(io.open(bak, encoding="utf-8", errors="replace").read())
    print(f"  {old_len:,} → {len(t2):,} 字符（减少 {old_len - len(t2):,}）")
    ok = True
    for kk, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {kk}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
