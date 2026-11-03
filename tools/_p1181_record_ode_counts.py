# -*- coding: utf-8 -*-
r"""Record the ODE-count reconciliation and the simplification pass.

    python tools/_p1181_record_ode_counts.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
MARK = "ODE 计数对账与简化"

ENT = """> **🧮 2026-10-17 22:20 —— ODE 计数对账（操作者选 A）＋ 全文去重简化**
>
> ### 一、162 个 ODE 拟合：**无法重跑**，已把能做的做实
>
> | 事实 | 数字 |
> |---|---|
> | `outputs/` 内 `dg_star_history.json` | **127** 个 |
> | 其中 ≥5 epoch（可拟合，与 `_p1_ledger.py` 同规则） | **111** 个 |
> | `outputs/theory/` 内（原台账口径） | **96** 个 |
> | 声称的 162 | **差 51 条轨迹从未归档**，配置与结果均不可恢复 |
>
> **已完成全量重拟**：`tools/_p1176_ode_fit_all.py`（**复用** `_p1_ledger.py` 的同一模型/网格/R²，非重写）
> ⇒ `outputs/analysis/ode_ledger_all.json`，**111 条逐 run 拟合**（96 theory + 15 散在 `flickr_rank`/`rank_rerun`/`coco_sweep_dgstar`）。
> 那 15 条含 R²=0.124 的低质量项、且疑为同批秩扫描的重跑副本 ⇒ **不并入正文验证集**，仅作归档佐证。
>
> ### 二、✅ 采用口径（A）：**96 条逐 run 拟合**
>
> | 统计 | 实测（`ode_ledger.json`）|
> |---|---|
> | 拟合总数 | **96**（55 LoRA + 30 Adapter + 11 full-FT）|
> | α<0 | **92/96** |
> | 例外 | **4 个，全为 Adapter**（最大 +0.011）|
> | LoRA α<0 | **55/55 全负** |
> | LoRA R² | mean **0.9486**（0.814–0.977）——与正文 0.949/0.814/0.977 完全一致 |
>
> ### 三、🧹 按操作者要求**去重简化**（原来四套数字互相矛盾）
>
> **改动前**：正文 8 处 "383 experiments"；分解 `221 + 162`（162 无归档）；`validation.tex` 2 处 **215 fits / 196 negative**；
> 结论里 **19 exceptions** 的混合枚举（14 Adapter + 4 LOCO + 3 BitFit）；6 处重复的 "55 LoRA runs (49 Flickr30k, 6 COCO)"。
> 其中 **215 的来源是 `alpha_stats_current.json` 把 5 份归档相加**：ledger 96 + LOCO 33 + **LOCO2 33（同一批 33 重复计）** + Adapter 50 + BitFit 3
> ⇒ 既重复计数、又与原逐 run 拟合不是同一人群。
>
> **改动后（唯一口径）**：
>
> | 位置 | 现在写的 |
> |---|---|
> | 结论 + 验证节（各 1 次）| **317 experiments** = 221 目录 + 96 ODE 拟合 |
> | 摘要 / 引言 / 实证节 | **删掉总数**，只留 "six backbones / three adaptation methods" |
> | α 符号 | **92 of the 96**，例外 **4 个全为 Adapter**（只出现 1 次）|
> | 补充 A 节 | **96 ODE-fitting runs（55 LoRA + 30 Adapter + 11 full-FT）** ← 唯一写构成的地方 |
> | "55 LoRA（49 Flickr30k, 6 COCO）" | 只在 `validation.tex` 拟合描述处保留 |
>
> 另修掉 `empirical.tex` 把 383 当成"catalogued runs"的第三处矛盾（目录实为 221）⇒ 改为不写数字。
>
> ### 四、重建与门禁
>
> | 项 | 结果 |
> |---|---|
> | `main_nc.pdf` | **68 页**（简化后 −1）；0 错误 / 0 未定义 / 0 Overfull |
> | `main_springer.pdf` | **49 页**；同上 |
> | `NC_submission/` | 已刷新：`Manuscript.pdf` **68 页**、源码包 45 文件、**独立编译 68 页一致** |
> | 台账 | **76/76 PASS，0 GAP**（新增 5 条 ODE 断言：96 / 92 / 4 / 例外全 Adapter / 317=221+96）|
>
> ### 五、诚实边界
>
> - **51 条轨迹确实不存在**，本轮的"重跑"只能覆盖 111 条；正文改用 96 口径后，**每个数字都可现场复现**；
> - 旧的 `alpha_stats_current.json`（215/196/19）**未删**，作为历史保留，台账注释已标明作废原因；
> - 若将来要恢复 162 规模，只能重做缺失训练实验，且**配置需重新界定**——不建议在投稿前做。
>
> **脚本**：`_p1175`（轨迹清点）｜`_p1176`（全量重拟）｜`_p1179`（简化改写）｜`_p1180`（台账重指）｜`_p1181`（本条）。
>

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK not in hp:
        i = hp.find("# 项目交接文档")
        j = hp.find("\n", i)
        hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)
        print("  handoff entry added")
    mp = io.open(MAP, encoding="utf-8").read()
    row = ("61. 🧮 **ODE 计数对账 + 去重简化（2026-10-17 22:20，操作者选 A）** —— **162 无法重跑**（归档只有 127 个轨迹、"
           "111 个 ≥5 epoch；**差 51 条从未归档**）；已完成全量重拟 `ode_ledger_all.json`（111 条，96 theory + 15 别处）。"
           "正文改用 **96 条逐 run 拟合**：96 fits / **92 α<0** / 4 例外全 Adapter / LoRA 55 全负 / LoRA R² 0.9486(0.814–0.977)。"
           "**去重**：383→**317**（=221+96）只在结论+验证节各 1 次；摘要/引言/实证删数；删 `215/196/19` 混合口径"
           "（其源 `alpha_stats_current.json` 把 LOCO 33 重复计）；补充 A 唯一写构成 **96（55 LoRA+30 Adapter+11 full-FT）**。"
           "NC **68 页** / Springer **49 页**（0/0/0）；投稿包 68 页独立编译一致；台账 **76/76 / 0 GAP**。"
           "详见 `HANDOFF.md` 22:20 条目。\n")
    if "ODE 计数对账 + 去重简化" not in mp:
        anchor = "60. 📚 **补 4 条模型引用"
        idx = mp.find(anchor)
        if idx >= 0:
            end = mp.find("\n", idx)
            mp = mp[: end + 1] + row + mp[end + 1:]
            io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
            print("  map item added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
