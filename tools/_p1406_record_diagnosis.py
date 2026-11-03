# -*- coding: utf-8 -*-
r"""Record the A1 split-size diagnosis and rebuild the A1 package.

    python tools/_p1406_record_diagnosis.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
EVID = "docs/EVIDENCE_MAP_2026-10-19.md"
MIRROR = "tools/_p1284_prepare_public_mirror.py"

ENT = """> **🔬 2026-10-20 09:10 —— A1 扩展集反转的根因诊断：不是统计量失效，是**小留出集的分辨率不足**
>
> 对 20 条轨迹逐 epoch 复算后：
>
> | 分组 | 留出集大小 | min-M 平均 regret | 末轮 | 首轮 | min-M / 二项 SE |
> |---|---|---|---|---|---|
> | 大留出 | 353–1212 图（16 runs）| **0.58** | 0.52 | 3.55 | 0.37 SE |
> | 小留出 | 60–144 图（4 runs）| **6.18** | 4.51 | 22.05 | 1.08 SE |
>
> 诊断结论：小留出集上准确率本身的标准误约 4–6 点，任何按该留出集挑 epoch 的规则都落在 ~1 SE 内，
> 与统计量无关；大留出集上 min-M 与"训到末轮"基本持平（0.58 vs 0.52），但远好于首轮（3.55）。
> 量化步长（fathomnet8 ≈ 1/70、inat_wild ≈ 1/72–1/144）解释了小留出集上 mass 的粗糙度，但**不是主因**：
> 最小值的并列数平均仅 1.1，"取最后一个最小值"只把 1.70 改到 1.68；3 点滑动平均可降到 1.35，仍不优于末轮。
>
> 主文已改为**按留出集大小分层**的表述：证书是"留出集足够大时的选择统计量"，换来的是早停而不带来精度增益；
> 小留出集上所有规则都受采样噪声支配。A1 **61 页 0/0/0**，ledger **216/216 PASS**。
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
    if "扩展集反转的根因诊断" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("123. 🔬 **A1 反转根因诊断（2026-10-20 09:10）** —— 按留出集大小分层：大留出（353–1212 图，16 runs）min-M "
           "**0.58** vs 末轮 0.52、首轮 3.55（0.37 SE）；小留出（60–144 图，4 runs）min-M 6.18（1.08 SE）、末轮 4.51、首轮 22.05 "
           "→ 小留出受采样噪声支配，非统计量失效；并列/平滑检验排除并列主因；主文改为分层表述；A1 61 页 0/0/0、ledger 216/216。\n")
    if "A1 反转根因诊断（2026-10-20 09:10）" not in m:
        anchor = "122. 🧩 **五项可选升级完成"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")
    ev = io.open(EVID, encoding="utf-8").read()
    add = ("\n| A1 split-size diagnosis (large splits minM 0.58 vs last 0.52; small splits noise-dominated) | "
           "`outputs/analysis/a1_monitor_diagnosis.json`, `a1_monitor_split_diagnosis.json` | "
           "`tools/_p1402_a1_monitor_diagnosis.py`, `_p1404_a1_split_size.py` |\n")
    if "A1 split-size diagnosis" not in ev:
        io.open(EVID, "w", encoding="utf-8", newline="").write(ev.rstrip() + "\n" + add)
        print("  evidence map extended")
    t = io.open(MIRROR, encoding="utf-8").read()
    new = ["outputs/analysis/a1_monitor_diagnosis.json", "outputs/analysis/a1_monitor_split_diagnosis.json",
           "tools/_p1402_a1_monitor_diagnosis.py", "tools/_p1404_a1_split_size.py",
           "tools/_p1405_a1_split_text.py", "tools/_p1406_record_diagnosis.py"]
    missing = [x for x in new if x not in t]
    if missing:
        anchor = '    "outputs/analysis/a1_monitor_combined.json",'
        assert t.count(anchor) == 1
        t = t.replace(anchor, anchor + "\n" + "\n".join('    "%s",' % x for x in missing), 1)
        io.open(MIRROR, "w", encoding="utf-8", newline="").write(t)
        print("  mirror list extended")
    r = subprocess.run([sys.executable, "tools/_p1336_build_venue_package.py", "--manuscript", "paper_a1/main.pdf",
                        "--title-page", "paper_a1/title_page.pdf", "--cover-letter", "paper_a1/cover_letter.pdf",
                        "--source", "paper_a1", "--figures", "paper_a1/figures", "--venue",
                        "Pattern Analysis and Applications (A1)", "--out", "SUBMISSION/_venue_builds/A1_PAA_next",
                        "--apply"], capture_output=True, text=True)
    print("  A1 package rebuild exit:", r.returncode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
