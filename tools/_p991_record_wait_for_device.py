# -*- coding: utf-8 -*-
r"""Record the decision to wait for a bigger device, and freeze the state of the LLaVA work.

Operator decision 2026-10-15 23:58: "那就不跑了，等super有机子了再跑" -- the rented devices tried today cannot
do the bf16 run, so the sweep waits for a larger machine. This records what exists, what is missing, and
exactly what to run when that machine arrives.

    python tools/_p991_record_wait_for_device.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "暂缓云端，等更大机器"

ENT = """> **⏸️ 2026-10-16 00:00 —— 操作者决定**暂缓**云端 LLaVA（等更大的机器）；今日两台租机都装不下 bf16**
>
> 操作者指令：**「那就不跑了，等super有机子了再跑」**。
>
> ### 一、🔍 为什么两台都不行（实测数据，不是推测）
>
> | 主机 | GPU / 显存 | bf16 结果 |
> |---|---|---|
> | 第一台（bjb1:43746）| **RTX 4080 SUPER / 32.8 GB** | ✅ **能跑**：显存峰值 **29.95 GB**、0.9 s/步；跑到 step 650/2250 时**主机失联**（非我关机）|
> | 第二台（bjb2:10925）| **RTX 4090 D / 24 GB（可用 23.5）** | ❌ **装不下**：加载时 `caching_allocator_warmup` 要再预留 **13.15 GB** ⇒ OOM；即使把该预留压到 1.5 GB（新增 `--alloc-warmup-gb`），**24 GB 本身也不够装 7B bf16 + LoRA 激活** |
>
> ⇒ **bf16 需要 ≥32 GB 显存**（第一台的 32.8 GB 是刚刚够）。
> **若要小卡也能跑，只能退回 4-bit**（本地 8.6 GB 都能跑，云端 24 GB 更宽裕），但那与操作者"不要 4bit"的要求冲突 ⇒ **按指令停在这里**。
>
> ### 二、✅ 本地已有的实验数据（都完好，与云主机无关）
>
> | 位置 | 内容 |
> |---|---|
> | `outputs/llava_sites/` | **frozen ×3**（s42/s123/s456）+ 基准跑的 `text_only_s42`（1 epoch）|
> | `outputs/llava_sites_local_baseline/` | 上述整目录副本（**注：内含 4.8 GB 的 `text_only_s42_ckpt.pt`**，可删）|
> | `outputs/llava_parity_local/` | 对照跑：frozen/text_only/**vision_only**（本地 20 对配置）|
> | `outputs/analysis/_p838_llava_full.LOCAL_BASELINE.out` | 全量跑日志（step 160/600、loss 0.8544）|
> | `outputs/analysis/_p952_parity_*.log` | 四次对照日志（含 **deterministic** 与重复性实验）|
> | `cloud_fixture/p3_llava_cloud.zip` | **700 张**精确数据包（103 MB，含 MANIFEST 与本地基线）|
>
> ### 三、✅ 已验证的结论（**与"跑没跑完"无关，这些是已完成的科学结论**）
>
> | 结论 | 证据 |
> |---|---|
> | **本地每步 ~56–63 s（4-bit）**，瓶颈 **100% 在前后向**（batch 准备 0.1 s vs 计算 918 s/10 步）| `_p938`/`_p940` 分项计时 |
> | **padding 只浪费 0.2%** ⇒ 调小 max-len 无用 | 首批 1230 tokens vs 逐条 1228 |
> | **本地不可逐步复现**（同配置两次差 **1.7e-3**），加确定性开关后收敛、但**慢 4.4×** | 三次 5 步对照 |
> | **云端端口正确性成立**：token 几何**逐字节一致**、同确定性配置**指标一致到 4e-4** | 本地 2.9495 vs 云端 2.9491 |
> | **bf16 vs 4-bit**（同样 5 步）：DG* 变化 **−0.911% vs −1.067%** ⇒ 差 **0.15 个百分点** | 云端两次冒烟 |
>
> ### 四、⏭️ 等大机器时的**一键流程**（都已写好并验证）
>
> ```bash
> # 1) 传两个文件到新主机：SUBMISSION/cloud_p3_setup.sh 与 SUBMISSION/_p820_llava_sites.py
> # 2) 在新主机上：
> bash cloud_p3_setup.sh 2000        # 钉版环境 → 全 import 自检 → 服务器端下模型 → 官方标注+按序下 2000 张图
> # 3) 跑全量（bf16，1500 训练/500 评测，3 epochs，3 seeds，4 arms）：
> #    --precision bf16 --coco-root /root/p3/coco_full --samples 1500 --eval-pairs 500 ...
> # 4) 跑完校验（只在全项通过时才关机）：
> python tools/_p984_verify_cloud_results.py --shutdown
> ```
>
> ⚠️ **对 >=32 GB 卡的唯一要求**：`--precision bf16`；若卡只有 24 GB ⇒ 必须 `--precision 4bit`（或把 `--alloc-warmup-gb 1.5` 再配合更小 max-len，但**不建议**——今天已证 24 GB 装不下）。
>
> ### 五、⚠️ 两台租机的现状
>
> | 主机 | 状态 |
> |---|---|
> | bjb1:43746 | **端口不可达**（23:52 起）|
> | bjb2:10925 | **端口不可达**（00:00 起），之前**未执行任何关机命令** |
>
> ⇒ **两台都已不在运行**；若平台仍在计费，请在 AutoDL 控制台确认**实例状态**（"关机"省显存费但系统盘可能仍计费，"释放"才彻底停止）。
> 第二台上**数据仍在数据盘**（2000 张图 + 14 GB 模型 + 环境），若**重开同一实例**（端口会变）可**零重建**继续。
>
> **工具**：`_p985`（一键重建补丁）｜`_p987`/`_p989`（重开实例的恢复脚本）｜`_p988`（warmup 上限）｜`_p990`（停机+状态报告）｜`_p991`（本条）。
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
    row = ("37. ⏸️ **暂缓云端 LLaVA，等更大机器（2026-10-16 00:00）** —— 两台租机实测：**4080 SUPER 32.8 GB 能跑 bf16**"
           "（峰值 29.95 GB、0.9 s/步，跑到 step 650/2250 时主机失联）；**4090 D 24 GB 装不下**（加载期 warmup 需额外 13.15 GB；"
           "新增 `--alloc-warmup-gb` 压到 1.5 GB 后**24 GB 仍不够**）⇒ **bf16 需 ≥32 GB 显存**。按操作者指令**停在这里**。"
           "本地数据完好（frozen ×3、全量日志 step 160/600、四次对照日志、700 张精确包）。**已完成的科学结论**：瓶颈全在前后向、"
           "padding 只浪费 0.2%、本地重复性 1.7e-3（确定性开关慢 4.4×）、**云端端口正确性成立（几何逐字节一致、指标 4e-4）**、"
           "**bf16 vs 4-bit 末端差 0.15 个百分点**。一键流程已备（`SUBMISSION/cloud_p3_setup.sh` + `_p820_llava_sites.py`）。"
           "两台租机**均已不在运行**。详见 `HANDOFF.md` 顶部 2026-10-16 00:00 条目。\n")
    anchor = "36. 🔌 **云主机中途失联（2026-10-15 23:55）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
