# -*- coding: utf-8 -*-
r"""Record round 4b: extended A1 monitoring validation (v2), package refresh, mirror staging.

    python tools/_p1364_record_round4b.py [--apply]
"""
from __future__ import annotations

import argparse
import io

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
MIRROR = "tools/_p1284_prepare_public_mirror.py"

ENT = """> **🎯 2026-10-19 20:10 —— A1 监控验证扩展完成（v2：2 backbone × 2 数据集 × 3 seed × 10 epoch = 12 轨迹 / 120 checkpoint）**
>
> | 规则（越接近 oracle 越好）| 平均 regret / 最差 |
> |---|---|
> | min-$M(0.01)$（事后最优）| **0.41 / 1.28** |
> | **顺序 min-$M$ 规则（只用已见 epoch，δ=0.01）** | **0.50 / 1.56** |
> | 训到末轮 | 0.60 / 1.73 |
> | 首轮 | 3.54 / 7.94 |
> | min-CG | 1.53 / 4.54 |
> | 顺序 CG 规则（δ=0.01）| 1.68 / 4.54 |
>
> 池化 120 点：$r(M,\\text{top-1})=-0.986$；CG 为 $+0.78$，但所有基于 CG 的停轮规则都不如任何基于 $M$ 的规则。
> 最优 epoch 分布 2–10（中位 6）。结论：证书在"早停是真决策"的域内评测中可用；迁移域中不如首轮是轨迹单调所致，不是统计量失效。
>
> 写入 `paper_a1/main.tex`（60 页 0/0/0），A1 ledger **188/188 PASS**；归档 `a1_monitor_interior_v2.json`、`_v2_rules.json`。
> 审计：**A1 仅剩预期 I-02**；P3 **READY/A**（补充材料新增 S7 后门禁更新为 10 节）；A23 / Commentary / Paper A Springer **READY/A**；
> Paper A NC 仅剩预期 I-02。A1/P3/Commentary 修回包已按最新稿重建。
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
    if "A1 监控验证扩展完成" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("116. 🎯 **A1 监控验证 v2（2026-10-19 20:10）** —— 12 轨迹/120 checkpoint；顺序 min-M 规则（只用来 epoch）平均 regret "
           "**0.50**（事后最优 0.41、训到末轮 0.60、首轮 3.54、CG 规则 1.68）；池化 $r(M)=-0.986$、$r(CG)=+0.78$；"
           "A1 60 页 0/0/0、ledger 188/188；P3 补充材料 S7 后门禁更新为 10 节、P3 READY/A；A1/P3/Commentary 修回包重建。\n")
    if "A1 监控验证 v2（2026-10-19 20:10）" not in m:
        anchor = "115. 📚 **暂缓项落地"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")
    t = io.open(MIRROR, encoding="utf-8").read()
    new = ["outputs/analysis/a1_monitor_interior_v2.json", "outputs/analysis/a1_monitor_interior_v2_rules.json",
           "outputs/analysis/p3_rank_local_control.json", "tools/_p1357_monitor_interior_v2.py",
           "tools/_p1358_p3_rank_control.py", "tools/_p1360_p3_supplement_control.py",
           "tools/_p1361_monitor_v2_analysis.py", "tools/_p1362_record_round4a.py",
           "tools/_p1363_a1_monitor_v2_insert.py"]
    missing = [x for x in new if x not in t]
    print(f"  mirror additions: {len(missing)}")
    if missing:
        anchor = '    "outputs/analysis/a1_monitor_interior.json",'
        assert t.count(anchor) == 1
        t = t.replace(anchor, anchor + "\n" + "\n".join('    "%s",' % x for x in missing), 1)
        io.open(MIRROR, "w", encoding="utf-8", newline="").write(t)
        print("  mirror list extended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
