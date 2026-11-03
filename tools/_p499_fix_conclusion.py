# -*- coding: utf-8 -*-
r"""修复 `_p498` 在 conclusion 里造成的文本粘连，并清掉残留的过期主张（2026-10-13）。

## 我犯的错（第 28 个）

`_p498` 用 `re.search(r"Experimental validation confirms these predictions through[^.]*\.[^.]*\.", ...)`
只匹配到**前两句** ⇒ 替换后留下残句 **`rates.5-7B, zero-shot Predictive Transfer identifies a sharp
alignment phase transition … reduces allocation uncertainty by $30\times$ …`** ⇒ **文本粘连 + 过期主张仍在**。

**⇒ 正则做跨句替换不可靠；结论段这种"整段重述"的地方应当整段重写。**

## 本次做法

**从"Experimental validation"起，到"universal brute-force predictor."止，整段重写**，
并同时：
- 删掉 `$30\times$`、`sharp alignment phase transition`、`190 runs`（已在别处）
- 把 `unique scalar satisfying the five requirements` 改为**需 R3′**
- 把 `theoretical guarantee rather than an empirical heuristic` 改为**如实口径**
- 保留 C1–C5（但 C3 措辞降级）

    python tools\_p499_fix_conclusion.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CO = REPO / "paper3" / "paper_ieee" / "sections" / "conclusion.tex"

# ① 从 "Experimental validation covers 126 runs" 起到 "universal brute-force predictor." 止
SEG_START = "Experimental validation covers 126 runs"
SEG_END = "universal brute-force predictor."

NEW_SEG = (
    r"Experimental validation covers 126 runs on the present protocol plus the"
    "\n"
    r"capacity-matched allocation study of Section~IV. We bracket the crossing in the"
    "\n"
    r"alignment energy at $r \in [5,6]$ without claiming it is sharp---the interval at"
    "\n"
    r"$r=5$ spans zero and an exact permutation test between neighbouring ranks is not"
    "\n"
    r"significant---and we attribute it to the measurement protocol rather than to the"
    "\n"
    r"model, since it does not reappear under real image--text pairs at the scales we could"
    "\n"
    r"run. On the allocation question itself the results are negative and we state them as"
    "\n"
    r"such: at an identical trainable-parameter count the allocation derived from $\Gamma$"
    "\n"
    r"beats the uniform-rank baseline at one learning rate but reverses at another and"
    "\n"
    r"vanishes once the arms are matched on training loss; it is indistinguishable from a"
    "\n"
    r"random allocation of the same budget; and an adaptive baseline (AdaLoRA), swept over"
    "\n"
    r"the same learning rates, reaches lower alignment energy than any of our arms. What"
    "\n"
    r"survives is the purpose rather than the win: $\Gamma$ allocates \emph{without"
    "\n"
    r"searching}, and that is the setting it is for."
)

# ② 唯一性句 → 需 R3′
UNIQ_OLD = (r"The central insight: $\Gamma = \langle \nabla E, u \rangle$ is not an arbitrary choice"
            r"---it is the unique scalar satisfying the five requirements forced by the PEFT"
            r" allocation problem structure.")
UNIQ_NEW = (r"The central insight: $\Gamma = \langle \nabla E, u \rangle$ is not an arbitrary"
            r" choice---it is the scalar singled out by the requirements of the PEFT allocation"
            r" problem \emph{once one accepts the additivity assumption (R3$'$), which we state"
            r" explicitly because (R3) alone does not imply it}.")

# ③ "theoretical guarantee" → 如实
GUA_OLD = (r"The Representation Theorem provides what prior rank allocation methods lacked: a"
           r" theoretical guarantee rather than an empirical heuristic.")
GUA_NEW = (r"The Representation Theorem provides what prior rank allocation methods lacked: a"
           r" structural characterisation rather than an empirical heuristic---a characterisation"
           r" whose scope our own controls then bound.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(CO, encoding="utf-8", errors="replace").read()
    i = t.find(SEG_START)
    j = t.find(SEG_END)
    print(f"  段区间：i={i}, j={j}")
    ok_uniq = t.count(UNIQ_OLD)
    ok_gua = t.count(GUA_OLD)
    print(f"  唯一性句命中 {ok_uniq} ｜ 'theoretical guarantee' 句命中 {ok_gua}")
    if i < 0 or j < 0 or ok_uniq != 1 or ok_gua != 1:
        print("  🔴 锚点不全")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = CO.with_suffix(".tex.bak_p499")
    if not bak.exists():
        shutil.copy2(CO, bak)
    t2 = t[:i] + NEW_SEG + t[j + len(SEG_END):]
    t2 = t2.replace(UNIQ_OLD, UNIQ_NEW).replace(GUA_OLD, GUA_NEW)
    io.open(CO, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(CO, encoding="utf-8", errors="replace").read()
    checks = {
        "粘连已除（无 rates.5-7B）": "rates.5-7B" not in t3,
        "删掉 30×": "30\\times" not in t3,
        "删掉 sharp phase transition": "sharp alignment phase transition" not in t3,
        "唯一性需 R3′": "(R3$'$)" in t3,
        "占位'结构刻画'而非'保证'": "structural characterisation" in t3,
        "含'negative and we state them as such'": "negative and we state them as" in t3,
        "含'without searching'定位": "without" in t3 and "searching" in t3,
        "字符数": True,
    }
    print(f"  {len(t):,} → {len(t3):,} 字符")
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
