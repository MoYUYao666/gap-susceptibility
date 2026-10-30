# -*- coding: utf-8 -*-
r"""自查：A1 的"零开销监控器"卖点在正文里是否兑现（2026-10-12）。

## 为什么

新标题把 *"**Zero-Overhead Monitor**"* 放在最前 → **这是全篇最重要的主张**。
若正文只是"τ 与准确率相关"，而没有**"监控器"该有的东西**（阈值／何时报警／实际何时用），
那么编辑会认为**标题承诺了正文没给的东西**——比原来的否定式标题更危险。

**本脚本**：把正文里与 monitor / overhead / threshold / signal 相关的句子全抽出来，逐条判。

    python tools\_p199_monitor_claim.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper_a1" / "main.tex"
RW = REPO / "paper_a1" / "related_work.tex"
OUT = REPO / "outputs" / "analysis" / "a1_monitor_claim.json"

KEYS = ["zero-overhead", "zero overhead", "monitor", "monitoring", "overhead",
        "threshold", "early", "training-time", "health signal", "checkpoint selection"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    text = ""
    for f in (MAIN, RW):
        if f.exists():
            text += io.open(f, encoding="utf-8", errors="replace").read() + "\n"

    print("=" * 84)
    print("与「监控」相关的句子（逐条）")
    print("=" * 84)
    hits = {}
    for k in KEYS:
        ms = list(re.finditer(re.escape(k), text, re.I))
        if not ms:
            continue
        hits[k] = len(ms)
        print(f"\n── 「{k}」{len(ms)} 处 ──")
        for m in ms[:4]:
            s = " ".join(text[max(0, m.start() - 300):m.start() + 340].split())
            print(f"   • {s[:440]}")
    print()
    print("=" * 84)
    print("覆盖统计")
    print("=" * 84)
    for k in KEYS:
        print(f"  {k:<22} {hits.get(k, 0)} 次")

    # 判定
    print()
    print("=" * 84)
    print("判定：正文是否给出「监控器」的三要素？")
    print("=" * 84)
    checks = {
        "① 可算性（无额外开销）": r"top-\$?k\$? (class )?sets|already (available|computed)|validation pass",
        "② 何时报警（阈值/趋势）": r"threshold|alarm|warn|falls below|erosion.*earlier|earlier.*than top-1",
        "③ 实际用它做过决策": r"we (use|used|select|selected|chose).{0,60}(tau|\\tau)|"
                              r"(tau|\\tau).{0,40}(select|choose|early stop)",
    }
    for tag, pat in checks.items():
        ms = list(re.finditer(pat, text, re.I))
        print(f"  {'✅' if ms else '🔴'} {tag}（{len(ms)} 处）")
        for m in ms[:2]:
            s = " ".join(text[max(0, m.start() - 200):m.start() + 260].split())
            print(f"       …{s[:380]}…")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"keyword_counts": hits, "checks": checks}, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
