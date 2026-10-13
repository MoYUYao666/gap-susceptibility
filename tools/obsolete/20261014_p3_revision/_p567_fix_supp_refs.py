# -*- coding: utf-8 -*-
r"""修 supplementary.tex 的未解析 `\ref` 与一处断头（2026-10-14）。

## 两个问题

### ① `Theorem ??` / `Lemma ??` / `Table ??`（PDF 里印出问号）

补充材料是从正文移出的内容，里面**带着指向正文 label 的 `\ref`**：
`\ref{thm:representation}`、`\ref{lem:r3-not-r3p}`、`\ref{tab:...}` ——
但**这些 label 在主文档里**，补充材料编译时解析不了 ⇒ 印成 `??`。

**⇒ 改法**：把这些 `\ref` 换成**明确文字**（"the Representation Theorem in the main text"、
"Lemma 1 of the main text" 等）。**不能删掉引用** —— 否则读者不知道指哪里。

### ② `oindent`（1 处）

`main.tex` 里的 `"\noindent"` 一经 Python 非 raw 字符串拼接 ⇒ `\n` 变真换行 ⇒ `oindent`。
本脚本一并修。

    python tools\_p567_fix_supp_refs.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUP = REPO / "paper3" / "paper_ieee" / "supplementary" / "supplementary.tex"

# label → 明确文字（指回主文档）
LABEL_TEXT = {
    "thm:representation": "the Representation Theorem in the main text",
    "thm:main": "the Representation Theorem in the main text",
    "lem:r3-not-r3p": "Lemma 1 of the main text",
    "cor:first-order": "Corollary 1 of the main text",
    "cor:optimal": "Corollary 2 of the main text",
    "cor:phase": "Corollary 3 of the main text",
    "cor:transfer": "Corollary 4 of the main text",
    "cor:paper2": "Corollary 5 of the main text",
    "eq:alloc": "Eq. 5 of the main text",
    "eq:rank": "Eq. 5 of the main text",
    "sec:theory": "Section III of the main text",
    "sec:experiments": "Section IV of the main text",
    "fig:phase_transition": "Supplementary Figure S1",
    "fig:counterfactual": "Supplementary Figure S2",
    "fig:ers": "Supplementary Figure S3",
    "tab:phase": "Supplementary Table S1",
    "tab:sample": "Supplementary Table S2",
    "tab:sharegpt": "Supplementary Table S3",
    "tab:comparison": "Supplementary Table S4",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(SUP, encoding="utf-8", errors="replace").read()
    print(f"  supplementary.tex {len(t):,} 字符")

    # 找所有 \ref / \eqref
    refs = re.findall(r"\\(?:ref|eqref|autoref)\{([^}]*)\}", t)
    print(f"  \\ref 共 {len(refs)} 处，去重：{sorted(set(refs))}")
    unknown = sorted(set(refs) - set(LABEL_TEXT))
    if unknown:
        print(f"  ⚠️ 未在映射表里的 label：{unknown} ⇒ 用「the main text」兜底")

    # 断头
    sev = [(t[:m.start()].count("\n") + 1, m.group(0))
           for m in re.finditer(r"(?m)^(oindent|abla|eq|ot)\b", t)]
    print(f"  断头命令：{len(sev)} 处 {sev[:5]}")

    if not a.apply:
        print("  （预演）")
        return 0
    bak = SUP.with_suffix(".tex.bak_p567")
    if not bak.exists():
        shutil.copy2(SUP, bak)

    # ① \ref → 明确文字
    def rep(m):
        lab = m.group(1)
        txt = LABEL_TEXT.get(lab, "the main text")
        return txt
    t2 = re.sub(r"\\(?:ref|eqref|autoref)\{([^}]*)\}", rep, t)
    # ② 断头
    t2 = re.sub(r"(?m)^oindent", "\\\\noindent", t2)
    t2 = re.sub(r"(?m)^abla", "\\\\nabla", t2)

    io.open(SUP, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(SUP, encoding="utf-8", errors="replace").read()
    left_ref = re.findall(r"\\(?:ref|eqref|autoref)\{", t3)
    left_sev = re.findall(r"(?m)^(oindent|abla|eq|ot)\b", t3)
    print()
    print(f"  复核：残留 \\ref {len(left_ref)} ｜ 残留断头 {len(left_sev)}")
    print(f"  → {len(t2):,} 字符")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
