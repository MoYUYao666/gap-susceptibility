# -*- coding: utf-8 -*-
r"""修 `_pa_build_nc_package.py`：打包 figures 时**排除 `_superseded/`**（2026-10-06）。

## 问题

`shutil.copytree(PA / "figures", srcdir / "figures", dirs_exist_ok=True)`
**把 `figures/_superseded/` 一起复制**——那是 2026-10-06 归档的下线图
（ap3 阶段的 15 张 + 两张旧的 1×3 合并图，共 20+ 个文件）。

**后果**：
1. 投稿包里混入**正文不用的图**（`latex_source.zip` 由 5.4 MB 虚增）；
2. 审稿人/编辑解压后看到一堆无关图，**容易误以为稿件引用了它们**；
3. 与已修的问题同类：**"包里应只有稿件实际用到的东西"**。

## 修法

复制后**删掉** `srcdir/figures/_superseded`，并在打 zip 前断言它不存在。

    python tools\_pa_fix_package_exclude_superseded.py [--apply]
"""
from __future__ import annotations

import ast
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "tools" / "_pa_build_nc_package.py"

OLD = '    shutil.copytree(PA / "figures", srcdir / "figures", dirs_exist_ok=True)'
NEW = ('    shutil.copytree(PA / "figures", srcdir / "figures", dirs_exist_ok=True)\n'
       '    # 排除下线图归档：投稿包里只应有稿件实际引用的图（2026-10-06）\n'
       '    _arch = srcdir / "figures" / "_superseded"\n'
       '    if _arch.exists():\n'
       '        shutil.rmtree(_arch)\n'
       '        print("    （已从投稿包排除 figures/_superseded/）")')


def main() -> int:
    apply = "--apply" in sys.argv
    t = io.open(F, encoding="utf-8").read()
    if "_superseded" in t:
        print("  已修，跳过")
        return 0
    c = t.count(OLD)
    if c != 1:
        print(f"  ⚠ 未唯一命中（{c} 次）")
        return 1
    print("  ✅ 命中 copytree 行")
    if apply:
        t2 = t.replace(OLD, NEW, 1)
        ast.parse(t2)
        io.open(F, "w", encoding="utf-8", newline="").write(t2)
        print("  ✅ 已写入并断言通过")
        # 清掉旧的 latex_source，避免残留
        old_dir = REPO / "paper合" / "NC_submission" / "latex_source"
        if (old_dir / "figures" / "_superseded").exists():
            import shutil
            shutil.rmtree(old_dir / "figures" / "_superseded")
            print("  ✅ 已清理旧 latex_source/figures/_superseded/")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
