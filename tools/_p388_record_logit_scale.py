# -*- coding: utf-8 -*-
r"""落账：`logit_scale` 不一致 → DINOv2 实验与论文 run 目标函数不同（2026-10-12）。

## 核实（我独立读权重 + 载入模型 + 读源码）

| 来源 | `logit_scale` | `exp` |
|---|---|---|
| `models/clip-vit-base-patch32/pytorch_model.bin`（权重真值） | **4.605170** | **100.0000** |
| `CLIPModel.from_pretrained(...)` 载入后 | **4.605170250** | **100.0000** |
| `config.json::logit_scale_init_value` | 2.6592 | 14.2857 |
| **`tools/_p293_dinov2_hetero_strict.py::LOGIT_SCALE_INIT`**（硬编码） | **2.6592** | **14.2857** |

**`src/trainer.py:419`**：`logit_scale = self.model.logit_scale.exp()` → 论文各臂用
**权重真值 exp = 100**（**不是** config 的 2.6592）。

→ **论文 run 的 logits 尺度 100 vs DINOv2 实验的 14.29 = 7.00×**

**归档无法佐证**：`tools/_p367` 扫全部 `results.json` → **归档里没有任何 `logit_scale` 字段**
→ 无法从归档验证每次训练实际用的尺度（这本身是可追溯性缺口）。

## 为什么这条比"归一化错配"更硬

| 项 | 性质 |
|---|---|
| 图像归一化用 CLIP 统计量 | 喂给**视觉塔的输入分布**不同（预处理） |
| **`logit_scale` 不一致** | **目标函数本身不同**（InfoNCE 的温度 = 100 vs 14.29） |

→ 温度差 7× 会直接改变 InfoNCE 的梯度尺度与有效难度，
**因此 DINOv2 的 ΔCG（−0.3913）不可与论文的 ΔCG（如 CLIP B/32 的 −0.0465）并列比较**。

## 影响面的**边界**（不要夸大）

- ✅ **不影响**：ΔCG 的**定义**、DINOv2 **三臂之间**的横向比较（三臂同温）
- ❌ **影响**：把 DINOv2 的 ΔCG **与论文表的 ΔCG 并列**（包括"落进 BioCLIP 区间 −0.29…−0.45"这个说法）

## 处置

1. **`model-coverage` 的报告**必须写明：**目标函数温度与论文不同（7×）**，
   因此其 ΔCG **只可用于三臂排序**，**不可与论文数值比较**（含不可说"与 BioCLIP 同量级"）。
2. 该条应加入论文的"未来工作/流程建议"：**实验记录必须落 `logit_scale` 等目标函数超参**
   （当前归档缺此字段，导致无法自查）。
3. **不改稿中的论文数字**（论文自身的 run 用权重真值 100，一致；问题只在跨实验可比性）。
"""


def main() -> int:
    import sys
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    import io
    from pathlib import Path
    REPO = Path(__file__).resolve().parents[1]
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    marker = "`logit_scale` 不一致"
    if marker in t:
        print("  已记录")
        return 0
    ent = ("> **🔴 2026-10-12（续）—— 核实：`logit_scale` 不一致，DINOv2 实验与论文 run "
           "**目标函数不同（7×）**，其 ΔCG **不可与论文并列**\n>\n")
    for line in ENT.splitlines():
        ent += "> " + line + "\n" if line.strip() else ">\n"
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ent + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("4.605170", "7.00", "logit_scale", "14.29"):
        assert k in t2, f"缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


ENT = r"""**核实（我独立读权重 + 载入模型 + 读源码）**

| 来源 | `logit_scale` | `exp` |
|---|---|---|
| `models/clip-vit-base-patch32/pytorch_model.bin`（权重真值） | **4.605170** | **100.0000** |
| `CLIPModel.from_pretrained(...)` 载入后 | **4.605170250** | **100.0000** |
| `config.json::logit_scale_init_value` | 2.6592 | 14.2857 |
| **`tools/_p293_dinov2_hetero_strict.py::LOGIT_SCALE_INIT`**（硬编码） | **2.6592** | **14.2857** |

**`src/trainer.py:419`**：`logit_scale = self.model.logit_scale.exp()` → 论文各臂用**权重真值 exp = 100**
（**不是** config 写的 2.6592）。

→ **论文 run 的 logits 尺度 100 vs DINOv2 实验的 14.29 = 7.00×**

**归档无法佐证**（`tools/_p367`）：扫全部 `results.json` → **归档里没有任何 `logit_scale` 字段**
→ 无法从归档验证每次训练实际用的尺度（**这本身是可追溯性缺口**）。

**为什么这条比"归一化错配"更硬**

| 项 | 性质 |
|---|---|
| 图像归一化用 CLIP 统计量 | 喂给视觉塔的**输入分布**不同（预处理） |
| **`logit_scale` 不一致** | **目标函数本身不同**（InfoNCE 温度 100 vs 14.29） |

**影响面的边界（不要夸大）**

- ✅ **不影响**：ΔCG 的**定义**、DINOv2 **三臂之间**的横向比较（三臂同温）
- ❌ **影响**：把 DINOv2 的 ΔCG **与论文表的 ΔCG 并列**（含"落进 BioCLIP 区间 −0.29…−0.45"这一说法）

**处置**

1. 上游报告须写明**目标函数温度与论文不同（7×）**，其 ΔCG **只可用于三臂排序**，
   **不可与论文数值比较**。
2. 加入"未来工作/流程建议"：**实验记录必须落 `logit_scale` 等目标函数超参**
   （当前归档缺此字段，导致无法自查）。
3. **不改论文中的数字**——论文自身 run 用权重真值 100，内部一致；问题只在**跨实验可比性**。"""


if __name__ == "__main__":
    raise SystemExit(main())
