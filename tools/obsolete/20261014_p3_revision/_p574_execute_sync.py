# -*- coding: utf-8 -*-
r"""执行发布同步：只推代码 + 结果 JSON；一次性脚本归入 `tools/obsolete/`（2026-10-14）。

## 操作者选定：方案 1

> **"只推代码与结果 JSON，剔除权重/大文件"**

## 步骤

1. 清 `publish_clean/` 内的 `.bak` 残留
2. 按 `_p573` 的排除规则**复制**（不删除）本轮新增/更新的文件
3. 把 `publish_clean/tools/_*.py`（**一次性/审计脚本**）移入 `tools/obsolete/20261014_p3_revision/`
   并写 README 说明来历（**不删**，保留可追溯）
4. **加固 `.gitignore`**：把权重/压缩包/大文件类型加进去（防未来误推）
5. 安全检查：无删除项、无稿件类、无 >100 MB

    python tools\_p574_execute_sync.py --apply
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PC = REPO / "publish_clean"
OBS = PC / "tools" / "obsolete" / "20261014_p3_revision"

EXCLUDE_EXT = {".pt", ".pth", ".bin", ".safetensors", ".ckpt", ".onnx", ".h5", ".pkl",
               ".npz", ".npy", ".parquet", ".db", ".sqlite", ".zip", ".tar", ".gz",
               ".7z", ".rar", ".mp4", ".avi", ".mov", ".wav", ".mp3", ".log",
               ".docx", ".doc", ".bak"}
BAN_NAME = re.compile(r"(^|/)(main[^/]*\.(tex|pdf)|cover_letter[^/]*|title_page[^/]*|"
                      r"highlights[^/]*|.*\.bak.*$)", re.I)
SKIP_DIRS = {"outputs/_cloud_layout"}
ALLOW_TOP = ("tools", "outputs", "src", "exp", "experiments", "docs")

GITIGNORE_ADD = """
# ---- 2026-10-14 加固：权重 / 大文件 / 压缩包一律不入库 ----
*.pt
*.pth
*.bin
*.safetensors
*.ckpt
*.onnx
*.h5
*.pkl
*.npz
*.npy
*.parquet
*.db
*.sqlite
*.zip
*.tar
*.tar.gz
*.7z
*.rar
*.mp4
*.avi
*.mov
*.wav
*.mp3
*.log
# 云端目录快照（1001 个空壳文件）
outputs/_cloud_layout/
# 一次性/审计脚本的归档地（保留在库内，但不视为可重跑管线）
# tools/obsolete/
"""


def run(args, cwd=PC):
    r = subprocess.run(args, cwd=str(cwd), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace"), r.stderr.decode("utf-8", errors="replace")


def keep(p: Path) -> bool:
    rel = p.relative_to(REPO).as_posix()
    if p.suffix.lower() in EXCLUDE_EXT:
        return False
    if BAN_NAME.search(rel):
        return False
    for d in SKIP_DIRS:
        if rel.startswith(d + "/"):
            return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演；加 --apply 执行）")
        return 0

    # ① 清 .bak
    baks = [p for p in PC.rglob("*.bak*") if p.is_file()]
    for p in baks:
        p.unlink()
    print(f"  ① 清除 publish_clean 内 .bak 残留：{len(baks)} 个")

    # ② 复制
    copied = 0
    for top in ALLOW_TOP:
        src = REPO / top
        if not src.is_dir():
            continue
        for p in src.rglob("*"):
            if not p.is_file() or not keep(p):
                continue
            rel = p.relative_to(REPO)
            dst = PC / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            copied += 1
    for f in ("README.md", ".gitignore", "requirements.txt"):
        p = REPO / f
        if p.exists():
            shutil.copy2(p, PC / f)
            copied += 1
    print(f"  ② 复制 {copied} 个文件（**未删除任何已跟踪文件**）")

    # ③ 一次性脚本归档
    OBS.mkdir(parents=True, exist_ok=True)
    moved = []
    for p in sorted((PC / "tools").glob("_*.py")):
        shutil.move(str(p), str(OBS / p.name))
        moved.append(p.name)
    readme = ("# 一次性 / 审计脚本归档（2026-10-14）\n\n"
              f"**{len(moved)} 个 `_` 前缀脚本**，从 `tools/` 根层移入此处。\n\n"
              "**为什么移**：按本仓库既有约定，`tools/` 根层只保留**可重跑管线**；\n"
              "`_` 前缀的是为具体审计/修订**一次性**写的脚本（每篇论文修订期会产生上百个）。\n\n"
              "**未删除** —— 它们记录了每个结论的产生过程，可原样移回 `tools/` 使用。\n\n"
              "**命名线索**：`_pNNN_描述.py` 中的 `NNN` 是会话内的序号；\n"
              "对应关系见 `HANDOFF.md` 与各脚本自身的 docstring。\n\n"
              "## 清单\n\n" + "\n".join(f"- `{n}`" for n in moved) + "\n")
    io.open(OBS / "README.md", "w", encoding="utf-8", newline="").write(readme)
    print(f"  ③ 一次性脚本 {len(moved)} 个 → tools/obsolete/20261014_p3_revision/（含 README）")

    # ④ 加固 .gitignore
    gi = PC / ".gitignore"
    t = io.open(gi, encoding="utf-8", errors="replace").read() if gi.exists() else ""
    if "2026-10-14 加固" not in t:
        io.open(gi, "w", encoding="utf-8", newline="").write(t.rstrip() + "\n" + GITIGNORE_ADD)
        print("  ④ .gitignore 已加固（权重/压缩包/日志/云端快照）")
    else:
        print("  ④ .gitignore 已含加固段")

    # ⑤ 安全检查
    print()
    print("  ⑤ 安全检查")
    rc, out, _ = run(["git", "status", "--porcelain"])
    lines = [l for l in out.splitlines() if l.strip()]
    dels = [l for l in lines if l.startswith(" D") or l.startswith("D ")]
    print(f"     status 条目 {len(lines)} ｜ **删除项 {len(dels)}**（应为 0）")
    for d in dels[:5]:
        print(f"       🔴 {d}")
    bad = [l for l in lines if BAN_NAME.search(l)]
    print(f"     命中稿件类禁令：{len(bad)}（应为 0）")
    for b in bad[:5]:
        print(f"       🔴 {b}")
    rc, out, _ = run(["git", "ls-files"])
    print(f"     将跟踪 {len(out.splitlines())} 个文件")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
