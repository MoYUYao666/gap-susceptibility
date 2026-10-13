# -*- coding: utf-8 -*-
r"""落账：按 B 统一口径，COCO 重跑并记录 DG*（2026-10-08 17:20）。

    python tools\_docs_coco_dgstar.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔁 2026-10-08 17:20 —— 按 B（统一口径）COCO 重跑，记录 **`DG*`****
>
> ### 操作者决定：B（统一口径，而非接受 `centroid_gap` 口径）
>
> 论文 ODE 的**理论状态变量是 `DG*`**（配对均方距离 `(1/N)Σ‖z_I−z_T‖²`），
> 而此前 COCO 补跑只记了 `centroid_gap`/`distribution_gap`
> （`gap_history.json`，7 个 epoch 点）——**`DG*` 无法从现有字段恢复**。
> **→ 重跑 36 run，启用 `DG*` 记录。**
>
> ### 关键发现：一行即可启用（`src/trainer.py:923`）
>
> **`train()` 自己会写 `dg_star_history.json`**，前提是 `_record_dg_star=True`
> （由 `trainer.enable_dg_star_tracking()` 置位）。
> 归档的 96 个 `dg_star_history.json` 就是 `experiments/theory/v1_rank_sweep.py:134` 这么来的。
>
> **→ 给协议脚本加 `--dg-star` 开关（默认关，不影响既有用法）**，脚本 `tools/_p35_add_dg_star_flag.py`。
>
> ### ✅ 已验证（`--smoke`，512 样本 1 epoch，最小代价）
>
> ```
> [dg-star] 已启用逐 epoch DG* 记录 → dg_star_history.json
> dg_star_history.json 键: ['cg', 'dg_empirical', 'dg_star', 'epochs']   ← 与归档结构完全一致
> dg_star = 1.3798（与 frozen 基线 1.3761 一致 ✅）
> ```
>
> ### 队列调整（两处，都是为了不浪费 GPU）
>
> | 调整 | 原因 |
> |---|---|
> | **旧口径 COCO 任务从队列移除** | 写 `outputs/coco_sweep/`（**无 `dg_star`**）→ 对论文的表无用。**已完成的 31/36 产物保留在盘上作对照** |
> | **实验 A 移到 COCO-DG\\* 之后** | A 四次未对齐、需先修学习率，若排在前面会白耗 ~10 min 再失败；COCO-DG\\* 是操作者选定的口径统一任务，**应优先拿到确定产出** |
>
> ### 运行状态
>
> ```
> [17:17:58] ▶ COCO-DG* both r=4  日志 COCO-DG_both_r_4.log
> Epoch 1: 98%|█████████▊| 39/40 [01:00<00:00, 1.53it/s, loss=0.1000]
> GPU: 7541 MiB / 8188 MiB, 94%
> ```
>
> **写入 `outputs/coco_sweep_dgstar/`**（新目录 → ① 保留旧 36 run 作对照；② 避免跳过逻辑按旧 `results.json` 误判）。
>
> ### 成本与产出
>
> - **12 配置 × 3 seed = 36 run**，单 run 约 40 min（含 DG\\* 的额外验证前向）→ **约 24 h**；
> - **产出**：每个 run 同时得到 `results.json` **与** `dg_star_history.json`（与正文同口径）→
>   **可替换 `tab:coco_ode` 为真正的 `DG*` 拟合**，口径与 Flickr30k 完全一致。
>
> ### 清掉的临时产物
>
> `outputs/_dgstar_smoke/`、`outputs/strict_freeze_smoke/`（冒烟测试残留）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "按 B（统一口径）COCO 重跑" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("按 B（统一口径）COCO 重跑", "trainer.py:923", "1.3798",
              "与归档结构完全一致", "outputs/coco_sweep_dgstar/"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0K." not in m:
        add = """
**0K. 🔁 COCO 按 B 统一口径重跑（记录 DG\\*，2026-10-08 17:20）**

- **操作者选 B**：论文 ODE 的状态变量是 `DG*`，此前 COCO 只记了 `centroid_gap` → **重跑 36 run**。
- **一行启用**：`trainer.enable_dg_star_tracking()` → `train()` 自写 `dg_star_history.json`（`src/trainer.py:923`）。
- **已加 `--dg-star` 开关**（默认关）；**冒烟已验证**结构一致、`dg_star=1.3798` 与 frozen 基线相符。
- **写入 `outputs/coco_sweep_dgstar/`**（保留旧 36 run 作对照，写新目录避免跳过逻辑误判）。
- 30 run × 3 seed = **36 run、约 24 h**；完成后即可替换 `tab:coco_ode` 为**真正的 `DG*` 拟合**。
- 脚本：`tools/_p35_add_dg_star_flag.py`、`tools/_p36_drop_old_coco_tasks.py`。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
