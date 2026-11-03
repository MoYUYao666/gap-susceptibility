# -*- coding: utf-8 -*-
r"""清理补充材料里残留的误加段，并修其 3 处断头命令（2026-10-13）。

    python tools\_p519_clean_supp.py [--apply]
"""
from __future__ import annotations

import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
SUP = PI / "supplementary" / "supplementary.tex"


def main() -> int:
    ap_apply = "--apply" in sys.argv
    s = io.open(SUP, encoding="utf-8", errors="replace").read()
    orig = len(s)

    # ① 移除 "Tables and Figures" 段（其内容现在在正文；避免重复）
    k = s.find("\\section{Tables and Figures}")
    if k > 0:
        e = s.find("\\bibliographystyle{IEEEtran}", k)
        if e < 0:
            e = len(s)
        print(f"  ① 移除 Tables and Figures 段：[{k}:{e}]（{e-k:,} 字符）")
        s = s[:k] + s[e:]

    # ② 修断头命令（行首 token + 前一行未闭合）
    lines = s.split("\n")
    FIX = {"abla": "nabla", "oindent": "noindent", "eq": "neq", "ot": "not"}
    hits = []
    for i, ln in enumerate(lines):
        m = re.match(r"^([a-z]{1,10})\b", ln)
        if not m or m.group(1) not in FIX:
            continue
        prev = lines[i - 1].rstrip() if i >= 1 else ""
        if prev.count("$") % 2 == 1 or any(prev.endswith(x) for x in
                                           ("(", "[", "|", "=", ",", "\\langle", "\\|")):
            hits.append((i, m.group(1)))
    print(f"  ② 断头命令 {len(hits)} 处：{[(i+1, t) for i, t in hits]}")
    for i, tok in hits:
        lines[i] = "\\" + FIX[tok] + lines[i][len(tok):]
    s2 = "\n".join(lines)
    delta = len(s2) - orig
    print(f"  ⇒ 字符 {orig:,} → {len(s2):,}（Δ{delta:+,}）")

    if not ap_apply:
        print("  （预演）")
        return 0
    bak = SUP.with_suffix(".tex.bak_p519")
    if not bak.exists():
        shutil.copy2(SUP, bak)
    io.open(SUP, "w", encoding="utf-8", newline="").write(s2)
    t = io.open(SUP, encoding="utf-8", errors="replace").read()
    sev = [t[:m.start()].count("\n") + 1 for m in re.finditer(r"(?m)^(abla|oindent|eq|ot)\b", t)]
    print(f"  ✅ 已写；残留断头 {len(sev)} 处 ｜ 含 Tables and Figures 段 "
          f"{'\\section{Tables and Figures}' in t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
