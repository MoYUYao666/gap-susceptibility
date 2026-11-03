# -*- coding: utf-8 -*-
r"""Record the Qwen2.5-VL integration state: the runner works, but the device cannot hold the model.

Measured on the host (RTX 4080 SUPER, 32,760 MiB) on 2026-10-16:

* the model loads, 8,292,166,656 parameters;
* the tower split is correct for Qwen -- `text_only` reports 20,185,088 trainable parameters in the text tower;
* evaluation fails with `OutOfMemoryError` at **31.09 GiB allocated of 31.48 GiB usable**, and the failure
  point does not move when batch, sequence length and evaluation batch are all reduced to their minimum
  (batch 1, max-len 512, eval-batch 1). Gradient checkpointing off does not change it either.

That is the signature of a fixed floor: the weights (16.6 GB in bf16) plus the AdamW state are what fill the
device, not the activations. LLaVA's peak was 29.95 GB, so Qwen's extra 2.6 GB does not fit in the remaining
headroom. A 7B Qwen run therefore needs either a device larger than 32 GB at bf16, or 4-bit quantisation.

    python tools/_p1045_record_qwen_state.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "Qwen2.5-VL 适配完成但 32 GB 装不下"

ENT = """> **🧩 2026-10-16 18:30 —— Qwen2.5-VL **适配已完成**，但**这台 32 GB 机器装不下 7B**（显存硬墙）；LLaVA 全部成果已归档**
>
> ### 一、✅ LLaVA 全量已完成、已校验、已归档（操作者要求"先保存所有结果包括 pt 模型"）
>
> | 项 | 值 |
> |---|---|
> | 运行 | `EXIT=0`、**12 条记录**、**零 arm 失败** |
> | 校验 | `tools/_p984_verify_cloud_results.py` → **all checks passed**：12 条齐全、尺度 1500/3/rank8 正确、**frozen 三 seed 逐位一致**（0.2619372457265854）、loss **1.0372 → 0.3914**、无 traceback/OOM |
> | **`.pt` 适配器** | **7 个**（both ×3 = 188 MB/个、text_only_s456 = 160 MB、vision_only ×3 = 28 MB），共 **774 MB** |
> | **已取回本地** | `outputs/llava_bf16_sites_cloud/`（12 条 JSON + 7 个 `.pt` + 日志 + 汇总，**大小逐一校验一致**）|
> | 云端快照 | `/root/p3/frozen_llava_1016_1640/`（results + 脚本 + 日志）|
>
> **结果汇总（bf16，1500 训练 / 500 评测，3 epochs，3 seeds）**：
>
> | arm | 可训练参数 | ΔDG* 均值 ± sd |
> |---|---|---|
> | frozen | 0 | **+0.297% ± 0.000%** |
> | text_only | 19,988,480 | **+0.297% ± 0.000%**（**与 frozen 完全相同**）|
> | vision_only | 3,645,440 | **+13.333% ± 4.737%** |
> | both | 23,633,920 | **+6.068% ± 6.547%** |
>
> ### 二、🧩 Qwen 适配：**已完成**（有可复用的运行器），但**显存装不下**
>
> 新建 `tools/_p1035_qwen_sites.py`（由冻结版 `_p820` **机械生成**，`tools/_p1034` 生成+断言），七项替换全部落地：
>
> | # | 差异 | 修法 |
> |---|---|---|
> | ① | LLaVA 类加载 Qwen 报 `hidden size (1280) is not a multiple of attention heads (12)` | 改用 `Qwen2_5_VLForConditionalGeneration`（含导入行）|
> | ② | LLaVA 提示词串 Qwen 不接受 | 用 `apply_chat_template` 生成提示（**仅 Qwen 路径**）|
> | ③ | `config.image_token_index` Qwen 没有 ⇒ 掩码失效 | 改用 `image_token_id`（**151655**，实测）|
> | ④ | 分塔按 LLaVA 命名 ⇒ `{'other': 391}` | Qwen 视觉塔是 `model.visual.blocks.*`、投影是 `visual.merger` ⇒ 修 `tower_of`（**已验证**：`text_only` 报 20,185,088 全在 text 塔）|
> | ⑤ | 手工调视觉塔报 `missing argument 'grid_thw'` | 不再手工调用：**hook `visual.merger`** 取投影后视觉特征（实测 shape `(587, 3584)`）|
> | ⑥ | `output_hidden_states=True` 保留 29 层激活 ⇒ OOM | 改为 **hook 词嵌入层**取文本侧（只需一个张量）|
> | ⑦ | 驱动脚本缺 `--no-grad-ckpt`（该开关在冻结快照之后才加）| 补回 `_p820` 并重新生成 |
>
> ### 三、❌ 硬墙：**32 GB 装不下 Qwen2.5-VL-7B（bf16）**
>
> 实测（`tools/_p1044`）：
>
> ```
> OutOfMemoryError: 31.09 GiB allocated of 31.48 GiB usable
> 把 batch / max-len / eval-batch 全部压到最小（1 / 512 / 1）后，失败点**不移动**
> 关掉梯度检查点也**不移动**
> ```
>
> ⇒ 这是**固定底噪**（权重 16.6 GB + AdamW 状态），**不是激活**：LLaVA 峰值 29.95 GB，Qwen 多出的 ~2.6 GB 没有余量。
> **Qwen2.5-VL-7B 只能在 >32 GB 的卡上按 bf16 跑，或改用 4-bit。**
>
> ### 四、⏭️ 待操作者选择（当前 GPU 已空闲、机器仍在运行）
>
> | 选项 | 说明 |
> |---|---|
> | **A. 换更大卡跑 Qwen-7B（bf16）** | 运行器已就绪（`tools/_p1035_qwen_sites.py`），换机即可跑 |
> | **B. 本机用 4-bit 跑 Qwen-7B** | 与操作者"不要 4bit"的口径冲突，需明确同意；本地 8.6 GB 都能跑 4-bit，24 GB 更宽裕 |
> | **C. 换小模型（Qwen2.5-VL-3B / Qwen2-VL-2B）** | 本机可跑，但参数量与 LLaVA-7B 不同，横向对比需注明 |
> | **D. 到此处关机** | LLaVA 已成完整闭环；Qwen 待有更大机器再说 |
>
> **工具**：`_p1031`（恢复冻结脚本）｜`_p1034`（生成 Qwen 运行器）｜`_p1038`/`_p1039`（参数名/处理器探针）｜`_p1042`（嵌入 hook）｜`_p1043`/`_p1044`（可行性实测）｜`_p1045`（本条）。
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
    row = ("41. 🧩 **Qwen2.5-VL 适配完成、32 GB 装不下（2026-10-16 18:30）** —— **LLaVA 全量已闭环**：**12 条记录**、"
           "`_p984` **all checks passed**（frozen 三 seed 逐位一致 0.2619372457265854、loss 1.0372→0.3914）、"
           "**7 个 `.pt` 适配器（774 MB）已取回本地** `outputs/llava_bf16_sites_cloud/`。结果：frozen/text_only **+0.297%**、"
           "vision_only **+13.333% ± 4.737%**、both **+6.068% ± 6.547%**。**Qwen 运行器已就绪**（`tools/_p1035_qwen_sites.py`，"
           "由冻结版机械生成+七项断言：模型类/chat template/`image_token_id` 151655/分塔 `model.visual.*`/**merger hook** 取视觉特征/"
           "**嵌入 hook** 取文本侧）。❌ **硬墙**：bf16 下 **31.09/31.48 GiB 已分配**，把 batch/max-len/eval-batch 压到最小"
           "（1/512/1）**失败点不移动**、关梯度检查点也**不移动** ⇒ 是权重+优化器底噪（Qwen 8.29 B vs LLaVA 7.06 B，多 ~2.6 GB）"
           "⇒ **7B 需 >32 GB 卡或 4-bit**。待操作者选 A/B/C/D。详见 `HANDOFF.md` 顶部 18:30 条目。\n")
    anchor = "40. 💾 **静默死亡真因=根分区写满（2026-10-16 12:40）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
