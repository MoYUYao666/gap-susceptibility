# -*- coding: utf-8 -*-
r"""判解码器 VLM 的 C3 缺口能否在本地补（2026-10-10）。

## C3 = 解码器 VLM 仅**单模型、单 seed、4-bit**

论文里关于它的证据（`supplement.tex` E 节）：
`outputs/vlm_strictfreeze/4bit/{both,text_only,vision_only}_seed42.json`

**要查**：
1. 那 3 个 run 的**配置**（样本量、epoch、模型）；
2. **单次 run 的耗时**（从日志/文件时间推）；
3. 本地 8 GB 能否并发/串行跑更多 seed；
4. 云端为何不能用（已实测的结论）。

    python tools\_p150_vlm_seed_feasibility.py
"""
from __future__ import annotations

import glob
import io
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    print("=" * 72)
    print("① 现有 3 个解码器 VLM run 的配置")
    print("=" * 72)
    for f in sorted(glob.glob(str(REPO / "outputs/vlm_strictfreeze/**/*.json"),
                              recursive=True)):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        print(f"\n  {Path(f).relative_to(REPO)}")
        for k in sorted(d):
            v = d[k]
            if isinstance(v, (dict, list)):
                v = f"<{type(v).__name__} len={len(v)}>"
            s = str(v)
            if len(s) > 80:
                s = s[:77] + "..."
            print(f"     {k}: {s}")

    print()
    print("=" * 72)
    print("② 训练脚本与耗时线索")
    print("=" * 72)
    sc = REPO / "tools" / "_p47_qwen_train.py"
    if sc.exists():
        t = io.open(sc, encoding="utf-8", errors="replace").read()
        print(f"  {sc.name}: {len(t.splitlines())} 行")
        for m in re.finditer(r"add_argument\(\s*'([^']+)'[^)]*default=([^,)]+)", t):
            print(f"     --{m.group(1):<14} default={m.group(2).strip()}")
    for lg in ("outputs/_qwen_vision_4bit.log", "outputs/_qwen_vlm_full.log",
               "outputs/_qwen_bf16_full.log"):
        p = REPO / lg
        if p.exists():
            print(f"\n  {lg}（{p.stat().st_size} B）：")
            lines = io.open(p, encoding="utf-8", errors="replace").read().splitlines()
            for ln in lines[-6:]:
                print("     " + ln.strip()[:110])

    print()
    print("=" * 72)
    print("③ 云端为何不能用（已有结论）")
    print("=" * 72)
    for f in ("outputs/analysis/layout_verdict.json", "outputs/analysis/data_parity.json"):
        p = REPO / f
        if p.exists():
            d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
            print(f"\n  {f}")
            for k in sorted(d)[:10]:
                v = d[k]
                if isinstance(v, (dict, list)):
                    v = f"<{type(v).__name__}>"
                print(f"     {k}: {str(v)[:100]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
