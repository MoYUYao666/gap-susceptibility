# -*- coding: utf-8 -*-
r"""Record the optional upgrade round (expanded A1 monitoring, A23 tau calibration, corrected Qwen check, P3 per-run table).

    python tools/_p1401_record_optional.py [--apply]
"""
from __future__ import annotations

import argparse
import io

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
EVID = "docs/EVIDENCE_MAP_2026-10-19.md"
PLAN = "docs/UPGRADE_PLAN_P3_A23_COMMENTARY_2026-10-19.md"

ENT = """> **🧩 2026-10-20 08:40 —— 五项可选升级全部完成（本地），其中 A1 扩展集结果**如实转弱**并已改写措辞**
>
> | 项 | 结果 |
> |---|---|
> | **A1 扩展集**（加 seeds 44/45 + 第四域 inat_wild）| **20 轨迹 / 200 checkpoint**：min-$M$ 平均 regret **1.70**（最差 10.00），末轮 **1.32**（最差 5.56）、首轮 7.25；置信度 1.91–3.91；顺序规则跨域不稳（3.82，最差 27.78）；池化 $r(M)=-0.977$。**结论：证书接近 oracle、优于置信度与首轮，但不优于"训到末轮"** ⇒ 主文新增两句如实报告（intro 贡献 + 监控段），措辞收敛为"域内选择统计量"，不再宣称普遍优于末轮；A1 **61 页 0/0/0**，ledger **208/208** |
> | **A23 τ 校准** | 线性重标定后 τ 的**关系**可跨编码器迁移（Spearman 0.71–0.86、Pearson 0.81–0.85、MAE 3.26–3.41 点），但**硬阈值仍不迁移**（BA 0.38–0.50）；已写入正文；A23 **66 页 0/0/0**，门禁更新为 66 页并 `ALL CHECKS PASSED` |
> | **P3 Qwen2-VL-2B 修正重跑** | 上轮无效原因找到：脚本用 `--llm-rank` 才改真实秩；修正后 trainable 1.4M/1.6M、ΔE **−352.0（r=5）/ −288.0（r=6）**，两秩均负、**r≤6 无符号翻转** ⇒ 作为"更小模型上的边界观察"写入补充材料，不当作复现 |
> | **P3 补充材料 per-run 表** | 新增 S12（8 个 run 的 $E(0..3)$ 与 ΔE 逐一列出），S11 同步更新 Qwen 说明；补充材料 **6 页 0/0/0**、门禁 12 节 |
> | **修回包** | A1（61 页）/ A23（66 页）/ P3（10 页 + supp 6 页）已重建；A1 仅预期 I-02、A23 复审 READY/A |
>
> 说明：A1 扩展集证据**削弱**了此前"min-M 优于末轮"的子集结论，文档与正文均按"两个数据集结果并列"处理，不隐藏反向证据。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "五项可选升级全部完成" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("122. 🧩 **五项可选升级完成（2026-10-20 08:40）** —— A1 扩展集 20 轨迹/200 cp：min-M 1.70 vs 末轮 1.32、首轮 7.25"
           "（如实转弱并改写措辞，61 页、ledger 208/208）；A23 τ 线性重标定关系可迁移（Spearman 0.71–0.86）但硬阈值不迁移（66 页）；"
           "P3 Qwen2B 修正重跑（−352/−288，r≤6 无翻转，边界观察）+ 补充材料 S12 per-run 表（6 页，12 节）；三包重建。\n")
    if "五项可选升级完成（2026-10-20 08:40）" not in m:
        anchor = "121. 🔖 **v2.0 版本 DOI 落账"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")
    ev = io.open(EVID, encoding="utf-8").read()
    add = """
| A1 expanded monitoring set (20 runs/200 checkpoints; minM 1.70, last 1.32) | `outputs/analysis/a1_monitor_combined.json` | `tools/_p1398_a1_combined.py`, `_p1399_a1_combined_text.py` |
| A23 tau calibration (linear rescaling transfers the relation, Spearman 0.71-0.86) | `outputs/analysis/a23_tau_calibration.json` | `tools/_p1393_a23_tau_calibration.py` |
| P3 corrected Qwen2-VL-2B check (trainable 1.4/1.6M; dE -352/-288) | `outputs/analysis/p3_qwen2b_crossing_fixed.json` | `tools/_p1391_qwen2b_fixed.py` |
"""
    if "A1 expanded monitoring set" not in ev:
        io.open(EVID, "w", encoding="utf-8", newline="").write(ev.rstrip() + add)
        print("  evidence map extended")
    pl = io.open(PLAN, encoding="utf-8").read()
    add2 = """
## Round 6 status (2026-10-20 08:40)

The five optional upgrades were executed: expanded A1 monitoring (extra seeds and a fourth domain, reported honestly even
though it weakens the subset result), A1 wording now describes the certificate as an in-domain selection statistic rather
than a universally superior stopping rule, A23 tau calibration (the relation transfers up to a linear rescaling, the hard
threshold does not), the corrected Qwen2-VL-2B local check (valid rank variation; both ranks negative, no sign flip up to
r=6, reported as a boundary), and a per-run supplementary table for the P3 re-runs.
"""
    if "Round 6 status (2026-10-20 08:40)" not in pl:
        io.open(PLAN, "w", encoding="utf-8", newline="").write(pl.rstrip() + "\n" + add2)
        print("  plan updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
