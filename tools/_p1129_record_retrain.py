# -*- coding: utf-8 -*-
r"""Record the retrain launch and the four defects found on the way, so nobody repeats them.

    python tools/_p1129_record_retrain.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "重训已启动（规范度量）"

ENT = """> **🚀 2026-10-17 10:40 —— 操作者选 A：**重训 12 run 已在跑**（规范度量 + 真权重）；途中又修掉 4 个缺陷**
>
> ### 一、✅ 已启动（实测状态）
>
> | 项 | 值 |
> |---|---|
> | 配置 | **1500 训练 / 500 评测**、3 epochs、rank 8、**bf16**、3 seeds、4 arms |
> | `steps_total` | **2250** ✅（此前错的 750 已修）|
> | frozen ×3 | **已完成**：`canonical DG\\* 0.8146 → 0.8199 (+0.650%)`、`legacy −0.517%` |
> | 当前 | `text_only_s42` step 125/2250、**1.07 s/步**、ETA ~11:20 |
> | 显存 | **30,204 MiB / 100%** |
> | 预计总时长 | 9 个训练 run × ~40 分钟 ⇒ **约 6 小时（~17:00）** |
>
> ### 二、🔧 为跑通这条链，又修掉 4 个缺陷（全部是我的）
>
> | # | 缺陷 | 现象 | 修法 |
> |---|---|---|---|
> | ① | **测量用了 `output_hidden_states=True`** | 在 transformers 5.x 下开销远超预期：**29.81 GiB 已分配** ⇒ 每个 arm 都 OOM（连 `--eval-batch 8` 也炸）| 改为在 **`lm_head` 上注册 `forward_pre_hook`** 抓末层隐状态（只付一个张量的代价）→ `_p1128` |
> | ② | **评测批 32 太大** | 29 层 × 32 样本 × 596 token × 4096 维 ≈ 4.5 GB 仅隐状态 | 启动器改 `--eval-batch 8` → `_p1127` |
> | ③ | **只有 500 张图**（原只下了保留集）| `ids` 仅 500 ⇒ `train_ids=500`（应 1500）、**`eval_ids` 为空** ⇒ measure 返回 None ⇒ 打印 TypeError | 补齐 **2000 张图** → `_p1125` |
> | ④ | **打印不容忍 None** | 空评测集时一个 arm 直接崩（守卫接住了，但没产出记录）| `_fmt()` 容忍 None 并告警"未测到任何对" → `_p1126` |
> | ⑤ | 缺 `--model` 参数 | 镜像下来的权重没有 `refs/main`，`HF_HUB_OFFLINE` 下按 repo 名加载会失败 | 补 `--model` 路径覆盖（只覆盖路径，不动提示词）→ `_p1122` |
>
> ### 三、✅ 冒烟与验证（在 8 小时前做的，全部通过）
>
> | 检查 | 结果 |
> |---|---|
> | 权重非空 | **`448 tensors`（240 MB）**，确实是 `...q_proj.lora_A.default.weight (8,4096)` |
> | 规范值 | `DG\\* 0.8095 → 0.8369 (+3.377%)`、`CG 0.8918`、`DG_emp 0.9001` |
> | 记录字段 | **10/10**（含 `dg_star_before/after/rel_change`、`cg_canonical_*`、`dg_empirical_*`）|
> | 规范值 ≠ 旧值 | ✅（证明是两个独立量）|
> | 静态检查 | `tools/_p1120_static_check.py` **11/11 PASS** |
> | 500 对真实评测 | `n_eval 500`、无 OOM（`_p1127`+`_p1128` 之后）|
>
> ### 四、📌 一处**必须记住的口径细节**
>
> `before` 在 **100 对**上测、`after` 在 **500 对**上测 ⇒ **frozen 的 "相对变化" 不是 0**（本次 +0.650%，归档那次 +0.297%）。
> 这是**抽样差异**、不是训练效应；四臂都与**同一 frozen 基线**比较，所以 arm 间比较仍然成立，但**不要**把 frozen 的 rel 当作噪声下界。
>
> ### 五、⏭️ 跑完后要做
>
> 1. `_p984` 式全项校验（记录齐全、尺度正确、frozen 三 seed 一致、无 traceback/OOM）；
> 2. 取回 12 条记录 + 7 个**真**适配器；
> 3. 把规范值过 `_claim_ledger.py`（要新加条目），再决定 Paper A 补充 F 节是否改写；
> 4. 若 text_only 的规范值与 frozen 有可分辨差异 ⇒ **就能回答"text-only 到底动不动"**。
>
> **工具**：`_p1124`（重训启动器）｜`_p1125`（补图）｜`_p1126`（打印容错）｜`_p1127`（降评测批）｜`_p1128`（hook 抓隐状态）｜`_p1129`（本条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    mp = io.open(REPO / "文件地图.md", encoding="utf-8").read()
    row = ("47. 🚀 **重训 12 run 已启动（规范度量 + 真权重，2026-10-17 10:40）** —— 操作者选 A。`steps_total` **2250** 已正确；"
           "**frozen ×3 已完成**（`canonical DG* 0.8146→0.8199 (+0.650%)`、legacy −0.517%）；`text_only_s42` 跑在 1.07 s/步，"
           "**预计 ~6 小时（~17:00）**。为跑通又修 5 处（全是我自己的）：**① `output_hidden_states=True` 在 transformers 5.x 下"
           "分配 29.81 GiB ⇒ 全臂 OOM**，改为 **`lm_head` forward_pre_hook 抓末层**（`_p1128`）② 评测批 32→8（`_p1127`）"
           "③ 只有 500 张图导致 `eval_ids` 为空、train 只有 500 ⇒ 补齐 2000 张（`_p1125`）④ 打印不容忍 None（`_p1126`）"
           "⑤ 补 `--model` 路径覆盖（`_p1122`）。冒烟验证：**权重 448 tensors/240 MB 非空**、规范值与记录字段 10/10、"
           "静态检查 11/11。⚠️ **口径**：`before` 用 100 对、`after` 用 500 对 ⇒ **frozen 的 rel≠0 是抽样差异**（本次 +0.650%）。"
           "详见 `HANDOFF.md` 顶部 10:40 条目。\n")
    anchor = "46. 🔴 **适配器为空 ⇒ arm 级规范度量必须重训"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
