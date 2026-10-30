# -*- coding: utf-8 -*-
r"""Organise the workspace without deleting anything: move backup files and root-level scratch into `_archive/`.

Nothing is removed. Every moved file keeps its original relative path under `_archive/`, and `MOVED.tsv` records
`old<TAB>new` so any document that cites a `.bak` path can still be resolved and so everything is one `mv` away from
being restored.

Deliberately NOT moved:
  * `tools/` -- 1402 one-off scripts are cited by path and line number from HANDOFF/docs, and the claim ledgers read
    artifact paths; reorganising them would break citations without any benefit;
  * `outputs/`, `data/`, `models/`, `paper*`, `publish_clean/`, `SUBMISSION/`, `docs/`, `src/`, `exp/`, `experiments/`
    -- live trees;
  * anything already under a directory named like an archive (`_bak_archive`, `backups`).

    python tools/_p1170_organize.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARCH = REPO / "_archive"
SKIP_DIR_NAMES = {".git", ".git-rewrite", "_archive", "backups", "_bak_archive", "publish_clean",
                  "data", "models", "outputs", "envs", "node_modules", "__pycache__"}

ROOT_SCRATCH = ["tmp_batch11_cjk_scan.json", "tmp_batch12_baseline.json", "_verify_batch2.py"]
ROOT_SCRATCH_DIRS = ["tmp_render"]


def is_backup(name: str) -> bool:
    return ".bak" in name


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    baks, scratch = [], []
    for root, dirs, files in os.walk(REPO):
        parts = set(Path(root).relative_to(REPO).parts)
        if parts & SKIP_DIR_NAMES:
            dirs[:] = []
            continue
        if any("_bak_archive" in d or d == "backups" for d in parts):
            dirs[:] = []
            continue
        for f in files:
            if is_backup(f):
                baks.append(Path(root) / f)
    for name in ROOT_SCRATCH:
        p = REPO / name
        if p.exists():
            scratch.append(p)
    for name in ROOT_SCRATCH_DIRS:
        p = REPO / name
        if p.is_dir():
            scratch.append(p)

    size = 0
    for p in baks + scratch:
        if p.is_file():
            size += p.stat().st_size
        else:
            for r, _d, ff in os.walk(p):
                for f in ff:
                    size += os.path.getsize(os.path.join(r, f))
    print(f"  backup files: {len(baks)}   scratch entries: {len(scratch)}   total {size/1024/1024:.1f} MB")
    print("  sample backups:")
    for p in baks[:6]:
        print("   ", p.relative_to(REPO))
    print("  scratch:", [str(s.relative_to(REPO)) for s in scratch])

    if not a.apply:
        print("\n  (dry run; --apply moves them under _archive/)")
        return 0

    ARCH.mkdir(exist_ok=True)
    moved = []
    for p in baks:
        rel = p.relative_to(REPO)
        dest = ARCH / "baks" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dest))
        moved.append((str(rel), str(dest.relative_to(REPO))))
    for p in scratch:
        rel = p.relative_to(REPO)
        dest = ARCH / "scratch" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dest))
        moved.append((str(rel), str(dest.relative_to(REPO))))

    with io.open(ARCH / "MOVED.tsv", "w", encoding="utf-8", newline="") as fh:
        fh.write("old_rel_path\tnew_rel_path\n")
        for old, new in moved:
            fh.write(f"{old}\t{new}\n")

    readme = """# _archive —— 归档区（**没有任何文件被删除**）

本目录由 `tools/_p1170_organize.py` 生成，目的是把散落的临时文件从工作区主视图移开，同时**保留全部内容**。

## 结构

| 目录 | 内容 |
|---|---|
| `baks/` | 全部 `*.bak*` 历史备份，**保留原来的相对路径**（如 `paper合/sections/x.tex.bak_p123` → `_archive/baks/paper合/sections/x.tex.bak_p123`）|
| `scratch/` | 根目录的临时脚本与临时渲染目录（`tmp_batch*.json`、`_verify_batch2.py`、`tmp_render/`）|
| `MOVED.tsv` | 逐条映射 `old_rel_path → new_rel_path`，可直接据此还原 |

## 还原方法

```powershell
# 单条还原：查 MOVED.tsv，把文件移回旧路径
python -c "import shutil,io; [shutil.move(n, o) for o,n in (l.rstrip().split('\t') for l in io.open('_archive/MOVED.tsv',encoding='utf-8').read().splitlines()[1:])]"
```

## 纪律

- **只移动、不删除**；移动前路径可查 `MOVED.tsv`；
- **不动** `tools/`（1,402 个一次性脚本被文档按路径与行号引用）、`outputs/`（结果溯源）、`data/`、`models/`、
  `paper*`（稿件树）、`publish_clean/`、`SUBMISSION/`、`docs/`、`src/`、`exp/`、`experiments/`；
- 已经在归档目录里的（`paper3/paper_ieee/_bak_archive/`、`backups/`）不再二次搬动。
"""
    (ARCH / "README.md").write_text(readme, encoding="utf-8")
    print(f"\n  moved {len(moved)} entries into _archive/")
    print("  wrote _archive/MOVED.tsv and _archive/README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
