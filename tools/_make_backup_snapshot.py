# -*- coding: utf-8 -*-
"""把工作区打成一份完整快照 zip（默认排除可重新下载的数据集与权重）。

约定（2026-09-24 操作者确认）：
  排除：`data/` `models/` `coco/` `flickr30k/`（合计约 120 GB，均可重新下载或按
        "模型只在服务器下载"的规则重新获取）
  包含：其余全部 —— 稿件、`outputs/`（12 GB 溯源 JSON）、`tools/`、`docs/`、`src/`、
        `exp/`、`experiments/`、`SUBMISSION/`、`备选/`（含两份归档稿件）、
        `HANDOFF.md` 等文档，以及 **`.git/`（含全部历史）** 与 `.worktrees/`

刻意排除：
  * `backups/` 自身与任何 `.zip/.7z/.tar.gz` 备份产物 —— 否则下一次备份会把上一次的备份打进去，体积指数增长
  * `备选/03_检查与备份产物/` —— 操作者已指定删除（属"旧备份"）
  * `cloud_upload/` —— 同上
  * `envs/` 默认包含（仅 103 MB，且含环境清单）；如需排除加 `--exclude-envs`

    python tools/_make_backup_snapshot.py [--out DIR] [--name FILE.zip] [--dry-run]

输出：`backups/<name>` + 同名 `.sha256` 校验文件 + `<name>.manifest.txt` 条目清单。
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# 顶层目录/文件排除（可重新下载的数据集与权重）
EXCLUDE_TOP_DIRS = {"data", "models", "coco", "flickr30k"}
# 指定删除的旧备份
EXCLUDE_PATHS = {
    "cloud_upload",
    "备选/03_检查与备份产物",
}
# 备份产物自身（按后缀，任意层级）
EXCLUDE_SUFFIXES = (".zip", ".7z", ".tar.gz", ".tgz", ".rar")
# 这些目录名直接整个跳过（git 内部无关目录）
EXCLUDE_DIR_NAMES = {".git-rewrite", "backups"}


def should_skip(rel: str, is_dir: bool, exclude_envs: bool) -> bool:
    rel_posix = rel.replace("\\", "/")
    parts = rel_posix.split("/")
    if not parts or not parts[0]:
        return False
    if parts[0] in EXCLUDE_TOP_DIRS:
        return True
    if exclude_envs and parts[0] == "envs":
        return True
    if any(p in EXCLUDE_DIR_NAMES for p in parts):
        return True
    # 顶层路径前缀匹配
    for ex in EXCLUDE_PATHS:
        if rel_posix == ex or rel_posix.startswith(ex + "/"):
            return True
    # 备份产物后缀（文件）
    if not is_dir and rel_posix.lower().endswith(EXCLUDE_SUFFIXES):
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(REPO / "backups"))
    ap.add_argument("--name", default=None)
    ap.add_argument("--compression", choices=["fast", "normal"], default="fast")
    ap.add_argument("--exclude-envs", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out)
    name = args.name or f"snapshot_{time.strftime('%Y%m%d_%H%M')}.zip"
    out_path = out_dir / name

    level = zipfile.ZIP_DEFLATED
    compresslevel = 1 if args.compression == "fast" else 6

    files: list[tuple[Path, str, int]] = []
    total = 0
    for root, dirs, fnames in os.walk(REPO):
        rel_root = os.path.relpath(root, REPO)
        rel_root = "" if rel_root == "." else rel_root
        # 目录剪枝
        dirs[:] = [d for d in dirs if not should_skip(os.path.join(rel_root, d), True, args.exclude_envs)]
        for fn in fnames:
            rel = os.path.join(rel_root, fn) if rel_root else fn
            p = Path(root) / fn
            try:
                size = p.stat().st_size
            except OSError:
                continue
            if should_skip(rel, False, args.exclude_envs):
                continue
            files.append((p, rel.replace("\\", "/"), size))
            total += size

    print(f"待打包文件: {len(files)} 个，合计 {total / 1024**3:.2f} GB")
    print(f"输出: {out_path}")
    if args.dry_run:
        print("--dry-run：未写文件")
        for p, rel, size in sorted(files, key=lambda x: -x[2])[:15]:
            print(f"  {size / 1024**2:>10.1f} MB  {rel}")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    written = 0
    with zipfile.ZipFile(out_path, "w", compression=level, compresslevel=compresslevel, allowZip64=True) as z:
        for i, (p, rel, size) in enumerate(files, 1):
            try:
                z.write(p, arcname=rel)
                written += 1
            except OSError as e:
                print(f"  ⚠ 跳过 {rel}: {e}")
            if i % 2000 == 0:
                print(f"  ... {i}/{len(files)}  ({time.time() - t0:.0f}s)")

    # 校验和
    h = hashlib.sha256()
    with open(out_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    digest = h.hexdigest()
    (out_dir / (name + ".sha256")).write_text(f"{digest}  {name}\n", encoding="utf-8")

    # 清单
    with open(out_dir / (name + ".manifest.txt"), "w", encoding="utf-8") as f:
        f.write(f"# {name}\n# files={written} bytes={total} sha256={digest}\n")
        for p, rel, size in sorted(files, key=lambda x: x[1]):
            f.write(f"{size}\t{rel}\n")

    zsize = out_path.stat().st_size
    print(f"\n完成：{written}/{len(files)} 个文件，用时 {time.time() - t0:.0f}s")
    print(f"  zip    : {zsize / 1024**3:.2f} GB  ({out_path})")
    print(f"  原始   : {total / 1024**3:.2f} GB   压缩比 {100 * zsize / max(total, 1):.1f}%")
    print(f"  sha256 : {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
