# -*- coding: utf-8 -*-
r"""落账：**批次污染查出** + 9-seed VLM 完成 + 批次修正队列启动（2026-10-10 晚）。

    python tools\_docs_batchfix.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴🔴 2026-10-10 晚 —— 查出**批次大小污染**（19 个 run 用了 batch 64）；9-seed VLM 完成；启动修正队列**
>
> ### 一、🔴 严重发现：批次大小在组内/跨臂不一致
>
> 操作者要求把 1–3 seed 的实验提到 5 seed。**我在补 seed 前按惯例核对配置，查出**：
>
> | 组 ／ 臂 | seed 42 | seed 123 | seed 456 | 判定 |
> |---|---|---|---|---|
> | `strict_freeze_b32_r4` 三臂 | 128 | 128 | 128 | ✅ |
> | **`strict_freeze_oclip/r4` 三臂** | **128** | **64** | **64** | 🔴 同臂混批次 |
> | **`strict_freeze_b16/r4` both** | 128 | 128 | **64** | 🔴 |
> | **`strict_freeze_b16/r4` vision_only** | 128 | 128 | **64** | 🔴 |
> | `coco_sweep`（both/text_only，**论文对照**） | 128 | 128 | 128 | ✅ |
> | **`coco_sweep_text_only`（本会话补的）** | **64** | **64** | **64** | 🔴 **跨臂不同批次** |
>
> **精确范围**（`tools/_p168_batchfix_plan.py`）：**19 个 run 的 `batch_size != 128`**
> （另 50 个已是 128）。明细存 `outputs/analysis/batchfix_plan.json`。
>
> ### 二、后果
>
> 1. **本会话报的"数据集翻转"结论被批次混淆**：论文对照 `both` 是 **128**，我补的 `text_only` 是 **64**
>    → 那张表的 `text_only` 数字（$-0.0488/-0.0944/-0.1315/-0.1396$）**与 `both` 不可直接比**；
> 2. **`oclip` 的效应量（本会话算的 $0.52/0.55$ sd）也不干净**：seed 42 = 128，123/456 = 64；
> 3. `b16` 的 `both`/`vision_only` 均值同样混了两个批次。
>
> **成因**：`--batch-size 64` 是本会话在**共享显存紧张**时段定的，但旧 run 的 128 先存在 → 同目录混两套。
>
> ### 三、操作者决定：**A + 统一 128**（先让 VLM 跑完，再修批次）
>
> **修正队列**（`tools/_p169_batchfix_queue.py`，**46 run**，串行）：
>
> | 阶段 | 内容 | run |
> |---|---|---|
> | P1 | OCLIP r4 三臂：seed 123/456 重跑（128）+ 补 789/1011 | 12 |
> | P2 | B/16 r4 both/vision：seed 456 重跑 + 三臂补 seed | 8 |
> | P3 | COCO text_only：r2/r8/r32/r64 重跑（128）+ 各补 seed | 19 |
> | P4 | B/32 r4 三臂：只补 seed（批次已全 128） | 6 |
>
> **幂等规则（以元数据为准，不以文件存在性为准）**：
> `results.json` 不存在 → 跑；存在但 `batch_size != 128` → **重跑覆盖**；已是 128 → 跳过。
> **预计 12–14 h**（B/16 的 `both`/`vision_only` 单 run 近 2 h，是主要成本）。
>
> ### 四、9-seed VLM 完成（27/27，0 失败）
>
> | 臂 | n | $DG^*$ 相对变化 | CG 跨度 |
> |---|---|---|---|
> | `text_only` | 9 | $+82.0\\pm8.5\\%$ | $0.160\\pm0.091$ |
> | `both` | 9 | $+88.0\\pm6.4\\%$ | $0.303\\pm0.126$ |
> | `vision_only` | 9 | $+18.0\\pm8.0\\%$ | $0.398\\pm0.077$ |
>
> **两两比较（CG 尺度）**：`text_only` vs `vision_only` = **$2.01$ sd（显著）**；
> `text_only` vs `both` = $0.92$ sd（不显著）；`vision_only` vs `both` = $0.64$ sd（不显著）。
>
> **→ 9 seed 把 5 seed 时的 $1.18$ sd 提升到 $2.01$ sd**：`vision_only` 最弱**由显著检验支持**。
> **但 `text_only` vs `both` 仍不可分辨**（$DG^*$ 相对变化上，`both` 的逐 seed 与 `text_only` 部分重叠）。
>
> **VLM 的批次一直一致**（batch 2，脚本内固定）→ **不受本次批次问题影响** ✅
>
> ### 五、待办
>
> | # | 项 |
> |---|---|
> | 1 | 修正队列跑完（约 12–14 h）→ 重算表 + 台账 + 重编译 |
> | 2 | 9-seed VLM 数字写进论文（现论文是 5 seed） |
> | 3 | `paper合` 定刊投出 |
> | 4 | A1 转投确认（`Neural Networks`，截止 `Nov 08`） |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "查出**批次大小污染**" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("查出**批次大小污染**", "19 个 run", "46 run", "2.01", "A + 统一 128", "batch 128"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
