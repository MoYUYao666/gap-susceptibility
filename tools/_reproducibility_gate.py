# -*- coding: utf-8 -*-
r"""**⚠️ 本工具已作废（2026-10-07）——它给出的是假门禁。**

实测：归档有 122,161 个数值，任何数字都能在 0.5% 容差内随机命中 →
**145/145"通过"纯属假象**。正确做法见 `tools/_claim_ledger.py`（人工指名出处 + 逐条断言）。

r"""**可复现门禁**：稿件里每个数字都必须能在归档里找到来源（2026-10-07）。

## 操作者的唯一原则

> **"所有数据必须要可复现有来源"**

## 本工具做什么

1. **抽取** `paper合/sections/*.tex` + `main_nc.tex` 里的**数值字面量**（正文与 caption）；
2. **搜索归档**：在 `outputs/**/*.json` 的全部数值里找匹配（相对容差 0.5%，覆盖四舍五入）；
3. 分类输出：
   - **✅ 有来源**：在归档 JSON 中直接命中；
   - **📐 可推导**：命中已知派生量（如 ODE 拟合的 R²、均值±sd）——由命名脚本产出；
   - **⚠️ 无来源**：既不在 JSON 也未在派生日志中 → **需处理（补来源或删除）**。

## 设计取舍（避免把工具做成摆设）

- 不追求"逐数字精确映射"（那需要人工标注每个数字），而是**先扫出"归档里根本不存在"的数字**——
  这类是**最可能的无来源项**；
- 数值比较用**相对容差**，因为稿件多为四舍五入；
- 忽略明显非数据的数字（年份、页码、章节号、引用 keys 里的数字、参数如 `$r{=}8$` 中的 8）。

    python tools\_reproducibility_gate.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SEC = REPO / "paper合" / "sections"
MAIN = REPO / "paper合" / "main_nc.tex"
OUT = REPO / "outputs" / "analysis" / "reproducibility_gate.json"

# 与数据无关的数字模式（年份、章节/图表号、rank/维度等）
IGNORE_CTX = re.compile(
    r"(19|20)\d{2}|%|\\\\ref|\\\\cite|\\\\label|arXiv|doi|eprint|"
    r"\$r\{?=?\}?\s*\d|\br\s*=\s*\d|\balpha\s*=\s*\d|\$n\s*=\s*\d|"
    r"\b\d+\s*(?:samples|epochs|seeds|pages|layers|classes|tokens)\b|"
    r"figures?|table|section|rank|dim|width|patch", re.I)


def tex_numbers() -> list[dict]:
    """抽取稿件中的小数（>=3 位有效）与显式大整数。"""
    out = []
    for f in sorted(glob.glob(str(SEC / "*.tex"))) + [str(MAIN)]:
        t = io.open(f, encoding="utf-8").read()
        for m in re.finditer(r"\$?(-?\d+\.\d{2,4})\$?", t):
            val = float(m.group(1))
            ctx = t[max(0, m.start() - 90):m.start() + 60].replace("\n", " ")
            if IGNORE_CTX.search(ctx):
                continue
            out.append({"file": Path(f).name, "value": val,
                        "raw": m.group(0), "ctx": ctx.strip()[:110]})
    return out


def archive_numbers() -> set[float]:
    """归档里出现过的全部数值（限 0.001–1000，避免噪声）。"""
    vals = set()
    for f in glob.glob(str(REPO / "outputs" / "**" / "*.json"), recursive=True):
        try:
            t = io.open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        for m in re.finditer(r"-?\d+\.\d+", t):
            try:
                v = float(m.group(0))
            except Exception:
                continue
            if 0.0005 < abs(v) < 1000:
                vals.add(v)
    return vals


def main() -> int:
    apply = "--apply" in sys.argv
    print("  收集归档数值…", flush=True)
    arch = archive_numbers()
    print(f"  归档数值集合: {len(arch)} 个")
    claims = tex_numbers()
    print(f"  稿件数值字面量: {len(claims)} 个")

    def in_archive(v: float) -> bool:
        if v == 0:
            return True
        for a in arch:
            if abs(a - v) <= max(0.0005, abs(v) * 0.005):
                return True
        return False

    hits, miss = [], []
    for c in claims:
        (hits if in_archive(c["value"]) else miss).append(c)

    print(f"\n  === 结果 ===")
    print(f"  ✅ 归档中可找到: {len(hits)}/{len(claims)} ({100*len(hits)/max(len(claims),1):.0f}%)")
    print(f"  ⚠️ 归档中未找到: {len(miss)}")

    if miss:
        print(f"\n  === ⚠️ 归档中未找到的数值（需逐项处置）===")
        seen = set()
        for c in miss:
            key = (c["file"], c["raw"])
            if key in seen:
                continue
            seen.add(key)
            print(f"    [{c['file']}] {c['raw']:>10}  …{c['ctx'][:88]}…")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"archive_value_count": len(arch), "claim_count": len(claims),
             "found": len(hits), "missing": len(miss),
             "missing_items": [{"file": c["file"], "raw": c["raw"], "ctx": c["ctx"]} for c in miss]},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
