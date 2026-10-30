# -*- coding: utf-8 -*-
r"""落账：COCO 补跑进度与已得数据（2026-10-08 14:30）。

    python tools\_docs_coco_progress.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import collections
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    apply = "--apply" in sys.argv
    fs = sorted(glob.glob(str(REPO / "outputs/coco_sweep/**/results.json"), recursive=True))
    byconf = collections.defaultdict(list)
    for f in fs:
        p = f.replace("\\", "/").split("/")
        byconf[f"{p[-4]} {p[-3]}"].append(f)
    lines = []
    for k in sorted(byconf):
        vs = []
        for f in byconf[k]:
            d = json.loads(io.open(f, encoding="utf-8").read())
            vs.append(d["final_gap"]["centroid_gap"] - d["initial_gap"]["centroid_gap"])
        lines.append(f"| `{k}` | {len(byconf[k])}/3 | {st.mean(vs):+.4f} |")
    table = "\n".join(lines)

    if not apply:
        print(f"  已完成 {len(fs)}/36；构成：")
        print(table)
        print("  （预演）")
        return 0

    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "COCO 补跑进度（16/36）" in t:
        print("  已记录，跳过")
        return 0
    ent = f"""> **📊 2026-10-08 14:30 —— COCO 补跑进度 16/36（数据已在积累）**
>
> ### 队列健康（定时核查）
>
> | 核查项 | 结果 |
> |---|---|
> | 已完成 | **16 / 36 run** |
> | **新失败** | ✅ **无**（10:19–10:22 的 8 条 `rc=2` 是 `--seeds` bug **修复前**的旧记录） |
> | 执行器 | ✅ 在跑（PID 45976） |
> | GPU | 7723 MiB / 8188 MiB，100%（**独占，无争用**） |
> | 单 run 耗时 | 36–48 min（均值 40） |
>
> ### 已完成配置的 CGΔ（`both` 臂，严格冻结）
>
> | 配置 | seed | CGΔ 均值 |
> |---|---|---|
> {table}
>
> **观察（暂定，待 `text_only` 臂补齐后才能定论）**：
> - COCO 的 CGΔ **普遍为负且量级大于 Flickr30k**（Flickr30k 的 both r8 为 −0.0258）；
> - **rank 效应非单调**：r1（−0.032）变化最小，r16/r32/r64（−0.15 量级）变化最大。
>
> ⚠️ **不得据此下结论**：`text_only` 臂（6 配置）尚未开始，**"最保护臂"需要两臂齐备才能判**。
>
> ### 剩余
>
> `both r=32` 还需 2 seed，然后 **`text_only` 6 配置 × 3 seed = 18 run** → 约 **14 h**。
>
> ### 严格冻结校验
>
> 每个完成的 run 都记录 `vis_nonzero=0`（仅 LoRA A/B 可训）——**协议未被破坏**。
"""
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ent + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("COCO 补跑进度 16/36", "不得据此下结论", "vis_nonzero=0", "无争用"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
