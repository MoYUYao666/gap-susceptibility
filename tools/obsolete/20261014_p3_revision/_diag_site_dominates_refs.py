# -*- coding: utf-8 -*-
r"""诊断：Paper A 是否已引用「site dominates allocation」所依据的已发表文献（2026-10-07）。

## 背景

PRL 综述（`-02402`，在审）§3 首条 robust 结论是 **"site dominates allocation"**，
依据 **3 篇已发表文献**：`zhang2023adalora`、`wang2024loraga`、`zanella2024cliplora`。

**操作者决定：综述不改。** 故只能从 **Paper A 侧**解决"同一命题两处主张而不互引"的风险。

**首选方案**：Paper A **引用这些已发表文献**（而非引用在审综述本身），
把"位置 > 配置"定位为「**文献已有此说（归纳）→ 我们直接测到 → 并给出机制与边界条件**」，
从而：① 独立佐证；② 贡献仍是"直接测量 + 梯度流理论"；③ **不必引用在审稿件**。

本脚本先诊断现状：**这些文献在不在 Paper A 的 bib 里？正文提没提？**

    python tools\_diag_site_dominates_refs.py
"""
from __future__ import annotations

import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BIB = REPO / "paper合" / "references.bib"
SEC = REPO / "paper合" / "sections"

# 综述所依据的 3 篇
NEEDLES = {
    "zhang2023adalora": ["adalora", "zhang"],
    "wang2024loraga": ["lora-ga", "loraga", "low-rank adaptation with gradient"],
    "zanella2024cliplora": ["cliplora", "clip-lora", "zanella"],
}


def main() -> int:
    bib = io.open(BIB, encoding="utf-8").read()
    keys = re.findall(r"^@\w+\{([^,]+),", bib, re.M)
    print("=== Paper A 的 bib 条目（%d 条）===" % len(keys))
    print("  " + ", ".join(keys))
    print()

    print("=== 诊断：综述所依据的 3 篇是否已在 Paper A 里 ===")
    low = bib.lower()
    for k, needles in NEEDLES.items():
        hits = [n for n in needles if n in low]
        print(f"  {k:<24} {'✅ 命中: ' + str(hits) if hits else '❌ 未在 bib 中'}")
    print()

    print("=== 正文里'位置 > 配置'这一命题怎么写的 ===")
    for f in sorted(SEC.glob("*.tex")):
        t = io.open(f, encoding="utf-8").read()
        for m in re.finditer(r"[^.]{0,220}(?:matters more than|position matters|which part of the model|"
                             r"where.{0,30}adapted|adaptation position)[^.]{0,220}\.", t, re.I):
            s = re.sub(r"\s+", " ", m.group(0)).strip()
            print(f"  [{f.stem}] …{s[:290]}…")
    print()

    print("=== 正文里是否已有'文献也观察到'类表述 ===")
    found = False
    for f in sorted(SEC.glob("*.tex")):
        t = io.open(f, encoding="utf-8").read()
        for m in re.finditer(r"[^.]{0,180}(?:consistent with|in line with|has been reported|"
                             r"prior work|earlier work|literature)[^.]{0,180}\.", t, re.I):
            s = re.sub(r"\s+", " ", m.group(0)).strip()
            print(f"  [{f.stem}] …{s[:250]}…")
            found = True
    if not found:
        print("  （未见此类表述）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
