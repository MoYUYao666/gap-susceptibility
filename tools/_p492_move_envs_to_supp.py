# -*- coding: utf-8 -*-
r"""把 theory 的证明与 experiments 的表/图移入 Supplementary（2026-10-13）。

## 依据（`tools/_p491` 精确分解）

| 节 | 散文 | 环境（表/图/公式/证明） |
|---|---|---|
| experiments | **30,217** | **7,765**（table 3,552 + tabular 2,203 + figure 1,407） |
| theory | **11,259** | **6,478**（**proof 2,501** + enumerate 2,063 + theorem 843 + equation 787） |
| discussion | 5,021 | 0 |
| introduction | 3,223 | enumerate 1,483 |

**⇒ 先移"环境"（低风险：结论留在正文，细节进补充）**：
1. `theory.tex` 的 **`proof` 环境**（2,501 字符）→ Supplementary，**保留 theorem/lemma 陈述**
2. `experiments.tex` 的 **table + figure**（≈7,162 字符）→ Supplementary，
   **正文保留每张表的"结论一句话"与引用**

**⚠️ 代价**：审稿阶段看不到补充材料 ⇒ **只移细节，不移结论**。

    python tools\_p492_move_envs_to_supp.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
TH = PI / "sections" / "theory.tex"
EX = PI / "sections" / "experiments.tex"
SUP = PI / "supplementary" / "supplementary.tex"


def extract_envs(text: str, env: str):
    """返回 (新文本, 抽出的环境列表)。"""
    pat = re.compile(rf"\\begin\{{{env}\*?\}}.*?\\end\{{{env}\*?\}}", re.S)
    found = [m.group(0) for m in pat.finditer(text)]
    return pat.sub("", text), found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    th = io.open(TH, encoding="utf-8", errors="replace").read()
    ex = io.open(EX, encoding="utf-8", errors="replace").read()
    sup = io.open(SUP, encoding="utf-8", errors="replace").read()

    th2, proofs = extract_envs(th, "proof")
    ex2, tables = extract_envs(ex, "table")
    ex3, figures = extract_envs(ex2, "figure")
    print(f"  theory: 抽出 proof {len(proofs)} 个（{sum(len(x) for x in proofs):,} 字符）")
    print(f"  experiments: 抽出 table {len(tables)} 个（{sum(len(x) for x in tables):,} 字符）"
          f" + figure {len(figures)} 个（{sum(len(x) for x in figures):,} 字符）")
    print(f"  theory {len(th):,} → {len(th2):,} ｜ experiments {len(ex):,} → {len(ex3):,}")

    if not a.apply:
        print("  （预演）")
        return 0
    for p in (TH, EX, SUP):
        bak = p.with_suffix(".tex.bak_p492")
        if not bak.exists():
            shutil.copy2(p, bak)

    io.open(TH, "w", encoding="utf-8", newline="").write(th2)
    io.open(EX, "w", encoding="utf-8", newline="").write(ex3)

    # 追加到补充材料
    add = ["\n\n\\section{Deferred Proofs}\n",
           "Proofs of the results stated in the main text.\n"]
    for i, pr in enumerate(proofs, 1):
        add.append(f"\n\\subsection{{Proof {i}}}\n")
        add.append(pr + "\n")
    add.append("\n\\section{Tables and Figures}\n")
    add.append("Tables and figures referred to from the main text, kept here so that the "
               "main text can remain within the journal's page limit. Each is cited by "
               "number in the main text.\n")
    for i, tb in enumerate(tables, 1):
        add.append(f"\n% ---- table {i} ----\n{tb}\n")
    for i, fg in enumerate(figures, 1):
        add.append(f"\n% ---- figure {i} ----\n{fg}\n")
    sup2 = sup.replace("\\bibliographystyle{IEEEtran}", "".join(add) + "\n\\bibliographystyle{IEEEtran}")
    io.open(SUP, "w", encoding="utf-8", newline="").write(sup2)
    print(f"  ✅ 补充材料 {len(sup):,} → {len(sup2):,} 字符")
    print(f"  ✅ theory {len(th2):,} ｜ experiments {len(ex3):,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
