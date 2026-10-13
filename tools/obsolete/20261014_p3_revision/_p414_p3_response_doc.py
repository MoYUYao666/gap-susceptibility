# -*- coding: utf-8 -*-
r"""由 JSON 数据渲染 P3 逐条应答工作文档（2026-10-12）。

**为什么数据外置**：分类文本含引号，写在 Python 字面量里会反复踩转义坑
（本项目已多次：PowerShell here-string、LaTeX `$`、中文引号、半角引号嵌套）。
→ **数据放 JSON（`write` 工具直写，不经 Python 转义），脚本只做渲染。**

输入：`outputs/analysis/p3_reviews_parsed.json`（意见原文）、
      `outputs/analysis/p3_review_classes.json`（分类与建议）
输出：`docs/P3_REVIEW_RESPONSE.md`

    python tools\_p414_p3_response_doc.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PARSED = REPO / "outputs" / "analysis" / "p3_reviews_parsed.json"
CLASSES = REPO / "outputs" / "analysis" / "p3_review_classes.json"
OUT = REPO / "docs" / "P3_REVIEW_RESPONSE.md"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.loads(io.open(PARSED, encoding="utf-8", errors="replace").read())
    c = json.loads(io.open(CLASSES, encoding="utf-8", errors="replace").read())
    meta = c["meta"]
    by = d["by_reviewer"]
    cls = {(x["reviewer"], x["n"]): x for x in c["classes"]}

    L = []
    L.append("# P3 审稿意见逐条应答（工作文档）")
    L.append("")
    L.append(f"> **稿件**：`{meta['manuscript']}` — *{meta['title']}*")
    L.append(f"> **期刊**：{meta['journal']}｜**决定**：**{meta['decision']}**（可修改后重审）")
    L.append(f"> **状态日期**：{meta['status_date']}｜**修订截止**：**{meta['revision_deadline']}**（逾期视为撤稿）")
    L.append(f"> **编辑**：{meta['editor']}（Editor-in-Chief）")
    L.append(f"> **总评**：*{meta['editor_note']}*")
    L.append(f"> **平台要求**：**{meta['platform_requirement']}**")
    L.append("")
    L.append(f"## 条目总览：**{d['total_items']} 条**"
             f"（R1 {by['R1']['n_items']}｜R2 {by['R2']['n_items']}｜R3 {by['R3']['n_items']}）")
    L.append("")
    L.append("## 归纳：条目高度重复，实际集中在以下根问题")
    L.append("")
    L.append("| 根 | 问题 | 出现于 | 处理类型 |")
    L.append("|---|---|---|---|")
    for r in c["root_problems"]:
        L.append(f"| **{r['id']}** | {r['name']} | {r['items']} | {r['kind']} |")
    L.append("")
    L.append("## 逐条应答（每条下方留空供填写回复）")
    L.append("")
    for rname in ("R1", "R2", "R3"):
        v = by[rname]
        L.append(f"### {rname}（{v['n_items']} 条）")
        L.append("")
        for it in v["items"]:
            n = it["n"]
            k = cls.get((rname, n), {"kind": "未判定", "action": "待人工判定"})
            L.append(f"#### {rname}.{n} — {k['kind']}")
            L.append("")
            L.append(f"> {it['text']}")
            L.append("")
            L.append(f"**建议动作**：{k['action']}")
            L.append("")
            L.append("**回复（待填）**：")
            L.append("")
            L.append("```")
            L.append("")
            L.append("```")
            L.append("")
        L.append("")
    L.append("## 回复撰写纪律（本项目铁律）")
    L.append("")
    L.append("1. **每个数字都要能指名产出脚本与归档文件+字段** —— 新补的实验必须先有归档才能写进回复。")
    L.append("2. **不许承诺做不到的事**：若某条只能澄清、不能补实验，就明确说明并把主张降级。")
    L.append("3. **区分「已做/已改」与「将做」**：不得混写。")
    L.append("4. **全称否定需机器穷举**：凡写「无 X / 从未 X」，先给出穷举产物（列表/计数/扫描范围）。")
    L.append(f"5. **截止 {meta['revision_deadline']}**，逾期视为撤稿。")
    L.append("")

    txt = "\n".join(L)
    if not a.apply:
        print(f"  （预演）将写 {len(txt)} 字符 → {OUT.relative_to(REPO)}")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(txt)
    print(f"  ✅ 已写 {OUT.relative_to(REPO)}（{len(txt)} 字符，{len(txt.splitlines())} 行）")
    kinds = {}
    for x in c["classes"]:
        kinds[x["kind"]] = kinds.get(x["kind"], 0) + 1
    print("  分类计数：")
    for k, v in sorted(kinds.items(), key=lambda x: -x[1]):
        print(f"     {k:<16} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
