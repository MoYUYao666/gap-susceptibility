# -*- coding: utf-8 -*-
r"""精确更正 `文件地图.md` 与 `哪篇是哪篇.md` 的 P1/P3 状态行（2026-10-07）。

上一版脚本的替换锚点与实际文本不符（我按记忆写的），故未命中，需按**磁盘实际文本**改。

实际文本（读自磁盘）：
- `哪篇是哪篇.md`：`| \`PR-D-26-10149\` | Pattern Recognition | **P1**（\`paper/\`） | Required Reviews Completed（2026-10-04） |`
- `文件地图.md` L75：`**Pattern Recognition：Required Reviews Completed（2026-09-30，意见已收齐、待编辑决定）**（PR-D-26-10149）`
- `文件地图.md` L76：`→ ✅✅ 2026-10-01 Under Review**；前身 TNNLS 已拒`
- `文件地图.md` L18：`> 📮 **2026-10-06 状态日期刷新为 Oct 06, 2026**（仍 **Under Review**；…`

    python tools\_docs_status_1007_fix.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

REPS = {
    "哪篇是哪篇.md": [
        ("| `PR-D-26-10149` | Pattern Recognition | **P1**（`paper/`） | Required Reviews Completed（2026-10-04） |",
         "| `PR-D-26-10149` | Pattern Recognition | **P1**（`paper/`） | **`Decision in Process`**（10-06；10-04 时为 Required Reviews Completed） |"),
    ],
    "文件地图.md": [
        ("**Pattern Recognition：Required Reviews Completed（2026-09-30，意见已收齐、待编辑决定）**（PR-D-26-10149）",
         "**Pattern Recognition：`Decision in Process`（2026-10-06，编辑决策中；10-04 时为 Required Reviews Completed）**（PR-D-26-10149）"),
        ("2026-10-01 Under Review**；前身 TNNLS 已拒",
         "2026-10-06 **Required Reviews Completed**（10-01 曾 Under Review）**；前身 TNNLS 已拒"),
        ("（仍 **Under Review**；来源：操作者报告 EM 列表）——详见 `HANDOFF.md` 同日条目。",
         "**🔴 该行已于 2026-10-07 更正**——当时记为仍 Under Review 系**滞后显示**，"
         "实际自 10-06 起为 **`Required Reviews Completed`**（10-07 EM 记录显示同一状态日期为该状态）。"
         "详见 `HANDOFF.md` 2026-10-07 条目。"),
    ],
}


def main() -> int:
    apply = "--apply" in sys.argv
    total = 0
    for name, reps in REPS.items():
        p = REPO / name
        t = io.open(p, encoding="utf-8").read()
        o = t
        for a, b in reps:
            if a in t:
                t = t.replace(a, b, 1)
                total += 1
                print(f"  ✅ {name}: …{a[:44]}…")
            else:
                print(f"  ⚠ {name}: 未命中 → {a[:56]}")
        if apply and t != o:
            io.open(p, "w", encoding="utf-8", newline="").write(t)

    if apply:
        # 断言：三份文档 P1 状态一致
        for f in ("HANDOFF.md", "文件地图.md", "哪篇是哪篇.md"):
            s = io.open(REPO / f, encoding="utf-8").read()
            assert "Decision in Process" in s, f"{f} 缺 Decision in Process"
        print("\n  ✅ 断言通过：三份文档均含 `Decision in Process`")
    print(f"  共 {total} 处" + ("（已写入）" if apply else "（预演）"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
