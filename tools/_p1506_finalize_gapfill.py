# -*- coding: utf-8 -*-
"""Finalize the R3.9 trained-arm note in the audit report and HANDOFF."""
import io
import json
import os

AUDIT = "docs/P3_RESUBMISSION_AUDIT_2026-10-21.md"
HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"


def arm(name):
    p = os.path.join("paper3", "scripts", "outputs", "experiments", name)
    if not os.path.exists(p):
        return None
    d = json.load(io.open(p, encoding="utf-8"))
    return d.get("delta_E"), d.get("E")


def main() -> int:
    ntk = arm("verify_r1_s42_ntk_arm.json")
    gam = arm("verify_r1_s42_bcexplicit_v5_s5_m4_d2.json")
    txt = io.open(AUDIT, encoding="utf-8").read()
    old_row = ("| **R3.9** 更多基线 | NTK 对角线分配 + Γ 分配 + uniform 的**计算对比**（CLIP，真实图文对） | "
               "NTK 规则把预算更多给 vision（8/5/2/1），Γ 规则为（5/5/4/2）；两种排序不一致 | ⚠️ 仅计算、未训练"
               "（HALoRA/IGU/Shap 仍未实现）|")
    new_row = ("| **R3.9** 更多基线 | NTK 分配 + Γ 分配 + uniform 的**计算对比**（CLIP），并**训练** NTK/Γ 两个显式四块 arm"
               "（LLaVA，blank-image，20 样本，3 epochs）| NTK 排序 (8/5/2/1) vs Γ (5/5/4/2) 不同；"
               f"训练结果：NTK arm ΔE {ntk[0]:+.1f}、Γ arm ΔE {gam[0]:+.1f}（均未改善）| ✅ NTK/Γ arm 已训练；"
               "HALoRA/IGU/Shap 仍未实现 |")
    if old_row in txt:
        txt = txt.replace(old_row, new_row, 1)
        io.open(AUDIT, "w", encoding="utf-8", newline="").write(txt)
        print("audit updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    note = (f"\n> **补充（2026-10-21 21:15）**：R3.9 的两个显式四块 arm 已训练：NTK arm ΔE **{ntk[0]:+.1f}**"
            f"（轨迹 {ntk[1]}），Γ arm ΔE **{gam[0]:+.1f}**（轨迹 {gam[1]}）；均高于初始能量。"
            "归档：`verify_r1_s42_ntk_arm.json`、`verify_r1_s42_bcexplicit_v5_s5_m4_d2.json`。\n")
    if "两个显式四块 arm 已训练" not in h:
        idx = h.find("R1 缺口补齐（改投后证据包）")
        if idx >= 0:
            end = h.find("\n\n", idx)
            h = h[:end] + note + h[end:]
            io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h)
            print("handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    row_old = ("141. 🧪 **R1 缺口补齐证据包（2026-10-21 19:25）** —— Hessian 实测（lr 下 −3.5%）；Qwen2.5-VL-3B "
               "r5 +608/r6 −48（crossing 不复现）；NTK 分配对比；caption 下游零结果；五 seed/env 矩阵。"
               "`docs/P3_GAPFILL_2026-10-21.md`。")
    row_new = ("141. 🧪 **R1 缺口补齐证据包（2026-10-21 21:15）** —— Hessian 实测（lr 下 −3.5%）；Qwen2.5-VL-3B "
               "r5 +608/r6 −48（crossing 不复现）；NTK/Γ 显式四块 arm 已训练（+396/+263）；caption 下游零结果；"
               "五 seed/env 矩阵。`docs/P3_GAPFILL_2026-10-21.md`。")
    if row_old in m:
        m = m.replace(row_old, row_new, 1)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m)
        print("map updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
