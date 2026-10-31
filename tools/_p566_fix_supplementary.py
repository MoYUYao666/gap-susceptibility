# -*- coding: utf-8 -*-
r"""修 supplementary.tex：中文字符 + 缺失图片路径（2026-10-14）。

## 两个错误

| # | 错误 | 根因 |
|---|---|---|
| ① | `File 'figures/fig3_ers.png' not found` | 补充材料在子目录，图在上一级 `figures/` |
| ② | `Unicode character 解 (U+89E3) not set up` | **我 `_p521`/`_p523` 移出内容时，把小节标题写成中文**（如「解码器 VLM」）⇒ 中文字符进了 tex |

    python tools\_p566_fix_supplementary.py [--apply]
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(SUP, encoding="utf-8", errors="replace").read()
    print(f"  supplementary.tex {len(t):,} 字符")

    # ① 中文字符
    cjk = [(m.start(), m.group(0)) for m in re.finditer(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", t)]
    print(f"  ① 中文字符段：{len(cjk)} 处")
    for pos, s in cjk[:12]:
        ln = t[:pos].count("\n") + 1
        ctx = " ".join(t[max(0, pos - 70):pos + 70].split())
        print(f"       L{ln}: 「{s}」  …{ctx[:110]}…")

    # ② 图片路径
    figs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", t)
    print(f"  ② 图片引用 {len(figs)} 处：{figs}")
    missing = []
    for f in figs:
        p = (SUP.parent / f).resolve()
        if not p.exists():
            missing.append(f)
    print(f"     不存在：{missing}")

    if not a.apply:
        print("  （预演）")
        return 0
    bak = SUP.with_suffix(".tex.bak_p566")
    if not bak.exists():
        shutil.copy2(SUP, bak)

    # 中文段 → 英文标题（保留描述性）
    REPL = {
        "解码器 VLM": "Decoder VLM",
        "下游检验": "Downstream check",
        "操作点探针": "Operating-point probe",
        "探针": "probe",
    }
    for zh, en in REPL.items():
        t = t.replace(zh, en)
    # 剩余中文：整体删掉（不应有）
    left = re.findall(r"[\u4e00-\u9fff]+", t)
    if left:
        print(f"  ⚠️ 仍有中文：{set(left)} ⇒ 逐段删除")
        t = re.sub(r"[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+", "", t)

    # 图片路径 → ../figures/
    for f in missing:
        t = t.replace("{" + f + "}", "{../" + f + "}")

    io.open(SUP, "w", encoding="utf-8", newline="").write(t)
    t2 = io.open(SUP, encoding="utf-8", errors="replace").read()
    cjk2 = len(re.findall(r"[\u4e00-\u9fff]", t2))
    figs2 = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]*)\}", t2)
    miss2 = [f for f in figs2 if not (SUP.parent / f).resolve().exists()]
    print()
    print(f"  复核：中文 {cjk2} 个 ｜ 图片引用 {figs2} ｜ 仍缺 {miss2}")
    print(f"  → {len(t):,} 字符")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
