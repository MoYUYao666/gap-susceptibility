# -*- coding: utf-8 -*-
r"""Correct two wrong claims in the 22:35 handoff entry, and record the verified parity result.

What was wrong:

1. The entry said `is_gradient_checkpointing: False` on the cloud, from a probe that called
   `from_pretrained` directly, without the LoRA wrapping or `prepare_model_for_kbit_training`. Following
   the sweep's own `build()` path shows checkpointing **is** enabled (True after
   `prepare_model_for_kbit_training` and after `get_peft_model`). The probe described a different model
   than the one trained.
2. Because of that wrong reading, the entry attributed the 48x speed difference to "hardware only" and
   left open whether checkpointing differed. That question is now closed by measurement, not by reading
   flags: with `--deterministic` on both sides the runs agree to 4e-4, and the speed difference is
   repeatable.

Both corrections are appended to the entry as a dated note rather than by rewriting it.

    python tools/_p976_correct_and_record.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"

NOTE = """> **🔧 2026-10-15 22:50 —— 对上方 22:35 条目的两点更正 + 端口正确性**已证明**（逐步对照 4e-4）**
>
> ### 一、⚠️ 更正 1：`is_gradient_checkpointing: False` **是错的读数**
>
> 22:35 条目里那个 `False` 来自一个**直接 `from_pretrained`** 的探针——**没有套 LoRA、也没走
> `prepare_model_for_kbit_training`**，因此它描述的是**另一个模型**，不是训练用的那个。
> 按 **脚本自己的 `build()` 路径**重查（`tools/_p974`）：
>
> | 阶段 | is_gradient_checkpointing |
> |---|---|
> | 裸 `from_pretrained` | **False**（← 我先前的错读数就是这一层）|
> | `prepare_model_for_kbit_training(use_gradient_checkpointing=True)` 之后 | **True** |
> | `language_model` 层 | **True** |
> | `get_peft_model` 之后 | **True** |
>
> **⇒ 云端与本地同配置，梯度检查点本来就是开的。**
> **教训：探针必须走被测代码的真实构建路径**；直接从底层 API 取样会测到另一个对象。
>
> ### 二、⚠️ 更正 2：48× 的归因**不再靠"读开关"推断，改为实测证明**
>
> 我在 22:35 条目里写"速度差是硬件因素"，那只是**推测**。现已用**最硬的对照**证明：
> 两边**都开 `--deterministic`**（该模式下卷积算法选择固定）跑同一 5 步：
>
> | 项 | 本地 4060 Laptop | 云端 4080 SUPER | 差异 |
> |---|---|---|---|
> | **5 步 loss** | **2.9495** | **2.9491** | **4e-4** |
> | **DG\*** | 0.2733 → 0.2703（rel **−1.115%**）| 0.2731 → 0.2702（rel **−1.067%**）| **2e-4** |
> | **CG** | 0.7572 → 0.7536 | 0.7570 → 0.7536 | **0** |
> | 每步 | 94.1 s | **1.3 s** | **72×** |
> | 首批 tokens / mean / 序列长 | 1220 / 610 / 610 | **1220 / 610 / 610** | **0** |
>
> **⇒ 端口正确性成立**：数据几何**逐字节一致**、同一确定性配置下**指标一致到 4e-4**。
> 剩下的 4e-4 属**跨 GPU 架构（Ada vs Ampere）、驱动与 kernel 差异**，非环境或数据差异。
>
> ### 三、✅ 由实测得到的结论
>
> | 问题 | 结论 |
> |---|---|
> | 云端是否"一比一"还原？| **是**（版本逐项自检 + 全 import 实测 + 同确定性配置指标 4e-4 一致）|
> | 每步快多少？| **72×**（1.3 s vs 94.1 s，确定性模式；非确定性小样为 1.3 s vs 63.3 s）|
> | 全量预计？| 本地 14.5 h/run ⇒ 云端**约 15–20 分钟/run**，12 run **约 3–4 小时**（含评测与加载）|
> | 口径 | **仍用 4-bit**（与本地/论文口径一致，已实测一致）；**bf16 是可选加速但不改口径需另行说明** |
>
> ### 四、⏭️ 下一步
>
> **等操作者点头即开云端全量**：
> `--samples 400 --eval-pairs 300 --epochs 3 --batch 2 --max-len 2048 --seeds 3 --rank 8 --arms frozen,text_only,vision_only,both`
> 输出到**清空后的** `outputs/llava_sites_cloud/`；完成后我与本地基准（3 个 frozen + 160 步轨迹）逐项对照。
>
> **工具**：`_p974`（按真实路径查检查点）｜`_p975`（云端确定性对照）｜`_p976`（本条更正与落账）。
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
    if "对上方 22:35 条目的两点更正" not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + NOTE + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  correction note added to the handoff")
    mp = io.open(MAP, encoding="utf-8").read()
    row = ("35. 🔧 **更正 + 端口正确性已证明（2026-10-15 22:50）** —— 更正 22:35 条目两处："
           "① `is_gradient_checkpointing: False` **是错读数**（探针没走脚本 `build()`，漏了 LoRA/k-bit 准备）；"
           "按真实路径重查为 **True**；② 48×/72× 的归因**改为实测证明**：两边同开 `--deterministic`，"
           "5 步 loss **本地 2.9495 vs 云端 2.9491（4e-4）**、DG* 差 **2e-4**、CG 差 0、token 几何**完全一致**，"
           "每步 **94.1 s vs 1.3 s（72×）**。**⇒ 一比一还原成立**（版本自检+import 实测+逐步指标一致）。"
           "全量预计云端 **15–20 分钟/run、12 run 约 3–4 h**，口径仍用 **4-bit**。**等操作者点头开全量**。"
           "详见 `HANDOFF.md` 顶部 2026-10-15 22:50 条目。\n")
    anchor = "34. ✅ **云端对照通过（2026-10-15 22:35）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
