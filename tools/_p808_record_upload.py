# -*- coding: utf-8 -*-
r"""Record the rank rerun, its result, and the GitHub upload.

    python tools/_p808_record_upload.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📤 2026-10-15 21:30 —— Paper A 的 rank 消融重跑完成 + **已上传 GitHub**（未建 tag，未动 Release）
>
> ### 一、✅ rank 消融重跑结果（真 LoRA，冻结基座）
>
> **配置**：COCO train2014 **5,000 图** → val2014 **3,000 图**（不相交）；**10 epoch / batch 128 / lr 1e-5 / dropout 0 / `α=2r` / seed 42**；
> 与论文原协议（`experiments/theory/v1_rank_sweep.py`）对齐 batch/epochs/samples/`α=2r`，**仅超参用修正值**。
>
> | rank | 可训练参数 | **dCG** | **R@1** | i2t R@1 | t2i R@1 | 耗时 |
> |---|---|---|---|---|---|---|
> | 2 | 49,152 | **+0.0135** | 0.6071 | 0.9337 | 0.2805 | 1753 s |
> | 4 | 98,304 | +0.0110 | 0.6095 | 0.9373 | 0.2817 | 2173 s |
> | 8 | 196,608 | +0.0147 | 0.6107 | 0.9367 | 0.2847 | 1578 s |
> | 16 | 393,216 | +0.0143 | 0.6122 | 0.9370 | 0.2874 | 1585 s |
> | 32 | 786,432 | +0.0095 | 0.6122 | 0.9357 | 0.2888 | 2406 s |
> | 64 | 1,572,864 | **+0.0021** | 0.6116 | 0.9340 | 0.2893 | — |
>
> **✅ 可训练参数精确等于 `196,608 × r/8`** ⇒ 真 LoRA 生效、rank 确实是被变动的旋钮。
>
> **🔴 两条结论（对论文的含义）**：
> 1. **`dCG` 随 rank 递减且非单调**（+0.0135 → +0.0021，中间起伏：+0.0110 / +0.0147 / +0.0143 / +0.0095）
>    ⇒ **论文"gap 对 configured rank 单调"的主张不成立**；实测是**高 rank 反而更好地保住 gap**；
> 2. **`R@1` 从 0.6071 微升到 0.6122（rank 2→16/32）后持平**（rank 64 为 0.6116）
>    ⇒ 检索对 rank 不敏感，**"低秩足够"成立**。
> 3. **`t2i` 随 rank 单调微升**（0.2805 → 0.2893）；`i2t` 基本持平（0.9337–0.9373）。
>
> **⚠️ 与论文原主张的差异须写进稿件**（`sections/empirical.tex` 的 rank 段），
> 因为原主张所依据的 run 正是"整塔微调"（rank 只控制 0.13% 参数），**不能支撑 rank 效应**。
>
> ### 二、✅ 已上传 GitHub（`43b733c3`）—— **严格遵守不建 tag 原则**
>
> | 项 | 值 |
> |---|---|
> | 推送命令 | `git push ssh-origin main`（**仅此**，无任何 tag/release 操作）|
> | 提交 | **`43b733c3`** ｜ 154 added / 3 modified / **0 deleted** |
> | 远端的 `main` | **`43b733c3`** = 本地 HEAD ✅ |
> | **tag 冻结核验** | **`v1.0-prl-revision` 仍指向 `e320e75`**（`refs/tags/v1.0-prl-revision` + `^{}` 两项均未变）✅ **未新增任何 tag** ⇒ **Zenodo 不会铸新 DOI** |
> | 已跟踪文件 | 2,060 → **2,214** |
> | 稿件类文件 | **0** ✅ |
> | ≥100MB 文件 | **0** ✅ |
>
> **本次上传内容**：`src/lora.py`（冻结基座）、`src/trainer.py`（checkpoint 存全量可训练状态）、`src/dataset.py`（collate 保留 `image_path`）；
> `outputs/analysis/` 新增 154 个结果 JSON（含 `coco_scaleup.json`、`rank_rerun.json`、`claim_ledger_paperA.json` 等）；
> `outputs/rank_rerun/`（6 个 rank 的聚合结果 + trainer 结果）+ `outputs/scaleup_coco/`。
>
> **排除内容（按 `AGENTS.md` 发布边界）**：稿件本体（`main*.tex/pdf`）、封面信、title page、highlights；
> 权重/压缩包（`.pt .zip .safetensors` …）；**1,501 个一次性会话脚本 `tools/_p*.py`**（仓库惯例：`tools/` 仅 199 个文件、7 个下划线文件均为 `_cloud_*.sh` 类正式工具）。
>
> ### 三、⚠️ 我的两处失误（如实记录）
>
> | # | 失误 | 处置 |
> |---|---|---|
> | 1 | 误把正式 `rank2` 的 `results.json` 当试跑残留移走 | **已立即恢复**并逐一验证在位（无数据丢失）|
> | 2 | 上传前安全检查**误报** `outputs/analysis/paperhe_highlights.json` 为稿件 highlights | 收紧判据：**只在 `submission/paper*/upload/latex_source` 目录下拦截**，分析产物放行；重跑后 **0 稿件类** |
>
> ### 四、⏳ 剩余
>
> 1. **把 rank 结论写进 Paper A**（`sections/empirical.tex`）—— 撤销"gap 对 rank 单调"，补上实测表；
> 2. `flickr30k` 29 个 run 的同类重跑（ODE 拟合基于它们）；
> 3. Paper A 投稿（建议在 1、2 完成后）。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "已上传 GitHub**（未建 tag" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("已上传 GitHub**（未建 tag", "43b733c3", "196,608 × r/8", "+0.0021",
              "v1.0-prl-revision", "误报"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
