# -*- coding: utf-8 -*-
r"""Record the adapter defect and the corrected canonical numbers.

This is the substantive finding of the 2026-10-17 session and it changes the plan, so it goes into the handover
documents before anything else:

* the canonical recomputation pipeline now measures the right quantity (the earlier run compared a pooled tensor
  with itself: DG* 0.000428, cos(I,T) 0.9997, because the text side averaged over 576 image tokens out of ~596);
* the corrected frozen value is **DG* 0.819799, CG 0.874735, DG_emp 0.881498** over the 500 held-out pairs;
* the trained arms cannot be recomputed at all, because **the saved adapter files contain no weights**: every
  checkpoint is `{'model': {}, 'opt': {...}, 'epoch': N}`, and the optimiser state holds only `step`, `exp_avg`
  and `exp_avg_sq` together with integer parameter indices. The cause is the identity test in my own
  `tools/_p1016_small_checkpoint.py`, fixed in `tools/_p1115_fix_ckpt_filter.py`.

    python tools/_p1116_record_adapter_defect.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "适配器为空"

ENT = """> **🔴 2026-10-17 10:30 —— 重要更正：**保存的 7 个适配器里没有任何权重**（`model: {}`），**arm 级规范度量无法重算**；
> 同时**规范度量本身已修好**，frozen 的数值首次可信**
>
> ### 一、⚠️ 先纠正我昨天对操作者的判断（错了）
>
> 我昨天说「**不用重训，只需重算**」——**该结论不成立**。今天实测：适配器文件里**没有可用的训练权重**。
>
> ### 二、🔍 规范度量：先修掉我自己的一处严重缺陷（已修）
>
> 首次在规范定义下测量 frozen，得到 **DG\\* = 0.000428**，比 Qwen 那批（0.2–2.2）**小三个数量级**。核查一批样本：
>
> ```
> 序列长度 596，其中图像 token 576 个（id 32000）
> cos(I, T) 每对 = 0.99971 … 0.99979          ← 两侧几乎同一个张量
> ||T_排除图像 − T_全部|| = 51.0 … 55.8        ← 原始范数才 ~60–70
> ```
>
> ⇒ 我的**文本侧把 576 个图像 token 也算进均值池化**，于是 `T ≈ I`，**DG\\* 在比"自己和自己"**。
> 该数字**无效**（`tools/_p47_qwen_train.py` 本来就把视觉区间排除，我照搬时漏了）。
>
> **已修**（`tools/_p1110_exclude_image_tokens.py`：文本侧掩码改为 `attention_mask & (tok != IMG_ID)`）：
>
> | | 修正前（错误）| **修正后（有效）** |
> |---|---|---|
> | **DG\\*** | 0.000428 | **0.819799** |
> | **CG** | 0.019940 | **0.874735** |
> | DG_emp | 0.020065 | **0.881498** |
> | 批次间 DG\\* 范围 | 3.7e-5 | 0.029433 |
>
> 归档：`/root/p3/outputs/canonical_recompute.json`（frozen = **500 对保留集**，脚本 `tools/_p1107_run_canonical.py`）。
> ⚠️ **frozen 的 0.819799 是"未训练模型"的规范值**，与归档 12 条用的旧定义（DG\\* 0.2612）**不是同一量**，不得混用。
>
> ### 三、❌ 适配器为空：arm 级重算**不可行**
>
> | 证据（在主机上读实际文件）| 内容 |
> |---|---|
> | `vision_only_s42_ckpt.pt`（28.2 MB）| `dict` 三个键：**`model: dict(0)`**、`opt`、`epoch` |
> | `opt['state']` | 280 条，每条只有 `step` / `exp_avg` / `exp_avg_sq` |
> | `opt['param_groups'][0]['params']` | `list[292]`，元素是 **int 索引**，不是张量 |
> | 加载到基座模型 | **`0 tensors`，missing 686** ⇒ 四个 arm 的 DG\\* **全部等于 frozen** |
>
> ⇒ **训练后的权重没有任何存下来**，优化器状态只有动量、**无法反推** ⇒ **arm 级规范度量必须重训才能得到**。
>
> ### 四、🧠 根因：**我自己的保存代码**（已修）
>
> `tools/_p1016_small_checkpoint.py` 引入的过滤用了**对象身份**比较：
>
> ```python
> _trainable = {k: v for k, v in mm.state_dict().items()
>               if any(t is v for t in (p for p in mm.parameters() if p.requires_grad))}
> ```
>
> 但 **`state_dict()` 返回的是分离副本**，`p is v` **永不成立** ⇒ 保存出 `model: {}`。
> （当初的**意图**是对的——整模型 14.4 GB 会把 30 GB 盘写满；**测试方法**错了。）
>
> **已修** `tools/_p1115_fix_ckpt_filter.py`：改为**按参数名**匹配（`named_parameters()` 与 `state_dict()`
> 名字一致），并留注释记录本次教训。**修改后 `ast` 校验通过**。
>
> ### 五、⏭️ 两条路（待操作者选）
>
> | 路 | 内容 | 代价 |
> |---|---|---|
> | **A. 重训 12 个 run（bf16）** | 修好的脚本会存**真权重**，并且**在训练途中直接记录规范 DG\\*/CG**（比只存权重更稳），得到 arm 级规范数值 | 约 **7.5 小时**（2250 步/run × 12，1 s/步）+ 32 GB 卡 |
> | **B. 不重训** | Paper A 补充 F 节保持"**口径不同的负结果**"（frozen/text-only 均为 +0.297%，与 frozen 逐位相同） | 0；`text-only 零变化` 的解释**仍是开放问题** |
>
> ⚠️ 无论走哪条，**归档 12 条记录本身有效**（门禁 `_p984` all checks passed），它们只是"旧定义下的数字"。
>
> **工具**：`_p1107`（规范重算）｜`_p1110`（修文本侧池化）｜`_p1112`（适配器按 arm 前缀匹配）｜`_p1113`/`_p1114`（查适配器与优化器状态）｜`_p1115`（修保存过滤）｜`_p1116`（本条）。
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
    row = ("46. 🔴 **适配器为空 ⇒ arm 级规范度量必须重训（2026-10-17 10:30）** —— **纠正昨天的\"不用重训\"结论：错了**。"
           "实测 7 个 `.pt` 全是 `{'model': {}, 'opt': {...}, 'epoch': N}`，`opt` 只有 `step/exp_avg/exp_avg_sq` + **int 索引**，"
           "**无权重、无法反推** ⇒ 四个 arm 加载后 `0 tensors`、DG* 全等于 frozen。**根因**：`_p1016` 的过滤用**对象身份**"
           "（`state_dict()` 是副本 ⇒ `p is v` 永不成立）⇒ 已由 `_p1115` 改为**按参数名**匹配。"
           "**同时规范度量已修好**（`_p1110`：文本侧排除图像 token，此前 `cos(I,T)=0.9997` 是自比自）："
           "**frozen 有效值 DG* 0.819799 / CG 0.874735 / DG_emp 0.881498**（500 对保留集），与旧的 0.2612 **不是同一量**。"
           "⏭️ 待选：**A 重训 12 run（约 7.5 小时）** 或 **B 不重训、F 节保持负结果**。归档 12 条本身有效。"
           "详见 `HANDOFF.md` 顶部 2026-10-17 10:30 条目。\n")
    anchor = "45. ⏸️ **LLaVA 规范度量重算"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(REPO / "文件地图.md", "w", encoding="utf-8", newline="").write(mp)
        print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
