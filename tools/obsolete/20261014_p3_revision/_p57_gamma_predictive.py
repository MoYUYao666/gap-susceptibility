# -*- coding: utf-8 -*-
r"""风险 #5：把"预测 `α`"改为**检验 `Γ_m` 的预测力**（2026-10-08）。

## 为什么这样改

`α` 预测（实验 A）6 次未对齐，**根因是"与归档可比的动力学"难复现**；
而 **`Γ_m` 不需要时间积分**——它是**瞬时**量：

    Γ_m = ‖∇_m DG*‖ · cos φ_m

**故可绕开 ODE 拟合，直接检验它是否预测"哪一侧适配更能降低 gap"。**

## 判据（**先写明**）

对每个骨干，比较三臂的 `CGΔ`（gap 变化）与 `Γ_m`：

- **若 `Γ_m` 大的一侧对应的臂确实使 gap 降得更多** → `Γ_m` 有预测力；
- 归档 `outputs/theory/encoder_side/encoder_side.json` 已有 CLIP 的两侧梯度范数，
  故本脚本用**已有数据**检验，**不需要新跑**。

**注意口径**：归档给的是 `norm_g_vision` / `norm_g_text`（**只看范数，不比 cos**），
故严格说检验的是 `‖∇_m DG*‖` 的预测力；`cos φ_m` 部分**需实测**（`_p54` 已在 Qwen 上给出）。

    python tools\_p57_gamma_predictive.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "gamma_predictive.json"


def main() -> int:
    apply = "--apply" in sys.argv
    es = REPO / "outputs/theory/encoder_side/encoder_side.json"
    sc = REPO / "outputs/analysis/strict_control_summary.json"
    gv = REPO / "outputs/analysis/gamma_vlm.json"
    for p in (es, sc):
        if not p.exists():
            print(f"  ❌ 缺 {p.relative_to(REPO)}")
            return 1
    e = json.loads(io.open(es, encoding="utf-8").read())["summary"]
    s = json.loads(io.open(sc, encoding="utf-8").read())["configs"]

    print("=== 双塔（CLIP B/32）===")
    print(f"  {'臂':<12} {'‖g_vision‖':>12} {'‖g_text‖':>12} {'CGΔ':>10}")
    for arm in ("text_only", "both", "vision_only"):
        r = e.get(arm, {})
        print(f"  {arm:<12} {r.get('norm_g_vision', float('nan')):>12.4f} "
              f"{r.get('norm_g_text', float('nan')):>12.4f} "
              f"{s[arm]['cg_delta_mean']:>+10.4f}")

    print("\n=== 解码器 VLM（Qwen2-VL-2B）===")
    if gv.exists():
        g = json.loads(io.open(gv, encoding="utf-8").read())["arms"]
        qv = json.loads(io.open(REPO / "outputs/analysis/qwen_verdict.json",
                                encoding="utf-8").read())["rows"]
        for arm in ("text_only", "both", "vision_only"):
            r = g.get(arm, {})
            print(f"  {arm:<12} {r.get('norm_g_vision', float('nan')):>12.4f} "
                  f"{r.get('norm_g_text', float('nan')):>12.4f} "
                  f"{qv[arm]['rel']*100:>9.1f}%（相对降幅）")

    print("\n=== 检验：‖∇_m DG*‖ 能否预测『哪一侧适配更有效』 ===")
    checks = []
    # CLIP：文字侧梯度 13.51 vs vision_only 臂的 CGΔ 最差
    cl_t = e.get("text_only", {}).get("norm_g_text", float("nan"))
    cl_v = e.get("vision_only", {}).get("norm_g_vision", float("nan"))
    cl_best = min(("text_only", "both", "vision_only"),
                  key=lambda a: s[a]["cg_delta_mean"])
    checks.append(("CLIP B/32", cl_t, cl_v, cl_best,
                   "text_only" if cl_t > cl_v else "vision_only"))
    print(f"  CLIP B/32  : ‖g_text‖={cl_t:.4f} vs ‖g_vision‖={cl_v:.4f} → "
          f"预测最优侧=**{'text_only' if cl_t > cl_v else 'vision_only'}** ｜ "
          f"实测最优臂=**{cl_best}** ｜ {'✅' if (cl_best == 'text_only') == (cl_t > cl_v) else '❌'}")

    if gv.exists():
        g = json.loads(io.open(gv, encoding="utf-8").read())["arms"]
        qv = json.loads(io.open(REPO / "outputs/analysis/qwen_verdict.json",
                                encoding="utf-8").read())["rows"]
        q_t = g["text_only"]["norm_g_text"]
        q_v = g["vision_only"]["norm_g_vision"]
        q_best = max(qv, key=lambda a: qv[a]["rel"])
        pred = "text_only" if q_t > q_v else "vision_only"
        print(f"  Qwen2-VL   : ‖g_text‖={q_t:.4f} vs ‖g_vision‖={q_v:.4f} → "
              f"预测最优侧=**{pred}** ｜ 实测最优臂=**{q_best}** ｜ "
              f"{'✅ 一致' if q_best == pred else '❌ 不一致'}")
        print(f"    ⚠️ 注意：Qwen 上实测最优是 `both`（不是单侧），而 `Γ_vision`={g['both']['Gamma_vision']:.3f} "
              f"≫ `Γ_text`={g['both']['Gamma_text']:.4f}")
        print(f"       → **`Γ_m` 的『范数大小』与『最优位置』在本例中并不一致**，须如实报告。")

    print("\n=== 结论 ===")
    print("  `Γ_m` 的可测性已被证实（硬校验：冻结侧梯度严格为 0，双模型一致）；")
    print("  但它对『最优位置』的预测力**在两个模型上并不一致**——")
    print("  **故论文应把 `Γ_m` 表述为『机制解释量』，而非『可直接用于选位置的预测器』。**")

    if apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "clip_b32": {"norm_g_text": cl_t, "norm_g_vision": cl_v, "best_arm": cl_best},
            "qwen": ({"norm_g_text": q_t, "norm_g_vision": q_v, "best_arm": q_best}
                     if gv.exists() else None),
            "conclusion": "Gamma_m is measurable and passes hard checks, but its norm does "
                          "not consistently predict the best position; report it as a mechanism "
                          "quantity, not as a position predictor",
        }, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
