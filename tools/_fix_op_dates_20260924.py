# -*- coding: utf-8 -*-
"""按行修正文档日期口径（可重跑、幂等）。

背景：系统日期在两次操作之间跨日，早期标注把不同天的活儿混成了同一个日期。
正确的口径：
  * **2026-09-22** = `paper合/` 与 `paper_a4/` 归档动作（git `01be1b0` = 09-22 20:05 证实）
  * **2026-09-23** = 昨日那轮（ap3 占位标记消解 / 篇幅结论 / `paper合` 弃用决定 / 五项决定结清 / EAAI 重新提交的事实日）
  * **2026-09-24** = 今天这轮（四项操作者决定、阶段条目、EAAI 记录入账、发布边界核查、文档一致性核查、长度报告生成）

模式（每行只改一处：该行中的 2026-09-22/23/24 会被统一替换为指定值）：
  'today'  -> 2026-09-24    'keep' -> 不动
  '2026-09-22' / '2026-09-23' -> 显式目标日期

    python tools/_fix_op_dates_20260924.py [--dry-run]

⚠️ 一次性工具，**不是幂等脚本**：锚点之间会互相干扰（同一行可能被多条规则命中），
因此已经用它做过两轮修正后，**不要再跑**——要改日期请逐处点改并复查。
保留本文件只为留下"日期口径怎么定的"这段推理与证据链。
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATES = ("2026-09-22", "2026-09-23", "2026-09-24")

# (文件, 行内锚点片段, 目标)
RULES: list[tuple[str, str, str]] = [
    # ---------------- HANDOFF.md ----------------
    ("HANDOFF.md", "**更新时间**：", "today"),
    ("HANDOFF.md", "阶段条目（最新，先读这条）", "today"),
    ("HANDOFF.md", "四项均于", "today"),
    ("HANDOFF.md", "操作者决定四条（", "today"),
    ("HANDOFF.md", "AUTHOR CONFIRMED", "today"),
    ("HANDOFF.md", "④ 篇幅口径 → 已核（", "today"),
    ("HANDOFF.md", "**📌 过期标注（", "today"),
    ("HANDOFF.md", "该断言已过期（", "today"),
    ("HANDOFF.md", "反而与操作者", "today"),
    ("HANDOFF.md", "**未公开**——", "today"),
    ("HANDOFF.md", "EAAI 综述已于", "2026-09-23"),
    ("HANDOFF.md", "五项）→ ✅", "2026-09-23"),
    ("HANDOFF.md", "**③ `paper合/` → 弃用**（操作者", "2026-09-23"),
    ("HANDOFF.md", "**已被", "2026-09-23"),
    # ---------------- 文件地图.md ----------------
    ("文件地图.md", "操作者 2026-09-2", "today"),          # 发布边界一节
    ("文件地图.md", "**发布边界（操作者", "today"),
    ("文件地图.md", "**可见性实测（", "today"),
    ("文件地图.md", "已彻底关闭**：操作者决定", "today"),
    ("文件地图.md", "自身已就绪（", "today"),
    ("文件地图.md", "**已归档、不在根目录**（", "2026-09-22"),
    ("文件地图.md", "深度审计修 15 项 →", "2026-09-22"),
    ("文件地图.md", "操作者决定 **`paper合` 路线弃用**", "2026-09-23"),
    ("文件地图.md", "经操作者明确 **弃用**", "2026-09-23"),
    ("文件地图.md", "操作者确认 **`paper合` 路线弃用**", "2026-09-23"),
    ("文件地图.md", "已于", "2026-09-23"),                 # EAAI 行
    ("文件地图.md", "已重新提交（", "2026-09-23"),
    # ---------------- docs ----------------
    ("docs/AP3_SUBMISSION_READINESS.md", "操作者指示（", "2026-09-23"),
    ("docs/AP3_SUBMISSION_READINESS.md", "2026-09-2 决定", "2026-09-23"),
    ("docs/AP3_SUBMISSION_READINESS.md", "已补齐（", "today"),
    ("docs/AP3_SUBMISSION_READINESS.md", "已消解（", "today"),
    ("docs/AP3_SUBMISSION_READINESS.md", "已核（", "today"),
    ("docs/AP3_SUBMISSION_READINESS.md", "占位标记消解记录（", "today"),
    ("docs/AP3_SUBMISSION_READINESS.md", "**：核查篇幅时发现", "today"),
    ("docs/AP3_SUBMISSION_READINESS.md", "，见 §8）", "today"),
    ("docs/AP3_SUBMISSION_READINESS.md", "作者已于", "today"),
    ("docs/AP3_SYNC_PLAN.md", "已核查（", "today"),
    ("docs/AP3_SYNC_PLAN.md", "现状锚点（", "2026-09-23"),
    ("docs/AP3_SYNC_PLAN.md", "**当前为 86 页**（", "2026-09-23"),
    ("docs/AP3_LENGTH_CHECK.md", "核查日期：", "today"),
    ("docs/AP3_LENGTH_CHECK.md", "收尾标注（", "today"),
    ("docs/AP3_LENGTH_CHECK.md", "本次联网抓取结果（", "today"),
    ("docs/AP3_LENGTH_CHECK.md", "对 ScienceDirect", "today"),
    ("docs/PAPERHE_OVERLAP_RESOLUTION.md", "：随 `paper合` 弃用", "today"),
    ("docs/PAPERHE_OVERLAP_RESOLUTION.md", "状态**：`paper合` 已被操作者弃用", "today"),
    ("备选/06_归档稿件/paper_ap3/main.tex", "AUTHOR CONFIRMED", "today"),
]

TARGETS = sorted({f for f, _, _ in RULES})


def main() -> int:
    dry = "--dry-run" in sys.argv
    print(f"{'文件':<42}{'改动':>6}{'保持':>6}")
    total_c = total_k = 0
    for rel in TARGETS:
        p = REPO / rel
        if not p.is_file():
            print(f"SKIP (missing) {rel}")
            continue
        text = io.open(p, encoding="utf-8").read()
        lines = text.split("\n")
        c = k = 0
        for f_of_rule, needle, target in RULES:
            if f_of_rule != rel:
                continue
            want = "2026-09-24" if target == "today" else target
            for i, line in enumerate(lines):
                if needle not in line:
                    continue
                hit = next((d for d in DATES if d in line), None)
                if hit is None:
                    continue
                if hit == want:
                    k += 1
                    continue
                lines[i] = line.replace(hit, want)
                c += 1
        if c and not dry:
            io.open(p, "w", encoding="utf-8", newline="").write("\n".join(lines))
        total_c += c
        total_k += k
        print(f"{rel:<42}{c:>6}{k:>6}")
    print(f"\n合计：改动 {total_c} 处，已一致 {total_k} 处" + ("（--dry-run 未写入）" if dry else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
