# -*- coding: utf-8 -*-
r"""落账：批次队列完成（30 成功/16 失败）+ COCO 路径 bug 的根因与修法（2026-10-11）。

    python tools\_docs_coco_bug.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔬 2026-10-11 13:27 —— 批次队列完成（成功 30 ｜ 失败 16）；COCO 路径 bug 已定位并修**
>
> ### 一、队列总结果（10-10 19:54 → 10-11 13:27，**17.5 h**）
>
> | 组 | 结果 |
> |---|---|
> | **OCLIP r4（12 run）** | ✅ **全成功**，批次已全 **128** |
> | **B/16 r4（8 run）** | ✅ **全成功**，批次已全 **128**（`both`/`vision_only` 单 run **2.2–2.6 h**） |
> | **B/32 r4（6 run）** | ✅ **全成功**（本就全 128，只补 seed） |
> | **COCO text_only（20 run）** | 🔴 **16 失败 + 4 错位**（见下） |
>
> ### 二、COCO 的失败根因（**我的队列传错路径**）
>
> `experiments/strict_freeze_control.py` 的输出路径是 **两层**：
> ```
> save_dir = "%s/%s/seed%d" % (OUT_DIR, tag, seed)
> ```
> 且 `--rank != 8` 时有**防污染校验**：`OUT_DIR` 必须含 `"r{rank}"` 子串，否则
> `raise SystemExit`（**rc=1**）。
>
> **我的队列传的是基础路径** `outputs/coco_sweep_text_only`：
> - `r2`/`r32`/`r64` → **校验拒绝**（7 秒 rc=1）→ **16 个失败**；
> - `r8` → 通过，但 **r8 时 `--name` 不改变 `tag`** → 结果**写进基础目录**
>   `OUT_DIR/text_only/seedN/` → **4 个错位结果**（10-11 11:46–12:22，batch=128）。
>
> ### 三、修法（`tools/_p172`）
>
> 1. **队列改传含 rank 的子目录**：`outputs/coco_sweep_text_only/r{rank}`
>    → 校验通过，落点与旧结构一致；
> 2. **错位结果改名保留证据**：`text_only/` → `text_only.MISPLACED_no_rank_segment/`
>    （**未删除**）；
> 3. **待补 20 run**（r2/r8/r32/r64 × 5 seed）→ 清单存 `outputs/analysis/coco_todo.json`。
>
> ### 四、COCO 修正驱动（`tools/_p173_coco_fix.py`）
>
> - **20 run**，`--batch-size 128`，`--out-dir .../r{rank}`
> - **逐 run 重试 2 次**——因为队列里 `r8/seed123` 曾遇
>   `torch.AcceleratorError: CUDA error: unknown error`，而队列**没有重试机制**
> - **判据以元数据为准**：文件存在**且 `batch_size == 128`** 才跳过
>
> **预计约 4.3 h**（r2 ~8 min/run、r8 ~10 min、r32/r64 ~13 min）。
>
> ### 五、接力**正确触发**（这是本链条的一个成功点）
>
> ```
> [13:30:11] 检测到队列完成：完成：成功 30 ｜ 失败 16
> [13:30:12] 仍有 1 个 strict_freeze 进程，等 60s     ← 防并发检查生效
> [13:31:13] 仍有 1 个 strict_freeze 进程，等 60s
> [13:32:14] 仍有 1 个 strict_freeze 进程，等 60s
> [13:33:14] ▶ 启动 VLM 13-seed
> ```
>
> **接力以日志标记为判据、并在启动前等待 CPU 上的残留进程退出**——设计按预期工作。
> 那个"残留进程"是我手动诊断 r2 时启动的（已终止），**接力正确地等它死了才启动**。
>
> ### 六、VLM 13-seed 进度
>
> | 时点 | 完成 |
> |---|---|
> | 13:33 启动 | 27/39（跳过已有 9 seed） |
> | 13:43 | **29/39** |
> | 预计 14:22 | 39/39 |
>
> ### 七、待办
>
> | # | 项 | 状态 |
> |---|---|---|
> | 1 | VLM 13-seed 跑完 | ▶ 进行中 |
> | 2 | **COCO 20 run 重跑**（`_p173`） | ⏸ 待 VLM 让出 GPU |
> | 3 | 重算全部表（批次已统一 + 5 seed） | 待 1、2 |
> | 4 | 同步台账 / 重编译 / 落账 | 待 3 |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "COCO 路径 bug 已定位并修" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("COCO 路径 bug 已定位并修", "成功 30 ｜ 失败 16", "MISPLACED_no_rank_segment",
              "17.5 h", "CUDA error: unknown error", "接力**正确触发**"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
