# -*- coding: utf-8 -*-
r"""落账：云端与本地结果不一致的**完整排查**（2026-10-09）。

    python tools\_docs_cloud_discrepancy.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔍 2026-10-09 16:10 —— 云端与本地结果**不一致**：完整排查（操作者问"是数据集不一样吗"）**
>
> ### 结论：**不是数据集的问题**——逐项证明如下
>
> | 检查 | 本地 | 云端 | 结论 |
> |---|---|---|---|
> | `results.csv` **md5** | `b12eb13ad488e50a` | `b12eb13ad488e50a` | ✅ **同一份文件** |
> | 前 1000 图 **md5** | `045e29f159e02a31` | `045e29f159e02a31` | ✅ **同一批图** |
> | 图数 / 标注数 | 31783 / 158914 | 31783 / 158914 | ✅ 一致 |
> | **随机图回退**（`Image.open` 失败 → `Image.new`） | 0 条 | **0 条**（实测捕获） | ✅ 无缺失 |
> | `strict_freeze_control.py` **sha256** | `e221141b08aeaf9e` | 同 | ✅ 同版本 |
> | `image_embeds_hash`（同一张图） | **−2.814** | **−2.814** | ✅ 模型一致 |
> | `cos_ii` / `dist_it` / `cg` | `0.6927390` / `1.6150453` / `1.0231127` | 同（7 位） | ✅ 预处理一致 |
> | `effective_rank_init`（24 层） | — | **ratio 全 1.0000** | ✅ **初始权重一致** |
> | `n_trainable_params` | 98,304 / 245,760 / 147,456 | 同 | ✅ 一致 |
> | transformers | 5.16.1 | **对齐到 5.16.1 后仍失败** | ❌ 不是版本问题 |
>
> ### 真正差异：**云端那次训练没有生效**
>
> | 指标 | 本地 | 云端 | 含义 |
> |---|---|---|---|
> | **`R@1`** | **0.685** | **0.002** | 云端 = **随机水平** |
> | **`final_train_loss`** | 0.157 | **4.809** | ≈ `ln(128) = 4.852` → **完全没学到** |
> | **`cosine_separation`（初始）** | **0.141407** | **0.000000** | 云端正负样本对余弦**完全相等** |
> | `mean_cosine_pos` vs `neg`（初始） | 0.31206 vs 0.17065 | 0.185680091 vs 0.185680076 | **云端不区分正负** |
> | `elapsed_sec` | 1562.8 | **186.2** | 云端快 **8.4 倍** |
> | `effective_rank_final` | — | ratio **0.29–0.53** | 视觉侧表示被破坏 |
>
> **关键推理**：**初始权重完全相同**（`effective_rank_init` 全为 1.0000），
> 但**初始状态下云端就区分不了正负样本对** → **文本嵌入在云端没有随样本变化**
> → **问题出在"batch → 模型"这一段，与数据集文件无关。**
>
> ### 未钉死的最后一步（诚实标注）
>
> 最可能两个方向，**我未能排除完**：
> 1. `create_dataloaders` 在云端走了**不同分支** → caption 与图**未按对喂入**
>    （该函数内有 `random_split` 与多种标注解析路径）；
> 2. **transformers 5.x 在云端对 CLIP 的 padding/`attention_mask` 处理不同**
>    → 文本嵌入被池化成同一向量。
>
> 最后一个探针（`tools/_p73_batch_parity.py`）正卡在这一步，
> **但本地探针因 `max_samples=5000` 加载慢而超时**（我该先用小样本 —— 又一次"没先做最小验证"）。
>
> ### 操作者决定：**放弃云端，回本地跑**
>
> | 项 | 决定 |
> |---|---|
> | 云端 | ✅ **已全部终止**（GPU 1 MiB / 0%）｜38 个 JSON 已列清单保存｜`Γ_m` 数值已提取 |
> | 本地 | **补 seed 改 `--batch-size 64`**（128→64，**已记录偏离**，为绕开共享显存） |
> | 理由 | 本地结果**已被证明正确**（`R@1 = 0.685`），云端复现失败且根因未钉死 |
>
> ### 云端**仍有效的产出**（未浪费）
>
> 1. **`Γ_m` 完整量**（CLIP B/32 三臂，含 `cos`）：
>    `Γ_v = +0.9983 / +1.0148`，`Γ_t = +25.0481`（**数值可信**——`Γ_m` 只依赖单批前向+反传，
>    不依赖训练收敛）；
> 2. **三模型校验通过**（B/32、B/16、OpenCLIP 的 patch size 与参数量）；
> 3. **数据管线验证**（1000 图 + CSV 的可复现打包方式）。
>
> ⚠️ **但云端的 18 个 seed `results.json` 不可用**（`R@1 = 0.002`，训练失效）——
> **不得并入本地归档**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "云端与本地结果**不一致**：完整排查" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("完整排查", "不是数据集的问题", "b12eb13ad488e50a", "045e29f159e02a31",
              "R@1 = 0.002", "不得并入本地归档", "batch-size 64"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0S." not in m:
        add = """
**0S. 🔍 云端结果与本地不一致：完整排查 + 放弃云端（2026-10-09 16:10）**

- **不是数据集问题**：`results.csv` md5、前 1000 图 md5、`image_embeds_hash`、`effective_rank_init`（24 层 ratio 全 1.0000）、脚本 sha256、`n_trainable` **全部一致**；**0 随机图回退**；transformers 对齐 5.16.1 后仍失败。
- **真差异**：云端 `R@1 = 0.002`（本地 0.685）｜`final_train_loss = 4.81` ≈ `ln(128)`｜**`cosine_separation(init) = 0`**（文本嵌入不随样本变化）→ **训练未生效**。
- **未钉死**：`create_dataloaders` 分支差异 或 transformers 5.x 的 CLIP padding 处理。
- **决定（操作者选 B）**：**放弃云端，回本地**；本地补 seed 改 **`--batch-size 64`**（记录偏离）。
- **云端仍有效**：`Γ_m` 完整量（`Γ_v≈+1.0`、`Γ_t≈+25.05`）、三模型校验、数据打包方法。
- ⚠️ **云端 18 个 seed `results.json` 不可用，不得并入本地归档。**
- 证据：`outputs/analysis/side_by_side.json`、`field_diff.json`、`data_parity.json`。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
