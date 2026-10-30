# -*- coding: utf-8 -*-
r"""落账：**COCO + 严格冻结下 `DG*` 框架失效**（2026-10-08 18:50）——本阶段最重要的发现。

    python tools\_docs_dgstar_failure.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴🔴 2026-10-08 18:50 —— 「COCO + 严格冻结」下 **`DG*` 框架失效**（已停队列，止损 ~20 h）**
>
> ### 实测证据（`tools/_p39_verify_dgstar_failure.py`）
>
> | 数据集（**严格冻结**） | `dg*`/`cg` **跨度比** | `dg*` R² | `cg` R² |
> |---|---|---|---|
> | **COCO（新跑）** seed42 | **0.055** | **0.679** | 0.931 |
> | **COCO（新跑）** seed123 | **0.030** | **0.124** | 0.927 |
> | **Flickr30k（归档）** seed42 | **1.568** | 0.957 | 0.874 |
> | **Flickr30k（归档）** seed123 | **1.215** | 0.956 | 0.902 |
>
> **→ 在 COCO + 严格冻结下，"配对嵌入距离"几乎不动（0.0032–0.0061），
> 而质心间隙正常收窄（0.108–0.111）。Flickr30k 上两者同步（比值 1.2–1.6）。**
>
> ### 解释（与检索性能自洽）
>
> COCO 上严格冻结后 **R@1 只有 0.12**（Flickr30k 为 0.62–0.70）
> —— **模型并未真正把配对的图文对拉近**；它只是让**两个模态的质心**靠近了。
> **质心靠近 ≠ 配对对齐。** 这正是 `DG*` 不动的物理含义。
>
> ### 一个必须区分的混淆
>
> 归档的 COCO `dg_star` 轨迹（跨度 0.082–0.101）来自 **`outputs/theory/coco/`**，
> 而那批 run 记 `n_trainable_params = 145,170,177` → **非严格冻结**（解锁整个骨干）。
> **→ 框架此前是在"骨干可训"的 COCO 上验证的；在严格冻结下不成立。**
>
> ### 这对论文意味着什么（**须谨慎，暂不改稿**）
>
> `DG*` 是论文 ODE 与"Visual Fragility"叙事的**状态变量**。本发现说明：
> **该框架的适用条件比论文所述更窄**——至少在 COCO 上，
> 只有当骨干也参与训练（模型真正移动）时 `DG*` 才是有信息的量。
>
> **可能的处置（待操作者定）**：
> 1. 在 limitation 明说：`DG*` 在"冻结骨干 + 低检索性能"的配置下不移动，ODE 拟合无意义；
> 2. 或把 COCO 的 ODE 表改用 **`CG`** 口径（`cg` R² 0.93，健康）并注明与 Flickr30k 不同量；
> 3. 或**不补 COCO 的 ODE 表**，只报告位置排序（CGΔ，已有 31 run）。
>
> ### 队列已停（止损）
>
> 新跑只完成 **2 / 36** run 即停 → **节省约 20 h GPU**。
> 旧跑 31 run 的 **CG 口径数据完整可用**（跨度与 R² 均健康，见上表①）。
>
> ### 本节自错计数
>
> 我在启动这个 36-run 队列前**没有先验证"`DG*` 在该配置下是否真的会动"**
> ——若先花 10 分钟在 1 个 run 上看轨迹，就能避免排入 24 h 的队列。
> **这与"α 实验四次未对齐"同属一类：先开跑，后验证量是否可测。**
> **→ 对策④：任何长队列开跑前，先跑 1 个 run 并检查目标量是否有足够动态范围。**
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "「COCO + 严格冻结」下" in t and "DG*` 框架失效" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("DG*` 框架失效", "0.030", "1.568", "质心靠近 ≠ 配对对齐",
              "节省约 20 h", "对策④"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")

    mp = REPO / "文件地图.md"
    m = io.open(mp, encoding="utf-8").read()
    if "0L." not in m:
        add = """
**0L. 🔴 COCO + 严格冻结下 `DG*` 框架失效（2026-10-08 18:50）—— 队列已停，止损 20 h**

- **实测**：COCO 严格冻结的 `dg*`/`cg` 跨度比 **0.030–0.055**（Flickr30k 为 **1.2–1.6**）；
  `dg*` 拟合 R² **0.124 / 0.679**，而同 run 的 `cg` R² **0.927 / 0.931**。
- **含义**：模型只让**质心**靠近，未真正拉近**配对**——与 COCO 的 R@1 仅 0.12 自洽。
- **混淆须区分**：归档 COCO 的 `dg_star`（跨度 0.08–0.10）来自 **非严格冻结** run（1.45 亿参数）
  → **框架此前在"骨干可训"的 COCO 上验证，严格冻结下不成立**。
- **可能处置**（待定）：① limitation 明说适用条件；② COCO 表改用 `CG` 口径；③ 只报位置排序，不补 ODE 表。
- 证据：`tools/_p39_verify_dgstar_failure.py`、`outputs/coco_sweep_dgstar/`（2 run）、`outputs/coco_sweep/`（31 run）。

"""
        anchor = "## 七、当前真正待办（按优先级）\n"
        m2 = m.replace(anchor, anchor + add, 1)
        io.open(mp, "w", encoding="utf-8", newline="").write(m2)
        print(f"  ✅ 文件地图.md 已更新（{len(m2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
