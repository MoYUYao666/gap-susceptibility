# -*- coding: utf-8 -*-
r"""Record the move to cloud execution: fixture, bundle, pinned environment, parity plan.

Operator instruction 2026-10-15: stop running on the local machine, run it in the cloud, keep the local
results as a reference to check the cloud against, reproduce the local environment one-to-one, and try a
small run first to confirm the port is correct.

    python tools/_p954_record_cloud_move.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "转云端已完成本地一比一打包"

ENT = """> **☁️ 2026-10-15 21:00 —— 转云端：本地跑已停、**一比一环境+数据包**已打好、本地对照试跑已完成**
>
> 操作者指令：**「跑云端，本地数据保留与云端对比确认云端是否正确，按本地环境一比一还原，并先试跑一点确认」**。
>
> ### 一、✅ 本地跑已停（保留为**基准**）
>
> | 项 | 处理 |
> |---|---|
> | 全量跑（PID 16676）| **20:45 停止**，进度止于 `text_only_s42` **step 160/600**、loss **0.8544** |
> | 已产出的记录 | **原样保留**：`outputs/llava_sites/{frozen_s42,frozen_s123,frozen_s456}.json` |
> | 备份 | `outputs/llava_sites_local_baseline/`（整目录副本）+ `_p838_llava_full.LOCAL_BASELINE.out`（日志副本）|
> | 清理 | 删掉 4.8 GB 的 `text_only_s42_ckpt.pt`（基准记录本身不受影响）|
>
> ⚠️ 磁盘上那条 `text_only_s42.json` 是**基准跑（--epochs 1）**留下的、`train_seconds=1064.6`，
> **不是**全量跑的结果；云端比对时以 `frozen_*` 与 `train_progress.json` 为准。
>
> ### 二、🔍 「一比一」的两个真正难点（都不是装包）
>
> | 难点 | 事实 | 处理 |
> |---|---|---|
> | **数据子集由标注文件的顺序决定** | 脚本 `ids = [i for i in by_img if ...]`，即 **caption 文件的迭代顺序**决定"前 400 张是哪 400 张"| 云端**不能重新下载 COCO**（会取到不同子集却看不出差别）⇒ 打**精确数据包** |
> | **环境很新，不能"装最新"** | 本地 **python 3.12.14 / torch 2.9.1+cu130 / transformers 5.16.1 / peft 0.20.0 / bitsandbytes 0.50.2 / accelerate 1.14.0** | `SETUP.sh` **逐版本钉死**并**自检版本** |
>
> ### 三、✅ 数据包（`cloud_fixture/`，700 张 = 400 训练 + 300 评测）
>
> | 项 | 值 |
> |---|---|
> | 图片 | **700 张**，**103.9 MB**（本地 40,504 张里**只用前 700 个 id**）|
> | 标注 | **裁剪过的** `captions_val2014.json`：只留这 700 张的 **3,505** 条 caption，**保持原顺序** |
> | `MANIFEST.json` | **id 顺序前 20 个 + id 序列 SHA-256** + 标注文件 SHA-256 + 图片总字节 + **本地对照基线值** |
> | 首 5 个 id | `[203564, 179765, 322141, 16977, 106140]` |
>
> ### 四、✅ 上传包 `cloud_fixture/p3_llava_cloud.zip`（**108 MB / 707 条目**）
>
> ```
> tools/_p820_llava_sites.py     带 --coco-root / --bench-steps / --report-every 的扫描脚本
> cloud_fixture/…                 700 张图 + 裁剪标注 + MANIFEST.json
> SETUP.sh                       逐版本安装 + 版本自检 + 服务器端下载模型（遵守"模型只在服务器下"规则）
> PARITY.sh                      小样试跑（20 训练对/10 评测对/25 步）
> RUN_FULL.sh                    全量（400/300/3 epochs/3 seeds/4 arms）
> ```
> 自检：`testzip()` 通过、**每个成员与源文件逐字节一致**（SHA-256 逐个比对）。
>
> ### 五、✅ 先试跑：云端跑 `PARITY.sh`，与本地对照
>
> 本地已用**完全相同命令**跑出基线（`outputs/llava_parity_local/`、`_p952_parity_local.log`）：
> **20 训练对 / 10 评测对 / 25 步 / 同 seed / 同 batch 2 / max-len 2048**。
> **首条心跳实测：`batch tokens: 1220 mean 610`**（与全量跑的 1230/615 同一量级，符合 data subset 一致）。
> **判定标准：云端逐步 loss 与本地基线一致到约 `1e-3`**；若不一致 ⇒ **停在试跑**，先查
> ① id 顺序 SHA-256 ② 图片数量/哈希 ③ 各包版本 ④ 是否用了同一 model revision。
>
> ### 六、⏭️ 待操作者
>
> 1. **拿到云主机（GPU 建议 ≥16 GB 显存，可上 bf16 免 4-bit 反而更快；但如需与本地严格同口径就仍用 4-bit）**；
> 2. 上传 `cloud_fixture/p3_llava_cloud.zip`，解压后 `bash SETUP.sh` → `bash PARITY.sh`；
> 3. **把 `parity_cloud.log` 发我**，我做逐步 loss 对照并给"可以开全量"的结论或差异定位。
>
> **工具**：`_p951`（`--coco-root`）｜`_p952`（数据包+MANIFEST）｜`_p953`（云端 zip + SETUP/PARITY/RUN_FULL）｜`_p954`（本条）。
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
    row = ("32. ☁️ **转云端：一比一数据包+环境包已打好（2026-10-15 21:00）** —— 本地全量跑 20:45 停（`text_only_s42` step 160/600），"
           "记录**保留为基准**（`outputs/llava_sites_local_baseline/`）。两个真难点：**数据子集由 caption 文件迭代顺序决定** ⇒ "
           "**不能重新下载 COCO**；**环境很新**（torch 2.9.1+cu130 / transformers 5.16.1 / peft 0.20.0 / bnb 0.50.2）⇒ 版本**钉死+自检**。"
           "数据包 `cloud_fixture/`：**700 张（400+300）/ 103.9 MB** + 裁剪标注（3,505 caption，保原序）+ `MANIFEST.json`（id 顺序与 SHA-256）。"
           "上传包 `cloud_fixture/p3_llava_cloud.zip`（**108 MB / 707 条目**，逐字节校验）含 **SETUP.sh / PARITY.sh / RUN_FULL.sh**。"
           "**先试跑**：本地基线已跑（20 训练对/10 评测对/25 步，首条 `batch tokens 1220 mean 610`），云端跑 `PARITY.sh` 后**逐步 loss 对齐到约 1e-3** 才算还原成功。"
           "详见 `HANDOFF.md` 顶部 2026-10-15 21:00 条目。\n")
    anchor = "31. 📧 **EM 的 Send E-mail 不能带附件"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
