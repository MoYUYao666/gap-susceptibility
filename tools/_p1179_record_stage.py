# -*- coding: utf-8 -*-
"""Record the 2026-10-17 evening continuation stage in the handover documents.

Updates (idempotent, marked by unique headings):
  * HANDOFF.md      - new top entry: schedule rebuild, P3 audit refresh, Paper A editorial fixes,
                      rebuild and gates, remaining operator decisions;
  * 文件地图.md     - a dated status block at the top of 当前总状态 and two numbered entries;
  * AUTOMATION_HANDOVER.md - current-status section refreshed (the old sole todo is done).

    python tools/_p1179_record_stage.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
AUTO = REPO / "AUTOMATION_HANDOVER.md"
MARK_H = "2026-10-17 21:20 —— 接续阶段"
MARK_M = "2026-10-17 21:20 更新（本块最新"
MARK_A = "2026-10-17 21:20（本阶段收尾）"

HANDOFF_ENTRY = r"""
> **✅ 2026-10-17 21:20 —— 接续阶段：重建定时任务 + P3 审计刷新 + Paper A 编辑缺陷修复与包重建**
>
> ### 一、自动化任务已按 AUTOMATION_HANDOVER.md 重建
>
> schedule_create weekly：**周一 06:00（Asia/Shanghai）**，id 前缀 @@schedule-aef088b2@@；prompt 为交接文件第三节的**逐字文本**；
> title 去掉频率词（工具规范禁止标题带执行频率），任务内容仍为"全部 6 篇稿件的竞争/可引用新论文"。
> 该任务随会话切换丢失属已知行为（交接文件已记录），本次为重建，不改变任务内容。
>
> ### 二、P3 审计脚本已按 10 页投稿版刷新（原唯一待办，已完成）
>
> | 项 | 结果 |
> |---|---|
> | audit_check.py | **72 PASS / 0 FAIL / 2 WARN**（warning：4 个未引用 label；已知 \nabla 缺陷） |
> | audit_pdf.py | **95 PASS / 0 FAIL**（新增 14 条补充材料数值检查，补回下移值的覆盖） |
> | 冻结核对 | main.pdf 10 页 / supplementary 6 页，SHA-256 与 CORRECTED_2026-10-15 及 UPLOAD_2026-10-15 **逐字节一致** |
> | 证据 | @@outputs/analysis/p3_audit_refresh_2026-10-17.json@@；文档 @@docs/P3_AUDIT_10PP_2026-10-17.md@@ |
>
> ⚠️ 记录一处**已知缺陷、未改**：@@paper3/paper_ieee/main.tex:67@@ 的 \nabla 丢了反斜杠，已投出的 main.pdf 摘要印成 "abla"；
> P3 在审、PDF 冻结，故只在新审计脚本中加 warning，留待下一轮修订。P3 稿件与 SUBMISSION/ 均未改动。
>
> ### 三、Paper A 独立只读核验：六类数字主张全真，但发现并修复编辑缺陷
>
> | 缺陷 | 修复 |
> |---|---|
> | discussion.tex 同一句**连续出现两次**（PDF 41–42 页可见） | 去重为一次 |
> | Limitations 顺序 Twelfth→Tenth→Eleventh→First–Ninth，且 Tenth 段被 Eleventh 段截断 | 重排 First–Ninth→Tenth→Eleventh→Twelfth，并接回 Tenth 段 |
> | "and and"、"heuristic heuristics"、"generaliz," | 逐处修正 |
> | 补充 G 节 "one pooled standard deviation" | 依归档复算比值 **2.01** → "about two pooled standard deviations" |
> | cover letter 页数 63/56（实为 67）；三处引用渲染成 **"[?, ?, ?]"**；1 行 Overfull 65.7pt | 页数按实测回写；引用改方法名 (AdaLoRA, LoRA-GA and CLIP-LoRA)；加 sloppy |
> | 摘要词数 246/236 不一致；highlights 最长 61 vs 实测 59 | 统一 **236 词 / 59 字符**；highlights 5 条 |
> | 表 I 称 "every row five-seed" 但 BioCLIP 为 **3 seed** | 题注写明 "except BioCLIP" |
> | 附录 A 目录被称 "383 experiments"（实为 **221 run**） | 改为 "(221 runs)" |
>
> **计数口径统一（依据归档实测）**：383 实验覆盖**六个 checkpoint**（CLIP B/32、ViT-L/14、OpenCLIP B/32、SigLIP、BioCLIP、BLIP-1；
> **CLIP B/16 的 15 个补跑不在 383 内**）；严格冻结三臂协议 = **五个 checkpoint、七个 rank 配置**。
> 据此改 8 处措辞（结论名单 B/16→BioCLIP；引言两处 five architectures→six backbones、two→three PEFT、three backbones→SigLIP；
> empirical seven backbones→five backbones (seven configurations)；两封 cover letter five architectures→six backbones）。
>
> ### 四、重建与门禁
>
> | 项 | 结果 |
> |---|---|
> | 编译 | NC **67 页** / Springer **49 页**；均 **0 错误 / 0 未定义引用 / 0 未定义引文 / 0 Overfull** |
> | 附件 | cover letter **3 页**×2（0 未定义引文、0 Overfull、无 "?"）、highlights 1 页 |
> | 门禁 | @@_claim_ledger_paperA.py@@ **74/74 PASS, 0 GAP**；@@_claim_ledger.py@@ **96/96** |
> | 投稿包 | @@_p1169@@ 重建：45 文件、独立编译 **67 页 0 错误**；@@_p1178@@ 同步 Cover Letter.pdf / Highlights.pdf 并按实测重写 README |
> | 包内哈希 | Manuscript.pdf = main_nc.pdf；Cover Letter.pdf = cover_letter_nc.pdf；Highlights.pdf = highlights_nc.pdf |
> | PDF 复核 | 重复句 1 处；Limitations 顺序 First→…→Twelfth；三类重复词 0 处；cover letter 无 "?" |
>
> ### 五、仍待操作者决定
>
> 1. **目标刊与投稿时点**：包按 Neurocomputing 准备；A1 已转投 Neural Networks（NEUNET-D-26-09426）、P1 已拒（2026-10-12），
>    两项原约束解除，但投哪家、何时投仍由操作者定。
> 2. **383 的 162 个 ODE 拟合**：归档 ode_ledger.json 仅 96 条，差额只有 HANDOFF 算术记录，未全部落为逐条文件。
> 3. **解码器两实验符号相反**（Qwen 降 gap / LLaVA 升 gap）的归因仍无法分离，正文已如实限定。
>
> **脚本**：_p1173（编辑修复）｜_p1174（双版重建+日志审计）｜_p1176（计数口径+cover 事实）｜_p1177（cover 去引用）｜_p1178（包同步+README）｜_p1179（本条）。

"""

MAP_BLOCK = r"""
> **✅ 2026-10-17 21:20 更新（本块最新；下方 2026-10-16 块中与之冲突的内容已过期）**
>
> | 项 | 现状（实测） |
> |---|---|
> | **Paper A** | **可投**：NC **67 页** / Springer **49 页**；0 错误 / 0 未定义 / 0 Overfull；双台账 **74/74** 与 **96/96**；投稿包 **45 文件**、独立编译 67 页；cover letter 3 页、highlights 5 条；README 已按实测重写 |
> | **Paper 3** | PRL @@PRLETTERS-D-26-02378R1@@ 在审、**稿件冻结**；审计脚本已按 10 页版刷新（audit_check 72 PASS / audit_pdf 95 PASS）；已知 \nabla 缺陷记录待下轮 |
> | **A1** | 已转投 Neural Networks @@NEUNET-D-26-09426@@（2026-10-12） |
> | **P1** | Pattern Recognition **已拒**（@@PR-D-26-10149@@，2026-10-12） |
> | **自动化** | 每周一 06:00 文献检索已按 @@AUTOMATION_HANDOVER.md@@ 重建 |
> | **待办** | ① 操作者定 Paper A 目标刊/投稿时点；② 383 的 162 个 ODE 拟合逐条归档缺口；③ 解码器符号归因 |
"""

MAP_ENTRIES = r"""
56. ✅ **P3 审计脚本按 10 页投稿版刷新（2026-10-17 21:00）** —— 旧脚本期望值来自 13 页草稿（6 miss / 19 miss）；重写后 @@audit_check.py@@ **72 PASS / 0 FAIL / 2 WARN**、@@audit_pdf.py@@ **95 PASS / 0 FAIL**，并**补回 14 条补充材料数值检查**（ShGPT、\Gamma 表、ERS）；冻结哈希与 CORRECTED_2026-10-15 及 UPLOAD_2026-10-15 **逐字节一致**。⚠️ 记录一处**已知缺陷、未改**：@@main.tex:67@@ 的 \nabla 缺反斜杠，已投 PDF 印成 "abla"（稿件冻结，只在新脚本加 warning）。脚本 @@_p1172@@；证据 @@outputs/analysis/p3_audit_refresh_2026-10-17.json@@；文档 @@docs/P3_AUDIT_10PP_2026-10-17.md@@。
57. ✅ **Paper A 编辑缺陷修复 + 投稿包重建（2026-10-17 21:20）** —— 独立只读核验确认六类数字主张全真，但修掉 9 类编辑缺陷：重复句、Limitations 顺序（First–Ninth→Tenth→Eleventh→Twelfth）与 Tenth 段截断、"and and"/"heuristic heuristics"/"generaliz"、G 节 pooled-sd（复算比值 **2.01**）、cover letter 页数 63/56→**67**、引用 **"[?, ?, ?]"**→方法名、摘要 246/236→**236**、highlights 61→**59**、表 I BioCLIP 3 seed、附录 A "383"→**221 run**。计数口径统一为 **383=六个 checkpoint**（CLIP B/16 的 15 个补跑不在 383 内）与**严格冻结 5 checkpoint/7 配置**，改 8 处措辞。重建：NC **67** / Springer **49**（0/0/0/0）、cover letter 3 页、包 45 文件独立编译 67 页、双台账 74/74 与 96/96。脚本 @@_p1173@@–@@_p1179@@；详见 @@docs/PAPERA_REVISION_SPEC.md@@ 第八节与 HANDOFF 顶部条目。
"""

AUTO_BULLETS = r"""- **Paper A**：可投。main_nc.pdf 67 页 / main_springer.pdf 49 页，0 错误 / 0 未定义 / 0 Overfull；双台账 74/74 与 96/96；NC_submission 45 文件、独立编译 67 页；cover letter/highlights 已同步、README 按实测重写（2026-10-17 21:20）。
- **Paper 3**：PRL PRLETTERS-D-26-02378R1 在审，投稿件冻结，**不改动**。审计脚本已按 10 页版刷新（audit_check 72 PASS / audit_pdf 95 PASS，含补充材料检查）；已知 nabla 排版缺陷记录待下轮。
- ✅ **原唯一待办（P3 审计脚本期望值）已完成**（2026-10-17 21:00）。
- **待操作者决定**：① Paper A 目标刊与投稿时点（包按 Neurocomputing 准备；A1 已转投 Neural Networks、P1 已拒，两项原约束解除）；② 383 中 162 个 ODE 拟合的逐条归档缺口。"""

FAILS = []


def need(cond, msg):
    if not cond:
        FAILS.append(msg)
        print("FAIL  " + msg)


def insert_after_line(text, anchor, block):
    i = text.find(anchor)
    need(i >= 0, "anchor not found: " + anchor[:40])
    if i < 0:
        return text
    j = text.find("\n", i)
    return text[: j + 1] + block + text[j + 1:]


def with_ticks(template):
    parts = template.split("@@")
    out = parts[0]
    for part in parts[1:]:
        out += chr(96) + part
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    handoff = io.open(HANDOFF, encoding="utf-8", newline="").read()
    if MARK_H not in handoff:
        head = handoff.find("# 项目交接文档")
        need(head >= 0, "HANDOFF title not found")
        j = handoff.find("\n", head)
        handoff = handoff[: j + 1] + with_ticks(HANDOFF_ENTRY) + handoff[j + 1:]
        print("  HANDOFF.md: entry added")
    else:
        print("  HANDOFF.md: entry already present")

    mapdoc = io.open(MAP, encoding="utf-8", newline="").read()
    if MARK_M not in mapdoc:
        mapdoc = insert_after_line(mapdoc, "## 🔴 当前总状态（2026-10-16 22:45 更新）", with_ticks(MAP_BLOCK))
        print("  文件地图.md: status block inserted")
    else:
        print("  文件地图.md: status block already present")
    if "56. ✅ **P3 审计脚本按 10 页投稿版刷新" not in mapdoc:
        anchor = "19:55 条目。"
        i = mapdoc.find(anchor)
        need(i >= 0, "文件地图: entry-55 anchor not found")
        if i >= 0:
            j = mapdoc.find("\n", i)
            mapdoc = mapdoc[: j + 1] + with_ticks(MAP_ENTRIES) + mapdoc[j + 1:]
        print("  文件地图.md: entries 56-57 appended")
    else:
        print("  文件地图.md: entries already present")

    auto = io.open(AUTO, encoding="utf-8", newline="").read()
    if MARK_A not in auto:
        head = "## 五、当前状态（交接时点 2026-10-17 20:20）"
        i = auto.find(head)
        need(i >= 0, "AUTOMATION_HANDOVER: status heading not found")
        if i >= 0:
            tail = auto.find("- **云端**", i)
            need(tail >= 0, "AUTOMATION_HANDOVER: cloud bullet not found")
            if tail >= 0:
                new = "## 五、当前状态（交接时点 2026-10-17 21:20）\n\n" + AUTO_BULLETS + "\n\n"
                auto = auto[:i] + new + auto[tail:]
                print("  AUTOMATION_HANDOVER.md: status refreshed")
    else:
        print("  AUTOMATION_HANDOVER.md: status already current")

    if FAILS:
        print("RESULT: %d failure(s); nothing written" % len(FAILS))
        return 1
    if a.apply:
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(handoff)
        io.open(MAP, "w", encoding="utf-8", newline="").write(mapdoc)
        io.open(AUTO, "w", encoding="utf-8", newline="").write(auto)
        print("  applied: HANDOFF.md, 文件地图.md, AUTOMATION_HANDOVER.md")
    else:
        print("(dry run; pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
