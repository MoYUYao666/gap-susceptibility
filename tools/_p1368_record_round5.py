# -*- coding: utf-8 -*-
r"""Record round 5: P3 current-protocol re-run confirms the [5,6] crossing; supplement table added; package refresh.

    python tools/_p1368_record_round5.py [--apply]
"""
from __future__ import annotations

import argparse
import io

HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
MIRROR = "tools/_p1284_prepare_public_mirror.py"
EVID = "docs/EVIDENCE_MAP_2026-10-19.md"
P3MEMO = "docs/P3_UPGRADE_MEMO_2026-10-19.md"

ENT = """> **🔁 2026-10-19 20:45 —— P3 重跑归因完成：[5,6] 跨越在**现行可复现脚本**上复现**
>
> 用户要求重跑，已用 `paper3/scripts/run_training.py` 现行默认（20 样本 = 16 训练/4 评测、lr $5\\times10^{-5}$、qkvo、float16、batch 1），
> seed 42、3 epoch，重跑 r=5、6、16（每次 23–28 min，本地 RTX 4060）：
>
> | rank | $E(0)\\to E(3)$ | $\\Delta E$ | 结论 |
> |---|---|---|---|
> | 5 | 3921.0 → 3827.0 → 3770.0 → 3910.5 | **−10.5** | 负 |
> | 6 | 3921.0 → 3842.0 → 3797.0 → 4036.0 | **+115.0** | 正 |
> | 16 | 3921.0 → 3687.5 → 4025.5 → 5156.0 | **+1235.0** | 强正 |
>
> ⇒ **现行脚本的临界区间就是 $[5,6]$**（与归档 E2 族一致）；旧族 $E_0=3927.0/3930.5$、现行 $E_0=3921.0$，两者差异来自脚本版本/配置
> 而非 seed 噪声，等于把"临界 rank 属于协议"从推断升级为**可复现实验**。
>
> 已写入：主文结论一句（`sections/conclusion.tex`）+ **补充材料 S8**（重跑表，含 4 个能量点与 ΔE）。
> P3 主文 **10 页 0/0/0**、补充材料 **6 页 0/0/0**；P3 门禁更新为 11 节；归档 `outputs/analysis/p3_rerun_protocol.json`。
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
    if "P3 重跑归因完成" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT + h[j + 1:])
        print("  handoff added")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("117. 🔁 **P3 重跑归因（2026-10-19 20:45）** —— 现行脚本默认配置重跑 r=5/6/16（seed42，3 epoch）：ΔE = **−10.5 / +115.0 / +1235.0**，"
           "临界区间 **[5,6] 在现行协议上复现**；旧族 E0=3927.0/3930.5、现行 E0=3921.0 ⇒ 差异来自脚本版本/配置；主文结论一句 + 补充材料 S8 重跑表；"
           "P3 10 页 + supp 6 页，均 0/0/0。\n")
    if "P3 重跑归因（2026-10-19 20:45）" not in m:
        anchor = "116. 🎯 **A1 监控验证 v2"
        idx = m.find(anchor)
        assert idx >= 0
        end = m.find("\n", idx)
        io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
        print("  map row added")
    ev = io.open(EVID, encoding="utf-8").read()
    add = ("| P3 current-protocol re-run (r=5,6,16: ΔE −10.5/+115.0/+1235.0, E0=3921) | "
           "`outputs/analysis/p3_rerun_protocol.json` | `tools/_p1365_p3_rerun_protocol.py` |\n")
    if "P3 current-protocol re-run" not in ev:
        io.open(EVID, "w", encoding="utf-8", newline="").write(ev.rstrip() + "\n" + add)
        print("  evidence map extended")
    pm = io.open(P3MEMO, encoding="utf-8").read()
    note = ("\n## Round 5 (2026-10-19 20:45): the [5,6] crossing re-run on the current protocol\n\n"
            "Previously only archived families were available; the current script gives E0 = 3921.0 while the archived E2 family\n"
            "gives 3927.0 and the r=5/r=6 verify runs give 3930.5. A fresh re-run of the current script (seed 42, three epochs)\n"
            "gives ΔE = -10.5 (r=5), +115.0 (r=6) and +1235.0 (r=16), so the [5,6] sign change is reproduced on the current,\n"
            "reproducible protocol; the previously noted [14,16] sweep bracket came from a different configuration of the same\n"
            "script lineage. Archive: outputs/analysis/p3_rerun_protocol.json; main text one sentence, supplement section S8.\n")
    if "Round 5 (2026-10-19 20:45)" not in pm:
        io.open(P3MEMO, "w", encoding="utf-8", newline="").write(pm.rstrip() + "\n" + note)
        print("  p3 memo extended")
    t = io.open(MIRROR, encoding="utf-8").read()
    new = ["outputs/analysis/p3_rerun_protocol.json", "tools/_p1365_p3_rerun_protocol.py",
           "tools/_p1366_p3_rerun_insert.py", "tools/_p1367_p3_rerun_supplement.py"]
    missing = [x for x in new if x not in t]
    print(f"  mirror additions: {len(missing)}")
    if missing:
        anchor = '    "outputs/analysis/p3_rank_local_control.json",'
        assert t.count(anchor) == 1
        t = t.replace(anchor, anchor + "\n" + "\n".join('    "%s",' % x for x in missing), 1)
        io.open(MIRROR, "w", encoding="utf-8", newline="").write(t)
        print("  mirror list extended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
