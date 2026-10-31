# -*- coding: utf-8 -*-
r"""核 R3.21 的真正症结：Random 组容量跨 16 倍（2026-10-12）。

## 待核

1. `Σ_k cost_k = 1,809,408`？→ `C·Σ_k cost_k`：C=4 → 7,237,632（与 Theory 组同）；C=64 → **16×**
2. 稿件 **Random 组定义**是否确实写 `{4,16,32,64}` 且 rank 均匀施于全部模块
3. ⚠️ **关键**：**Theory 组自己是否也跨容量**？若 Theory 组跑的是 r=4/16/32/64 各一次，
   则 `σ(Theory)=27 vs σ(Random)=808` 的对比**两侧都跨容量** → 问题比成员说的更严重
4. 正文"绝对否定"（no Γ measurement）与附录 D 是否真冲突

    python tools\_p424_verify_r321_confound.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EX = REPO / "paper3" / "paper_ieee" / "sections" / "experiments.tex"
AP = REPO / "paper3" / "paper_ieee" / "sections" / "appendix.tex"
OUT = REPO / "outputs" / "analysis" / "r321_confound_verify.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rep = {}
    ex = io.open(EX, encoding="utf-8", errors="replace").read()
    apx = io.open(AP, encoding="utf-8", errors="replace").read()

    print("=" * 100)
    print("① 成本与容量表（算术核对）")
    print("=" * 100)
    p = REPO / "outputs" / "analysis" / "p3_alloc_budget_probe.json"
    sum_cost = None
    if p.exists():
        d = json.loads(io.open(p, encoding="utf-8", errors="replace").read())
        pb = d.get("per_block", {})
        for k, v in pb.items():
            print(f"  {k:<16} cost_per_rank = {v.get('cost_per_rank'):,}")
        sum_cost = sum(v.get("cost_per_rank", 0) for v in pb.values())
        print(f"  Σ_k cost_k = {sum_cost:,}")
    if sum_cost:
        print()
        print("  C · Σ_k cost_k：")
        for C in (4, 16, 32, 64):
            print(f"     C={C:<3} → {C * sum_cost:>13,}  （相对 C=4: {C/4:.0f}×）")
        rep["sum_cost"] = sum_cost
        rep["capacity_by_C"] = {str(C): C * sum_cost for C in (4, 16, 32, 64)}

    print()
    print("=" * 100)
    print("② 稿件里 Random 组与 Theory 组的定义（逐字）")
    print("=" * 100)
    i = ex.find("Counterfactual Validation")
    seg = ex[i:i + 2200] if i >= 0 else ""
    print(seg[:2000])
    rep["counterfactual_segment"] = seg[:2000]

    print()
    print("=" * 100)
    print("③ Theory 组的 rank 是否跨容量（找 155/152/167 那组数）")
    print("=" * 100)
    for m in re.finditer(r"\+155|r=4\)|r=16|r=32|r=64", ex):
        ln = ex[:m.start()].count("\n") + 1
        print(f"  L{ln}: …{' '.join(ex[max(0,m.start()-160):m.start()+200].split())[:340]}…")
        print()

    print("=" * 100)
    print("④ 正文的绝对否定 vs 附录 D 的 Γ 计算")
    print("=" * 100)
    for pat, src, name in ((r"No \$?\\?Gamma\$? measurement", ex, "experiments"),
                           (r"no .{0,30}measurement", ex, "experiments(泛)"),
                           (r"compute_gamma_llava", apx, "appendix"),
                           (r"illustrate the \$\\Gamma\$-based allocation", apx, "appendix")):
        for m in re.finditer(pat, src, re.I):
            ln = src[:m.start()].count("\n") + 1
            print(f"  [{name}:{ln}] …{' '.join(src[max(0,m.start()-200):m.start()+340].split())[:460]}…")
            print()

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
