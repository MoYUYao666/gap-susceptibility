# A1 类别对齐（λ_reg）实验：三处缺陷审计与重跑说明

**审计日期**：2026-09-14
**触发原因**：补种子的 λ_reg 剂量-响应结果出现无法解释的种子分裂
（同 λ 下 seed 42 的 τ≈0.713、seed 123/456 的 τ≈−0.087，而三者 50k top-1
分别为 58.05 / 58.16 / 58.08，几乎一致）。
**结论**：定位到 **3 个独立缺陷**，其中第 3 个使论文 `revision_additions.tex`
块 4/6/7 的"训练期类别对齐有害"结论**不被现有实验支持**，必须重跑。

---

## 缺陷 1：τ 的冻结参照与当前分片不对应（测量层面）

### 症状
`outputs/a1_class_aligned/lr0.0/` 下三个种子：

| seed | τ (ep1→ep10) | top1_50k | val_loss |
|---|---|---|---|
| 42 | 0.7594 → 0.7105（平滑衰减后平台） | 58.05 | 2.364 |
| 123 | −0.0867 → −0.0864（恒定） | 58.16 | 2.306 |
| 456 | −0.0895 → −0.0885（恒定） | 58.08 | 2.340 |

准确率与 val_loss 三种子一致，τ 却差 0.8——指向测量而非训练。

### 判定实验
`tools/_a1_tau_diag.py`：载入**零 LoRA 增量**（B=0，此时模型就是基座，
`Sc` 必须逐元素等于 `S0`）。

```
init (B=0, ΔW=0)   tau_mean=-0.0868   [compute_tau=-0.0868]
 逐样本 τ 分布: τ=+0.0:862  τ=-0.2:830  τ=-0.4:817  τ=+0.2:702 ...
```

自洽检查给出 **−0.0868 而非 1.0000**，且逐样本 τ 近乎均匀铺在 −1..1 的
离散格点上（纯噪声）→ 参照本身与输入图像不匹配。

`tools/_a1_rowmatch.py` + `tools/_a1_label_probe.py` 进一步定位：

| 检验 | 结果 | 判读 |
|---|---|---|
| 旧 `S0` 的 argmax vs 当前标签 | 0.14% | 随机水平（1/1000） |
| 当前基座 argmax vs 当前标签（offset 0） | **59.10%**（5k）/ **59.29%**（50k） | 当前数据是真实 ImageNet-1K val |
| ‖S0[i]−B[i]‖ vs ‖S0[i]−B[随机行]‖ | 1.2246 vs 1.2285 | 行与行**无对应** |
| 行最近邻是否双射 | 否 | 非单纯行序置换 |

### 结论
2026-08-16 建缓存时磁盘上的分片，与 2026-09-14 重下的分片**不是同一批图像**。
后者为 50,000 行、50 张/类、标签 0..999，基座零样本 **59.29%**，与档案中旧数据
的 **59.28%**（`outputs/imagenet1k_zs_50k_plain.json`，2026-08-14）在同一基准上
等价——即两副本是**同一基准的不同副本**，但逐行不对应。

**影响**：2026-09-14 批次的全部 τ 无效（含 `eval_epoch*.json` 与 `results.json`
中的 τ 轨迹）。50k top-1 与 val_loss 不受影响（不依赖 `S0`）。

---

## 缺陷 2：类别名表多一个占位类（口径层面）

当前分片的 `ClassLabel` 有 **1001** 项，末尾为占位类 `'none'`；
`eval_50k` 直接由 `names` 构造文本集 → 多出一个垃圾类
`"a photo of a none"`。

**影响**：2026-09-14 批次的 50k top-1 在 **1001 类**上计算，
而 2026-08-17 的 seed 42 结果在 **1000 类**上——两者不可直接比较。
（当前数据真实标签为 0..999，占位类无样本。）

**修复**：新增 `imagenet_class_names()`，只取真实 1000 类，
并断言与 `data/imagenet_1k_names.json` 一致（已通过）。

---

## 缺陷 3：质心表按位置索引而非按类 ID（训练层面，最严重）

```python
cls_ids = sorted(set(labels.tolist()))
cents = torch.stack([base[labels == c].mean(0) for c in cls_ids])   # 行序 = cls_ids 位置
...
c_ema = cents.cuda().clone()
cc = F.normalize(c_ema[y], dim=-1)        # y 是伪标签的【类 ID】
```

`c_ema[y]` 用类 ID 取行，但 `cents` 的行序是 `cls_ids` 的位置。
旧 5k 子集只覆盖 **998** 个类（`cents.shape == (998, 512)`），
因此只要缺失的类不在末尾，其后所有类的质心就整体错位一格。
缺失的两个类恰好是最后两个 ID 的概率 ≈ 2×10⁻⁶。

`tools/a1_refs_rebuild.py` 用旧 `cents` 与新全量质心匹配还原
（`outputs/a1_class_aligned/old_cents_cls_ids_recovery.json`），
匹配余弦 mean=0.956，还原结果**不是** `0..997`——即缺失类散布在中间，
**错位实际生效**。

**影响**：08-16 与 09-14 两批 λ>0 的训练，正则项把图像拉向的是
**另一个类的质心**。故"训练期类别对齐有害（top-1 58.1→54.4、τ 0.711→0.611、
val 2.36→2.10）"这一结论，以及块 6 的早停叙事、块 7 的协议比较，
**均不被这些实验支持**，须以修好的代码重跑后重写。

> λ=0 的**训练**不受此缺陷影响（align 项权重为 0，`c_ema` 更新不影响梯度、
> 不消耗 RNG），但其**测量**仍受缺陷 1/2 影响。

---

## 已执行的修复动作

| 动作 | 位置 |
|---|---|
| 质心表改为按类 ID 索引的 1000 行表，缺失类用类名文本嵌入兜底 | `tools/train_class_aligned.py` |
| 只取真实 1000 类（剔除占位类 `'none'`） | `tools/train_class_aligned.py` |
| 端点 val_loss 并入训练路径（原先只存在于 eval-only，导致每个端点要额外跑一遍） | `tools/train_class_aligned.py` |
| 训练 JSON 记录分片/参照指纹（`fingerprint`） | `tools/train_class_aligned.py` |
| 逐 epoch τ 改为 `--tau-every-epoch` 开关（默认关，省 GPU；权重每 epoch 都存，可精确补测） | `tools/train_class_aligned.py` |
| 旧参照备份 | `outputs/a1_class_aligned/frozen_refs.STALE_2026-08-16.pt` |
| 旧结果归档 | `outputs/a1_class_aligned/_archive_broken_cents_0816_0914/` |
| 参照重建（cents 1000×512 按类 ID；S0/topk5 基于当前分片） | `outputs/a1_class_aligned/frozen_refs.pt` |
| 质心类 ID 还原记录 | `outputs/a1_class_aligned/old_cents_cls_ids_recovery.json` |
| 重跑（14 次训练 + 5 次 eval-only + 2 个 no-EMA 对照） | `tools/a1_class_aligned_rerun.ps1` → `a1_class_aligned_rerun.log` |

诊断脚本（保留备查）：`tools/_a1_tau_diag.py`、`tools/_a1_rowmatch.py`、
`tools/_a1_label_probe.py`、`tools/_a1_refs_mismatch.py`、`tools/_a1_class_offset.py`、
`tools/a1_refs_rebuild.py`、`tools/a1_tau_recompute.py`。

---

## 待办（重跑完成后）

1. 用重跑的真实 JSON 重写 `paper_a1/revision_additions.tex` **块 4**（剂量-响应）、
   **块 6**（早停表 + 叙事）、**块 7**（协议说明）——注意块 6 原表中
   epoch 1/2/3/5 的数字来自 08-16 那份**已被覆盖的旧代码检查点**，
   与 epoch 10（08-17 修复后）不同源，属另一处独立错误。
2. 更新 `tools/ap3_a1_revision_check.py` 中 B4/B6 的断言数值。
3. 逐脚本排查：所有 2026-09-14 之前基于 `data/imagenet_hf/` 的数字都绑定在
   **已不存在的那份副本**上（`tools/clip_a1_*.py`、`clip_domain_matrix.py`、
   `clip_degradation_matrix.py`、`clip_dynamics.py` 等）。基准级数字
   （50k 零样本）与当前副本等价，可沿用；但"索引耦合"的量
   （冻结参照 τ、按索引取固定子集）**无法用当前副本复现**，需要重算或在
   论文/交接文档中明确标注口径。
4. `clip_a1_tau_trajectory.py` 产出的 `a1_tau_trajectory.json`
   （τ 0.767→0.748、top-1 58.86→58.90%，块 7 引用）同属上述第 3 类，需复核。
