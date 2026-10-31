# -*- coding: utf-8 -*-
r"""检查"正文引用标记 ↔ 参考文献表"的一致性（双向）。

抓两类问题：
  1. **悬空引用（dangling）**：正文写了 `[key]`，但参考文献表里没有该 key → 编译会出未定义引用；
  2. **孤儿条目（orphan）**：参考文献表里有条目，但全文从未引用 → 占篇幅且可能是不该留的；
  3. **跨工作流 key 不一致**：同一篇文献在不同章用了不同 key（如 A 用 hu2021lora、B 用 hu2022lora），
     合并后只保留一个，另一个在正文里就成了悬空引用。

用法：
    python tools/_check_citation_keys.py
输出：paper_review/citation_key_report.md
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DIR = REPO / "paper_review"
SECTIONS = sorted((DIR / "sections").glob("*.md"))

# 支持 [key]、[@key]、[@key; @key2]、[key, key2] 等写法
TOKEN = re.compile(r"\[@?([A-Za-z][A-Za-z0-9_:.\-]{2,60}(?:\s*[;,]\s*@?[A-Za-z][A-Za-z0-9_:.\-]{2,60})*)\]")


def tokens_in(text: str) -> list[str]:
    out = []
    for m in TOKEN.finditer(text):
        for part in re.split(r"[;,]", m.group(1)):
            k = part.strip().lstrip("@").strip()
            # 过滤占位符与非 key 词（如模板里的 A-xx、key）；真实 citation key 形如 author2021word
            if not re.match(r"^[A-Za-z][A-Za-z0-9_:.\-]*\d{2,}", k):
                continue
            out.append(k)
    return out


def main() -> int:
    refs = json.loads((DIR / "refs_all.json").read_text(encoding="utf-8"))
    known = {(e.get("key") or "").strip() for e in refs}

    used: dict[str, list[tuple[str, int]]] = defaultdict(list)
    per_section: dict[str, int] = {}
    for p in SECTIONS:
        text = p.read_text(encoding="utf-8")
        ks = tokens_in(text)
        per_section[p.name] = len(set(ks))
        for k in ks:
            used[k].append((p.name, 0))

    dangling = sorted(k for k in used if k not in known)
    orphan = sorted(k for k in known if k not in used)

    print(f"参考文献表：{len(known)} 条 ｜ 正文引用到的 key：{len(used)} 个\n")
    print("各章引用 key 数：")
    for n, c in per_section.items():
        print(f"  {n:<26} {c}")

    print(f"\n=== ❌ 悬空引用（正文有、表里无）：{len(dangling)} ===")
    for k in dangling:
        print(f"  {k}")
    print(f"\n=== ⚠️ 孤儿条目（表里有、正文未引）：{len(orphan)} ===")
    for k in orphan:
        print(f"  {k}")

    lines = ["# 引用一致性报告", "",
             f"参考文献表 **{len(known)}** 条 ｜ 正文引用 **{len(used)}** 个 key ｜ "
             f"**悬空 {len(dangling)}** ｜ **孤儿 {len(orphan)}**", ""]
    if dangling:
        lines += ["## ❌ 悬空引用（必须修：要么补进表，要么改正文 key）", ""]
        lines += [f"- `{k}`" for k in dangling] + [""]
    if orphan:
        lines += ["## ⚠️ 孤儿条目（要么在正文引用，要么删除）", ""]
        lines += [f"- `{k}`" for k in orphan] + [""]
    if not dangling and not orphan:
        lines.append("✅ 双向一致：无悬空引用、无孤儿条目。")
    lines += ["", "## 各章引用 key 数", ""]
    lines += [f"- `{n}`: {c} 个" for n, c in per_section.items()]
    (DIR / "citation_key_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n写出 {(DIR / 'citation_key_report.md').relative_to(REPO)}")
    return 1 if (dangling or orphan) else 0


if __name__ == "__main__":
    raise SystemExit(main())
