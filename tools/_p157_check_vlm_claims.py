# -*- coding: utf-8 -*-
r"""核对论文正文对解码器 VLM 位置排序的主张（2026-10-10）。

## 背景

- 论文 `tab:vlm`（4-bit、**单 seed**）：`both` −83.8% ｜ `text_only` −73.9% ｜ `vision_only` −11.0%
- 我的新实验（bf16、**3 seed**）：三臂差异**全部不显著**（0.84 sd / 0.07 sd）
- 且论文称 bf16 不可行（27 min 未完成 1 epoch），而**我实测 bf16 batch 2 只需 216–340 s**

**要查**：正文/摘要/结论里有没有基于这个单 seed 排序的**具体主张**。

    python tools\_p157_check_vlm_claims.py
"""
from __future__ import annotations

import glob
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

KEYS = ["decoder", "Qwen", "vlm", "VLM", "tab:vlm", "Decoder-Based"]


def main() -> int:
    print("=" * 74)
    print("① 所有提到解码器 VLM 的句子")
    print("=" * 74)
    for f in sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"[^.]{0,260}(decoder-based|Qwen2-VL|Decoder-Based VLM)"
                             r"[^.]{0,320}\.", t, re.I):
            s = " ".join(m.group(0).split())
            print(f"\n  [{Path(f).name}] …{s}…")

    print()
    print("=" * 74)
    print("② 是否引用了 tab:vlm")
    print("=" * 74)
    for f in sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex"))):
        t = io.open(f, encoding="utf-8", errors="replace").read()
        for m in re.finditer(r"ref\{tab:vlm\}|ref\{sec:vlm\}", t):
            i = t.rfind("\n", 0, m.start() - 200)
            s = " ".join(t[max(0, m.start() - 300):m.start() + 300].split())
            print(f"  [{Path(f).name}] …{s}…")
            print()

    print("=" * 74)
    print("③ 我的新结果（bf16, 3 seed）")
    print("=" * 74)
    import json
    p = REPO / "outputs" / "analysis" / "vlm_bf16_seeds_verdict.json"
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8").read())
        for arm, v in d["per_arm"].items():
            print(f"  {arm:<12} n={v['n']}  CG {v['cg_mean']:.4f} ± {v['cg_sd']}  "
                  f"逐 seed {v['cg']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
