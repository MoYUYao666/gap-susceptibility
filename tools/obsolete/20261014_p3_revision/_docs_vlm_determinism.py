# -*- coding: utf-8 -*-
r"""落账：解码器 VLM 的可复现性排查（**4-bit 非确定**）+ bf16 多种子研究启动（2026-10-10）。

    python tools\_docs_vlm_determinism.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🧪 2026-10-10 —— 解码器 VLM 补 seed 时查出**训练管线不可复现**（4-bit），改 bf16 重跑**
>
> ### 一、事情的起因
>
> 操作者要补 C3 缺口（解码器 VLM **单模型、单 seed**）。跑之前我按惯例先做**复跑校验**
> （用 `--seed 42` 重跑，与归档逐值比对），**结果不一致**：
>
> | 臂 | 归档（10-08 21:19） | 复跑 | |
> |---|---|---|---|
> | `vision_only` | `cg_span = 0.305599` | `0.341650` | ❌ |
> | `text_only` | `cg_span = 0.277818` | `0.228144` | ❌（且归档是 bf16，复跑是 4-bit） |
>
> ### 二、**根因一：seed 在数据打乱之后才设**（脚本缺陷，已修）
>
> ```
> line 192| loader, _, _ = create_dataloaders(...)   ← shuffle=True 在此消费全局 RNG
> line 195| batches = list(loader)                  ← 批顺序就此固定
> line 200| torch.manual_seed(seed)                 ← seed 在这之后才设！
> ```
>
> **→ 批次打乱由进程初始 RNG 决定，与 `seed` 无关** → 跨 `python` 调用不可复现。
>
> **已修**（`tools/_p152_fix_determinism.py`）：把 `torch.manual_seed(seed)` 提到
> `create_dataloaders` **之前**，并去掉循环内的重复 seed。
> **修后第 1 epoch 的 loss 几乎相同**（1.38557 vs 1.38499）→ **证实批顺序已固定**。
>
> ### 三、**根因二（修完仍不可复现）：4-bit 量化非确定**
>
> 修完 seed 顺序后，同 seed 42 跑两次**仍不同**（`cg_span` 0.3041 vs 0.4073）。
> **逐精度实测**（`tools/_p155_determinism_source.py`，同 seed 42、同配置、两次独立进程）：
>
> | 精度 | 第 A 次 | 第 B 次 | 可逐位复现 |
> |---|---|---|---|
> | **bf16** | `cg_span = 0.110064`，`cg = [0.19617, 0.10458, 0.08610]` | **完全相同** | ✅ **是** |
> | **4-bit** | 0.3041 | 0.4073 | ❌ **否** |
>
> **→ 非确定性来自 `bitsandbytes` 的 NF4 路径**（已知问题），**bf16 路径确定**。
>
> ### 四、附带查出：**4-bit 与 bf16 的量级差很大**
>
> | 精度 | `cg_span` 量级 |
> |---|---|
> | bf16 | **0.11 – 0.58** |
> | 4-bit | **0.28 – 0.41** |
>
> ⚠️ **而归档的三臂精度本来就不齐**：`both`/`vision_only` 是 **4-bit**，
> **`text_only` 是 bf16**（`4bit=False`）——**此前没人注意到**。
> **这正是 C5（4-bit vs bf16 差异未量化）的实质**。
>
> ### 五、处置：改 bf16 跑多种子（**可复现**）
>
> | 项 | 值 |
> |---|---|
> | 配置 | `--maxsamples 400 --epochs 3 --batch 2`（**无 `--4bit`**） |
> | seed | **42 / 123 / 456 × 3 臂 = 9 run** |
> | 输出 | `outputs/vlm_seeds_bf16/` |
> | 驱动 | `tools/_p156_vlm_bf16_seeds.py`（幂等、逐 run 记时间） |
> | 可行性 | ✅ 三臂**均已实测跑通**（bf16 batch 2 不 OOM） |
> | 单 run 耗时 | `text_only` **204 s** ｜ `vision_only` **937 s** ｜ `both` **485 s** |
> | 预计 | **9 run ≈ 1.7 h**（13:10 启动 → 约 **14:45** 完成） |
>
> ### 六、顺带给脚本加的两个参数（都可复核）
>
> | 参数 | 为什么 |
> |---|---|
> | `--seed` | 原脚本**硬编码 `torch.manual_seed(42)`** 与输出名 `{arm}_seed42.json` → 不加会覆盖归档 |
> | `--outdir` | 输出目录也硬编码 → 新 run 会与归档混写 |
>
> **备份**：`tools/_p47_qwen_train.py.bak_noseed`
> **冒烟验证**：`--seed 999 --outdir outputs/_smoke_seed` → 产出 `text_only_seed999.json` ✅
>
> ### 七、要写进论文的（跑完后）
>
> | # | 内容 |
> |---|---|
> | 1 | 三臂 **mean ± sd**（bf16，3 seed）+ 排序是否显著 |
> | 2 | **"训练管线在 4-bit 下不可逐位复现；bf16 下确定"** → **limitation**（这是可复现性问题，必须披露） |
> | 3 | **4-bit 与 bf16 的量级差异** → 量化 C5 |
> | 4 | 澄清：归档三臂**精度不齐**，论文表用哪一套要说清 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "训练管线不可复现" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("训练管线不可复现", "0.110064", "0.3041", "0.4073",
              "seed 在数据打乱之后才设", "bitsandbytes", "1.7 h"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
