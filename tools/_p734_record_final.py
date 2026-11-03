# -*- coding: utf-8 -*-
r"""Record the 222 -> 215 resolution and the .gitignore defect it uncovered.

    python tools/_p734_record_final.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔧 2026-10-15 00:30 —— 查清并修好 222 vs 215：根因是 `.gitignore` 裸规则误排除结果目录**
>
> ### 一、操作者指令
>
> > **"222 vs 215怎么回事，改对"**
>
> ### 二、🔴 根因（**不是计数口径问题，是归档缺口**）
>
> 台账口径：`glob("outputs/theory/**/dg_star_history.json")`（`tools/_p1_ledger.py`）。
>
> | | 数量 |
> |---|---|
> | 该 glob 在磁盘上匹配 | **96** |
> | **其中 git 已跟踪** | **87** |
> | **被排除未入库** | **9** |
>
> **被排除的 9 个全部是** `outputs/theory/coco/{coco_both_r8,coco_full_ft,coco_text_r8}/seed{42,123,456}/dg_star_history.json`。
>
> **原因**：`.gitignore` **L54 是裸规则 `coco/`** —— **无前导斜杠 ⇒ 匹配任意层级**，
> 于是把 **`outputs/theory/coco/`（结果数据）**也忽略了；而这条规则**本意是排除根目录的 MS-COCO 数据集**。
> （同理 `flickr30k/`、`data/`、`datasets/` 也是裸规则。）
>
> **⇒ 后果**：审稿人从公开仓库去数，只会得到 **87**（比磁盘 96 还少），**222 无论如何数不出来**。
>
> ### 三、✅ 修复
>
> | 动作 | 结果 |
> |---|---|
> | `.gitignore` 四条数据集规则**加前导斜杠锚定**（`coco/` → `/coco/` 等） | ✅ |
> | 锚定后**新暴露 113 个未跟踪文件** | 全部是 **JSON 结果数据**（`outputs/coco/` 17、`outputs/flickr30k` 60、`outputs/theory` 36），共 **0.14 MB**，**零违禁内容**（无权重/压缩包/日志/图片）⇒ **全部收录** |
> | 重新生成 `ode_ledger.json` | `n_runs_total = 96`（与磁盘一致） |
> | 提交并推送 | ✅ `2b48e40..e6f67dd  main -> main` |
>
> **远端核对**：`git ls-remote ssh-origin main` = **`e6f67dd`** ✅ ｜ 已跟踪文件 **2,060**（原 1,947）
> ｜ `outputs/theory/**` 下 `dg_star_history.json` = **96**（= 台账口径，可复现）
> ｜ `outputs/**` 下另有 `coco_sweep_dgstar/` 2 个，不属台账口径。
>
> ### 四、🔴 为什么仍是 215 而不是 222：**那 7 个拟合不可恢复**
>
> `outputs/analysis/ode_ledger.json` **仅有一个提交**（`7ee00598b`，2026-10-13），
> **入库时就已经是 96 个 run** ⇒ 2026-10-05 那次审计看到的 **103-run 版本从未进入仓库**。
> **⇒ 差的 7 个拟合不在归档中，无法找回。**
>
> ### 五、✅ 稿件已按归档支持的数字改写（`tools/_p733`）
>
> **现行逐源核算**（`outputs/analysis/alpha_stats_current.json`）：
>
> | 来源 | n | α<0 | 非负 |
> |---|---|---|---|
> | `ode_ledger.json` | 96 | 92 | 4 |
> | `ode_loco.json` | 33 | 32 | 1 |
> | `ode_loco2.json` | 33 | 32 | 1 |
> | `theory/adapter/adapter_all_results.json` | 50 | 40 | **10** |
> | `theory/bitfit/bitfit_results.json` | 3 | 0 | **3** |
> | **合计** | **215** | **196** | **19** |
>
> **关键**：**例外数 19 完全不变**，且最大例外 **+0.060828 → 稿件的 +0.061 ✅**。
> 变的只有总数（222→215）与负数（203→196），以及家族分解（Adapter 例外实测 **14** 而非 10）。
>
> **改写的位置（4 处，旧数字零残留）**：
>
> | 文件 | 旧 | 新 |
> |---|---|---|
> | `conclusion.tex` L9 | `$222$ fits … $\alpha<0$ in $203$ … ten of the fifty Adapter fits` | `$215$ … $196$ … fourteen of the fifty Adapter fits … four LoRA fits fitted leave-one-configuration-out` |
> | `validation.tex` L73 | `$203$ of the $222$ fits` | `$196$ of the $215$ fits` |
> | `validation.tex` L73 | `ten Adapter fits … four LoRA fits` | `fourteen Adapter fits … four leave-one-configuration-out LoRA fits` |
> | `validation.tex` L109 | `$203$ of the $222$ archived fits` | `$196$ of the $215$ archived fits` |
>
> **⚠️ 家族分解的口径说明**：`ode_loco*.json` 存的是 leave-one-configuration-out 拟合系数（1 例外各）。
> 为**不改变数值含义**，稿件写「four LoRA fits fitted leave-one-configuration-out」而非含糊的"four LoRA fits"。
>
> ### 六、✅ 重编译与同步
>
> | 检查 | 结果 |
> |---|---|
> | 编译 | **63 页 / 0 错误** |
> | 台账 | **PASS 21 ｜ GAP 0** |
> | 包内 Manuscript | `main_nc.pdf` → **927,235 字节** |
> | 源包 | `latex_source.zip` → **55 成员 / 1,989,677 字节** |
>
> ### 七、剩余
>
> ① 上传 `paper合/NC_submission/` ② 若操作者认为稿件应保留 222 的口径，
> 需指出那 7 个拟合在哪（我已确认不在仓库与磁盘）
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
    if "查清并修好 222 vs 215" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("查清并修好 222 vs 215", "无前导斜杠", "e6f67dd", "215", "196",
              "leave-one-configuration-out"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
