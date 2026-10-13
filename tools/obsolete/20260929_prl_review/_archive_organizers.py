# -*- coding: utf-8 -*-
r"""把两个整理脚本自身也移入归档（保持 tools/ 根层只剩可重跑管线）。

    python tools/_archive_organizers.py [--apply]
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARCH = REPO / "tools" / "obsolete" / "20260929_prl_review"
NAMES = ["_organize_20260929.py", "_rebuild_archive_manifest.py"]


def main() -> int:
    apply = "--apply" in sys.argv
    for name in NAMES:
        src = REPO / "tools" / name
        dst = ARCH / name
        if not src.exists():
            print(f"  跳过（不存在）：{name}")
            continue
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", f"tools/{name}"],
                                 cwd=REPO, capture_output=True).returncode == 0
        print(f"  {'git mv' if tracked else 'move  '} {name} → obsolete/20260929_prl_review/")
        if apply:
            if tracked:
                r = subprocess.run(["git", "mv", f"tools/{name}", str(dst.relative_to(REPO))],
                                   cwd=REPO, capture_output=True, text=True)
                if r.returncode != 0:
                    print(f"    ⚠ git mv 失败：{r.stderr.strip()}")
                    continue
            else:
                shutil.move(str(src), str(dst))
    if not apply:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
