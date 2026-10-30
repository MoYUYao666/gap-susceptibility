# -*- coding: utf-8 -*-
r"""把 `paper合/`（Paper A = P1+P2）从备选移回仓库根目录，为整改开工。

## 依据

`备选/归档清单.txt:111,115`：
  - `paper合` 于 2026-09-24 被操作者归档（P1+P2 合并稿，当时不处理与 P1 的残留重合）；
  - 移回方法：**整个目录移回仓库根目录**，`备选/归档清单.txt:118–123` 明确说明
    "**移回即恢复，不修脚本**"——14 个脚本用**字面相对路径**打开 `paper合/`，所以不能改名、不能换位置。

## 安全规则

- **不复制、只移动**（避免两份 `paper合/` 并存造成混乱）；
- 目标存在时**拒绝执行**，不覆盖；
- 移动后用**子目录与文件计数**断言完整性（归档前 65 文件，见 `文件地图.md`）。

    python tools/_restore_paperhe.py            # 预演
    python tools/_restore_paperhe.py --apply
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "备选" / "06_归档稿件" / "paper合"
DST = REPO / "paper合"
EXPECTED_FILES = 65          # 归档时记录（文件地图.md / 归档清单）


def count(d: Path) -> tuple[int, int]:
    files = [p for p in d.rglob("*") if p.is_file()]
    dirs = [p for p in d.rglob("*") if p.is_dir()]
    return len(files), len(dirs)


def main() -> int:
    apply = "--apply" in sys.argv
    if not SRC.exists():
        raise SystemExit(f"❌ 源不存在：{SRC}")
    if DST.exists():
        raise SystemExit(f"⛔ 目标已存在，拒绝覆盖：{DST}")
    nf, nd = count(SRC)
    print(f"源: {SRC.relative_to(REPO)}")
    print(f"  {nf} 文件 / {nd} 子目录（归档时记录为 {EXPECTED_FILES} 文件）")
    if nf != EXPECTED_FILES:
        print(f"  ⚠ 与记录不一致（{nf} ≠ {EXPECTED_FILES}）——请人工确认后再移")
    print(f"目标: {DST.relative_to(REPO)}")
    if not apply:
        print("\n（预演，加 --apply 生效）")
        return 0
    shutil.move(str(SRC), str(DST))
    nf2, nd2 = count(DST)
    assert DST.exists(), "移动后目标不存在"
    assert not SRC.exists(), "移动后源仍存在（应为 move 而非 copy）"
    assert nf2 == nf, f"文件数变化：{nf} → {nf2}"
    print(f"\n✅ 已移回：{DST.relative_to(REPO)}（{nf2} 文件 / {nd2} 子目录，计数一致）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
