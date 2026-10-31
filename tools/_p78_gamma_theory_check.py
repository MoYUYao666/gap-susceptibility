# -*- coding: utf-8 -*-
r"""**严格核实**：`Σ_m Γ_m‖g_m‖` 是否真在三臂间几乎不变？（2026-10-09）

## 为什么这是关键

论文 `theory.tex:67-69`：
```
per-modality contribution = <∇_m DG*, g_m> = Γ_m · ‖g_m‖
total instantaneous rate     = d(DG*)/dt = −η Σ_m Γ_m ‖g_m‖
```

**若该理论量在三臂间几乎相同，而实测 CGΔ 差 4 倍**
→ **理论无法解释"位置为何重要"**（而论文声称它"统一解释了"位置效应）。

## 但有一个陷阱我必须先排除

`Γ_m·‖g_m‖ = <∇_m DG*, g_m>` 是**内积**（可正可负），
而 `‖g_m‖` 是范数（恒正）→ **`Γ_m` 必须与 `‖g_m‖` 配对才等于内积**。
**故不能只用 `Γ_v+Γ_t` 判断**，须逐项算 `Γ_m × ‖g_m‖`。

**本脚本用归档与实测逐项计算，并给出三种口径**：
1. `Σ_m Γ_m`（简单相加，论文摘要里的说法）；
2. `Σ_m Γ_m · ‖g_m‖`（论文公式里的量）；
3. `Σ_m <∇_m DG*, g_m>`（内积原式，最严谨）。

    python tools\_p78_gamma_theory_check.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "gamma_theory_check.json"


def main() -> int:
    apply = "--apply" in sys.argv
    g = json.loads(io.open(REPO / "outputs/analysis/gamma_clip.json",
                           encoding="utf-8").read())
    sc = json.loads(io.open(REPO / "outputs/analysis/strict_control_summary.json",
                            encoding="utf-8").read())["configs"]

    print("=== 逐项计算（CLIP B/32，rank 8，8 批平均，单批瞬时）===")
    print(f"  {'臂':<13}{'Γ_v':>10}{'‖g_v‖':>10}{'Γ_v·‖g_v‖':>13}"
          f"{'Γ_t':>10}{'‖g_t‖':>10}{'Γ_t·‖g_t‖':>13}{'Σ(内积)':>12}{'实测CGΔ':>11}")

    rows = {}
    for arm in ("text_only", "both", "vision_only"):
        r = g["arms"][arm]
        Gv, Gt = r["Gamma_vision"], r["Gamma_text"]
        nv, nt = r["norm_grad_vision"], r["norm_grad_text"]
        # Γ_m = ‖∇_m DG*‖·cosφ_m；而 <∇_m DG*, g_m> = Γ_m·‖g_m‖ 仅当 g_m 与
        # ∇_m DG* 同向、且 cos φ_m 定义为与"总可训梯度"的夹角时成立。
        # 故这里给出 Γ_m·‖g_m‖ 的**形式值**，并单独标注其成立前提。
        iv, it = Gv * nv, Gt * nt
        s = iv + it
        cg = sc[arm]["cg_delta_mean"]
        rows[arm] = {"Gamma_v": Gv, "Gamma_t": Gt, "norm_v": nv, "norm_t": nt,
                     "prod_v": iv, "prod_t": it, "sum_prod": s, "cg_delta": cg,
                     "cos_v": r["cos_phi_vision"], "cos_t": r["cos_phi_text"]}
        print(f"  {arm:<13}{Gv:>+10.4f}{nv:>10.4f}{iv:>+13.4f}"
              f"{Gt:>+10.4f}{nt:>10.4f}{it:>+13.4f}{s:>+12.4f}{cg:>+11.4f}")

    print("\n=== 离散度对比（理论量 vs 实测）===")
    sums = [rows[a]["sum_prod"] for a in rows]
    cgs = [rows[a]["cg_delta"] for a in rows]
    sp = (max(sums) - min(sums)) / abs(sum(sums) / 3) * 100
    cp = (max(cgs) - min(cgs))
    print(f"  Σ(Γ_m·‖g_m‖): 范围 {min(sums):+.4f} ~ {max(sums):+.4f} ｜ "
          f"极差/均值 = **{sp:.2f}%**")
    print(f"  实测 CGΔ    : 范围 {min(cgs):+.4f} ~ {max(cgs):+.4f} ｜ "
          f"极差 = **{cp:.4f}**（{cp/abs(sum(cgs)/3)*100:.1f}%）")
    print(f"\n  → 理论量极差 **{sp:.2f}%**，实测极差 **{cp/abs(sum(cgs)/3)*100:.1f}%**"
          f" ｜ 相差 **{(cp/abs(sum(cgs)/3)*100)/max(sp,1e-9):.0f} 倍**")

    print("\n=== 判读（三条，逐条说明）===")
    print(f"  ① **排序**：按 Σ(Γ_m‖g_m‖) 排序 = "
          f"{sorted(rows, key=lambda a: -rows[a]['sum_prod'])}")
    print(f"     按实测 CGΔ 排序（越小越好）  = "
          f"{sorted(rows, key=lambda a: rows[a]['cg_delta'])}")
    print("  ② **量级**：见上（理论极差 vs 实测极差）")
    print("  ③ ⚠️ **前提未验**：`Γ_m·‖g_m‖ = <∇_mDG*, g_m>` 要求 `cos φ_m` 是")
    print("     `∇_mDG*` 与 `g_m` 的夹角；而本项目 `_p58` 里 `cos` 是")
    print("     **`∇_mDG*` 与「全部可训梯度之和」的夹角** → **两者不等价**，")
    print("     故本表的 `Γ_m·‖g_m‖` **只是形式值，不是内积**。")
    print("     **→ 要真正检验理论，须直接测 `<∇_mDG*, g_m>` 的内积**（见备注）。")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "rows": rows,
            "dispersion": {"sum_prod_pct": sp, "cg_delta_range": cp,
                           "ratio": (cp / abs(sum(cgs) / 3) * 100) / max(sp, 1e-9)},
            "caveat": "cos in _p58 is the angle to the SUM of all trainable grads, "
                      "not to each modality's own grad; so Gamma_m*norm is a formal "
                      "value, not the inner product. Measuring <grad_m DG*, g_m> "
                      "directly is required to test the theory.",
            "ordering_by_theory": sorted(rows, key=lambda a: -rows[a]["sum_prod"]),
            "ordering_by_measurement": sorted(rows, key=lambda a: rows[a]["cg_delta"]),
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
