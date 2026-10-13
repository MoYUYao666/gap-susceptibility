# -*- coding: utf-8 -*-
r"""落账：过夜队列的两处故障与修复（2026-10-07 23:00）。

    python tools\_docs_overnight_fixes.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔧 2026-10-07 23:00 —— 过夜队列的两处故障与修复（实测）**
>
> ### ① 下载渠道：**HF 双源全超时，ModelScope 可用**
>
> | 渠道 | 实测 |
> |---|---|
> | `hf-mirror.com` | ❌ 超时 |
> | `huggingface.co` | ❌ 超时 |
> | **`www.modelscope.cn`** | ✅ **HTTP 200** |
>
> 装 `modelscope`（1.40.1）后改用 ModelScope 下载 CLIP B/16。
>
> **⚠️ 踩坑 1**：ModelScope 的**默认** `snapshot_download` 会拉 **`flax_model.msgpack`（570 MB，JAX 权重，
> 对 `transformers.CLIPModel` 完全无用）**——已加 `ignore_file_pattern` 排除 flax/tf。
>
> **⚠️ 踩坑 2**：**下载中断会留 `pytorch_model.bin.incomplete`**（实测 360 MB / 599 MB），
> 而我的脚本按"目录非空即跳过"→ **误判为已完成**。已改为**校验 `patch_size == 16` 才算成功**，
> 失败则续传/重试。真实权重为 `pytorch_model.bin`（599 MB），**实测速率约 11 MB/s**。
>
> ### ② 我自己的操作事故：**误杀过夜驱动**
>
> 为停掉卡住的下载，我用 `Get-Process python | Stop-Process` 按「**CPU 低 + 启动 <5 min**」筛进程
> —— **把刚启动的过夜驱动一起杀了**（job `pwsh-128` exit 1）。
>
> **教训**：**按 CPU/启动时间筛进程不可靠**；应**按命令行内容精确匹配**再停。
> **已确认 α 实验未受影响**（PID 39676 持续在跑）。
>
> ### 当前实测
>
> - **α 实验**：11/30 epoch，约 2.5 min/epoch → **预计 00:00 前后完成**
> - **GPU**：7730 MiB / 8188 MiB（α 独占，**8 GB 只能跑一个**）
> - **B/16 下载**：清理残件后重下中
>
> ### 待办
>
> 1. B/16 下载完成（校验 patch_size=16）→ **重启过夜驱动**
>    （队列：③a OpenCLIP B/32 → ③b CLIP B/16 → ④ Qwen2-VL）；
> 2. 次日读 `outputs/_overnight_driver.log` 逐步核对。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "过夜队列的两处故障与修复" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("flax_model.msgpack", "误杀过夜驱动", "patch_size == 16", "11/30 epoch"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
