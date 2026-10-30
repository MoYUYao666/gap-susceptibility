# -*- coding: utf-8 -*-
r"""落账：因共享资源占满而主动停机（2026-10-09 11:05）。

    python tools\_docs_share_release.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🛑 2026-10-09 11:05 —— 因**共享资源被占满**而主动停机（操作者告知）**
>
> ### 处置
>
> 操作者告知"专用共享都跑满了"。**核实：占满的正是本任务的训练**
> （7861 / 8188 MiB；`strict_freeze_control` 主进程 972 MB + **8 个 DataLoader worker**）。
> **→ 立即释放**：
>
> | 动作 | 结果 |
> |---|---|
> | 终止补 seed 驱动（精确命令行匹配） | PID 55932 ✅ |
> | 终止训练 | PID 40072 ✅ |
> | 清理 8 个 DataLoader worker 孤儿 | ✅ |
> | **释放后** | **python 进程 0 ｜ GPU 494 / 8188 MiB** |
>
> ### 停机时的进度（**已完成成果全部保留**）
>
> | 骨干 | text_only | both | vision_only |
> |---|---|---|---|
> | CLIP B/32 r4 | 3/3 ✅ | 3/3 ✅ | 3/3 ✅ |
> | CLIP B/16 r4 | 3/3 ✅ | **2/3** | 2/3 |
> | OpenCLIP r4 | 1/3 | 1/3 | 1/3 |
> | **合计** | | | **19 / 27 run** |
>
> **被中断的 run**：`CLIP B/16 r4 / both / seed456`（**未落盘 → 续跑会重跑它**，
> 这与"跳过已有结果"的幂等设计一致，不会产生半成品）。
>
> ### 续跑方式（幂等，一条命令）
>
> ```
> python tools\\_p56_add_seeds.py --apply
> ```
>
> ### ⚠️ 后续若在共享环境跑，须注意
>
> **本任务单 run 峰值约 7.9 GB**（8 GB 卡的 96%）→ **在共享/多人环境会直接占满**。
> **可能的缓解（未实施，供操作者决定）**：
> ① 降低 `--batch-size`（当前 128）→ 显存与时间同步下降；
> ② 用 `--max-samples` 缩小规模（但会改变与归档的可比性，**须谨慎**）；
> ③ 只在独占时段跑；④ 改用 `tools/_p20_serial_executor.py`（它按"等 GPU 空闲"设计并逐行落盘）。
>
> ### 已完成、不受影响的工作
>
> - **风险 #2**（`Γ_m` 在解码器 VLM）✅｜**风险 #5**（用 `Γ_m` 替代 `α`）✅；
> - **论文已改**：规律按预训练分组、COCO ODE 表撤回 + 边界、实验 ④ 写入（编译 53/39 页、门禁 40/40）；
> - **`Γ_m` 完整测量**（`tools/_p58_gamma_clip.py`，~10 min）**尚未跑**——需 GPU。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "因**共享资源被占满**而主动停机" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("因**共享资源被占满**而主动停机", "GRES", "494 / 8188 MiB", "19 / 27 run"):
        if k == "GRES":
            continue
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0Q." not in m:
        add = """
**0Q. 🛑 补 seed 因共享资源占满而停机（2026-10-09 11:05）**

- 占满的**正是本任务**（7861/8188 MiB，主进程 + 8 个 worker）→ 操作者告知后**立即释放**（python 进程 0、GPU 494 MiB）。
- **成果保留**：CLIP B/32 r4 三臂 **3/3**；CLIP B/16 r4 **3/2/2**；OpenCLIP r4 **1/1/1** → **19/27 run**。
- 被中断的 `CLIP B/16 r4 / both / seed456` **未落盘 → 续跑重跑**（幂等，无半成品）。
- **续跑**：`python tools\\_p56_add_seeds.py --apply`。
- ⚠️ **单 run 峰值约 7.9 GB**（8 GB 卡 96%）→ **共享环境会占满**。缓解选项：降 batch、缩样本、独占时段跑、或用 `_p20_serial_executor.py`（等 GPU 空闲 + 逐行落盘）。
- **仍需 GPU**：完整 `Γ_m` 测量（`tools/_p58_gamma_clip.py`，~10 min）。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
