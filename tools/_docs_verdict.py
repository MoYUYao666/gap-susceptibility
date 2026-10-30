# -*- coding: utf-8 -*-
r"""落账：同秩对照**判定**（2026-10-08 10:00）—— 本阶段最重要的结论。

    python tools\_docs_verdict.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🎯 2026-10-08 10:00 —— 同秩对照判定：**patch size 不是决定因素；决定因素指向预训练****
>
> ### 判决（`tools/_p25_samerank_verdict.py` → `outputs/analysis/samerank_verdict.json`）
>
> **在相同 rank（r4）、相同协议（严格冻结 5000 样本）、相同样本量下**：
>
> | 骨干 | patch | text_only | both | vision_only | 最保护 |
> |---|---|---|---|---|---|
> | **CLIP B/32 @ r4** | 32 | **−0.0297** | −0.0186 | +0.0124 | **text_only** |
> | **CLIP B/16 @ r4** | 16 | **−0.0190** | +0.0150 | +0.0433 | **text_only** |
>
> **→ 同秩下两者最保护臂相同（都是 text_only）。patch size 不影响排序。**
>
> ### 叠加其它证据
>
> | 骨干 | patch | **预训练** | 最保护 | rank |
> |---|---|---|---|---|
> | CLIP B/32 | 32 | WIT | text_only | 8（5 seed） |
> | CLIP B/32 | 32 | WIT | text_only | **4** |
> | **CLIP B/16** | **16** | **WIT** | **text_only** | **4** |
> | OpenCLIP B/32 | 32 | LAION | text_only | 4 |
> | SigLIP B/16 | 16 | **WebLI（sigmoid）** | **both** | 8（5 seed） |
> | BioCLIP B/16 | 16 | **生物域** | **both** | 4（3 seed） |
>
> **→ 四个「text_only 最保护」的骨干全部是**对比式图像-文本预训练**（WIT ×3 + LAION ×1）；
> 两个「both 最保护」的骨干**都不是**（SigLIP 用 sigmoid 目标、BioCLIP 为生物域）。**
>
> **结论：排序跟的是**预训练目标/语料**，不是 patch size。**
> 论文原文 *"every patch-16 backbone puts both there"* **被证伪**。
>
> ### ⚠️ 效应量异质，结论须按最弱处表述（**我修正了自己上一版的错误说法**）
>
> 上一版 HANDOFF 我写"差异约为 sd 的 11 倍"——那是用 **0.0030**（CLIP B/32 r8 的 `text_only` sd）
> 去除 **B/16 的 0.034**。**这个算法不严谨**（单 seed 对照 vs 另一配置的 sd）。
> **逐项核对后**：
>
> | 骨干 | 相邻臂差异 | 差异/sd（参照 0.0030） |
> |---|---|---|
> | CLIP B/32 @ r8（5 seed 实测 sd=**0.0030**） | 0.0207 | 4.48 |
> | CLIP B/32 @ r4 | 0.0111 | 3.68 |
> | CLIP B/16 @ r4 | 0.0340 | 11.28 |
> | **OpenCLIP @ r4** | **0.0062** | **2.06** ← **最弱** |
>
> **→ 必须说清**：**方向在 4 个配置上完全一致**（都 text_only 最保护），
> **但效应量异质**，其中 **OpenCLIP 仅约 2 sd** ——单看它不足以判定。
> **稳健的是"方向一致性"（4/4），不是"每个配置都显著"。**
>
> ### 论文改法（**待操作者确认**）
>
> | 选项 | 改法 |
> |---|---|
> | **①按预训练分组** | 把规律从"patch size 决定"改为"**对比式图文预训练（WIT/LAION）→ text_only 最保护；其它目标（sigmoid/生物域）→ both**" |
> | ②仅收窄 | 保留 patch size 说法但加"在 CLIP 系内不成立"的 caveat |
> | ③撤回 | 删去规律，只报告各骨干的实测排序 |
>
> **我倾向①**：它**由 6 个配置支持**（4 text_only + 2 both），且**给出了机制性解释**
> （对比式目标下文本侧适配更保对齐；非对比目标下需要两侧同时适配）。
> **但这是新主张，须在文中标明其证据为 6 个骨干的观察，并列出 OpenCLIP 效应最弱这一点。**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "同秩对照判定：patch size 不是决定因素" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("patch size 不是决定因素", "−0.0297", "预训练目标/语料", "仅约 2 sd",
              "我修正了自己上一版的错误说法"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
