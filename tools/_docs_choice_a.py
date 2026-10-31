# -*- coding: utf-8 -*-
r"""落账：操作者选 A（让队列跑完）+ 云端问题的一句话总结（2026-10-09 18:10）。

    python tools\_docs_choice_a.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **▶️ 2026-10-09 18:10 —— 操作者选 **A**（让队列跑完）；云端问题一句话总结**
>
> ### 云端问题（**一句话**）
>
> > **云端的模型权重、数据、脚本、预处理我都逐项验证与本地完全一致，
> > 但那一套云端深度学习环境把 `batch → 模型` 这一段跑坏了
> > （`R@1 = 0.002`、loss 卡在 `ln(128)`、初始就区分不了正负样本对），
> > 所以我判它是**环境问题而不是数据集问题**——而根因我未能钉死，因此**放弃云端**。**
>
> **支撑（逐项实测）**：
>
> | 检查 | 结果 |
> |---|---|
> | `results.csv` md5 | `b12eb13ad488e50a`（两边相同） |
> | 前 1000 图 md5 | `045e29f159e02a31`（两边相同） |
> | `image_embeds_hash`（同图） | `−2.814`（两边相同） |
> | `effective_rank_init`（24 层） | ratio **全 1.0000** |
> | 随机图回退 | **0 条** |
> | **但 `R@1`** | **0.002**（本地 0.685） |
> | `Γ_m` 对照 | 视觉侧 0.34×/0.41×、文本侧 1.93×/2.41× → **同样不可用** |
>
> ### 操作者决定：**A —— 让本地队列跑完**
>
> | 项 | 状态 |
> |---|---|
> | 运行中 | `CLIP B/16 r4 / vision_only`（17:23 起） |
> | 剩余 | OpenCLIP `text_only`/`both`/`vision_only` × seed 123/456 → **≈5 h** |
> | 跑完自动接 | `Γ_m` 完整测量（已串联在驱动尾部） |
> | 中断保护 | **幂等**（已有 `results.json` 的 run 自动跳过） |
>
> ### 待办（队列跑完后）
>
> 1. 用 `_p75_new_seed_check.py` 复核**排序稳定性**（含 OpenCLIP 的 3 seed）；
> 2. **重算** OpenCLIP 的效应量（我先前"仅约 2 sd"用的参照量选错，见 2026-10-08 条目）；
> 3. 汇总 OpenCLIP 的 `text_only` 是否仍最保护；
> 4. 更新 `docs/PAPERA_REVIEWER_RISKS.md` 里 #1/#3 两条的状态。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "操作者选 **A**（让队列跑完）" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("操作者选 **A**（让队列跑完）", "环境问题而不是数据集问题",
              "重算** OpenCLIP 的效应量", "≈5 h"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
