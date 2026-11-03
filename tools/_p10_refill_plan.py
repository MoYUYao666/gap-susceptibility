# -*- coding: utf-8 -*-
r"""重跑计划：把此前**因无来源而删掉/未做**的数据补上（2026-10-07）。

## 操作者指示

> **"可以把没有的补上，重跑"**

**这是对唯一原则的正确执行**：删掉是因为"没有来源"，**重跑就能有来源** → 数据回到论文里，
而且这次**可复现**。

## 三项要补的

| # | 缺什么 | 归档现状 | 需补 | 成本估算 |
|---|---|---|---|---|
| **A** | **COCO 逐配置 ODE 表**（原 15 行，删剩 3 行） | 3 配置 × 3 seed | **12 配置 × 3 seed**（r∈{1,2,4,16,32,64} × {text,both}） | 36 run × ~25 min ≈ **15 h** |
| **B** | **α 预测实验**（因 `max_samples=2000` 无效） | 无效 | 用 **`max_samples=5000`**（与归档同口径）重跑 | 3 seed × 10 ep ≈ **2–3 h** |
| **C** | **④ Qwen2-VL 解码器对照**（唯一 script 缺口） | 无 | 写脚本 + 三臂跑 | **3–4 h** |

## 队列（**GPU 串行**，8 GB 只能一个）

1. ③b CLIP B/16 —— **运行中**
2. **B α 重跑（5000 样本）** ← **优先**（解决"最致命"的那条）
3. **A COCO 逐配置重跑**（补回被删的表）
4. **C Qwen2-VL**（写脚本后跑）

## 为什么 B 优先于 A

- **B 解决的是论文中心论断的可信度**（ODE 系数能否由梯度预测）；
- **A 补的是一张附表**（COCO 跨数据集稳健性）——重要，但不是中心论断。

    python tools\_p10_refill_plan.py [--apply]
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# A：COCO 逐配置（14 配置，与论文原表一致）
COCO_RANKS = [1, 2, 4, 8, 16, 32, 64]
COCO_SITES = ["text_only", "both"]


def main() -> int:
    apply = "--apply" in sys.argv
    n_coco = len(COCO_RANKS) * len(COCO_SITES)
    print("=== 重跑计划 ===")
    print(f"  A. COCO 逐配置：{n_coco} 配置 × 3 seed = {n_coco*3} run"
          f"（r∈{COCO_RANKS} × {COCO_SITES}）")
    print(f"     └ 成本 ≈ {n_coco*3*25/60:.0f} h（按 25 min/run）")
    print("  B. α 重跑：3 seed × 10 epoch，max_samples=5000 ≈ 2–3 h")
    print("  C. Qwen2-VL 三臂：需先写脚本 ≈ 3–4 h")
    print()
    gpu = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu",
                          "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
    print(f"  当前 GPU: {gpu}")

    if not apply:
        print("\n  （预演）")
        return 0

    # 生成 A 的命令清单（供逐条执行/队列使用）
    cmds = []
    for site in COCO_SITES:
        for rk in COCO_RANKS:
            tag = f"coco_{site}_r{rk}"
            cmds.append(
                f'python experiments/strict_freeze_control.py '
                f'--out-dir outputs/coco_sweep/r{rk} --name {tag}_ '
                f'--rank {rk} --alpha-mult 2 --tags {site} '
                f'--seeds 42 123 456 --epochs 10 --max-samples 5000 '
                f'--batch-size 128 --skip-frozen --dataset coco')
    out = REPO / "outputs" / "analysis" / "refill_commands.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    io.open(out, "w", encoding="utf-8", newline="").write("\n".join(cmds) + "\n")
    print(f"\n  ✅ A 的 {len(cmds)} 条命令已写 {out.relative_to(REPO)}")
    print("     ⚠️ 注意：strict_freeze_control.py 当前是否支持 --dataset？需先核对（下一步）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
