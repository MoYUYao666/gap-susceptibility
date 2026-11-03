# -*- coding: utf-8 -*-
r"""修发布库的两处非英文残留（2026-10-14）。

## 我的第 36 个错

`publish_clean/.gitignore` **不是合法 UTF-8** —— 我用 **PowerShell `Add-Content`** 追加了两段中文注释，
而 **PowerShell 默认按系统 ANSI（中文 Windows = GBK）写** ⇒ 文件混入 GBK 字节 ⇒
`utf-8` 解码在偏移 2027 失败。

**⇒ 修复**：整份重写为**纯 ASCII 英文**（也消除"英文库里出现中文"的问题）。

**⚠️ 教训**：**向已存在的 UTF-8 文件追加内容，绝不能用 PowerShell 的 `Add-Content`/`Out-File`**
（与 `Get-Content -Raw | Set-Content` 那次同类）。**必须用 Python 显式 `encoding="utf-8", newline=""` 写。**

## 另两处：全角标点

| 文件 | 内容 | 处置 |
|---|---|---|
| `tools/ap3_a1_revision_check.py` | `print(' n=3: %s；n=1: %s')` 里的**全角分号 `；`** | 改 ASCII `;` |
| `tools/clip_ocean_rank1_bound.py` | docstring 里的**全角句号 `。`** | 改 `.` |

    python tools\_p605_fix_gitignore_punct.py [--apply]
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

GITIGNORE = """# Byte-compiled / cache
__pycache__/
*.py[cod]
*.pyc
.pytest_cache/

# Virtual environments
.venv/
venv/
env/

# Model weights and large binaries (never published)
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

# Archives
*.zip
*.tar
*.tar.gz
*.7z
*.rar

# Media
*.mp4
*.avi
*.mov
*.wav
*.mp3

# Logs and run output
*.log
outputs/_cloud_layout/

# Local backups (never published)
*.bak
*.bak_*
*.orig

# Datasets (obtainable from their own sources)
data/
datasets/
flickr30k/
coco/

# Internal documentation (reviewer reports, response plans, venue decisions)
docs/

# One-off and archived revision scripts
tools/obsolete/

# Manuscripts and submission material (this repository holds code and results only)
paper/
paper2/
paper3/
paper_a1/
paper_a2/
paper_a23/
paper合/
paper_ap3/
main*.tex
main*.pdf
cover_letter*
title_page*
highlights*
*.docx
*.doc
SUBMISSION/

# Editor / OS noise
.DS_Store
Thumbs.db
.idea/
.vscode/
"""

PUNCT_FIXES = [
    ("tools/ap3_a1_revision_check.py", "；", ";"),
    ("tools/clip_ocean_rank1_bound.py", "。", "."),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    # ① .gitignore
    gi = PC / ".gitignore"
    old = gi.read_bytes()
    print(f"  ① .gitignore：{len(old):,} 字节")
    try:
        old.decode("utf-8")
        print("     当前是合法 UTF-8")
    except UnicodeDecodeError as e:
        print(f"     🔴 非法 UTF-8：{e}")
    print(f"     新版本（纯 ASCII 英文）：{len(GITIGNORE):,} 字符 / "
          f"{len(GITIGNORE.encode('utf-8')):,} 字节")

    # ② 全角标点
    print()
    print("  ② 全角标点")
    edited = []
    for rel, bad, good in PUNCT_FIXES:
        p = PC / rel
        if not p.exists():
            print(f"     🔴 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(bad)
        # 只改**代码/文档文本**里的全角标点（此处两处都不是 CJK 关键功能串）
        print(f"     {rel:<44} 含「{bad}」{n} 处 → 「{good}」")
        if n and a.apply:
            bak = p.with_suffix(p.suffix + ".bak_p605")
            if not bak.exists():
                shutil.copy2(p, bak)
            io.open(p, "w", encoding="utf-8", newline="").write(t.replace(bad, good))
            edited.append(rel)

    if not a.apply:
        print("  （预演）")
        return 0

    shutil.copy2(gi, gi.with_suffix(".bak_p605"))
    io.open(gi, "w", encoding="utf-8", newline="").write(GITIGNORE)

    # 复核
    print()
    print("  ③ 复核")
    b = gi.read_bytes()
    try:
        b.decode("utf-8")
        print(f"     ✅ .gitignore 现为合法 UTF-8（{len(b)} 字节，纯 ASCII：{b.decode('ascii', 'ignore') == b.decode('utf-8')}）")
    except UnicodeDecodeError as e:
        print(f"     🔴 仍非法：{e}")
    import ast
    for rel, _, _ in PUNCT_FIXES:
        p = PC / rel
        t = io.open(p, encoding="utf-8").read()
        cjk_p = len(re.findall(r"[\u3000-\u303f\uff00-\uffef]", t))
        if p.suffix == ".py":
            ast.parse(t)
        print(f"     {rel:<44} 全角标点残留 {cjk_p} ｜ ast={'OK' if p.suffix=='.py' else 'n/a'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
