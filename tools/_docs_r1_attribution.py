# -*- coding: utf-8 -*-
r"""落账：`tab:position_strict` 的 R@1 列三类归因 + 两格无来源（2026-10-12）。

    python tools\_docs_r1_attribution.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔴 2026-10-12（续）—— `tab:position_strict` 的 **R@1 列**查实三类归因；**2 格在归档中无来源**
>
> ### 结论（`tools/_p325`、`_p326`、`_p327`，均为**独立读归档重算**，非转述）
>
> | 类 | 格 | 归档出处 | 判定 |
> |---|---|---|---|
> | **① 同一行两半来自不同配置** | OpenCLIP 行三格 **R@1**（0.643 / 0.680 / 0.672） | **`strict_freeze_openclip`**（**rank 8**，n_tr = 196,608 / 491,520 / 294,912，seeds …**1024**） | 🔴 该行 **ΔCG** 却来自 **`strict_freeze_oclip/r4`**（**rank 4**，n_tr = 98,304 / 245,760 / 147,456，seeds …**1011**）→ **两半不是同一配置** |
> | **② 取自非严格冻结** | `CLIP B/32† text_only = 0.621` | **`outputs/flickr30k_seeds/rq2_text_only`**，5-seed 均值 **0.6210**，`n_trainable = **145,170,177**` | 🔴 严格冻结表这一格用了**非严格冻结**那批；该格严格冻结值是 **0.6222**（n_tr = **98,304**） |
> | **③ 无来源** | `CLIP B/16† text_only = **0.651**` | 94 个 n≥3 组中**一个都不命中** | 🔴 **无出处** |
> | **③ 无来源（附条件）** | `CLIP B/32† both = **0.679**` | 唯一命中者是 `strict_freeze_rank/r4/both` 的 **3-seed 子集**（42/123/456，n_tr=245,760，均值 **0.679667**） | 🔴 非本行所报的 **5-seed 单元** |
>
> **ΔCG 列 12/12 在 4 位小数上精确可复现**，且**表的论证用的是 ΔCG 列**。
>
> ### 归因的正确写法（供 response letter 用）
>
> > ΔCG 12/12 可复现；R@1 列 **6 格可复现**，**3 格来自另一 rank 的归档**（OpenCLIP 行），
> > **1 格来自非严格冻结的归档**（CLIP B/32† text_only），
> > **2 格在现有归档中找不到来源**（CLIP B/32† both = 0.679、CLIP B/16† text_only = 0.651）。
>
> ### 我自己的两个错（均已修）
>
> 1. **第一版 caption 归因不准**：写成"4 格差 ≤0.0064、可能来自丢失的 seed 集"——
>    实际是"两棵树混用 + 旧约定 + 2 格无来源"，**性质更严重**，不能笼统成"漂移"。
> 2. **第二版 caption 又错一处**：写"0.679 没有任何组命中"——
>    实际 `strict_freeze_rank/r4/both` 的 **3-seed 子集命中**（0.679667→0.679）。
>    已改为精确表述（`_p328`）。**这是本阶段我第三次因"扫描粒度/未穷举"而下错结论。**
> 3. 我第一版容差扫描按到 `seed*/results.json` 分组 → 每组 1 个 run → 报"0 个 n≥3 的组"。
>    **正确粒度是到 arm 为止的路径**（`outputs/<top>/<…>/<arm>`）。已修（`_p326`）。
>
> ### 稿中处置（已编译、已提交 `c7bc920`）
>
> `tab:position_strict` 的 caption 现**逐条披露**：ΔCG 精确可复现；OpenCLIP 三格的 rank 不一致；
> `0.621` 那格取自非严格冻结；两格标注"在发表精度下无法从归档复现"，
> 并**逐个给出重算值**（0.6366 / 0.6818 / 0.6698 / 0.6222 / 0.6796 / 0.6502）。
> 承诺"给出重算值"后**必须兑现**，否则就是承诺落空。
>
> ### 同批另查实的隐患（task-8 成员发现，我已系统核查）
>
> `strict_freeze_control.py` 默认 `target_modules=["q_proj","v_proj"]`，而 **DINOv2 的层名是
> `query`/`value`/`key`** → 默认值在 DINOv2 上**一个 LoRA 层都注不进去**（静默假实验）。
> **我实例化全部 backbone 读 state_dict 核查**（`tools/_p310`）：CLIP B/32、B/16、SigLIP、
> OpenCLIP **全部兼容**（`q_proj`/`v_proj` 各 ×24），**只有 DINOv2 不匹配**。
> **并扫论文归档**（`tools/_p309`，502 个含可训参数量字段的文件）：真注入计数
> 196,608（×25）/ 294,912（×30）/ 491,520（×18）；12 个 `n_trainable_params = 0`
> **全部是 `*_frozen` 冻结基线** → **论文归档无此问题**。
>
> ### 状态
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | `main_nc` | **60** | 0 | 0 | 0 |
> | `main_springer` | **44** | 0 | 0 | 0 |
> | 投稿包 | **60** | 0 | 0 | — |
>
> **仍在跑**：task-7（更低 lr + 补 seed，GPU 占用中）｜task-8（DINOv2 等 GPU；
> LLaVA-7B 实测 bf16 权重 **13.157 GiB > 8 GiB** 显存 → 本地不可行）
"""


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "R@1 列**查实三类归因" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("R@1 列**查实三类归因", "145,170,177", "0.679667", "rank 8",
              "0.6502", "查实三类归因"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
