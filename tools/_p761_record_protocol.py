# -*- coding: utf-8 -*-
r"""Record the retrieval-protocol investigation and its measured results in the handoff.

    python tools/_p761_record_protocol.py --apply"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔬 2026-10-15 04:00 —— 更大数据集实验：先查出**检索协议有真 bug**，另发现 COCO 实验规模只有声称的 1/5**
>
> ### 一、操作者指令
>
> > **"新跑更大数据集"** —— 回应审稿人 R2-3（*"Broader validation on larger datasets and modern VLMs"*）。
>
> 执行前的环境勘查：**实验服务器 `192.168.1.103` 不可达**（ping 失败）⇒ 只能用**本地 RTX 4060 Laptop 8 GB**（现有实验也是在这块卡上跑的）。本机 **32 核 / 8.6 GB 显存**。
>
> ### 二、🔴 发现一：`src/trainer.py` 的检索指标**在数学上是错的**
>
> **原实现**：
> ```python
> sim_matrix = image_embeds @ text_embeds.T         # (N,N)
> correct = (topk(sim_matrix) == arange(N))         # 对角线 = 正样本
> ```
>
> **问题**：`COCODataset._load_annotations()` **逐条 caption 建样本**（每图约 5 条）。把整个 loader 展平成 `(N,N)` 后，**第 i 行与第 i 列不再是同一对** —— 正确的那条 caption 落在**别的行**。训练损失没问题（batch 内 loader 保证配对），**只有评测**坏掉。
>
> **实测（`tools/_p760`，逐例循环，2,000 图 / 10,005 条 caption，冻结 CLIP）**：
>
> | 协议 | R@1 | R@5 | R@10 |
> |---|---|---|---|
> | **t2i**（caption → 自己的图） | **0.2857** | 0.5306 | 0.6456 |
> | **i2t**（图 → 自己的 caption） | **0.4755** | 0.7645 | 0.8500 |
> | **diagonal**（档案的约定） | **0.0951** | 0.3221 | 0.4306 |
>
> **⇒ 档案里 COCO 的 `R@1 < 0.001` 与本实测的 diagonal 0.0951、正确协议 0.29–0.48 **相差两个数量级**，说明**产生那些数字的代码路径还有更严重的问题**（不只是"少算几条"）。
> **这正是 R1-W4 要求的"先核实检索协议"** —— 审稿人的怀疑是有根据的。
>
> **⚠️ 我在过程中写错过一次**：向量化实现一度给出 i2t R@1 = **0.9957**（不可能，CLIP ViT-B/32 在 COCO 上限约 0.5–0.6），且与逐例检查（own rank 19/1/4/4/3）矛盾 ⇒ **改写成逐例循环**（`_p760`）后得 0.4755。**教训：向量化指标必须与逐例循环交叉验证。**
>
> ### 三、🔴 发现二：COCO 实验的**有效规模只有此前的 1/5**
>
> `kek` 加载器按 caption 行截断：`max_samples=10000` ⇒ 实测**仅 1,999–2,000 张唯一图**（10,005 行 ÷ 5）。
> `experiments/theory/coco_validation.py` 用的正是 `MAX_SAMPLES = 10000`（与 `pr_stats_hardened.json :: n_rows = 204` 同量级问题）。
> ⇒ 稿件称 "COCO cross-dataset validation" 时，**实际规模是 ~2,000 图**。
>
> ### 四、🔴 发现三：另有一处**数据泄漏隐患**（已在本轮新脚本中避免）
>
> `create_dataloaders()` 对 COCO **train 与 val 用同一 `split` 参数**建两个 loader（见 `src/dataset.py`），
> 而旧 COCO 实验正是走的这条路 ⇒ **评测集与训练集可能同源**。
> **本轮新脚本 `tools/_p754_coco_scaleup.py` 强制 `train`=train2014、`val`=val2014，并断言两者不相交。**
>
> ### 五、✅ 已交付的可复跑修复
>
> | 文件 | 改动 | 性质 |
> |---|---|---|
> | `src/dataset.py :: _collate_fn` | 保留 `image_path`（评测归属信息的唯一来源） | 向后兼容 |
> | `src/trainer.py :: _compute_retrieval_metrics` | 改为**显式归属**协议（图 ↔ 其自身全部 caption），分块相似度矩阵防 OOM | 修 bug |
> | `tools/_p754_coco_scaleup.py` | 大规模实验脚本：train2014/val2014 严格分离、按**唯一图**计规模、修正协议、8 worker、`no_grad` + 分块 | 新增 |
> | `tools/_p760_loop_measure.py` | 逐例循环的**权威测量**（不可能有广播错误） | 新增 |
>
> ### 六、⚠️ 遇到的技术障碍（如实记录）
>
> **LoRA 微调在 COCO 上不收敛**：`text_only` r=8 跑 2 epoch，loss 3.99→3.53，修正协议下 R@1 = **0.0070**（而 frozen 基线 **0.5165 / 0.4755**）。同样条件下 Loss 停在 log(32)≈3.47 附近 ⇒ **梯度几乎没推动模型**，不是单纯欠训练。诊断脚本 `tools/_p755` 因 `tr.model.processor` 接口不存在而中断，**未查完**。
> **⇒ 这意味着：现有 COCO 结果的 R@1 数值，连同"COCO 上近随机"的结论，都需要在修好训练后重测。**
>
> **训练吞吐（实测）**：1,000 图 ≈ 65 s/epoch（8 worker）。10,000 图 × 3 epoch × 5 seed × 2 arm ≈ **5.4 小时**（本机串行）。
>
> ### 七、结论与待决
>
> **本轮的净收益不是"跑出一个更大的数"，而是查清了 R1-W4 指出的问题确实存在，并且比审稿人说的更具体。**
>
> | # | 事项 | 状态 |
> |---|---|---|
> | 1 | 检索指标 bug | ✅ 定位 + 修复 + 逐例验证 |
> | 2 | 有效规模只有 1/5 | ✅ 量化 |
> | 3 | train/val 同源隐患 | ✅ 新脚本已避免 |
> | 4 | **LoRA 在 COCO 上不收敛** | 🔴 **根因未查完**（下一步） |
> | 5 | 大规模（10,000 图）正式跑 | ⏸ **待 4 解决后再跑**（否则跑出来仍是坏数） |
>
> **⚠️ 关键判断**：**在 (4) 解决之前跑 10,000 图没有意义** —— 会产出又一批 R@1≈0.007 的数。
> **这不是拖延**：审稿人 R1-W4 的原话就是 *"the retrieval protocol ... should first be carefully verified"*。
> **⇒ 建议下一步：查清 LoRA 为何在 COCO 上不学习（换更大 lr / 只调 logit_scale / 比对 Flickr 能学的原因），再启动大规模跑。**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "检索协议有真 bug" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("检索协议有真 bug", "0.0951", "1/5", "0.9957", "不收敛", "5.4 小时"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
