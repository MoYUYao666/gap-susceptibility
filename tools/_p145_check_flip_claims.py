# -*- coding: utf-8 -*-
r"""核实"MS-COCO 反转排序"这一主张在论文里出现在哪、是否与其他叙述冲突（2026-10-10）。

## 已实测

`tab:position` 的 COCO 行三值同源（`outputs/coco/rq2_*`）：
`text_only=-0.041` ｜ `both=-0.052` ｜ `vision_only=+0.031`
→ **`text_only` 的间隙增长最小**（−0.041 > −0.052）→ **表里加粗 `text_only` 正确**
→ **但表注说 "MS-COCO reverses that ordering" 与数据矛盾**

    python tools\_p145_check_flip_claims.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    pats = [r"revers\w*", r"flip\w*", r"opposite order", r"ordering.{0,40}revers"]
    print("=== 所有含 reverse/flip 的句子（按文件）===")
    for f in sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for pat in pats:
            for m in re.finditer(pat, t, re.I):
                s = " ".join(t[max(0, m.start() - 330):m.start() + 300].split())
                print(f"\n[{Path(f).name}] …{s}…")

    print("\n\n=== `rq2` 那批实验的元信息（判协议）===")
    for g in ("outputs/coco/rq2_*.json", "outputs/flickr30k/rq2_*.json"):
        for f in sorted(glob.glob(str(REPO / g))):
            try:
                import json
                d = json.loads(io.open(f, encoding="utf-8").read())
            except Exception as e:
                print(f"  {Path(f).name}: 读取失败 {e}")
                continue
            keys = [k for k in d if k not in
                    ("final_gap", "initial_gap", "history", "final_retrieval")]
            print(f"\n  {Path(f).name}")
            for k in sorted(keys)[:18]:
                v = d[k]
                if isinstance(v, (dict, list)):
                    v = f"<{type(v).__name__} len={len(v)}>"
                print(f"     {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
