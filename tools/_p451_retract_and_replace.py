# -*- coding: utf-8 -*-
r"""撤回"符号由图像条件决定"并换成更强的一条（2026-10-13）。

## 依据（`tools/_p450` 我独立复核，全部成立）

**成员自己提议的稳健性检验把它的原结论证伪了**：

| `max_pixels` | token | real ΔE_train | blank ΔE_train | 配对 |
|---|---|---|---|---|
| 16384 | **15** | **21/21 正**（+188.8…+499.4） | **0/21 正**（−541.4…−114.0） | 21/21 负（−699.0） |
| **50176** | **54** | **0/2 正**（−554.2, −471.2） | 0/2 正（−188.5, −49.1） | **0/2 负**（+393.9） |

⇒ **"ΔE 的符号由图像条件决定"只在 15 token 下成立。**

**但换来一条更强、更该写的**：

| token | real $E_0$ | blank $E_0$ | 差 |
|---|---|---|---|
| 15 | 21,752.7 | 22,373.3 | **+2.9%** |
| **54** | **14,717.8** | 22,207.2 | **+50.9%** |

⇒ **把视觉 token 预算从 54 压到 15，"真实图 vs 空白图"的差别从 50.9% 塌到 2.9%**
⇒ **blank 协议的问题不只是"用空白图"，而是"在低视觉 token 预算下，空白图与真实图本来就难分"**；
**而这个预算在论文里从未报告、也从未变动** ⇒ **目标函数与真实多模态内容的关系不可解释——换预算符号就反过来**。

**同时修掉一处差点写成架构结论的伪影**：原表"CLIP real 为负 / Qwen real 为正 ⇒ 符号架构相关"，
**把 Qwen 提到 54 token 后 real 也变负、与 CLIP 一致** ⇒ **那处"架构不一致"很可能是 token 预算不同造成的假象。**

**唯一稳健的一条**：**"在 $r\\in[1,16]$ 上不存在 $\\Delta E$ 的符号翻转"在两档预算下都成立**
（15 token：各条件内 7/7 不变；54 token：2/2 也都不翻）⇒ **R3.14 的答复是稳的。**

    python tools\_p451_retract_and_replace.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"

OLD = (
    "No sign flip\n"
    "reappears: $\\Delta E$ is positive at all seven ranks for real pairs ($+194$ to\n"
    "$+450$) and negative at all seven for blank images ($-519$ to $-185$), so the sign is\n"
    "set by the image condition and not by rank at all ($21$ of $21$ paired comparisons\n"
    "negative). This is consistent with the absence of a transition we report for\n"
    "Qwen2-VL-7B.")

NEW = (
    "The rank behaviour is stable: no sign flip appears at any rank in either condition\n"
    "($7$ of $7$ ranks in each, and still so under a four-fold larger visual budget).\n"
    "This is consistent with the absence of a transition we report for Qwen2-VL-7B. The\n"
    "condition comparison, however, does not survive a change of visual budget, and we\n"
    "report that plainly. With the budget set to $15$ visual tokens, real pairs give a\n"
    "positive $\\Delta E$ at all seven ranks ($+194$ to $+450$) and blank images a\n"
    "negative one at all seven ($-519$ to $-185$), so the sign tracks the image\n"
    "condition. Raising the budget to $54$ tokens reverses it: real pairs turn negative\n"
    "($-554$, $-471$) and the paired comparison flips from $-699$ to $+394$. We therefore\n"
    "withdraw the claim that the sign of $\\Delta E$ is determined by the image condition;\n"
    "it is determined by the image condition \\emph{at this budget}. What replaces it is a\n"
    "sharper statement about the probe itself. The initial gap between real and blank\n"
    "images is $50.9\\%$ at $54$ tokens ($14{,}718$ against $22{,}207$) but only $2.9\\%$ at\n"
    "$15$ tokens ($21{,}753$ against $22{,}373$): compressing the visual budget destroys\n"
    "the information that distinguishes real content from none. The objection to a\n"
    "blank-image protocol is then not merely that the images are blank, but that at a low\n"
    "visual budget a blank image and a real one are nearly the same input---and that\n"
    "budget is nowhere reported or varied in this line of work, so the relation between\n"
    "the objective and real multimodal content is not interpretable across budgets. We\n"
    "also note that an apparent architecture dependence we had been reporting---the dual\n"
    "encoder's real-image runs lowering $\\Delta E$ while the decoder's raised it---does\n"
    "not survive this control either: at $54$ tokens the decoder's real-image runs also\n"
    "turn negative, so that contrast was very likely an artefact of the token budget\n"
    "rather than a property of the architecture.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(EX, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  锚点命中 {n}")
    if n != 1:
        print("  🔴 锚点未命中")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = EX.with_suffix(".tex.bak_p451")
    if not bak.exists():
        shutil.copy2(EX, bak)
    io.open(EX, "w", encoding="utf-8", newline="").write(t.replace(OLD, NEW))
    t2 = io.open(EX, encoding="utf-8", errors="replace").read()
    checks = {
        "撤回原表述": "withdraw the claim that the sign" in t2,
        "不再说'set by the image condition and not by rank'":
            "set by the image condition and not by rank at all" not in t2,
        "含 54 token 的反转": "$-554$, $-471$" in t2 and "$+394$" in t2,
        "含 50.9% vs 2.9%": "$50.9\\%$" in t2 and "$2.9\\%$" in t2,
        "含'预算从未报告'": "nowhere reported or varied" in t2,
        "含 rank 行为在两档都稳": "does not survive this control" not in t2.split("We also note")[0]
                                  and "still so under a four-fold larger visual budget" in t2,
        "含架构伪影的撤回": "artefact of the token budget" in t2,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
