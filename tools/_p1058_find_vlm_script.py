# -*- coding: utf-8 -*-
r"""Find the script that produced the archived Qwen2-VL batch, and report which gap definition it used.

This decides what a comparable LLaVA re-run would have to reproduce. The archive is
`outputs/analysis/vlm_bf16_detail.json` with per-seed `dg_star`, `cg`, `loss`, `dg_rel_pct` and `dg_span`.

    python tools/_p1058_find_vlm_script.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NEEDLES = ("vlm_bf16_detail", "dg_rel_pct", "dg_span", "cg_span")


def main() -> None:
    hits: dict[str, list[tuple[int, str]]] = {}
    for py in list(REPO.glob("tools/*.py")) + list(REPO.glob("exp/*.py")) + list(REPO.glob("tools/*/*.py")):
        try:
            text = io.open(py, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        found = [(i, l.strip()) for i, l in enumerate(text.splitlines(), 1)
                 if any(n in l for n in NEEDLES)]
        if found:
            hits[str(py.relative_to(REPO))] = found

    print(f"=== scripts mentioning the VLM archive ({len(hits)}) ===")
    for name, found in sorted(hits.items()):
        print(f"  {name}: {len(found)} lines")
        for i, l in found[:3]:
            print(f"     {i:>5}: {l[:110]}")

    # which gap definition does the VLM script use?
    print("\n=== gap definition used by those scripts ===")
    for name in hits:
        text = io.open(REPO / name, encoding="utf-8", errors="replace").read()
        has_w2 = bool(re.search(r"sigma|std\(", text)) and "sqrt" in text
        has_pair = bool(re.search(r"cdist|pairwise", text))
        print(f"  {name}: variance/W2-style={has_w2} | pairwise-style={has_pair}")
        m = re.search(r"def [a-z_]*gap[a-z_]*\(.*?\n(?:.*\n){0,12}", text)
        if m:
            print("     excerpt:")
            for l in m.group(0).splitlines()[:10]:
                print("       " + l[:104])


if __name__ == "__main__":
    main()
