# -*- coding: utf-8 -*-
r"""Report where Paper A's VLM material lives and what the file map says is pending for it.

Reads through Python because the console mangles the Chinese in `文件地图.md`.

    python tools/_p1050_paperA_state.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PAPER = REPO / "paper合"


def main() -> None:
    print("=== VLM / LLaVA / Qwen mentions in paper合 ===")
    pat = re.compile(r"(LLaVA|llava|VLM|Qwen|vision-language|tower-resolved|decoder)", re.I)
    for tex in sorted(PAPER.rglob("*.tex")):
        if ".bak" in tex.name:
            continue
        hits = [(i, l.rstrip()) for i, l in enumerate(io.open(tex, encoding="utf-8", errors="replace"), 1)
                if pat.search(l)]
        if hits:
            print(f"  {tex.relative_to(REPO)}: {len(hits)} lines")
            for i, l in hits[:6]:
                print(f"    {i:>4}: {l.strip()[:104]}")
            if len(hits) > 6:
                print(f"    ... {len(hits) - 6} more")

    print("\n=== numbers claimed for the VLM work (files in outputs) ===")
    for name in ("llava_sites.json", "qwen_sites.json"):
        for p in REPO.glob(f"outputs/**/{name}"):
            print(f"  {p.relative_to(REPO)}  {p.stat().st_size:,} bytes")

    print("\n=== file map: lines mentioning Paper A to-dos ===")
    mp = io.open(REPO / "文件地图.md", encoding="utf-8", errors="replace").read().splitlines()
    keys = ("待办", "待", "未完成", "下一步", "Paper A", "paper合")
    for i, l in enumerate(mp, 1):
        if any(k in l for k in keys) and len(l.strip()) > 20:
            print(f"  {i:>4}: {l.strip()[:150]}")
    print(f"  (file map has {len(mp)} lines)")


if __name__ == "__main__":
    main()
