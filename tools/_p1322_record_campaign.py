# -*- coding: utf-8 -*-
r"""Record the real fine-tuning campaign and the per-epoch margin-monitor result.

    python tools/_p1322_record_campaign.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
WHICH = REPO / "哪篇是哪篇.md"
AUTO = REPO / "AUTOMATION_HANDOVER.md"
MIRROR = REPO / "tools" / "_p1284_prepare_public_mirror.py"
NOVDOC = REPO / "docs" / "A1_NOVELTY_STEP1_2026-10-18.md"

NOVSEC = """

---

## 第 18 步（2026-10-19 01:30）：真实微调 campaign + margin 质量逐 epoch 监控器，A1 **58 页**，台账 **157/157**

### 实验

`tools/_p1319_realfinetune_campaign.py`：CLIP ViT-B/32 + LoRA，**18 个真实微调 run**（3 个本地分类数据集 × 2 个干预变体
〔仅文本塔 / 两塔〕× 3 个种子 × 4 epoch），每个 epoch 在**固定 5,000 图 ImageNet-5k holdout** 上评迁移，记录
top-1、CG、$M(0.01)$、$M(0.02)$、$\\tau_5$。

**结果**：72 个真实 checkpoint，CG 跨 0.464–0.768、top-1 跨 5.68–57.36%。

### 证据 1：真实微调的匹配对（不再是合成）

- $|\\Delta\\mathrm{CG}|\\le0.03$ 的匹配对 **670 对**（$\\le0.01$ 有 254 对）；
- 最宽跨 run 对：**48.5 点 @ $\\Delta$CG=0.0242**（DTD/both ep3 8.9% vs Food-101/text ep1 57.4%），
  paired bootstrap 95% CI 绝对值 **[47.0, 50.0]**；
- 最宽**同 run 内**对：**19.6 点 @ $\\Delta$CG=0.0125**（同数据、同种子、仅 epoch 不同），CI **[18.4, 20.9]**；
- ⇒ 真实微调的 dissociation 不小于合成（稀疏 32.7），与加密扫描（50.6）同量级。

### 证据 2：margin 质量作逐 epoch 监控器

跨 72 个 checkpoint：CG 相关 **+0.577**（符号与合成族相反！）、$\\tau_5$ **+0.987**、$M(0.01)$ **−0.987**、$M(0.02)$ −0.908。

逐 run 选 epoch（18 个 run，oracle 均值 47.8%）：**min $M(0.01)$ regret 0.06 点**、$\\tau$ regret 0.0、
min-CG regret **5.65**、训到最后一轮 regret **13.8**（最差 29.4）。

⇒ 证书不仅能诊断，**可以直接当早停/选型规则**；同时 CG 在两个真实族间**变号**，再次说明它不能当指标。

### 入稿

- §realpairs 增 campaign 段 + `tab:campaign`（跨 run/同 run 两组极端匹配对 + CI）；
- 对决表 `tab:showdown` 增"real fine-tuning"列，并补 CG 变号的警示句；
- 原"轨迹不可比"段替换为 campaign 逐 epoch 监控结果；
- 选择表 `tab:selection` 增 18 个真实 run 的 epoch 选择行；
- 摘要中"6.6 点真实配对"改为"72 个真实 LoRA checkpoint、最宽 48.5 点 @ 0.024"（摘要 **249 词**，≤250）。

A1 **58 页**、0/0/0；三台账 **157/157、96/96、76/76**；审计 `a1_paa` READY/A。
"""

ENT = """> **🏋️ 2026-10-19 01:30 —— 真实微调 campaign（18 runs / 72 ckpt / 670 匹配对）+ margin 质量逐 epoch 监控，A1 **58 页**，台账 **157/157**
>
> **实验**：CLIP B/32 + LoRA，3 数据集 × 2 变体（仅文本塔 / 两塔）× 3 种子 × 4 epoch，每 epoch 在固定 5,000 图
> ImageNet-5k 上评迁移（`_p1319`）。共 **72 个真实 checkpoint**，CG 0.464–0.768、top-1 5.68–57.36%。
>
> **真实匹配对**：$|\\Delta$CG|≤0.03 有 **670 对**；最宽跨 run **48.5 点 @ 0.0242**（CI [47.0, 50.0]）；最宽**同 run 内**
> **19.6 点 @ 0.0125**（CI [18.4, 20.9]）——真实微调的 dissociation 与加密合成扫描同量级。
>
> **逐 epoch 监控**：跨 checkpoint $M(0.01)$ 相关 **−0.987**（CG 仅 +0.577，且**符号翻转**）；逐 run 选 epoch：
> min-$M$ regret **0.06** 点、τ 0.0、min-CG **5.65**、训到末轮 **13.8**（最差 29.4）。
>
> 入稿：campaign 段 + `tab:campaign`、对决表加 real 列、替换"轨迹不可比"段、选择表加真实 run 行、摘要更新（**249 词**）。
> 三台账 **157/157、96/96、76/76**；审计 **READY grade A：pass=61 fail=0 warn=0**。
>

"""

MIRROR_ADD = '''    "outputs/analysis/a1_campaign.json",
    "outputs/analysis/a1_campaign_analysis.json",
    "tools/_p1319_realfinetune_campaign.py",
    "tools/_p1320_campaign_analysis.py",
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    n = io.open(NOVDOC, encoding="utf-8").read()
    if "第 18 步" not in n:
        io.open(NOVDOC, "w", encoding="utf-8", newline="").write(n.rstrip("\n") + NOVSEC)
        print("  novelty doc appended")
    h = io.open(HANDOFF, encoding="utf-8").read()
    if "真实微调 campaign" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + ENT.replace("\\n", "\n") + h[j + 1:])
        print("  handoff added")
    w = io.open(WHICH, encoding="utf-8").read()
    old = "主定理 + 对决表 + 选择规则** | 58 + 1 title page |"
    new = "主定理 + 对决表 + 选择规则 + 真实 campaign** | 58 + 1 title page |"
    print(f"  which row: {w.count(old)}")
    if w.count(old) == 1:
        io.open(WHICH, "w", encoding="utf-8", newline="").write(w.replace(old, new, 1))
    au = io.open(AUTO, encoding="utf-8").read()
    au2 = au.replace("**A1 claim ledger 139/139**", "**A1 claim ledger 157/157**")
    if au2 != au:
        io.open(AUTO, "w", encoding="utf-8", newline="").write(au2)
        print("  automation updated")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("96. 🏋️ **真实微调 campaign + 逐 epoch 监控（2026-10-19 01:30）** —— 18 runs × 4 epoch = **72 个真实 checkpoint**；"
           "$|\\Delta$CG|≤0.03 有 **670 对**，最宽 **48.5 点 @ 0.0242**（CI [47.0,50.0]），同 run 内 **19.6 点 @ 0.0125**；"
           "$M(0.01)$ 跨 checkpoint 相关 **−0.987**（CG +0.577，**符号翻转**）；min-$M$ 选 epoch regret **0.06** vs 训到末轮 **13.8**。"
           "A1 **58 页**、台账 **157/157**、审计 READY/A。\\n")
    if "真实微调 campaign + 逐 epoch 监控" not in m:
        anchor = "95. ➕ **四项强化"
        idx = m.find(anchor)
        if idx >= 0:
            end = m.find("\n", idx)
            io.open(MAP, "w", encoding="utf-8", newline="").write(m[: end + 1] + row + m[end + 1:])
            print("  map row added")
    mm = io.open(MIRROR, encoding="utf-8").read()
    if "a1_campaign.json" not in mm:
        anchor = '    "outputs/analysis/a1_margin_mass.json",'
        assert mm.count(anchor) == 1
        mm = mm.replace(anchor, anchor + "\n" + MIRROR_ADD.rstrip("\n"), 1)
        io.open(MIRROR, "w", encoding="utf-8", newline="").write(mm)
        print("  mirror staging list extended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
