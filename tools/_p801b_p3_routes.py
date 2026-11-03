# -*- coding: utf-8 -*-
r"""Check whether P3's text depends on the sixteen affected CLIP runs.

P3's rank claims come from the LLaVA and Qwen experiments, which use HuggingFace peft and are
unaffected. The sixteen affected runs are the CLIP route_c/d/e experiments, so the remaining question
is whether P3 cites any of their numbers.

    python tools/_p801b_p3_routes.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P3 = REPO / "paper3" / "paper_ieee"
OUT = REPO / "outputs" / "analysis" / "p3_route_dependency.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    keys = ["route_c", "route_d", "route_e", "Route C", "Route D", "Route E",
            "c1_gapreg", "c3_gapinit", "d1_alpha64", "d2_r4_alpha64", "d5_r16_alpha64",
            "e1_dges", "e3_dges", "gap_reg", "GapReg", "gap-reg"]
    print("=" * 104)
    print("references to the affected CLIP route experiments in P3")
    print("=" * 104)
    hits = {}
    for f in sorted(P3.rglob("*.tex")):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for k in keys:
            for m in re.finditer(re.escape(k), t, re.I):
                ln = t[:m.start()].count("\n") + 1
                seg = " ".join(t[max(0, m.start() - 130):m.start() + 190].split())
                hits.setdefault(str(f.relative_to(P3)), []).append((k, ln, seg[:260]))
    if not hits:
        print("  none")
    for f, rows in hits.items():
        print()
        print(f"  {f}: {len(rows)} hit(s)")
        for k, ln, seg in rows[:4]:
            print(f"     L{ln} [{k}] {seg[:230]}")
    print()
    print("=" * 104)
    print("P3's own experiment sources, by script")
    print("=" * 104)
    for p in sorted((REPO / "paper3" / "scripts").rglob("*.py")):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        peft = "get_peft_model" in t
        print(f"  {p.relative_to(REPO / 'paper3' / 'scripts')!s:<40} peft={peft}")
    print()
    print("  a run is affected only if it was produced by the custom wrapper in src/lora.py;")
    print("  the LLaVA and Qwen scripts import HuggingFace peft, which freezes the base model.")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"references": {k: len(v) for k, v in hits.items()}},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
