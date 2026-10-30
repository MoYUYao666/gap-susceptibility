# -*- coding: utf-8 -*-
r"""诊断 `vision_only` 为何远慢于 `text_only`（2026-10-08 21:10）。

## 观察

| 臂 | 可训张量 | 5 epoch 用时 |
|---|---|---|
| `text_only` | 392（语言侧） | **722 s（12 min）** |
| `vision_only` | 258（视觉侧） | **>22 min 且第一 epoch 未完成** |

**差异只应在可训张量上（258 vs 392，视觉侧更少）** → 视觉侧**不该更慢**。

## 可能的解释

1. **视觉塔的 LoRA 落在 `attn.qkv`（3840×1280）等大矩阵上** →
   每步反传的**激活量远大于语言侧**（语言侧是 1536 维的 7 个小投影）；
2. `attention_mask` 维度不同导致视觉 token 更多；
3. GPU 显存吃紧 → 交换/重试。

## 本脚本（不占 GPU 训练）

读日志时间戳与 GPU 状态，并检查**视觉塔参数形状**以量化解释 1。

    python tools\_p48_diag_vision_slow.py
"""
from __future__ import annotations

import io
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    log = REPO / "outputs" / "_qwen_vision.log"
    print("=== 日志状态 ===")
    if log.exists():
        st = log.stat()
        print(f"  大小 {st.st_size} B ｜ 创建 "
              f"{datetime.fromtimestamp(st.st_ctime):%H:%M:%S} ｜ 最后写入 "
              f"{datetime.fromtimestamp(st.st_mtime):%H:%M:%S}")
        age = (datetime.now() - datetime.fromtimestamp(st.st_ctime)).total_seconds() / 60
        print(f"  已运行 {age:.1f} min")
        t = io.open(log, encoding="utf-8", errors="ignore").read()
        print(f"  含 '已写': {'已写' in t} ｜ 含 'ep 1': {'ep  1' in t or 'ep 1' in t}")
        print(f"  含错误: {[k for k in ('Error','Traceback','Accelerator') if k in t]}")
    else:
        print("  日志不存在")

    print("\n=== GPU ===")
    r = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu",
                        "--format=csv,noheader"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print("  " + (r.stdout or "").strip())

    print("\n=== 视觉塔 vs 语言塔的 LoRA 目标形状（量化解释 1）===")
    print("  视觉塔（Qwen2-VL-2B, patch16, hidden 1280）:")
    print("    attn.qkv : (3840, 1280)  → LoRA A(8,1280) B(3840,8)")
    print("    attn.proj: (1280, 1280)")
    print("    mlp.fc1  : (5120, 1280)")
    print("    mlp.fc2  : (1280, 5120)")
    print("  语言塔（hidden 1536）:")
    print("    q/k/v/o_proj, gate/up/down_proj : (1536, 1536) 或 (8960, 1536)")
    print()
    print("  → 视觉塔 32 块 × (qkv + proj + fc1 + fc2) = 128 个线性层")
    print("    语言塔 28 层 × 7 = 196 个线性层")
    print("  → **层数相当**，但视觉侧的反传要**经整条视觉塔回到投影层**，")
    print("     而语言侧只反传到各层自身的 LoRA —— **计算图路径长度不同**。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
