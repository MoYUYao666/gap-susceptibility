# -*- coding: utf-8 -*-
r"""落定 ap3 的处置：**方案 B**（操作者 2026-10-05 决定）。

## 决定

> 操作者选 **B**：**保留 `paper_ap3/` 目录，但明确标注"不可投"**，仅作 P1+P2+P3 合并的**技术参考**。

## 为什么不是 A（归档）

A 会把 ap3 移除/归档；B **保留其作为技术参考的价值**（含 Representation Theorem、GFAP、
跨架构分配等 P3 理论构件的**完整推导**，而这些在已投 PRL 的 11 页 `paper3/` 里被压缩了）。
**代价**：目录仍在根目录，可能被误当可投稿——**故必须在显眼处标注不可投**。

## 本脚本做什么

1. `HANDOFF.md`：在 ap3 结论条目上追加"**方案 B 已定案**"；
2. `文件地图.md`：把先前的"建议归档"改为"**B 已定案：保留但不可投**"；
3. **在 `paper_ap3/` 目录内放一个显眼的 `⚠️_不可投_READ_ME.md`**——
   让任何进入该目录的人（包括未来的我）第一眼就知道它不可投、以及为什么。

    python tools\_docs_ap3_optionB.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
AP3 = REPO / "paper_ap3"

README = r"""# ⚠️ 本目录不可投（NOT SUBMITTABLE）

> 定案日期：**2026-10-05** ｜ 决定人：操作者（方案 B）

## 一句话

**这是 P1 + P2 + P3 的合并稿（86 页），不能投任何期刊。**

## 为什么

| 原因 | 说明 |
|---|---|
| **含 P3 内容** | `paper_ap3/sections/` 里 **Representation Theorem 出现 9 处、GFAP 出现 11 处**，与 `paper3/` 共享同一套核心理论构件 |
| **P3 已在审** | P3 已于 **2026-09-26** 投 *Pattern Recognition Letters*（稿号 **`PRLETTERS-D-26-02378`**，Regular Article，Under Review）→ **投 ap3 即一稿两投** |
| **去掉 P3 也无用** | ap3 去掉 P3 后就是 **P1 + P2**，**等同 `paper合/`**（43 页，已在编且更完整） |
| **P1 未定** | ap3 原受 P1 决定红线约束；但**即使 P1 被拒**，上面两条依然成立 |

## 三条分支穷举

| P1 结果 | 能否投 ap3 | 原因 |
|---|---|---|
| 接收 | ❌ | P1 内容已另行发表，ap3 失去意义 |
| 拒稿 | ❌ | 红线解除，但含 P3 与 PRL 在审稿重叠；去掉 P3 等同 `paper合` |
| 修回 | ❌ | 红线仍在，P3 重叠不变 |

## 那它有什么用（B 方案的意义）

**作为技术参考保留**：本目录含 P3 理论构件的**完整推导**（Representation Theorem、GFAP 及其推论、
跨架构分配），而已投 PRL 的 `paper3/` 只有 **11 页**，这些推导被大幅压缩。
**需要完整推导时来这里看，但不要把这里的内容投出去。**

## 唯一可能复活的情形

**若 P3 被 PRL 拒稿** → 重新评估 ap3（P3 归位后或可作为整体投出）。
**这是未来事件，当前不围绕它做任何工作。**

## 现在该投什么

| 稿件 | 范围 | 页数 | 状态 |
|---|---|---|---|
| **`paper合/`** | P1 + P2 | 43 | ✅ **在编主稿**（目标 Neurocomputing），已过投稿前审核 |
| `paper3/` | P3 | 11 | 🏃 已投 PRL `PRLETTERS-D-26-02378`，在审 |

## 出处

- 决定：操作者 2026-10-05 选 **B**
- 记录：`HANDOFF.md`、`文件地图.md`（ap3 条目）
- 核实脚本与证据见 `HANDOFF.md` 的"ap3 已无可投路径"条目
"""


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0

    # ① 目录内放显眼 README
    dst = AP3 / "⚠️_不可投_READ_ME.md"
    if not dst.exists():
        print("  ✅ 将新建 paper_ap3/⚠️_不可投_READ_ME.md")

    # ② HANDOFF：追加 B 定案
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    add_h = ("\n> **✅ 2026-10-05 定案（方案 B）**：操作者选择 **B —— 保留 `paper_ap3/` 目录，"
             "但明确标注不可投**，仅作 P1+P2+P3 合并的**技术参考**。\n"
             "> 理由：本目录含 P3 理论构件的**完整推导**（Representation Theorem、GFAP、跨架构分配），"
             "而已投 PRL 的 `paper3/` 仅 11 页、推导被压缩——**保留其参考价值**。\n"
             "> **防误用**：已在 `paper_ap3/⚠️_不可投_READ_ME.md` 写明「不可投」及原因，"
             "并在 `文件地图.md` 的 ap3 条目标注。\n")
    if "定案（方案 B）" not in t:
        n += 1

    # ③ 文件地图：把"建议归档"改成 B 定案
    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    old = "**🗂️ 2026-10-05 结论：ap3 已无可投路径，建议归档。**"
    new = ("**🗂️ 2026-10-05 结论：ap3 已无可投路径。✅ 方案 B 已定案：保留目录但不可投"
           "（仅作技术参考；目录内已放 `⚠️_不可投_READ_ME.md`）。**")
    has_old = old in m
    if has_old:
        n += 1
    m_add = ("\n> **✅ 2026-10-05 方案 B 定案**：ap3 **保留**（不归档），但**标注不可投**。"
             "目录内新增 `paper_ap3/⚠️_不可投_READ_ME.md`（写明三条分支均不可投、"
             "以及它作为 P3 理论构件完整推导的参考价值）。\n")
    if "方案 B 定案" not in m:
        n += 1

    print(f"  待改 {n} 处")

    if apply:
        io.open(dst, "w", encoding="utf-8", newline="").write(README)
        s = io.open(dst, encoding="utf-8").read()
        for k in ("不可投", "PRLETTERS-D-26-02378", "一稿两投", "复制"[:0] + "paper3/"):
            assert k in s, f"README 断言失败：缺 {k}"
        print(f"  ✅ 已写 {dst.relative_to(REPO)}")

        if "定案（方案 B）" not in t:
            io.open(hp, "w", encoding="utf-8", newline="").write(t.rstrip() + add_h)
            t2 = io.open(hp, encoding="utf-8").read()
            assert "定案（方案 B）" in t2 and "不可投_READ_ME" in t2
            print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

        if has_old:
            m = m.replace(old, new, 1)
        if "方案 B 定案" not in m:
            m = m.rstrip() + m_add
        io.open(mp, "w", encoding="utf-8", newline="").write(m)
        m2 = io.open(mp, encoding="utf-8").read()
        assert "方案 B" in m2 and "不可投_READ_ME" in m2, "文件地图断言失败"
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
