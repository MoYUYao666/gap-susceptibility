# -*- coding: utf-8 -*-
r"""把台账的 22 条失效断言改为归档现值（2026-10-11）。

## 失效清单（门禁输出）

| 类 | 条数 | 旧 → 新 |
|---|---|---|
| `CLIP B/32@r4` 三臂 | 3 | $-0.0288/-0.0188/+0.0127$ → $-0.0304/-0.0204/+0.0166$ |
| `CLIP B/16@r4` 三臂 | 3 | $-0.0172/+0.0107/+0.0313$ → $-0.0166/+0.0124/+0.0376$ |
| `VLM`（5 seed → 13 seed） | 8 | 见 `vlm_bf16_detail.json` |
| `VLM` 种子范围 | 3 | $59.39/76.3/33.03$ → $47.8/78.77/35.72$ |
| `COCO text_only` 全秩 | 4 | $-0.0488/-0.0944/-0.1315/-0.1396$ → $-0.0247/-0.0690/-0.1153/-0.1359$ |

**规则**：只改**值**与**标签里的 seed 数**，**出处路径不动**（路径仍指向同一归档）。

    python tools\_pa_ledger_fix22.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_claim_ledger.py"

REPL = [
    # CLIP B/32@r4 三臂（3seed → 5seed）
    ('"CLIP B/32@r4 text_only CGΔ(3seed均值)", -0.0288',
     '"CLIP B/32@r4 text_only CGΔ(5seed均值)", -0.030382'),
    ('"CLIP B/32@r4 both CGΔ(3seed均值)", -0.0188',
     '"CLIP B/32@r4 both CGΔ(5seed均值)", -0.020375'),
    ('"CLIP B/32@r4 vision_only CGΔ(3seed均值)", 0.0127',
     '"CLIP B/32@r4 vision_only CGΔ(5seed均值)", 0.016577'),
    # CLIP B/16@r4 三臂
    ('"CLIP B/16@r4 text_only CGΔ(3seed均值)", -0.0172',
     '"CLIP B/16@r4 text_only CGΔ(5seed均值)", -0.016574'),
    ('"CLIP B/16@r4 both CGΔ(3seed均值)", 0.0107',
     '"CLIP B/16@r4 both CGΔ(5seed均值)", 0.012357'),
    ('"CLIP B/16@r4 vision_only CGΔ(3seed均值)", 0.0313',
     '"CLIP B/16@r4 vision_only CGΔ(5seed均值)", 0.037551'),
    # VLM 汇总（5seed → 13seed）
    ('("text_only", 67.43, 7.33, 0.1958)', '("text_only", 66.47, 8.32, 0.168)'),
    ('("vision_only", 15.76, 10.36, 0.3636)', '("vision_only", 18.03, 8.78, 0.3919)'),
    ('("both", 86.55, 8.12, 0.3228)', '("both", 87.94, 5.35, 0.2913)'),
    ('VLM {_arm} DG* 相对变化(%), n=5', 'VLM {_arm} DG* 相对变化(%), n=13'),
    ('VLM {_arm} DG* 相对变化 sd, n=5', 'VLM {_arm} DG* 相对变化 sd, n=13'),
    ('VLM {_arm} CG 跨度均值, n=5', 'VLM {_arm} CG 跨度均值, n=13'),
    # VLM 种子范围
    ('("text_only", 59.39, 76.3)', '("text_only", 47.8, 78.77)'),
    ('("vision_only", 8.51, 33.03)', '("vision_only", 8.51, 35.72)'),
    ('("both", 73.14, 95.05)', '("both", 73.14, 95.05)'),
    # COCO text_only 全秩（batch 128）
    ('("r2", -0.0488, -0.0247)', '("r2", -0.0247, -0.0247)'),
    ('("r8", -0.0944, -0.0690)', '("r8", -0.0690, -0.0690)'),
    ('("r32", -0.1315, -0.1153)', '("r32", -0.1153, -0.1153)'),
    ('("r64", -0.1396, -0.1359)', '("r64", -0.1359, -0.1359)'),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(F, encoding="utf-8").read()
    n = 0
    print("=== 逐条替换 ===")
    for old, new in REPL:
        c = t.count(old)
        mark = "✅" if c == 1 else ("⚠️" if c == 0 else "🔴")
        if c == 1:
            t = t.replace(old, new, 1)
            n += 1
        print(f"  {mark} 命中 {c}: {old[:66]}")
    print(f"  → {n}/{len(REPL)}")

    # 兜底：COCO 的旧值若以别种写法存在，直接替换数字
    for old_v, new_v in (("-0.0488", "-0.0247"), ("-0.0944", "-0.0690"),
                         ("-0.1315", "-0.1153"), ("-0.1396", "-0.1359")):
        if old_v in t:
            t = t.replace(old_v, new_v)
            print(f"  ✅ 兜底替换 {old_v} → {new_v}")

    try:
        ast.parse(t)
    except SyntaxError as e:
        print(f"  ❌ 语法错误: {e}")
        return 1
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".py.bak_fix22")
    if not bak.exists():
        io.open(bak, "w", encoding="utf-8", newline="").write(
            io.open(F, encoding="utf-8").read())
    io.open(F, "w", encoding="utf-8", newline="").write(t)
    print("  ✅ 台账已修")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
