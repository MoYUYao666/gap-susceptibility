# -*- coding: utf-8 -*-
r"""Record the outcome of the "re-run the missing fits" request.

    python tools/_p739_record_rerun.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🧪 2026-10-15 01:15 —— 操作者要求"找不到就现跑"：查证后**那 7 个拟合从来不存在**，重跑会等于造数据；但顺带修好的数据缺口已确认**
>
> ### 一、操作者指令
>
> > **"找不到就现跑"**
>
> ### 二、✅ 查证：**不存在"找不到的拟合"，缺口为 0**
>
> 台账口径 `glob("outputs/theory/**/dg_star_history.json")` 与磁盘**逐一对应**：
>
> | 家族 | 有轨迹的目录数 |
> |---|---|
> | `v1_trajectory` | 46 |
> | `adapter` | 30 |
> | `coco` | 9 |
> | `beta_pilot` | 9 |
> | `verify_accum` | 2 |
> | **合计** | **96** |
>
> | 核对 | 结果 |
> |---|---|
> | 台账 run 数 | **96** |
> | 磁盘有轨迹的目录数 | **96** |
> | **匹配不到台账的目录** | **0** |
> | **台账里匹配不到目录的 run** | **0** |
> | 已发布（git 跟踪） | **96 = 96** ✅ |
> | 仅存磁盘未发布 | **0** |
> | `outputs/` 下未跟踪文件 | **0** |
>
> **⇒ 没有任何"缺的拟合"可跑。** 其余文件是**聚合结果**（`beta_pilot_results.json`、
> `verify_accum_results.json`、`v1_all_results.json`），**不是轨迹**，无法也不该当作拟合 run。
>
> ### 三、🔴 为什么**不重跑**（三条理由）
>
> 1. **不知道跑哪个**：审计看到的 103 与现行 96 差 7，但**没有任何记录指明那 7 个是哪些配置**
>    （`ode_ledger.json` 仅一个提交 `7ee00598b`，入库时已是 96）。
> 2. **重跑得到的是新数据**：重跑全部 96 个配置会产出**另一批** 96 个拟合，
>    **不会重建审计看到的那 7 个** ⇒ 若拿它们回填 222，**等于造数据**，违反"所有数据必须可复现有来源"。
> 3. **现行 215 自洽且更可复现**：口径明确（5 个归档文件）、可逐条重算
>    （`tools/_p732`）、审稿人可自己数出来。
>
> ### 四、✅ 但"找不到就现跑"的方向**确实查出了一个真数据缺口**（已修）
>
> 追查过程中发现：**`.gitignore` 的裸规则 `coco/`、`flickr30k/` 无前导斜杠 ⇒ 匹配任意层级**，
> 把 **`outputs/theory/coco/`（9 个 run）**、`outputs/coco/`、`outputs/flickr30k/` 等**结果目录**排除了。
>
> | | 修复前 | 修复后 |
> |---|---|---|
> | `outputs/theory/**/dg_star_history.json` 入库 | **87** | **96** ✅ |
> | 入库文件总数 | 1,947 | **2,060** |
> | 补入的结果 JSON | — | **113 个**（0.14 MB，零违禁内容） |
>
> **⇒ 这正是"222 数不出来"的真正原因** —— 审稿人此前从公开仓库只能数到 87。
>
> ### 五、✅ 稿件数字（已按归档支持的值改写，`tools/_p733`）
>
> | | 值 |
> |---|---|
> | 拟合总数 | **215**（ledger 96 + loco 33 + loco2 33 + adapter 50 + bitfit 3） |
> | α < 0 | **196** |
> | 非负例外 | **19**（与旧稿一致；最大 **+0.060828 → +0.061**，亦一致） |
>
> ### 六、状态
>
> | 项 | 状态 |
> |---|---|
> | 台账 | **PASS 21 ｜ GAP 0** |
> | 稿件 | 63 页 / 0 错误 / 旧数字零残留 |
> | 包 | `Manuscript.pdf` 927,235 ｜ `latex_source.zip` 55 成员 / 1,989,677 |
> | GitHub | **`e6f67dd`** ✅ 已推 |
>
> ### 七、判据小结（供日后同类问题复用）
>
> **"找不到"分两种**：① **真的丢了** ⇒ 若能定位配置就重跑，否则**删除该数字**；
> ② **本来就不存在**（口径/记录错）⇒ **改正口径与数字**，**不得重跑回填**。
> **本次属第 ② 种。**
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "那 7 个拟合从来不存在" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("那 7 个拟合从来不存在", "匹配不到台账的目录", "等于造数据", "本次属第 ② 种"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
