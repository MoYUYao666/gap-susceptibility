# -*- coding: utf-8 -*-
r"""Record the two faults found while preparing the cloud port, and the final bundle state.

    python tools/_p960_record_parity_faults.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "对照试跑暴露两个缺陷"

ENT = """> **🧪 2026-10-15 21:50 —— 云端对照准备暴露**两个缺陷**（已修）；包已重新打（含实测容差）**
>
> ### 一、🔴 缺陷 1：`--bench-steps` **只跳出内层循环**，计时/对照跑"跑漏了"
>
> | 项 | 事实 |
> |---|---|
> | 现象 | 操作者问"后台还在跑什么"，查出 **PID 8164 还在跑**：对照试跑本应 25 步就停，实际跑完 `text_only` **又跑进了 `vision_only`**（写了 `vision_only_s42.json`）|
> | 根因 | 20 个训练对 ÷ batch 2 = **每 epoch 只有 10 步**，`step_i` 永远到不了 25；而 `break` 在**内层**循环里 |
> | 代价 | 若不发现，会**逐个 arm × seed 一直跑下去**（计时跑变成长跑）|
> | 修法 | `tools/_p956`：**外层 epoch 循环也判上限**并打印一行原因；实测新参数下 `bench stop after 5 steps` 正常触发 |
>
> ### 二、🔴 缺陷 2：脚本**一个确定性开关都没有** ⇒ 本地自己就不可逐步复现
>
> | 跑次 | step-5 loss | 秒/步 |
> |---|---|---|
> | 第 1 次 | **2.9466** | 63.3 |
> | 第 2 次（同配置）| **2.9449** | 51.3 |
> | 第 3 次（**加确定性开关**）| **2.9496** | **278.9** |
>
> * **离散 1.7e-3**，根因：**未设** `cudnn.deterministic` / `benchmark` / 确定性算法 ⇒ cuDNN 每次**自由选卷积算法** + 4-bit kernel 自身抖动；
> * ⇒ **我原先定的"云端对齐到 1e-3"不成立**，已改为**实测容差 `5e-3`**；
> * ⇒ 开关**代价 4.4×**（63 → 279 s/步）⇒ 已改为**可选 `--deterministic`**（`tools/_p958`），
>   **仅用于小样对照**，**全量跑默认关闭**（否则一个 run 从 14 h 变 60 h）。
>
> ### 三、✅ 云端包最终状态（`cloud_fixture/p3_llava_cloud.zip`，**108.0 MB / 707 条目**）
>
> | 内容 | 说明 |
> |---|---|
> | `tools/_p820_llava_sites.py` | **含 `--coco-root` / `--bench-steps`（已修）/ `--report-every` / `--deterministic`** |
> | `cloud_fixture/` | 700 张图 + 裁剪标注 + `MANIFEST.json` |
> | `MANIFEST.json` | id 顺序 SHA-256、标注 SHA-256、图片数、**容差 5e-3**、**本地基线 loss**、**确定性实测数据** |
> | `SETUP.sh` | 逐版本安装（python 3.12.14 / torch 2.9.1+cu130 / transformers 5.16.1 / peft 0.20.0 / bnb 0.50.2 / accelerate 1.14.0）+ **版本自检** + 服务器端下模型 |
> | `PARITY.sh` | 小样对照，**注释里写明容差来源与 `--deterministic` 选项** |
> | `RUN_FULL.sh` | 全量（400/300/3 epochs/3 seeds/4 arms）|
>
> 自检：`testzip()` 通过、成员与源**逐字节一致**、**包内 manifest 的容差 = 5e-3**、**包内 PARITY.sh 含 `--deterministic`**、**包内 sweep 是带 flag 的版本**。
>
> ### 四、⏳ 等 SSH
>
> 收到后：`nvidia-smi` 报机型 → 上传包 → `bash SETUP.sh` → `bash PARITY.sh` →
> **我把云端逐步 loss 与 `MANIFEST.json → parity_baseline.losses_at_step`（step 5 = 2.9466）对照，容差 5e-3** →
> 给"可开全量"或差异定位（查 id 顺序 → 图片哈希 → 包版本 → model revision）。
>
> ⚠️ 本机 GPU 现已空闲（429 MiB），**无实验在跑**。
>
> **工具**：`_p956`（bench-steps 修复）｜`_p957`/`_p958`（确定性开关→改 flag）｜`_p959`（容差+重打包）｜`_p960`（本条）。
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
    mp = io.open(MAP, encoding="utf-8").read()
    row = ("33. 🧪 **对照试跑暴露两个缺陷（2026-10-15 21:50）** —— ① **`--bench-steps` 只跳出内层循环**，"
           "对照跑跑完 `text_only` 又跑进 `vision_only`（20 对 ÷ batch 2 = 每 epoch 仅 10 步，永远到不了 25）；"
           "已修（外层也判上限）。② 脚本**无任何确定性开关** ⇒ 同配置两次 step-5 loss **2.9466 vs 2.9449（离散 1.7e-3）**，"
           "故**原定 1e-3 容差不成立**，改为**实测 5e-3**；确定性开关**代价 4.4×**（63→279 s/步）⇒ 改为可选 "
           "`--deterministic`，**仅用于小样对照**。云端包已重打（**108 MB/707 条目**，含容差、基线 loss、确定性实测数据、"
           "带 flag 的 sweep 与注明的 PARITY.sh）。**本机 GPU 已空闲，无实验在跑**，等 SSH。详见 `HANDOFF.md` 顶部 2026-10-15 21:50 条目。\n")
    anchor = "32. ☁️ **转云端：一比一数据包+环境包已打好（2026-10-15 21:00）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
