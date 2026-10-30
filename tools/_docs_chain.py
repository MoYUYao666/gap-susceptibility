# -*- coding: utf-8 -*-
r"""落账：批次修正队列在跑 + VLM 13-seed 接力已挂（2026-10-10 晚）。

    python tools\_docs_chain.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **⛓️ 2026-10-10 晚 —— 夜跑链条：批次修正队列（46 run）→ 完成后自动接 VLM 13-seed**
>
> ### 一、操作者指令
>
> > **"所有的跑完之后 VLM 就跑 11-13 seed"**
>
> ### 二、链条设计（**串行，单卡铁律**）
>
> | 阶段 | 内容 | run | 状态 |
> |---|---|---|---|
> | **①** | `tools/_p169_batchfix_queue.py`：批次统一到 **128** + 补到 5 seed | **46** | ▶ **20:00 起跑** |
> | **②** | `tools/_p171_chain_vlm13.py`：**轮询** ①的完成标记，出现后启动 VLM | — | ▶ **已挂起等待** |
> | **③** | `tools/_p156_vlm_bf16_seeds.py`：VLM 补到 **13 seed** | 12 | 待 ② 触发 |
>
> **判据以日志为准**（`完成：成功 N ｜ 失败 M`），**不以 rc 为准**——
> 本会话已吃过"rc=0 但什么都没做"的教训（见"静默跳过"条目）。
> **启动前再查一次没有 `strict_freeze` 进程**，防并发。
>
> ### 三、① 的进度（截至 21:14，已跑 72 分钟）
>
> **12/46 完成**：
> - ✅ **P1 OCLIP r4 全部 12 run**（重跑 seed123/456 + 补 789/1011，三臂）
>   - 重跑耗时 335–401 s（正常）；旧文件已改名 `results.batch64.bak` 留证
> - ▶ P2 B/16 r4 起跑（`text_only/seed789`）
>
> **剩余估算**：
>
> | 阶段 | run | 预计 |
> |---|---|---|
> | B/16（`both`/`vision_only` 单 run 近 2 h） | 8 | **~8.5 h** |
> | COCO text_only（~10 min/run） | 19 | ~3.2 h |
> | B/32 r4（~6–25 min） | 6 | ~1.5 h |
> | **合计** | 34 | **~13 h** → 约 **次日 10:00** |
>
> ### 四、跑完要做的（不待指令）
>
> | # | 项 |
> |---|---|
> | 1 | 重算"数据集翻转"表（批次已统一）+ 严格冻结表（5 seed） |
> | 2 | 同步门禁台账（`_claim_ledger.py`） |
> | 3 | 重编译 Springer / NC（现 40 / 56 页） |
> | 4 | VLM 13-seed 数字写进论文 `tab:vlm`（现为 5 seed） |
> | 5 | 落账 + 提交 |
>
> ### 五、VLM 的 seed 轨迹（供参考）
>
> | seed 数 | `text_only` | `both` | `vision_only` | `text_only` vs `vision_only` |
> |---|---|---|---|---|
> | 1 | — | — | — | — |
> | 3 | $+66.8\\pm6.5\\%$ | $+85.2\\pm11.2\\%$ | $+12.4\\pm4.7\\%$ | $4.9$ sd |
> | 5 | $+67.4\\pm7.3\\%$ | $+86.5\\pm8.1\\%$ | $+15.8\\pm10.4\\%$ | $1.18$ sd |
> | **9** | $+82.0\\pm8.5\\%$ | $+88.0\\pm6.4\\%$ | $+18.0\\pm8.0\\%$ | **$2.01$ sd（显著）** |
> | 13 | 待跑 | 待跑 | 待跑 | 待跑 |
>
> **注意 `text_only` 的均值随 seed 数漂移较大**（66.8 → 67.4 → 82.0），
> 因为 seed 456 与 2323 等给出极高的相对变化（95.3%）；**13 seed 会进一步稳定它**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "夜跑链条" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("夜跑链条", "13 h", "2.01", "results.batch64.bak", "不以 rc 为准"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
