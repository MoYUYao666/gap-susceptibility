# -*- coding: utf-8 -*-
r"""落账 A-1 目标刊对照结论（2026-10-07）。

交付件：**`docs/PAPERA_VENUE_DECISION.md`**（由 write 工具写出；本脚本做 HANDOFF/文件地图同步 + 断言）。

    python tools\_docs_venue_decision_1007.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **🎯 2026-10-07 —— A-1 目标刊对照完成：**5 个候选里 2 个可行、2 个出局、1 个勉强****
>
> 交付件：**`docs/PAPERA_VENUE_DECISION.md`**（逐字段引 Guide 原文）。
> 输入：操作者提供的 5 份 Guide PDF（桌面 → `期刊指南/`，**身份已逐份校验**）。
>
> ### 决定性差异：**篇幅**
>
> | 刊 | Guide 原文 | 判定 |
> |---|---|---|
> | **IVC** | *"the acceptable **word count range is 4500-7500 words**"* | ❌ **出局**：我们约 **11,254 词**，超约 50% |
> | **IF** | Research article *"**must be 10–35 pages**"*；*"Failure to comply … may result in **desk rejection**"* | ❌ **出局**：我们约 45–52 页；引用 44 条 ✅ 达标（限 50） |
> | **KBS** | *"preferably no more than **20 double line spaced** manuscript pages"* | ⚠️ **勉强**：约 2.2 倍（**非硬性**：preferably） |
> | **ESWA** | **未提及**篇幅上限（穷举 9 类关键词） | ✅ **可行** |
> | **CVIU** | **未提及**篇幅上限 | ✅ **可行** |
>
> ### 另一处差异：**匿名方式**（决定工作量）
>
> | 单盲（✅ 作者信息保留） | **双盲（⚠️ 须拆题名页 + 匿名稿）** |
> |---|---|
> | KBS、CVIU、IVC、IF | **ESWA** |
>
> ### 其余字段**全部达标**（5 刊要求一致）
>
> 摘要 ≤**250** 词（我们 **244**）｜ 关键词 **1–7**（我们 **6**）｜
> Highlights **3–5 条、每条 ≤85 字符**（我们 **5 条、最长 61**）｜ Research data 均 **Option C**。
>
> ### 建议
>
> **首选 ESWA**（无篇幅上限；唯一门槛是双盲拆分，属一次性工作）；
> **次选 CVIU**（无上限 + 单盲，工作量最小，但范围偏视觉、**scope 匹配需自评**）。
>
> ### ⚠️ 一处诚实标注
>
> **篇幅换算为估算**：三种口径给出 23 / 45 / 52 页，差异大（口径 ① 按 LaTeX 源行数明显低估）。
> **采信 45–52 页**。**最终判定须用目标刊 LaTeX 模板实排**——仍为未完成项。
>
> ### 下一步（待操作者）
>
> ① **确认选刊**（ESWA 或 CVIU）；② 若 ESWA → 制作双盲版；
> ③ 核对 **Option C** 的数据可用性措辞；④ 用目标刊模板实排得权威页数；⑤ 重写封面信。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演，加 --apply）")
        return 0

    vp = REPO / "docs" / "PAPERA_VENUE_DECISION.md"
    assert vp.exists(), "交付件不存在"
    vt = io.open(vp, encoding="utf-8").read()
    for k in ("4500-7500", "10–35", "Maximum 50 references", "double anonymized",
              "preferably no more than 20", "244", "6 个", "61", "篇幅换算为估算"):
        assert k in vt, f"交付件缺 {k}"

    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "A-1 目标刊对照完成" not in h:
        anchor = "> **📋 2026-10-06 —— A-1 换刊评估：依据、**两处自我更正**、与未完成项**"
        i = h.find(anchor)
        if i < 0:
            anchor = "> **📮 2026-10-07 —— EM 状态快照"
            i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ENT + "\n" + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("4500-7500", "10–35", "preferably no more than 20", "PAPERA_VENUE_DECISION.md"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")

    # 文件地图：待办 2b 的阻塞项更新
    fp = REPO / "文件地图.md"
    t = io.open(fp, encoding="utf-8").read()
    old = "**⏳ 阻塞项**：候刊 **Guide for authors PDF**"
    if old in t and "2026-10-07 已解" not in t:
        i = t.find(old)
        j = t.find("\n", t.find("不填") if t.find("不填") > i else i + 400)
        seg = t[i:i + 520]
        t = t[:i] + ("**✅ 阻塞项已于 2026-10-07 解除**：5 份 Guide 已由操作者提供并存档 `期刊指南/`。\n"
                     "   **对照结论**（`docs/PAPERA_VENUE_DECISION.md`）：**IVC 出局**（字数控 4500–7500，我们约 11,254 词）、\n"
                     "   **IF 出局**（页数硬上限 10–35，我们约 45–52 页；超限可 desk rejection）；\n"
                     "   **KBS 勉强**（preferably ≤20 双倍行距页，约 2.2 倍）；\n"
                     "   **✅ 可行 = ESWA（首选，无上限，但双盲需拆题名页）／ CVIU（次选，无上限 + 单盲，scope 需自评）**。\n"
                     "   **下一个待办 = 操作者确认选刊**。\n"
                     "   ~~原记（已过期）：候刊 Guide for authors PDF（优先 KBS、ESWA、CVIU）——无官方 Guide 无法产出符合本项目标准的对比表~~\n") + t[i + len(seg):]
        io.open(fp, "w", encoding="utf-8", newline="").write(t)
        t2 = io.open(fp, encoding="utf-8").read()
        for k in ("阻塞项已于 2026-10-07 解除", "IVC 出局", "IF 出局", "可行 = ESWA"):
            assert k in t2, f"文件地图断言失败：缺 {k}"
        print(f"  ✅ 文件地图.md 待办 2b 已更新（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
