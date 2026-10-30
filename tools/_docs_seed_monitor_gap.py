# -*- coding: utf-8 -*-
r"""落账：当前进度 + 驱动的一处**监控缺陷**（2026-10-09 11:00）。

    python tools\_docs_seed_monitor_gap.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📊 2026-10-09 11:00 —— 进度 19/27 run ｜ 发现驱动一处**监控缺陷****
>
> ### 进度
>
> | 骨干 | text_only | both | vision_only |
> |---|---|---|---|
> | CLIP B/32 r4 | 3/3 ✅ | 3/3 ✅ | 3/3 ✅ |
> | CLIP B/16 r4 | 3/3 ✅ | **2/3（跑中）** | 2/3 |
> | OpenCLIP r4 | 1/3 | 1/3 | 1/3 |
> | **合计** | | | **19/27 run** |
>
> **当前 run 确在推进**：`best_checkpoint.pt` 于 **09:32** 更新（非卡死）。
> `CLIP B/16 r4 / both` 自 02:56 起跑 **seed456**，已约 **2.5 h**（与 `both` 臂 55 min–3 h 的实测区间相符）。
>
> ### ⚠️ 驱动的监控缺陷（`tools/_p56_add_seeds.py`）
>
> 驱动用 `subprocess.run(capture_output=True)` 捕获训练 stdout →
> **输出只在子进程结束后才写入日志** →
> **运行期间看不到逐 epoch 进度，只能靠检查点文件的 mtime 推断是否卡死。**
>
> **这与昨夜过夜驱动的缺陷同类**（那次是"捕获在内存不落盘"）。
> **改进方向**（若日后再用）：改用 `Popen(stdout=文件)` 流式落盘，
> 或复用 `tools/_p20_serial_executor.py`（它已实现逐行落盘 + 超时杀进程组）。
>
> **本次不改**（队列正在跑，改脚本会影响在跑实例）；**记入文档供下次复用**。
>
> ### 后续（自动）
>
> 补 seed 跑完 → 自动接 **完整 `Γ_m` 测量** → 按操作者选 A **定 `Γ_m` 口径**。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "驱动一处**监控缺陷**" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("19/27 run", "监控缺陷", "best_checkpoint.pt` 于 **09:32**",
              "只能靠检查点文件的 mtime 推断"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
