# -*- coding: utf-8 -*-
r"""落账「Paper A 与 PRL 综述的区别 + 重叠风险」（2026-10-07）。

交付件：`docs/PAPERA_VS_COMMENTARY.md`（由 write 工具写出）。本脚本做 HANDOFF/文件地图同步 + 断言。

    python tools\_docs_paperA_vs_commentary.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = r"""> **⚖️ 2026-10-07 —— Paper A 与 PRL 综述的区别（操作者问）｜**发现一处实质重叠 + 同出版商风险****
>
> **交付件**：`docs/PAPERA_VS_COMMENTARY.md`（逐项实测对比）。
>
> ### 一句话结论
>
> **两篇是"主张"与"证据"的关系，不是重复。**
>
> | | PRL 综述（Commentary，在审 `-02402`） | Paper A（`paper合/`） |
> |---|---|---|
> | 体裁 | **批判性综述** | **原创研究** |
> | 材料 | **已发表文献** | **自己的 383 个实验** |
> | 做什么 | **论证领域把问题问错了**（where vs how 两个正交决策被混为一谈） | **测量该问题 + 梯度流理论**（Gap Susceptibility、ODE R²=0.986） |
> | 产出 | **报告清单** | **设计准则**（选最小有效秩；text-only 的"保护性"是架构属性） |
>
> ### 主题交集（词频实测，支持"不重复"）
>
> 综述全文里：**`modality gap` 0 次 ｜ `retrieval` 0 次 ｜ `centroid` 0 次 ｜ `Distribution Gap` 0 次 ｜ `gradient flow` 0 次**
> → **Paper A 的研究对象在综述里根本不出现。**
>
> ### ⚠️ 但有一处**实质重叠**，必须处理
>
> 综述 `main_prl.tex:159` 第一条 robust 结论：
> *"**site dominates allocation** … **which site is trainable matters more than how a budget is divided within it**"*
> Paper A 摘要：*"**which part of the model is adapted matters more than how its adapters are configured**"*
> **→ 同一个命题。** 区别在依据：综述是**文献归纳**，Paper A 是**自己的 204 个实验 + 推导**。
> **且两篇互不引用** → 若都发表，同一作者两处主张同一命题而不互引，**易被读成自我重复**。
>
> ### ⚠️⚠️ 同出版商风险
>
> | 稿件 | 出版商 | 状态 |
> |---|---|---|
> | 综述 `-02402` | **Elsevier**（PRL） | Under Review |
> | P1 `PR-D-26-10149` | **Elsevier**（Pattern Recognition） | Decision in Process |
> | **Paper A → CVIU/ESWA** | **Elsevier** | 待投 |
>
> **→ 同一作者在 Elsevier 旗下将同时有三个相关稿件在审/将投**，须在封面信如实披露三者关系。
>
> ### ✅ 建议（最要紧的一条）
>
> **两篇互相引用**——**对双方都有利**：
> ① **综述 → Paper A**：其首条 robust 结论目前**只有文献归纳**；加上"并由直接实验证实"可把
> *"appear robust"* 升级为 **"confirmed by controlled experiment"**；
> ② **Paper A → 综述**：其"位置 > 配置"目前是**自己的新发现**；引用综述可定位为
> **"独立文献调查也支持"** → **削弱"孤证"质疑**。
> 两稿都还在审/未投，**改动成本低**（综述若需改动，按其刊修订规则处理）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    vp = REPO / "docs" / "PAPERA_VS_COMMENTARY.md"
    assert vp.exists(), "交付件不存在"
    vt = io.open(vp, encoding="utf-8").read()
    for k in ("modality gap", "site dominates allocation", "同出版商", "互相引用", "局限"):
        assert k in vt, f"交付件缺 {k}"

    hp = REPO / "HANDOFF.md"
    h = io.open(hp, encoding="utf-8").read()
    if "Paper A 与 PRL 综述的区别" not in h:
        anchor = "> **🔎 2026-10-07 —— 选项 3"
        i = h.find(anchor)
        assert i > 0, "未找到 HANDOFF 锚点"
        io.open(hp, "w", encoding="utf-8", newline="").write(h[:i] + ENT + "\n" + h[i:])
        h2 = io.open(hp, encoding="utf-8").read()
        for k in ("PAPERA_VS_COMMENTARY.md", "site dominates allocation", "互相引用", "同出版商"):
            assert k in h2, f"HANDOFF 断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(h2.splitlines())} 行）")

    fp = REPO / "文件地图.md"
    t = io.open(fp, encoding="utf-8").read()
    if "PAPERA_VS_COMMENTARY" not in t:
        old = "## 七、当前真正待办（按优先级）"
        new = ("## 七、当前真正待办（按优先级）\n\n"
               "0. 🆕 **Paper A 与 PRL 综述的关系** → `docs/PAPERA_VS_COMMENTARY.md`：\n"
               "   **两篇是「主张 vs 证据」的关系（核心词汇零交集）**；但综述 §3 首条 robust 结论\n"
               "   *site dominates allocation* 与 **Paper A 摘要的「位置比配置更重要」是同一命题**，\n"
               "   且**两篇互不引用** → **建议两篇互相引用**（对双方都更有力）。\n"
               "   另：综述（PRL）、P1（PR）、Paper A（CVIU/ESWA）**同属 Elsevier**，\n"
               "   **封面信须如实披露三者关系**。\n")
        assert old in t, "文件地图锚点未命中"
        io.open(fp, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
        t2 = io.open(fp, encoding="utf-8").read()
        assert "PAPERA_VS_COMMENTARY" in t2
        print(f"  ✅ 文件地图.md 已加待办 0（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
