# -*- coding: utf-8 -*-
r"""Record the LLaVA throughput measurement and the added step timing.

Operator question: "怎么卡了" (why is it stuck). Answer, with evidence: it is not stuck. The measurement
underscores how much was invisible before -- the run printed once per epoch, so an 86-minute epoch and a
hang looked the same.

    python tools/_p941_record_llava_timing.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "LLaVA 吞吐实测"

ENT = """> **⏱️ 2026-10-15 16:10 —— LLaVA「卡住了吗」= 没卡，是**慢**；已加每步计时（`--report-every` / `--resume`）**
>
> 操作者问：**「怎么卡了」**。
>
> ### 一、🔍 判定：**没卡，在算**（三类证据）
>
> | 证据 | 实测 | 含义 |
> |---|---|---|
> | GPU 利用率（60 s 窗口，3 s 一次）| **min 99% / max 100% / 均值 100%** | 设备**满载**，不是在等主机 |
> | GPU 显存（同窗口）| 7593→7661 MiB，**抖动 68 MiB**（另一次窗口 200 MiB）| **每步都在重新分配** ⇒ 步骤在完成；死锁的核会**纹丝不动** |
> | 进程 I/O 与内存 | 读 308 MB、写 **2,806 B**、工作集 1.7 GB（32 GB 机器）| **无磁盘颠簸、无换页** |
> | Python 侧 CPU | 20 s 内 **+0.13 s（≈1% 单核）** | 计算**全在 GPU**，主机只在等 |
>
> **⇒ 结论：作业正常，只是慢。**
>
> ### 二、📐 慢到什么程度（从日志时间戳算出）
>
> 命令行实参（从进程读出）：
> `--samples 400 --eval-pairs 300 --epochs 3 --batch 2 --max-len 2048 --seeds 3 --rank 8 --arms frozen,text_only,vision_only,both`
>
> | 量 | 值 |
> |---|---|
> | `text_only_s42` epoch 1 完成时刻 | 日志 mtime **14:28:22**（13:02:42 启动）|
> | epoch 1 墙钟 | **≈85.7 分钟**（200 步，batch 2）|
> | **每步** | **≈25.7 秒** |
> | 一个 run（3 epoch）| **≈4.3 小时** |
> | 队列 | **12 run**（4 arm × 3 seed），已完成 **3**（frozen）|
> | **剩余 9 个 run 预计** | **≈38 小时**（连当前这个共 ≈4.4 天）|
>
> **慢的根因**：`batch 2` + `max-len 2048`。400 训练对 + 300 评测对，每对要过**视觉塔 576 个 patch**
> 加 LLM，batch 2 时 GPU 只有 **7.6 GB / 8.6 GB** 被用、却已 100% 占用 ⇒ **每步把序列算完，但吞吐被 batch 卡死**。
>
> ### 三、✅ 已加（`tools/_p940`，就加在训练循环里）
>
> | 新增 | 作用 |
> |---|---|
> | `--report-every N`（默认 10）| 每 N 步打印：`step i/总步 loss 秒/步 已用分钟 ETA` |
> | `train_progress.json` | 每个心跳**覆写**该文件（步数/损失/秒每步/ETA），**不看日志也能从文件看进度** |
> | **分项计时** | 每 epoch 末打印 **batch 准备 vs 计算**；每 run 打印**评测耗时**——直接指出该优化哪一段 |
> | **每 epoch 存档 `*_ckpt.pt`** + `--resume` | 中断**可续跑**，不再整跑重来 |
>
> ⚠️ **当前这跑（PID 40300）加载的是旧脚本内存镜像，改文件不影响它**：想要**逐秒可见**就得重启；
> 它已跑 3 小时 25 分（含 epoch 1 的 86 分钟）。
>
> ### 四、⏳ 待操作者决定（三个选项）
>
> | 选项 | 效果 | 代价 |
> |---|---|---|
> | **A. 不动**，让当前跑完 + 后续按原参数 | 结果与论文口径**完全一致** | **≈38 小时** |
> | **B. 原地重启**（仅启用新计时）| 立刻**能看到每步 ETA** | 丢掉当前 3.4 小时进度 |
> | **C. 重启并调参**（`--batch 8`、`--max-len 1024`）| 预计 **4–6× 加速 ⇒ 8–10 小时** | **改了两项超参**（batch、max_len），论文/补充材料里**必须写明**；`--max-len 1024` 对 caption（约 14 token）**无信息损失** |
>
> **⇒ 未擅自重启或改参**；等操作者选。
>
> **工具**：`_p938`（存活采样）｜`_p939`（从日志算 ETA）｜`_p940`（加计时，已应用）｜`_p941`（本条落账）。
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
    row = ("27. ⏱️ **LLaVA「卡住了吗」= 没卡（2026-10-15 16:10）** —— 实测 GPU **99–100%**、显存**抖动 68–200 MiB**、"
           "写盘仅 2.8 KB、Python CPU 1% ⇒ **在算，只是慢**。每步 **≈25.7 s**（batch 2 + max-len 2048），"
           "一个 run **≈4.3 h**，**剩余 9 run ≈38 h**。已给 `_p820` 加 `--report-every`（每步心跳+ETA）、"
           "`train_progress.json`、**batch/计算分项计时**、每 epoch `*_ckpt.pt` + `--resume`。"
           "⚠️ 当前进程用的是旧脚本内存镜像，**要逐秒可见须重启**；**未擅自重启或改参**，待操作者选 A/B/C。"
           "详见 `HANDOFF.md` 顶部 2026-10-15 16:10 条目。\n")
    anchor = "26. 🗜️ **P3 LaTeX 源码包已重建（2026-10-15 15:00）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
