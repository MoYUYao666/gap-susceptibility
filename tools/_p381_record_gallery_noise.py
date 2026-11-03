# -*- coding: utf-8 -*-
r"""落账：评测画廊继承 train transform → 全部 CG/DG/R@1 带抽样噪声（2026-10-12）。

## 已核实（我独立读源码 + 实测，非转述）

### 根因
`src/dataset.py`：
- L401：`kwargs = {"split": "train", ...}` → `train_dataset = cls(...)`
- L75：`self.transform = get_clip_transform(image_size, is_train=(split == "train"))`
  → **train 用 `RandomHorizontalFlip(p=0.5)` + `ColorJitter(0.1,0.1,0.1)`**
- L416-425：Flickr30k 走
  `train_dataset, val_dataset, test_dataset = random_split(train_dataset, [...])`
- **`random_split` 返回 `Subset`，它保留被包装对象的 `transform`**
  → **val / test 画廊 = 同一 `Flickr30kDataset` 实例 → 继承 train transform**

### 实测证据（`tools/_p359_transform_chain.py` → `outputs/analysis/transform_chain.json`）
- `[train]/[val]/[test]` 三条 loader 的 `loader.dataset` 都是 `Subset`，
  其 `.dataset`（L1）**都是同一个带 `RandomHorizontalFlip` + `ColorJitter` 的 `Flickr30kDataset`**
- **同一 index 取两次**：`max|Δ|` = **3.5568 / 3.8270 / 3.5568 / 3.8270 / 0.2551**
  （翻转命中时为巨大镜像差；未命中时 0.255 来自 ColorJitter）

### 影响面（`tools/_p380_eval_paths.py` → `outputs/analysis/eval_paths_audit.json`）
- **66 个文件**调用 `create_dataloaders`，**其中 66 个都未显式关随机变换**
- 论文关键产出脚本**全部受影响**：
  `experiments/main.py`（主表来源）、`strict_freeze_control.py`（`tab:position_strict`）、
  `seed_experiments.py`、`siglip_experiments.py`、`coco_experiments.py`、
  `blip2_experiments.py`、`paper/scripts/noise_sensitivity.py`（R1.3 的注入器）、
  `paper/scripts/weight_svd_analysis.py`
- **不受影响**：`tools/train_class_aligned.py`（自建评测，`cdl=0`）

→ **结论：本项目每一个 CG/DG/R@1（含论文全部数字）都是随机画廊的一次抽样，不是确定量。**

## 这解释了什么（此前已记录、当时未找到的原因）

| 此前查到的现象 | 现在的解释 |
|---|---|
| `tab:position_strict` 的 R@1 列 **6/12 格复现不出**（我原判"2 格无来源"） | **很可能是画廊抽样差异**，而非无来源 |
| `1e-4` 复现与 2026-08 归档"**非逐位一致**"（task-5 的 C 项） | 同上 |
| 任务-6 见到"**超出指标理论上限**"的现象 | 画廊随机性改变了检索对的难度分布 |

## 修复（最小、一行）

`src/dataset.py` 的 Flickr30k 分支：把评测画廊从 `train_dataset` 的 `Subset` 上取，
改为**给 val/test 用 `is_train=False` 的独立 dataset 实例**（或在评测前把 transform 换成 eval 版）。

**⚠️ 未修** —— 修它会改变后续所有数字，且**不会**追溯修好已有归档。
**须先量化噪声量级，再决定是否改稿**（见下）。

## 待办

1. **量化**：同一冻结 checkpoint 重复评测 N 次 → CG/DG/R@1 的 sd 与极差；
   与论文**臂间差异**（ΔCG 0.02–0.05、R@1 0.01–0.07）比较 → **噪声是低一个数量级还是同量级**。
2. 若**同量级** → 论文若干"排序"结论需重估，须加 limitation（或修正结论）。
3. 审计成员（dinov2-auditor）正在做 CPU 探针（`tools/_p357_dinov2_norm_probe.py`）。
4. 修复方案落成脚本并**只用于后续**（不追溯改归档）。
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    import io
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[1]
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    marker = "评测画廊继承 train transform"
    if marker in t:
        print("  已记录")
        return 0
    ent = "> **🔴🔴 2026-10-12（续）—— 发现：评测画廊继承 train transform → **全部 CG/DG/R@1 带抽样噪声****\n>\n"
    for line in ENT.splitlines():
        ent += "> " + line + "\n" if line.strip() else ">\n"
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ent + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in (marker, "3.5568", "66 个文件", "random_split", "transform_chain.json"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


ENT = r"""**已核实（我独立读源码 + 实测，非转述）**

**根因** —— `src/dataset.py`：
- L401：`kwargs = {"split": "train", ...}` → `train_dataset = cls(...)`
- L75：`self.transform = get_clip_transform(image_size, is_train=(split == "train"))`
  → **train 用 `RandomHorizontalFlip(p=0.5)` + `ColorJitter(0.1,0.1,0.1)`**
- L416–425：Flickr30k 走 `random_split(train_dataset, [...])`
- **`random_split` 返回 `Subset`，保留被包装对象的 `transform`** → **val/test 画廊继承 train transform**

**实测证据**（`tools/_p359_transform_chain.py` → `outputs/analysis/transform_chain.json`）：
三条 loader 的 `loader.dataset` 都是 `Subset`，其 `.dataset`（L1）**都是同一个带
`RandomHorizontalFlip` + `ColorJitter` 的 `Flickr30kDataset`**；
**同一 index 取两次**的 `max|Δ|` = **3.5568 / 3.8270 / 3.5568 / 3.8270 / 0.2551**
（翻转命中时为镜像差；未命中时 0.255 来自 ColorJitter）。

**影响面**（`tools/_p380_eval_paths.py` → `outputs/analysis/eval_paths_audit.json`）：
**66 个文件**调用 `create_dataloaders`，**全部未显式关随机变换**；论文关键产出脚本**全部受影响**
（`experiments/main.py` = 主表来源、`strict_freeze_control.py` = `tab:position_strict`、
`seed_experiments.py`、`siglip_experiments.py`、`coco_experiments.py`、`blip2_experiments.py`、
`paper/scripts/noise_sensitivity.py` = R1.3 注入器、`weight_svd_analysis.py`）。
**不受影响**：`tools/train_class_aligned.py`（自建评测）。

→ **本项目每一个 CG/DG/R@1（含论文全部数字）都是随机画廊的一次抽样，不是确定量。**

**这解释了三个此前未找到原因的现象**：

| 现象 | 解释 |
|---|---|
| `tab:position_strict` R@1 列 **6/12 格复现不出**（我原判"2 格无来源"） | **很可能是画廊抽样差异** |
| `1e-4` 复现与 2026-08 归档"非逐位一致"（task-5 的 C 项） | 同上 |
| task-6 见到的"超出指标理论上限" | 画廊随机性改变检索对难度分布 |

**修复（最小）**：Flickr30k 分支的 val/test 改用 `is_train=False` 的**独立 dataset 实例**。
**⚠️ 未修** —— 修它会改变后续所有数字，且**不追溯修好已有归档**；
**须先量化噪声量级再决定是否改稿**。

**待办**：① 同一冻结 checkpoint 重复评测 N 次 → 与论文臂间差异（ΔCG 0.02–0.05、R@1 0.01–0.07）
比较，判断噪声是低一个数量级还是同量级；② 若同量级 → 加 limitation 或修正结论；
③ 审计成员正在跑 CPU 探针 `tools/_p357_dinov2_norm_probe.py`；④ 修复脚本只用于后续。"""


if __name__ == "__main__":
    raise SystemExit(main())
