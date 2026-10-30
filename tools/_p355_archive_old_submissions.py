# -*- coding: utf-8 -*-
r"""把 `SUBMISSION/` 下**已失效的旧投稿目录**移入 `SUBMISSION/_old/`（2026-10-12）。

## 判定（依据 = 投稿状态，不是时间）

| 目录 | 依据 | 处置 |
|---|---|---|
| `A1_Neurocomputing/` | **桌面拒（2026-10-10）**，已被 `A1_NeuralNetworks/` 取代 | → `_old/` |
| `A23_OceanEngineering/` | **桌面拒（2026-09-18）**，已被 `A23_JOE/` 取代 | → `_old/` |
| `P1_PatternRecognition/` | **已被拒**（操作者 2026-10-12 确认） | → `_old/` |

**保留在 `SUBMISSION/` 根**（仍在用）：
`A1_NeuralNetworks/`、`PaperA_Neurocomputing/`、`P3_PRL/`、`Review_PRL/`、`A23_JOE/`

## 安全

- 移动前**先列清单**，移动后**逐目录核对文件数**（`_old/` 内合计应等于移动前合计）。
- 用 `git mv` 保留历史。

    python tools\_p355_archive_old_submissions.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SUB = REPO / "SUBMISSION"
OLD = SUB / "_old"
MOVES = ["A1_Neurocomputing", "A23_OceanEngineering", "P1_PatternRecognition"]


def count(d: Path) -> int:
    return len([p for p in d.rglob("*") if p.is_file()]) if d.exists() else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 88)
    print("移动前")
    print("=" * 88)
    before = {}
    for name in MOVES:
        before[name] = count(SUB / name)
        print(f"  {name:<30} {before[name]:>3} 文件")
    print(f"  合计 {sum(before.values())} 文件将被移入 _old/")

    if not a.apply:
        print("\n  （预演）")
        return 0

    OLD.mkdir(exist_ok=True)
    moved = {}
    for name in MOVES:
        src, dst = SUB / name, OLD / name
        if not src.exists():
            print(f"  ⚠️ {name} 不存在，跳过")
            continue
        if dst.exists():
            print(f"  ⚠️ {dst.name} 已存在于 _old/，跳过")
            continue
        # 优先 git mv（保留历史），失败则普通移动
        try:
            r = subprocess.run(["git", "mv", str(src), str(dst)],
                               cwd=REPO, capture_output=True, encoding="utf-8",
                               errors="replace")
            if r.returncode != 0:
                raise RuntimeError(r.stderr.strip()[:200])
        except Exception:
            shutil.move(str(src), str(dst))
        moved[name] = count(dst)

    print()
    print("=" * 88)
    print("移动后核对")
    print("=" * 88)
    ok = True
    for name in MOVES:
        if name in moved:
            same = moved[name] == before[name]
            ok = ok and same
            print(f"  {'✅' if same else '🔴'} {name:<30} {before[name]} → {moved[name]}")
    print(f"  _old/ 现有 {count(OLD)} 文件（应为 {sum(before.values())}）")
    if count(OLD) != sum(before.values()):
        ok = False
        print("  🔴 文件数不符")

    print()
    print("=" * 88)
    print("SUBMISSION/ 根目录现状")
    print("=" * 88)
    for d in sorted(SUB.iterdir()):
        if d.is_dir():
            print(f"  {d.name:<48} {count(d):>3} 文件")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
