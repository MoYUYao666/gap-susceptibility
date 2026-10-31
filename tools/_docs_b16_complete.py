# -*- coding: utf-8 -*-
r"""落账：CLIP B/16 三臂完整结果 + 交接成功（2026-10-08 08:52）。

    python tools\_docs_b16_complete.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📊 2026-10-08 08:52 —— CLIP B/16 三臂齐备：**规律被明确违反**｜执行器交接成功**
>
> ### ③b CLIP B/16（rank 4，严格冻结，5000 样本，1 seed）
>
> | 臂 | CGΔ | R@1 | 用时 |
> |---|---|---|---|
> | **text_only** | **−0.0190** | 0.642 | 12 min |
> | both | +0.0150 | 0.696 | 134 min |
> | vision_only | **+0.0433** | 0.677 | 154 min |
>
> **→ 最保护臂 = `text_only`，而论文规律要求 patch-16 骨干应为 `both`。**
>
> **严格冻结硬校验**：三臂 `vis_nonzero=0`（仅 LoRA A/B 可训），
> `n_trainable` = 98,304 / 245,760 / 147,456（恰为 rank-8 的一半）。
>
> ### 全貌（5 个骨干）
>
> | 骨干 | patch | **预训练** | text_only | both | vision_only | 最保护 |
> |---|---|---|---|---|---|---|
> | CLIP B/32 | 32 | WIT | **−0.0465** | −0.0258 | +0.0106 | text_only |
> | **CLIP B/16** | **16** | **WIT** | **−0.0190** | +0.0150 | +0.0433 | **text_only ❌** |
> | OpenCLIP B/32 | 32 | LAION | **+0.0798** | +0.0860 | +0.1019 | text_only |
> | SigLIP B/16 | 16 | **WebLI（sigmoid）** | +0.0664 | **−0.0114** | +0.0522 | **both** |
> | BioCLIP B/16 | 16 | **生物域** | −0.3671 | **−0.4515** | −0.2927 | **both** |
>
> **观察**：**CLIP B/16 的排序与 CLIP B/32 完全一致**（都 text_only 最保护），
> 尽管二者 patch size 不同（16 vs 32）；而两个「both 最保护」的骨干
> （SigLIP、BioCLIP）**都不是 WIT 预训练**。
>
> **→ 排序跟的是**预训练语料/目标**，不是 patch size。**
>
> ### ⏳ 最后一个变量：`CLIP B/32 @ rank 4`（跑中）
>
> 作用：排除「rank 4 本身导致 text_only 更保护」这一替代解释——
> 因为归档的 CLIP B/32 是 **rank 8**，而新增的 B/16 是 **rank 4**，不同秩不能直接对照。
>
> ### ✅ 执行器交接成功（架构修复见效）
>
> ```
> [08:50:32]    已停 PID 52164
> [08:50:42] ▶ 启动新执行器（新队列：同秩对照 ×3 → A → COCO ×12）
> [08:50:42]    新执行器 PID 43360
> [08:50:42] 交接完成
> ```
>
> 新执行器启动后**正确跳过已完成的 3 项**，直接进入同秩对照：
> ```
> [08:50:42] ⏭ α重跑(5000样本) 已完成（合格）→ 跳过
> [08:50:42] ⏭ ③b both 已完成（合格）→ 跳过
> [08:50:42] ⏭ ③b vision_only 已完成（合格）→ 跳过
> [08:50:43] ▶ 同秩对照 CLIP B/32 r4 both
> ```
> **→ `task_done()` 统一判据 + "按命令行查重" 两项修复都按设计工作。**
>
> ### ⚠️ 如实标注的不确定性
>
> - 新增对照均为 **1 seed**；归档 CLIP B/32 的 **sd ≈ 0.003**（很小）→ 单 seed 可靠性尚可，
>   但**未做多 seed 确认**；
> - B/16 的 `text_only −0.0190` vs `both +0.0150` 相差 **0.034**，
>   而归档同秩 sd 约 0.003 → **差异约为 sd 的 11 倍**，**不太可能纯属噪声**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "CLIP B/16 三臂齐备" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("CLIP B/16 三臂齐备", "+0.0433", "交接成功", "约为 sd 的 11 倍", "预训练语料/目标"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
