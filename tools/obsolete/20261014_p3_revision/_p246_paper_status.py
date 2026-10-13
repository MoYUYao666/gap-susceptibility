# -*- coding: utf-8 -*-
r"""核实：`paper/`（PR-D-26-10149 的原稿）现在是否仍是 PR 审阅时的版本（2026-10-12）。

## 为什么

若 `paper/` **未被更新**，则：
- PR 的审稿意见**仍然完全有效**（未被回应过）
- 而我们**已经把同样的问题在 `paper合` 里解决**
  （批次统一、5 seed、组内统计、标题收窄）

→ 这意味着 **`paper合` = `paper/` 的"已修版"**，正是 R1.1/R1.2/R2.1 要求的。

**本脚本**：查 `paper/` 是否含 PR 点名的旧数值与措辞。

    python tools\_p246_paper_status.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P1 = REPO / "paper"
OUT = REPO / "outputs" / "analysis" / "paper_p1_status.json"

# PR 审稿人点名的具体特征
STALE = [
    (r"Visual Fragility", "R2.4：Visual Fragility（仍描述性）"),
    (r"direct causal evidence", "R1.3：被指为过度因果声称的措辞"),
    (r"zero-overhead|zero overhead", "R1.5：被指不实的 zero-overhead"),
    (r"DG-Guided Early Stopping|DG-ES", "R1.5/R2.5：过早终止问题"),
    (r"\+0\.079", "R1.1/R3.1：符号翻转的 +0.079"),
    (r"-0\.081", "R1.1：核心实验的 −0.081"),
    (r"0\.827|r\s*=\s*-0\.827", "R1.2：r=−0.827（被指伪重复）"),
    (r"across architectures", "R1.4：跨架构概化"),
    (r"applies to any", "R1.4：过强概化"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    files = sorted(glob.glob(str(P1 / "*.tex"))) + sorted(
        glob.glob(str(P1 / "sections" / "*.tex")))
    print("=" * 94)
    print(f"`paper/` 共 {len(files)} 个 tex；查 PR 点名的旧特征")
    print("=" * 94)
    found = {}
    for pat, desc in STALE:
        hits = []
        for f in files:
            t = io.open(f, encoding="utf-8", errors="replace").read()
            n = len(re.findall(pat, t, re.I))
            if n:
                hits.append((Path(f).name, n))
        found[desc] = hits
        icon = "🔴 仍在" if hits else "✅ 已无"
        print(f"  {icon} {desc}")
        for fn, n in hits[:4]:
            print(f"        {fn} × {n}")

    print()
    print("=" * 94)
    print("对照：`paper合/` 里是否还有这些（应为'已修'）")
    print("=" * 94)
    fh = sorted(glob.glob(str(REPO / "paper合" / "sections" / "*.tex")))
    for pat, desc in STALE:
        n = 0
        for f in fh:
            t = io.open(f, encoding="utf-8", errors="replace").read()
            n += len(re.findall(pat, t, re.I))
        print(f"  {'✅ 已无' if n == 0 else '🔴 仍有 ' + str(n)}  {desc}")

    print()
    print("=" * 94)
    print("判定")
    print("=" * 94)
    n_still = sum(1 for v in found.values() if v)
    print(f"  `paper/` 里 PR 点名的特征仍有 {n_still}/{len(STALE)} 类")
    if n_still >= len(STALE) // 2:
        print("  → **`paper/` 基本未按 PR 意见修改**（原稿状态）")
    print("  → 而 `paper合/` 是**合并 + 已修**版：批次已统一、5 seed、组内统计、标题收窄")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"p1_still_has": {k: v for k, v in found.items() if v},
             "n_classes": len(STALE), "n_still": n_still},
            ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
