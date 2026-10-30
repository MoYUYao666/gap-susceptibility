# -*- coding: utf-8 -*-
r"""落账：`tab:position_strict` 全格溯源 + R@1 漂移披露（2026-10-12）。

    python tools\_docs_strict_provenance.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔍 2026-10-12（续）—— `tab:position_strict` 全 12 格溯源完成；发现「归档重名」并披露 R@1 漂移**
>
> ### 触发
>
> task-8 成员（model-coverage）报"R@1 列 5/12 复现不出论文值"。**我独立复核，结论更精确。**
>
> ### 根因：归档的 `experiment` 字段**不足以唯一标识 run**
>
> | 目录 | n_trainable（三臂） | text_only ΔCG |
> |---|---|---|
> | **`outputs/strict_freeze_oclip/r4`** ← **论文用的是这个** | 98,304 / 245,760 / 147,456 | **+0.0802** 🎯 |
> | `outputs/strict_freeze_openclip` | 196,608 / 491,520 / 294,912 | +0.0694 |
>
> **两套 OpenCLIP 共用同样的 `experiment` 名**（`strict_text_only` / `strict_both` /
> `strict_vision_only`）。同样地，**`strict_both` 这一个名字下有 7 种参数量**
> （61,440 … 3,932,160），`strict_text_only` 也有 7 种。
> → **"按 experiment 名取均值重算"这个方法本身不成立**，必然混池。
> 成员得到 0.6366 正是两套的混合值。
>
> ### 逐格对标（`tools/_p322_strict_final_match.py`）
>
> | 行 | 归档目录 | ΔCG | R@1 |
> |---|---|---|---|
> | CLIP B/32 (WIT) | `strict_freeze` | ✅ 3/3 | ✅ 3/3 |
> | OpenCLIP B/32 (LAION) | `strict_freeze_oclip/r4` | ✅ 3/3 | ⚠️ 3/3 漂移（+0.0064 / −0.0018 / −0.0022） |
> | CLIP B/32† (r4) | `strict_freeze_b32_r4` | ✅ 3/3 | ⚠️ 2/3 漂移（+0.0012 / +0.0006） |
> | CLIP B/16† (r4) | `strict_freeze_b16/r4` | ✅ 3/3 | ⚠️ 1/3 漂移（−0.0008） |
>
> **ΔCG 列 12/12 精确复现**（4 位小数）；**R@1 列 6/12 精确**，
> 其余 6 格漂移 **0.0006–0.0064**，最大是 **OpenCLIP text-only：发表 0.643 vs 归档 5-seed 均值 0.6366**。
>
> **并已排除**：查 `results.json` 里**全部**召回字段
> （`R@1` / `R@1_i2t` / `R@1_t2i` / `R@5*` / `R@10*`），**没有任何字段的 5-seed 均值能命中 0.643**
> → 该值可能来自**现已无法重建的 seed 集**。
>
> ### 处置（按"每个数字要有来源"铁律）
>
> **在 `tab:position_strict` 的 caption 中如实披露**（`tools/_p324`）：ΔCG 12 格精确可复现；
> R@1 有 4 格与重算均值最多差 0.0064（点名 OpenCLIP text-only 的 0.643 vs 0.6366）；
> 说明为何**标注差异而非改数**——归档 `experiment` 字段区分不开那两套 OpenCLIP。
>
> ### 顺带查实的另一个真隐患（task-8 成员发现）
>
> `strict_freeze_control.py` 默认 `target_modules=["q_proj","v_proj"]`，
> 而 **DINOv2 的层名是 `query`/`value`/`key`** → 用默认值在 DINOv2 上**一个 LoRA 层都注不进去**，
> 静默变成假实验。**我系统核查了论文用到的全部 backbone**（`tools/_p310`，实例化模型读 state_dict）：
>
> | backbone | `q_proj`/`v_proj` | 判定 |
> |---|---|---|
> | CLIP B/32、B/16、SigLIP B/16、OpenCLIP laion2B | 各 ×24 | ✅ 兼容 |
> | **DINOv2-base** | **不存在** | 🔴 仅它不匹配 |
>
> **并回头扫论文归档**（`tools/_p309`，502 个含可训参数量字段的文件）：
> 真注入计数 **196,608（×25）/ 294,912（×30）/ 491,520（×18）**；
> 12 个 `n_trainable_params = 0` **全部是 `*_frozen` 冻结基线**。
> → **论文归档无此问题**；该坑只影响 DINOv2 这个新实验。
>
> ### 状态
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | `main_nc` | **60** | 0 | 0 | 0 |
> | `main_springer` | **43** | 0 | 0 | 0 |
> | 投稿包 | **60** | 0 | 0 | — |
>
> **PR 核验 26/26** ｜ 提交 `58d8874`
>
> ### 仍在跑
>
> - **task-7**：更低 lr（1e-7/3e-7）+ 高 lr 补 seed（GPU 占用中）
> - **task-8**：DINOv2 等 GPU（脚本已就绪；LLaVA-7B 已实测 bf16 权重 13.157 GiB > 8 GiB 显存 → 本地不可行）
"""

MAP_ROW = ("| `outputs/analysis/strict_final_match.json` | `tab:position_strict` **12 格逐格溯源**"
           "（ΔCG 12/12 精确；R@1 6/12 精确，其余漂移 ≤0.0064）｜`tools/_p322` |")


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "tab:position_strict` 全 12 格溯源完成" in t:
        print("  HANDOFF 已记录")
    else:
        i = t.find("# 项目交接文档")
        j = t.find("\n", i)
        io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
        print(f"  ✅ HANDOFF 已追加")

    # 文件地图
    mp = REPO / "文件地图.md"
    if mp.exists():
        m = io.open(mp, encoding="utf-8").read()
        if "_p322" in m:
            print("  文件地图 已记录")
        else:
            anchor = "\n## "
            k = m.find(anchor, m.find("\n", m.find("# ")))
            if k < 0:
                k = len(m)
            io.open(mp, "w", encoding="utf-8", newline="").write(
                m[:k] + "\n" + MAP_ROW + "\n" + m[k:])
            print("  ✅ 文件地图 已更新")

    t2 = io.open(hp, encoding="utf-8").read()
    for key in ("全 12 格溯源完成", "strict_freeze_oclip/r4", "0.0064",
                "DINOv2", "196,608（×25）"):
        assert key in t2, f"断言失败：缺 {key}"
    print(f"  HANDOFF {len(t2.splitlines())} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
