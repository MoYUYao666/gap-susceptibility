# -*- coding: utf-8 -*-
r"""整理 P3 目录：归档备份、清理过期件、重排修订包（2026-10-13）。

## 整理项（**归档而非删除** —— 保留可回退性，符合"不静默覆盖"）

| # | 项 | 处置 |
|---|---|---|
| ① | `paper3/paper_ieee/**` 的 **56 个 `.bak_*`**（1.1 MB） | 移入 **`paper3/paper_ieee/_bak_archive/`**（按原目录分层），并写 `MANIFEST.md` |
| ② | 修订包里的 **`main_REVISING.pdf`**（10-13 03:55 的 14 页**过期**版） | 移入 **`SUBMISSION/P3_PRL_revision/_superseded/`**，README 注明"已过期" |
| ③ | `SUBMISSION/` 下**同类目录并存** | **不动**（`P3_PRL` 是投稿版、`P3_PRL_revision` 是修订版、`Review_PRL` 是审稿记录），
只在 `SUBMISSION/README.md` 增补三者关系说明 |
| ④ | **两版文件对照** | 在修订包 README 里写清"投稿件 / 补充材料 / 完整版 / 已过期"四类的区别 |

**⚠️ 关键纪律**：**归档 = 移动 + 记账，不是删除**。任何"最终版"的判断都要写明依据。

    python tools\_p541_tidy_p3_folders.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"
ARCH = PI / "_bak_archive"
DEST = REPO / "SUBMISSION" / "P3_PRL_revision"
SUPERSEDED = DEST / "_superseded"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("=" * 96)
    print("① 归档 .bak_* 备份")
    print("=" * 96)
    baks = sorted(p for p in PI.rglob("*.bak*") if p.is_file())
    print(f"  找到 {len(baks)} 个（共 {sum(p.stat().st_size for p in baks)/1024:.0f} KB）")
    by_dir = {}
    for p in baks:
        rel = p.relative_to(PI).parent
        by_dir.setdefault(str(rel), []).append(p)
    for d, ps in sorted(by_dir.items()):
        print(f"     {d:<20} {len(ps):>3} 个")

    print()
    print("=" * 96)
    print("② 修订包里的过期件")
    print("=" * 96)
    stale = DEST / "manuscript" / "main_REVISING.pdf"
    print(f"  {stale.name}：存在 {stale.exists()}"
          f"{'（%.0f KB，10-13 03:55 的 14 页版）' % (stale.stat().st_size/1024) if stale.exists() else ''}")
    print(f"  ⇒ 与最终件对照：main.pdf（10 页）/ main_full.pdf（13 页）/ supplementary.pdf（5 页）")

    if not a.apply:
        print()
        print("  （预演）")
        return 0

    # ① 归档备份
    ARCH.mkdir(parents=True, exist_ok=True)
    lines = ["# `.bak_*` 备份归档（2026-10-13 整理）", "",
             "**这些是我在 P3 修订过程中每个修改脚本留下的原地备份。**",
             "**归档原因**：`paper3/paper_ieee/` 根目录与 `sections/` 下积压了 56 个备份（1.1 MB），",
             "干扰「当前版本」的辨识。**未删除** —— 全部移入本目录，按原目录分层。",
             "",
             "**权威历史**：git（`git log -- paper3/paper_ieee/sections/experiments.tex`）",
             "**每个备份的来历**：见对应脚本 `tools/_p4xx_*.py` 的 docstring。",
             "",
             "| 原位置 | 文件 | 大小 | 脚本 |", "|---|---|---|---|"]
    moved = 0
    for p in baks:
        rel = p.relative_to(PI)
        dst = ARCH / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dst))
        moved += 1
        m = __import__("re").search(r"\.bak_?(p[0-9a-z]+)$", p.name)
        script = f"`tools/_{m.group(1)}_*.py`" if m else "—"
        lines.append(f"| `{rel.parent}` | `{p.name}` | {dst.stat().st_size:,} B | {script} |")
    lines += ["", f"**合计 {moved} 个文件。**", "",
              "**⚠️ 若要回退某一版**：先确认对应脚本的意图，再从本目录复制回原位，",
              "**不要直接覆盖当前文件**（当前版本含后续修订）。"]
    io.open(ARCH / "MANIFEST.md", "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print(f"\n  ✅ 已归档 {moved} 个 → {ARCH.relative_to(REPO)}/（含 MANIFEST.md）")

    # ② 过期件
    if stale.exists():
        SUPERSEDED.mkdir(parents=True, exist_ok=True)
        shutil.move(str(stale), str(SUPERSEDED / stale.name))
        print(f"  ✅ 过期件移入 {SUPERSEDED.relative_to(REPO)}/")

    # 复核
    print()
    left = sorted(p for p in PI.rglob("*.bak*") if p.is_file())
    print(f"  复核：paper3/paper_ieee/ 残留 .bak_* = {len(left)} 个（应为 0）")
    print(f"  复核：归档目录文件数 = {sum(1 for _ in ARCH.rglob('*') if _.is_file())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
