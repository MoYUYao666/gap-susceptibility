# -*- coding: utf-8 -*-
r"""Append the current remote state to 文件地图.md without rewriting history.

The map still describes the remote as 1ca7744 with 1303 files. That is now stale: the remote is
e6f67dd with 2060 files after the ignore-rule fix. Per the project rule, stale statements are
marked stale and the new value appended rather than silently overwritten.

    python tools/_p735_map_update.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
M = REPO / "文件地图.md"

BLOCK = """> **📌 2026-10-15 00:45 —— 远端与 `.gitignore` 现状更新（上方 L219-L238 的 `1ca7744` / 1303 文件已过期）**
>
> | 项 | 旧记录（**过期**） | **现行（实测 2026-10-15）** |
> |---|---|---|
> | 远端 `main` | `1ca7744` | **`e6f67dd`** |
> | 已跟踪文件数 | 1,303 | **2,060** |
> | 核对命令 | — | `git -C publish_clean ls-remote ssh-origin main` |
>
> **本阶段改动**：
>
> 1. **`.gitignore` 四条数据集规则加前导斜杠锚定**（`coco/` → `/coco/`，同理 `flickr30k/`、`data/`、`datasets/`）。
>    **原因**：裸规则**无前导斜杠 ⇒ 匹配任意层级**，把 `outputs/theory/coco/`、`outputs/coco/`、
>    `outputs/flickr30k/` 等**结果目录**也排除了；规则本意只是根目录的数据集。
>    **⇒ 影响**：锚定后新暴露 **113 个未跟踪结果 JSON**（0.14 MB，零违禁内容），已全部收录。
>    **⇒ 修复前**：Paper A 台账的 96 个 `outputs/theory/**/dg_star_history.json` 里**只有 87 个入库**
>    ⇒ 审稿人从公开仓库数不出稿件声称的拟合总数。
> 2. **推送**：`2b48e40..e6f67dd  main -> main` ✅
> 3. **Paper A 的 α 统计按归档改写**（222/203 → **215/196**，例外仍为 **19**）——
>    详见 `HANDOFF.md` 顶部 2026-10-15 条目。
>
> **远端现状核对（2026-10-15 实测）**：
> - `outputs/theory/**` 下 `dg_star_history.json` = **96**（= `_p1_ledger.py` 的 glob 口径，**可复现**）
> - `outputs/**` 下另有 `coco_sweep_dgstar/` **2** 个，**不属**台账口径
> - 稿件类 / 权重 / ≥100 MB 文件 = **全部 0** ✅
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(M, encoding="utf-8").read()
    if "远端与 `.gitignore` 现状更新" in t:
        print("  already recorded")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0
    lines = t.splitlines(keepends=True)
    # insert after the publish_clean discussion block, before the next table row
    idx = None
    for i, l in enumerate(lines):
        if "现状核对命令" in l:
            idx = i + 1
            break
    if idx is None:
        for i, l in enumerate(lines):
            if "publish_clean/`" in l:
                idx = i + 1
    if idx is None:
        print("  anchor not found; appending at the end")
        idx = len(lines)
    out = "".join(lines[:idx]) + "\n" + BLOCK + "\n" + "".join(lines[idx:])
    io.open(M, "w", encoding="utf-8", newline="").write(out)
    t2 = io.open(M, encoding="utf-8").read()
    for k in ("远端与 `.gitignore` 现状更新", "e6f67dd", "2,060", "/coco/", "113 个未跟踪"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  文件地图.md lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
