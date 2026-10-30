# -*- coding: utf-8 -*-
r"""落账：③a OpenCLIP 复现规律 + 可复现原则的落实（2026-10-07 深夜）。

    python tools\_docs_patchsize_3a.py [--apply]
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    v = json.loads(io.open(REPO / "outputs/analysis/patchsize_verdict.json",
                           encoding="utf-8").read()) if (REPO / "outputs/analysis/patchsize_verdict.json").exists() else {}
    oc = v.get("OpenCLIP B/32 (r4)", {})
    cg = oc.get("cg_delta", {})
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "③a OpenCLIP 复现 patch-size 规律" in t:
        print("  已记录，跳过")
        return 0
    ent = f"""> **🧪 2026-10-07 深夜 —— ③a OpenCLIP 复现 patch-size 规律（patch-32 组 2→3 个骨干）**
>
> 脚本：`experiments/strict_freeze_control.py --model models/openclip --rank 4`
> 判定：`tools/_p9_patchsize_verdict.py` → `outputs/analysis/patchsize_verdict.json`
>
> ### 结果（OpenCLIP B/32, rank 4, 严格冻结）
>
> | 臂 | CGΔ | 判定 |
> |---|---|---|
> | **text_only** | **{cg.get('text_only', float('nan')):+.4f}** | **最保护 ← 与 patch-32 预期一致** |
> | both | {cg.get('both', float('nan')):+.4f} | |
> | vision_only | {cg.get('vision_only', float('nan')):+.4f} | |
>
> **严格冻结硬校验通过**：`n_trainable` = 98,304 / 245,760 / 147,456
> —— 恰为 rank-8 口径（196,608 / 491,520 / 294,912）的**一半**，且仅 LoRA A/B 可训。
>
> ### 意义
>
> 论文的规律（*"every patch-32 backbone has the text-only arm at the smallest gap change"*）
> **在第三个 patch-32 骨干上复现** → patch-32 组由 **2 个增至 3 个**。
>
> ### ⚠️ 一处必须如实标注的差异
>
> OpenCLIP 的**三臂 CGΔ 全为正**（+0.080 / +0.086 / +0.102 = gap 全部变宽），
> 而 CLIP B/32 上 text-only 为**负**（−0.0465，gap 收窄）。
> **→ 规律复现的是"排序"（text-only 最保护），不是"符号"（是否收窄）。**
> **这限制了结论强度**：可以说"排序在同一 patch size 内稳固"，**不能说"text-only 总能收窄 gap"**。
>
> ### 队列状态
>
> | 序 | 实验 | 状态 |
> |---|---|---|
> | 1 | α 预测 | ✅ 完成（**结论无效**，需 `max_samples=5000` 重跑） |
> | 2 | **③a OpenCLIP B/32 r4** | ✅ **完成，规律复现** |
> | 3 | **③b CLIP B/16 r4** | ⏳ **运行中**（关键对照：同族、仅 patch size 不同） |
> | 4 | ④ Qwen2-VL | 无脚本 → 跳过 |
>
> ### 可复现原则的落实（同日）
>
> 已写入 `AGENTS.md`（最高优先级）：稿件每个数字必须**指名脚本 + 归档字段**；
> **无来源者一律删除**；**自动模糊匹配不算验证**（附假门禁教训）。
> 门禁：`tools/_claim_ledger.py` → **24/24 通过**。
> 据此已删 `supplement.tex` COCO 表**无来源的 12 行**（15 行 → 3 行，仅留归档中存在的配置）。
"""
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ent + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("③a OpenCLIP 复现", "98,304", "排序", "排序", "24/24"):
        if k == "排序":
            continue
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
