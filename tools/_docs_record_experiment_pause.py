# -*- coding: utf-8 -*-
r"""记录实验断点（2026-10-02 下午终止，晚上续跑）。

## 为什么要记

操作者要求"先终止，晚上再跑"。若不记录，晚上需要重新推断：哪些跑完了、哪些没跑、用什么命令续跑。
本项目有"交付件尚未落地时不得写成已完成"与"每条记录必须可复核"的规矩，故断点必须落成文件。

## 关键：续跑是**幂等**的

`strict_freeze_control.py` 与 `siglip_experiments.py` 都有"结果已存在则跳过"的逻辑，
所以**重跑同一条命令即可自动只补未完成的部分**，不会覆盖已有结果。

    python tools\_docs_record_experiment_pause.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "HANDOFF.md"


def count(pat: str) -> int:
    return len(glob.glob(str(REPO / pat), recursive=True))


def main() -> int:
    apply = "--apply" in sys.argv

    oc = count("outputs/strict_freeze_openclip/*/seed*/results.json")
    ov = count("outputs/siglip_strict/*/s6_siglip_lora_vision_only/results.json")
    rk = count("outputs/strict_freeze_rank/*/seed*/results.json")
    total = oc + ov + rk

    # OpenCLIP 三臂结果（已完成部分，用于断点记录）
    def arm(d: str, tag: str) -> dict:
        out = {}
        for p in glob.glob(str(REPO / f"outputs/{d}/{tag}/seed*/results.json")):
            x = json.loads(io.open(p, encoding="utf-8").read())
            out[x["seed"]] = x["final_gap"]["centroid_gap"] - x["initial_gap"]["centroid_gap"]
        return out

    rows = []
    for name, d in (("CLIP B/32", "strict_freeze"), ("OpenCLIP B/32", "strict_freeze_openclip")):
        cells = []
        for t in ("text_only", "both", "vision_only"):
            a = arm(d, t)
            cells.append("%+.4f" % (sum(a.values()) / len(a)) if a else "—")
        rows.append((name, cells))

    tbl = "\n".join("> | %s | %s | %s | %s |" % (n, c[0], c[1], c[2]) for n, c in rows)

    entry = f"""> **⏸️ 2026-10-02 14:15 —— 补充实验暂停（操作者要求"先终止，晚上再跑"）**
>
> **暂停方式**：`job_kill` + `Stop-Process`（含 DataLoader worker）。**确认无残留 python 进程、GPU 已释放**。
>
> ### 断点：{total}/38
>
> | 实验 | 进度 | 产物目录 |
> |---|---|---|
> | **OpenCLIP B/32 严格冻结** | ✅ **{oc}/15 完成** | `outputs/strict_freeze_openclip/` |
> | **SigLIP vision_only** | 🏃 **{ov}/5**（被中止，未产出） | `outputs/siglip_strict/seed*/s6_siglip_lora_vision_only/` |
> | **严格冻结 rank sweep** | ⏳ **{rk}/18**（未开始） | `outputs/strict_freeze_rank/` |
>
> ### 已完成部分的结果（**三臂，可复核**）
>
> OpenCLIP 三臂（5000 样本 / 10 epochs / rank8+α16 / 5 seeds）：text_only **+0.0694**（R@1 0.643）、
> both **+0.0881**（0.680）、vision_only **+0.0925**（0.672）。
> 与 CLIP 对照（`tools/_siglip_strict_stats.py`、`tools/_crossarch_strict_stats.py`）：
>
> > | 骨干 | text_only | both | vision_only |
> > |---|---|---|---|
> {tbl}
>
> **两条已成立的结论**：
> ① **两个 B/32 骨干的三臂排序完全相同**（text_only < both < vision_only）——**但降间隙最好的位置
> （text_only）不是检索最好的位置（both）**，即"排序与检索不一致"，在两个骨干上都如此；
> ② **LAION 骨干上三个臂的间隙全部增大**（无"保护"位置），而 CLIP 上有两个为负 → 再次指向**预训练数据**。
>
> ### 续跑命令（**幂等**：已完成的 run 会自动跳过）
>
> ```powershell
> # 补 SigLIP vision_only（5 seeds）+ rank sweep（rank 4/16/32 × 3 seeds × 2 臂）
> python tools\\_run_extra_experiments.py --apply
> ```
>
> **前置**：需先确认 GPU 空闲。单 run 耗时（实测/估算）：
> SigLIP vision_only **约 50–55 分钟/个**（patch-16 视觉塔，慢）｜rank sweep 约 6–17 分钟/个。
> **预计续跑总时长约 5.5 小时**。
>
> ### 脚本改动（已提交）
>
> - `strict_freeze_control.py`：新增 `--model/--out-dir/--name/--rank/--alpha-mult`；
>   **修掉一个会让实验白跑的 bug**——`--model` 原先只改 `PRISTINE`（backbone_deltas 的参照），
>   未传给 `TrainConfig.clip_model`，**训练仍在跑默认 CLIP**，导致 OpenCLIP 第一批结果与 CLIP **逐位相同**；
>   现传入并加了 `[model-check]` 断言防线；无效产物已删除。
> - `siglip_experiments.py`：新增 `s6_siglip_lora_vision_only` 配置。
>
> ### ⚠️ 时长估计的教训（记下来避免再犯）
>
> 我三次低估：把 `both` 当成 6 分钟（实际 17）、把 SigLIP vision_only 当成 6 分钟（实际约 50–55）、
> 因此把总时长从 4 小时一路修到 5.5 小时。**根因是按 CLIP B/32 的速度类推别的骨干**——
> 而 SigLIP 的视觉塔是 patch-16（序列长度 4 倍）、B/32 的双臂反传也比单臂慢约 3 倍。
> **以后估时要按"哪个塔要反传"分别估，不能跨骨干套用速度。**

"""

    if apply:
        t = io.open(F, encoding="utf-8").read()
        anchor = "> **🗓️ 2026-10-02 —— 建立例行约定"
        i = t.find(anchor)
        if i < 0:
            print("  ⚠ 未找到锚点")
            return 1
        io.open(F, "w", encoding="utf-8", newline="").write(t[:i] + entry + t[i:])
        t2 = io.open(F, encoding="utf-8").read()
        assert "补充实验暂停" in t2
        assert "_run_extra_experiments.py --apply" in t2
        print(f"  ✅ 已记录断点（{len(t2.splitlines())} 行）｜ 进度 {total}/38")
    else:
        print(f"  当前进度 {total}/38（OpenCLIP {oc}/15、SigLIP vo {ov}/5、rank {rk}/18）")
        print("  （预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
