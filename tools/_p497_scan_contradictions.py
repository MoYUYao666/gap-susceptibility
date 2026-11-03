# -*- coding: utf-8 -*-
r"""全稿扫描：仍有与已修订结论矛盾的旧主张（2026-10-13）。

## 触发

我连续发现两处"改了正文没改别处"：
- **摘要**含 $30\\times$、*unique*、*phase transition*、旧 run 计数（已重写）
- **discussion** 含 *"exactly one"*、*"they are forced"*、*"phase transition at $r_c$"*、
  *"necessary consequence"*（已修）

**⇒ 必须做一次**穷举扫描**，而不是等下一篇再撞。**

## 扫描对象

`paper3/paper_ieee/sections/*.tex` + `main.tex` + `supplementary/*.tex`

## 已修订结论 ⇔ 旧主张对照表（判据）

| 已修订为 | 旧主张的**特征串**（应不存在或已标注） |
|---|---|
| $30\\times$ **必须删除** | `30\times`、`30x`、`reduces uncertainty` |
| **唯一性需 R3′** | `exactly one`、`they are forced`、`is not proposed`、`forced---the allocation` |
| **phase transition → bracketed** | `phase transition at`、`sharp phase transition` |
| **$r_c$ 属协议** | `model-independent`（除否定式）、`universal` |
| **arch 相关已撤回** | `architecture-dependent`（除非同句有 token budget） |
| **分配未胜随机** | `reduces allocation uncertainty`、`eliminates`、`beats the uniform`（除非否定式） |
| **blank 非中性** | 若写 blank 是中性/无偏，违规 |
| **190 runs 旧计数** | `190 runs` |
| **$\\beta=0.137$ 出处** | `CLIP-derived` |
| **rank-vs-参数记账** | `equal parameter budget` |

    python tools\_p497_scan_contradictions.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
OUT = REPO / "outputs" / "analysis" / "p3_contradiction_scan.json"

RULES = [
    ("30× 应已删除", [r"30\s*\\times", r"30x\b", r"reduces? (?:allocation )?uncertainty"]),
    ("唯一性需 R3′", [r"exactly one", r"they are forced", r"is not proposed", r"it is forced"]),
    ("phase transition 应降级", [r"phase transition at", r"sharp phase transition",
                                r"sharp phase transition", r"\bsharp phase\b",
                                r"statistically supported\\s+transition",
                                r"appears in LLaVA but not"]),
    ("r_c 属协议", [r"model-independent", r"\buniversal\b"]),
    ("arch 相关应撤回", [r"architecture-dependent"]),
    ("分配应未胜随机", [r"eliminates allocation uncertainty", r"beats the uniform-rank"]),
    ("旧 run 计数", [r"\b190 runs\b", r"181 sweep"]),
    ("β 出处应更正", [r"CLIP-derived"]),
    ("记账口径应明确", [r"equal parameter budget"]),
    ("blank 不应被称中性", [r"blank images are neutral", r"neutral probe"]),
]

# 允许出现的语境（否定/撤回/更正语句）
ALLOW = ("withdraw", "no longer", "must not", "not a", "rather than", "we record",
         "arrefact", "artefact", "we do not", "does not", "cannot", "instead of",
         "is not", "are not", "was withdrawn", "incorrect", "earlier",
         # 否定/转折语境（我先前漏掉这两类，造成假阳性）
         "not that", "unconditional", "but reverses", "but we", "unable to",
         "could not reproduce", "we first read", "rather than the architecture")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    files = sorted(glob.glob(str(PI / "sections" / "*.tex"))) + \
        sorted(glob.glob(str(PI / "*.tex"))) + \
        sorted(glob.glob(str(PI / "supplementary" / "*.tex")))
    files = [f for f in files if not f.endswith(".bak") and ".bak_" not in f]
    print(f"  扫描 {len(files)} 个 tex")
    print()
    hits = []
    for f in files:
        t = io.open(f, encoding="utf-8", errors="replace").read()
        base = os.path.relpath(f, PI)
        for label, pats in RULES:
            for p in pats:
                for m in re.finditer(p, t, re.I):
                    ln = t[:m.start()].count("\n") + 1
                    ctx = t[max(0, m.start() - 200):m.start() + 200]
                    low = ctx.lower()
                    allowed = any(k in low for k in ALLOW)
                    hits.append({"file": base, "line": ln, "rule": label,
                                 "match": m.group(0), "allowed": allowed,
                                 "ctx": " ".join(ctx.split())[:220]})
    bad = [h for h in hits if not h["allowed"]]
    print("=" * 108)
    print("需处理（不在撤回/否定语境里）")
    print("=" * 108)
    if not bad:
        print("  ✅ 无")
    for h in bad:
        print(f"  🔴 {h['file']}:{h['line']} 【{h['rule']}】匹配 {h['match']!r}")
        print(f"      …{h['ctx']}…")
    print()
    print(f"  命中总数 {len(hits)}（其中**允许语境** {len(hits)-len(bad)} 处）")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps({"hits": hits, "needs_action": bad}, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0 if not bad else 2


if __name__ == "__main__":
    raise SystemExit(main())
