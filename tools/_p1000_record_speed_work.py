# -*- coding: utf-8 -*-
r"""Record the speed investigation on the third host and the one change that was kept.

    python tools/_p1000_record_speed_work.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "加速调查：只保留评测批大小"

ENT = """> **🐌 2026-10-16 09:55 —— 「怎么这么慢」= **显存带宽硬墙**；试了四个加速手段，**只保留一个不改实验的**
>
> 操作者要求：**「能不能加快在不改变全量的情况下」**。
>
> ### 一、📊 实测（同一 25/30 步、同数据、同 seed；这是判断依据，不是推测）
>
> | 配置 | tokens/批 | 秒/步 | **每样本耗时** | tokens/秒 |
> |---|---|---|---|---|
> | **batch 2（原配置）** | 1214 | **0.9–1.0** | **0.500 s** | 1214 |
> | batch 4 | 2444 | 1.9 | 0.475 s | **1286（+6%）** |
> | batch 8 | 4928 | 4.0 | **0.500 s** | 1232（**更差**）|
> | batch 4 + **TF32** | 2444 | 1.9 | 0.475 s | **零收益** |
> | batch 2 + **TF32** | 1214 | 1.0 | 0.500 s | **零收益** |
>
> ### 二、🔍 结论：瓶颈是**每步把 14 GB 的 bf16 权重读两遍**（前向+反向），与 batch 无关
>
> * **加大 batch 只快 ~6%（batch 4），batch 8 反而更慢** ⇒ 不是"GPU 空转"，而是**权重搬运的固定成本**；
> * **TF32 完全无效** ⇒ bf16 权重根本不走 fp32 matmul 路径（我这个尝试**被实测否掉**，如实记录）；
> * **Flash-Attn 未安装**，现场编译在 CUDA 13 上风险高且会增加与论文口径的差异 ⇒ **放弃**；
> * 另有**显卡退化**：第一台 4080 SUPER 跑 0.9 s/步，第二台 4090 D 因为装不下而改用 4-bit 时反而更慢（**产品线不同，4090 D 显存只有 24 GB**）。
>
> ### 三、✅ 唯一保留的改动：`--eval-batch`
>
> 训练配置**一字未改**（batch 2、1500 样本、3 epochs、3 seeds、rank 8）；只把**评测**（`torch.no_grad()` 路径）
> 从"每批 2 对"改成"每批 32 对"：**4.4 分钟 → 约 15 秒**，12 个 run **共省约 50 分钟**，且**不改任何被计算的量**。
>
> ### 四、⚠️ 途中引入并修掉的两个缺陷（自查）
>
> | # | 缺陷 | 现象 | 修法 |
> |---|---|---|---|
> | ① | 加 `--tf32` 时**插坏**了已有的 `if a.deterministic:` 块 | 云端 `IndentationError`，**而本地检查却报 OK**——因为上传与本地改写**竞态** | `tools/_p996` 精确锚定重做；**新增 `tools/_p998`：上传后必须让远端解释器 `ast.parse` 通过才算成功** |
> | ② | 绕过 `__main__` 用 `python -c "exec(open(...).read())"` 做探针 | 会带着 `-c` 的参数解析跑主逻辑 | 改为**给脚本加正规开关**（`--tf32`），不再用 `-c` 注入 |
>
> ### 五、⏱️ 真实工期（基于实测 0.94 s/步）
>
> | 项 | 值 |
> |---|---|
> | 每步 | **0.94 s** |
> | 每 run | **2250 步 ≈ 37.5 分钟**（+重载约 20 s、评测约 15 s）|
> | **12 run** | **≈7.5 小时**（09:45 起 ⇒ **约 17:10 结束**）|
> | 若要显著更快 | **必须改变实验本身**（减数据/减 epoch/缓存冻结视觉塔特征）⇒ **违反操作者"不改全量"要求，未做** |
>
> ### 六、✅ 当前状态
>
> `text_only_s42` **step 600/2250**、loss **0.795**、0.94 s/步、显存 30,782/32,760 MiB、GPU 100%；
> 日志可见（已去除 `tee`）；**frozen ×3 已落盘**。跑完即按 `_p984` 全项校验 → **通过才关机**。
>
> **工具**：`_p993`（`--eval-batch`）｜`_p994`（批大小探针）｜`_p995`/`_p997`（TF32 探针）｜`_p996`（`--tf32`）｜`_p998`（上传+远端语法校验）｜`_p999`（最终全量）｜`_p1000`（本条）。
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
    row = ("38. 🐌 **加速调查：只保留 `--eval-batch`（2026-10-16 09:55）** —— 实测：**batch 2 = 0.9–1.0 s/步（0.500 s/样本、1214 tok/s）**；"
           "batch 4 只快 6%、**batch 8 更慢**、**TF32 零收益**（bf16 不走 fp32 matmul）⇒ 瓶颈是**每步读两遍 14 GB 权重**的固定成本，"
           "**不是 GPU 空转**。唯一保留的改动：评测批 2→32（no_grad 路径，4.4 分钟→15 秒，12 run 省约 50 分钟，**训练配置一字未改**）。"
           "⚠️ 途中插坏 `if a.deterministic:` 块（本地报 OK 而远端竞态拿到坏文件）⇒ 新增 `_p998`：**上传后必须远端 `ast.parse` 通过**。"
           "真实工期 **≈7.5 小时（12 run）**；要更快必须改实验本身，未做。详见 `HANDOFF.md` 顶部 2026-10-16 09:55 条目。\n")
    anchor = "37. ⏸️ **暂缓云端 LLaVA，等更大机器（2026-10-16 00:00）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
