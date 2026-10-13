# -*- coding: utf-8 -*-
r"""落账：过夜串行队列 + 下载渠道问题（2026-10-07 夜）。

    python tools\_docs_overnight.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def sh(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=25).stdout.strip()
    except Exception:
        return "(失败)"


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    gpu = sh(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader"])
    ep = 0
    lg = REPO / "outputs/theory/alpha_from_gradients/run_both.log"
    if lg.exists():
        ep = len([l for l in io.open(lg, encoding="utf-8", errors="ignore") if " DG*=" in l])

    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    ent = f"""> **🌙 2026-10-07 深夜 —— 过夜串行队列已启动（操作者选 A）**
>
> ### 🔴 下载渠道问题（实测）
>
> | 渠道 | 结果 |
> |---|---|
> | `hf-mirror.com` | ❌ **超时** |
> | `huggingface.co` | ❌ **超时** |
> | **`www.modelscope.cn`** | ✅ **HTTP 200** |
> | `modelscope` Python 包 | ⏳ **安装中**（pip 后台） |
>
> → **CLIP B/16 的下载被网络卡住**。已改用 ModelScope（`tools/_p4_download_clip_b16_ms.py`，
> 四个候选源逐个试 + **下载后强制校验 `patch_size==16`**）。
>
> ### ✅ 替代路径：**OpenCLIP 已验证可跑同一协议**
>
> 冒烟测试（`--model models/openclip --rank 4 --smoke`）**通过**：
> `text_only seed=42 cg 0.7029 → 0.7089  R@1=0.8039  **vis_nonzero=0**`（正是严格冻结的标志）。
> → **OpenCLIP 可把 patch-32 组从 2 个骨干加到 3 个**（加固现有规律，但**不是**核心的 patch-16 检验）。
>
> ### 🌙 过夜队列（`tools/_p7_overnight_driver.py`，已在后台）
>
> | 序 | 实验 | 前提 | 超时上限 |
> |---|---|---|---|
> | 1 | **α 预测（both 臂）** | 运行中（{ep}/30 epoch） | 3 h |
> | 2 | **③a OpenCLIP B/32 × rank4（三臂）** | GPU 空闲 | 3 h |
> | 3 | **③b CLIP B/16 × rank4（三臂）** | 模型就位 | 模型 30 min ｜ 跑 3 h |
> | 4 | **④ Qwen2-VL 三臂** | 脚本就绪 | 5 h |
>
> **驱动设计**：**只等 JSON 落盘**（不靠 sleep 猜时间）；每步独立超时；全部动作追加写
> `outputs/_overnight_driver.log`，便于次日核查。
>
> ### 当前 GPU
>
> `{gpu}`（α 实验独占，**8 GB 只能跑一个**）
>
> ### 次日待办
>
> 1. 读 `outputs/_overnight_driver.log` 核对每一步；
> 2. 若 ③b 因下载失败跳过 → **改由操作者提供 B/16** 或接受"patch-16 组仍为 2 个"并在论文保留现有措辞；
> 3. 汇总 α 的"预测 vs 拟合"结果 → 决定是否写入 `validation.tex`；
> 4. ④ 若跑成 → 回应 discussion 自认的"decoder-based VLMs remains open"。
"""
    if "过夜串行队列已启动" not in h:
        anchor = "> **📊 2026-10-07 夜 —— 六项实验状态总览（实测）**"
        i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ent + "\n" + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("过夜串行队列已启动", "hf-mirror.com", "modelscope", "vis_nonzero=0", "_overnight_driver.log"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
