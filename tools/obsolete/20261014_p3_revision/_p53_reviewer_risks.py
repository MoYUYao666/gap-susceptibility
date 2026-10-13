# -*- coding: utf-8 -*-
r"""审稿人质疑面清单：**逐条给出"是否已有证据/能否补"**（2026-10-08）。

## 做法（避免凭印象列清单）

对每一条候选局限，**先从论文实际文本与归档中确认它是否成立**，
再给"现有证据 / 可补的实验 / 成本"。

**三条来源**：
1. 论文自己已承认的 limitation（`discussion.tex` L24）；
2. 本阶段实测发现的边界（DG\* 不动、位置随数据集翻转、效应量异质）；
3. 方法层面（单 seed、规模、协议、超参）。

    python tools\_p53_reviewer_risks.py [--apply]
"""
from __future__ import annotations

import glob
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "PAPERA_REVIEWER_RISKS.md"


def main() -> int:
    apply = "--apply" in sys.argv
    dis = io.open(REPO / "paper合" / "sections" / "discussion.tex", encoding="utf-8").read()
    i = dis.find("Several limitations warrant discussion")
    j = dis.find("Several extensions follow")
    lim = " ".join(dis[i:j].split())

    print("=== 论文已承认的 limitation（逐条）===")
    for m in re.finditer(r"(First|Second|Third|Fourth|Fifth|Sixth|Seventh),", lim):
        s = lim[m.start():m.start() + 200]
        print(f"  • {s[:185]} …")
    print(f"\n  共 {len(re.findall(r'(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh),', lim))} 条")

    print("\n=== 归档可支撑的证据面 ===")
    counts = {
        "严格冻结 run（Flickr30k 各骨干）": len(glob.glob(
            str(REPO / "outputs/strict_freeze*/**/results.json"), recursive=True)),
        "COCO CG 口径 run": len(glob.glob(
            str(REPO / "outputs/coco_sweep/**/results.json"), recursive=True)),
        "ODE 轨迹（dg_star_history）": len(glob.glob(
            str(REPO / "outputs/theory/**/dg_star_history.json"), recursive=True)),
        "种子数（CLIP B/32 严格冻结）": len(glob.glob(
            str(REPO / "outputs/strict_freeze/both/seed*/results.json"))),
        "解码器 VLM 臂": len(glob.glob(
            str(REPO / "outputs/vlm_strictfreeze/*.json"))),
    }
    for k, v in counts.items():
        print(f"  {k:<38} {v}")

    if not apply:
        print("\n  （预演；加 --apply 写 docs/PAPERA_REVIEWER_RISKS.md）")
        return 0

    doc = f"""# Paper A 审稿人质疑面清单（2026-10-08）

> 生成脚本：`tools/_p53_reviewer_risks.py`。**每条都标"现有证据 / 可补 / 成本"。**
> 只列**会实质影响接受与否**的条目，不列修辞问题。

## A. 论文自己已承认的（{len(re.findall(r'(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh),', lim))} 条）

| # | 内容（摘要） | 状态 |
|---|---|---|
| 1 | 理论假设梯度流 + **轨迹平均耦合系数** | 已诚实标注；`cos=0.9977` 支持 |
| 2 | 覆盖对比式双塔 + **一个解码器 VLM** | ✅ **本阶段已补**（Qwen2-VL，含三点初步性说明） |
| 3 | `DG*` 作 Distribution Gap 的**可微代理**，无误差界 | 已标注 |
| 4 | **`DG*` 并非在所有配置下都移动**（COCO 严格冻结） | ✅ **本阶段已补**（含实测数字） |
| 5 | `α`、`β` 为**逐 run 拟合**，非由梯度预测 | 已标注；**α 预测实验 6 次未对齐** |
| 6 | 轨迹是原 sweep 的**子集**（55 LoRA run / 3 seed） | 已标注 |

## B. 本阶段实测新发现的边界

| # | 风险 | 现有证据 | 可补 | 成本 |
|---|---|---|---|---|
| **B1** | **"位置规律"曾被归因于 patch size，实测不成立** | 6 骨干 + **同秩对照**；已改为按预训练分组 | 已改稿 | 0 |
| **B2** | **最优位置随数据集翻转**（Flickr30k=text_only、COCO=both） | COCO 9 配置两臂齐备处 4/4 为 both | 补 `text_only` 缺的 3 个秩 | ~5 h |
| **B3** | **效应量异质**：OpenCLIP 相邻臂差异仅约 **2 sd** | 已写入表注 | 补 OpenCLIP 多 seed | ~3 h |
| **B4** | **COCO 的 `DG*` 在严格冻结下不动** → 该配置不适用 | 已写入 limitation 与补充说明 | 见 C1 | — |

## C. 方法层面（**审稿人最可能追问**）

| # | 风险 | 现状 | 可补 | 成本 |
|---|---|---|---|---|
| **C1** | **COCO 被撤回的 ODE 表** | 表已撤、原因已写 | **方案 A：用可训骨干协议重跑 9 个缺的配置**（r8 已有归档） | **~18 h** |
| **C2** | **严格冻结对照多为单 seed** | CLIP B/32 为 5 seed；其余新增为 1 seed | 三个骨干补 2 seed | ~4 h |
| **C3** | **解码器 VLM 为单模型、单 seed、规模小** | 已三点标注 | 补 seed / 补第二个 VLM（如 LLaVA） | 2–4 h；LLaVA 需下载 |
| **C4** | **`α` 预测未获答案** | 论文未声称可预测 | 方案 D（改报 `Γ_m`，不需时间积分） | ~1 h |
| **C5** | **4-bit 与 bf16 的差异未量化** | 论文表用 4-bit | **bf16 三臂正在跑** → 若排序一致则替换 | 进行中 |
| **C6** | **训练规模小**（400–5000 样本、3–10 epoch） | 用于测**排序方向**，非最终性能 | 无法在不增加数十小时的情况下解决；**应在文中明确"不报最终精度"** | 0 |
| **C7** | **`Γ_m`（梯度敏感性）未在解码器 VLM 上验证** | 论文核心量之一 | 在 Qwen 上测 `∇DG*` | ~1 h |

## D. 与其它稿件的关系（**编辑/审稿人会查重**）

| # | 风险 | 现状 |
|---|---|---|
| **D1** | 三篇 Elsevier 在投（P1@PR、Commentary@PRL、Paper A） | 封面信已如实披露三者关系 |
| **D2** | Commentary §3 首条 robust 结论与本稿摘要命题**同义** | Paper A 已加 `Placement Against Prior Work` 并引用 AdaLoRA/LoRA-GA/CLIP-LoRA；**但综述本身未引本稿**（操作者决定不改） |

## 建议的补实验优先级（按"质疑强度 / 成本"比）

1. **C1**（COCO ODE 表）—— 唯一"表被撤回"的硬伤，18 h，**已在执行**；
2. **C5**（bf16 vs 4-bit）—— **正在跑**，若一致即可去掉一个 caveat；
3. **C2**（多 seed）—— 4 h，直接回应"sanity of a single run"；
4. **C7**（`Γ_m` 在解码器 VLM 上）—— 1 h，补全"两大量都在新架构上验证"；
5. **B2/B3**（数据集翻转 + 效应量）—— 5 h / 3 h，加固而非救火。

## 现有证据规模（脚本实测）

"""
    for k, v in counts.items():
        doc += f"- {k}: **{v}**\n"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(doc)
    print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}（{len(doc.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
