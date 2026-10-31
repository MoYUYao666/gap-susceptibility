# -*- coding: utf-8 -*-
r"""落账：拟合 vs 预测的实证核查 + **归档完整性问题**（2026-10-07）。

## 做了什么

按操作者"都做"的指示，跑两项：

| # | 实验 | 状态 |
|---|---|---|
| **1** | **从梯度预测 α**（`tools/_p2_alpha_from_gradients.py`） | ⏳ 后台运行中 |
| **2** | **留一配置交叉验证**（`tools/_p1_ode_loco.py`、`_p1_ode_loco2.py`、`_p1_ode_r2_caliber.py`、`_p1_archive_completeness.py`） | ✅ 完成 |

## 实验 2 的结果

### ① 我第一版的方法有错，已自我修正

`_p1_ode_loco.py` 把 **LoRA / Adapter / full-FT 混在一个池**里做 LOCO，特征仅用 $DG^*_0$ →
平均 R² = **−1.680**、corr(α̂, α_fit) = **0.120**。

**但这个结果不可采信**：跨**方法**外推本来就该失败（Adapter 的 $d$ 与 LoRA 的 $r$ 不同量纲）。
`_p1_ode_loco2.py` **限定在 LoRA 族内（18 配置）**重做：

| 口径 | 平均 R² | 中位 R² | corr(α̂, α_fit) |
|---|---|---|---|
| 混方法池（**已弃**） | −1.680 | 0.576 | 0.120 |
| **LoRA 族内（采信）** | **+0.7446** | **0.9520** | **0.640** |

**→ 同族内 ODE 系数可外推；跨族不可外推（且本不该期望能）。**

### ② 🔴 **发现归档完整性问题（严重，必须先解决）**

正文声称（`validation.tex:30`、`conclusion.tex:9`）：

> "We fit the ODE on **162 experiments（81 per dataset）** … 81 runs total（14 配置 × 5 seeds + frozen + full-FT）"

**但 `outputs/theory/` 里实际只有 96 个 `dg_star_history.json` run**：

| 目录 | runs | 正文声称 |
|---|---|---|
| `v1_trajectory`（Flickr30k） | **46** | 81 |
| `coco` | **9**（3 配置 × 3 seeds） | 81（14 配置 × 5 seeds + 5+5） |
| `beta_pilot` | 9 | — |
| `adapter` | 30 | — |
| `verify_accum` | 2 | — |
| **合计** | **96** | **162** |

**差额 66 runs。**

### ③ 由此**复现不出正文的 R²**

| 口径 | 本地实测 | 正文 |
|---|---|---|
| LoRA 全部（55 runs） | **0.9486** | 0.985–0.986 |
| LoRA + Flickr30k（43 runs） | 0.9530 | 0.985 ± 0.008（81 runs） |
| LoRA + COCO（6 runs） | 0.9032 | 0.971 ± 0.007（81 runs） |
| 全部 96 runs | 0.8583 | — |

**逐秩对照**（`validation.tex:61-66`，Flickr30k both 位）：

| 秩 | 正文 R² | 本地实测（n=3） |
|---|---|---|
| r=2 | 0.975 | **0.937** |
| r=64 | 0.981 | **0.938** |

**→ 本地归档不足以复现正文的 0.985–0.986。**

## 这为什么重要（两个独立后果）

| # | 后果 | 严重性 |
|---|---|---|
| **A** | **可复现性**：正文的 ODE 拟合数字**无法从 `outputs/` 复现**——这与本项目"每个数字有可核来源"的硬规则冲突 | 🔴 高 |
| **B** | **我的结论受限**：LOCO 建在**较小且拟合口径不同**的子集上 → 只能作为**方向性**证据，不能当成正文数字的替代 | 🟡 中 |

**可能的原因（不选边）**：
1. 正文的 162 runs **未全部归档**（COCO 的 14×5 只归档了 3×3）；
2. 正文用了**不同拟合口径**（逐 run vs 种子均值；或含 OpenCLIP/SigLIP）；
3. 正文的 run 计数含**未落盘**的中间产物。

**注**：我**没有发现任何编造迹象**——96 个 run 的数据都在、都能拟合，只是**数量与正文声称不符**。

## 下一步（建议）

1. **等实验 1 跑完**（从梯度预测 α），它**不依赖归档完整性**，结论独立成立；
2. **查清 162 的来源**——需要找回 COCO 的 14×5 与 Flickr30k 的 81 原始轨迹，
   或**把正文的 run 计数与 R² 改为与归档一致**（后者是可立即执行的诚实选项）；
3. **在正文中如实标注**拟合口径（逐 run / 种子均值）与本地可复现的范围。

    python tools\_docs_fit_vs_predict.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0

    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    ent = r"""> **🔬 2026-10-07 —— 拟合 vs 预测核查 + 🔴 发现**归档完整性问题****
>
> 按操作者"都做"执行两项：① 从梯度预测 α（⏳ 后台跑）② 留一配置交叉验证（✅ 完成）。
> 脚本：`tools/_p1_ode_loco.py`、`_p1_ode_loco2.py`、`_p1_ode_r2_caliber.py`、
> `_p1_archive_completeness.py`、`_p2_alpha_from_gradients.py`。
>
> ### ① 我的第一版方法有错，已自我修正
>
> `_p1_ode_loco.py` 把 **LoRA / Adapter / full-FT 混池**做 LOCO → 平均 R²=**−1.680**、corr=**0.120**。
> **不可采信**（跨方法外推本就不该成功）。`_p1_ode_loco2.py` **限定 LoRA 族（18 配置）**：
>
> | 口径 | 平均 R² | 中位 | corr(α̂, α_fit) |
> |---|---|---|---|
> | 混池（已弃） | −1.680 | 0.576 | 0.120 |
> | **LoRA 族内（采信）** | **+0.7446** | **0.9520** | **0.640** |
>
> **→ 同族内 ODE 系数可外推；跨族不可（且本不该期望能）。**
>
> ### ② 🔴 归档完整性问题（**必须先解决**）
>
> 正文（`validation.tex:30`）称 **162 experiments（81 per dataset，14 配置 × 5 seeds + frozen + full-FT）**，
> 但 `outputs/theory/` 实际只有 **96 个 run**：
>
> | 目录 | 实测 | 正文 |
> |---|---|---|
> | `v1_trajectory`（Flickr30k） | **46** | 81 |
> | `coco` | **9**（3 配置 × 3 seeds） | 81（14 配置 × 5 seeds + 5 + 5） |
> | 其它（beta_pilot 9 / adapter 30 / verify_accum 2） | 41 | — |
> | **合计** | **96** | **162**（差 **66**） |
>
> **由此复现不出正文的 R²**：
>
> | 口径 | 本地 | 正文 |
> |---|---|---|
> | LoRA 全部（55） | **0.9486** | 0.985–0.986 |
> | LoRA + Flickr30k（43） | 0.9530 | 0.985 ± 0.008（81 runs） |
> | LoRA + COCO（6） | 0.9032 | 0.971 ± 0.007（81 runs） |
>
> 逐秩（Flickr30k both 位）：正文 r=2→**0.975**／r=64→**0.981**；本地实测 **0.937／0.938**。
>
> ### 为什么重要（两个独立后果）
>
> | # | 后果 |
> |---|---|
> | **A** | **可复现性**：正文 ODE 拟合数字**无法从 `outputs/` 复现**——与"每个数字有可核来源"的硬规则冲突 |
> | **B** | **我的结论受限**：LOCO 建在较小且口径不同的子集上 → 仅作**方向性**证据 |
>
> **可能原因（不选边）**：① 162 runs 未全部归档；② 正文用了不同拟合口径（逐 run vs 种子均值，
> 或含 OpenCLIP/SigLIP）；③ 计数含未落盘的中间产物。
> **⚠️ 未发现任何编造迹象**——96 个 run 的数据都在、都能拟合，只是**数量与正文声称不符**。
>
> ### 下一步
>
> 1. 等实验 1（从梯度预测 α，**不依赖归档完整性**）；
> 2. **查清 162 的来源**，或**把正文的 run 计数与 R² 改为与归档一致**（可立即执行的诚实选项）；
> 3. 正文中**如实标注拟合口径**（逐 run / 种子均值）与可复现范围。
"""
    if "归档完整性问题" not in h:
        anchor = "> **✉️ 2026-10-07 —— Paper A 封面信已起草（操作者要求）**"
        i = h.find(anchor)
        if i < 0:
            anchor = "> **✅ 2026-10-07 —— `site dominates allocation`"
            i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ent + "\n" + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("归档完整性问题", "0.9486", "162", "96", "未发现任何编造迹象"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")

    fp = REPO / "文件地图.md"
    t = io.open(fp, encoding="utf-8").read()
    if "归档完整性" not in t:
        old = "## 七、当前真正待办（按优先级）\n"
        new = (old + "\n"
               "0a. 🔴 **Paper A 归档完整性问题（2026-10-07 发现）**：正文称 ODE 拟合跨 "
               "**162 runs（81/数据集）**，但 `outputs/theory/` 只有 **96 个 run**（Flickr30k 46、"
               "COCO 9），差额 **66**；由此**复现不出正文的 R²=0.985–0.986**（本地 LoRA 全部 55 runs 实测 "
               "**0.9486**）。**两个出口**：① 找回缺失轨迹；② **把正文的 run 计数与 R² 改为与归档一致**。\n"
               "   证据：`tools/_p1_archive_completeness.py`、`_p1_ode_r2_caliber.py`；详见 `HANDOFF.md` 同日条目。\n")
        io.open(fp, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
        t2 = io.open(fp, encoding="utf-8").read()
        assert "归档完整性问题" in t2
        print(f"  ✅ 文件地图.md 已加待办 0a（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
