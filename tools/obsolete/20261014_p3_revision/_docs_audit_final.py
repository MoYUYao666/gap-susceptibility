# -*- coding: utf-8 -*-
r"""落账：完整统计审核（20/20 通过）+ 查出的 4 个问题全部修正（2026-10-11 晚）。

    python tools\_docs_audit_final.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **✅✅ 2026-10-11 晚 —— 完整统计审核：**20/20 项匹配、0 问题**；门禁 80/80**
>
> ### 一、审核方法（`tools/_audit_statistics.py`）
>
> **不接受"看起来对"**：论文里的每个数字，**独立从 `results.json` 重算**并逐项断言。
>
> | # | 审核项 | 方法 |
> |---|---|---|
> | 1 | 批次一致性 | 每组每臂 `batch_size` 必须一致（128） |
> | 2 | seed 覆盖 | 论文声称的 n 与实际文件数一致 |
> | 3 | 表格数字 | 从归档重算 mean/sd，与论文源码逐一比对 |
> | 4 | 统计口径 | sd = 样本 sd（ddof=1）；效应量 = 合并 sd |
> | 5 | 未污染 | 排除 `*.bak` / `.MISPLACED_*` |
>
> ### 二、审核结果
>
> ```
> 审核汇总：20/20 项数字匹配 ｜ 问题 0 个
> 门禁：✅ 通过 80 ｜ ❌ 失败 0
> ```
>
> | 段 | 结果 |
> |---|---|
> | ① 批次与 seed | ✅ 25 组全部 batch 128；COCO r4/r16/r64 两臂均 **5/5 seed** |
> | ② `tab:position_strict` | ✅ **9/9** 匹配（含 OpenCLIP 效应量 $1.49$/$2.71$ sd） |
> | ③ 数据集翻转 | ✅ **6/6**（Flickr30k 与 COCO 各两臂 + 全秩 4 项） |
> | ④ `tab:vlm` 13 seed | ✅ **3/3**（均值/sd/范围） |
> | ⑤ 污染检查 | ✅ 19 个 `.bak` + 1 个 `MISPLACED` 目录**均被判据排除** |
>
> ### 三、审核查出的 **4 个问题**（全部已修）
>
> | # | 问题 | 性质 | 修法 |
> |---|---|---|---|
> | **1** | VLM `both` 的 sd 写成 $5.3$，实际 **$5.351741$ → $5.4$** | **真错**（四舍五入） | 改 3 处（supplement ×2 + discussion ×1） |
> | **2** | COCO r4 的 `text_only` 用**旧 3-seed 数据**（新跑目录里当时没有 r4） | **口径不一致** | 补跑 5 seed → $-0.043013\pm0.002777$ |
> | **3** | 论文把 **5-seed 的 `text_only`** 与 **3-seed 的 `both`** 对比（COCO r4/r16/r64） | **口径不一致** | **补 `both` 到 5 seed**（11 run）→ r4 $-0.087733$、r16 $-0.152271$、r64 $-0.152655$ |
> | **4** | `_p147` 取数**混了新跑与旧 sweep**（n=8 → $-0.0424$） | **口径不一致** | 改为只取新跑 → $-0.0430$ |
>
> **另有 2 处是我自己脚本的硬编码旧值**（审计脚本 + 台账里的 Flickr30k r4），已同步。
>
> ### 四、修正后的关键数字
>
> **数据集翻转（r4，两臂各 5 seed，batch 128）**
>
> | 数据集 | `text_only` | `both` | 最保护 |
> |---|---|---|---|
> | Flickr30k | **$-0.0304\pm0.0039$** | $-0.0204\pm0.0028$ | `text_only` |
> | MS-COCO | $-0.0430\pm0.0028$ | **$-0.0877\pm0.0022$** | `both` |
>
> **→ 翻转结论不变**，且现在**两臂 seed 数一致**。
>
> **COCO `text_only` 全秩单调**：r2 $-0.0247$ → r8 $-0.0690$ → r32 $-0.1153$ → r64 $-0.1359$
>
> ### 五、本阶段踩的坑（**同一类错第 3 次**）
>
> | # | 脚本 | 错 |
> |---|---|---|
> | 1 | `_p169` | `--out-dir` 缺 rank 段 → COCO 16 失败 + r8 写错目录 |
> | 2 | `_p173` | 同一个错（我修了 `_p169` 但没把教训用到新脚本） |
> | 3 | `_p183` | **又是同一个错** |
>
> **根因**：`strict_freeze_control.py` 要求 `--out-dir` 含 `"r{rank}"` 子串（防污染校验），
> 否则 `raise SystemExit`；**而它的输出路径只有 `OUT_DIR/tag/seedN` 两层，rank 必须由调用方拼进 OUT_DIR**。
>
> **教训（已写进文档）**：**任何新写的实验驱动，`--out-dir` 必须拼 `/{rank}`**；
> 且**"静默跳过"与"路径被拒"都表现为 rc=0/rc=1 的快速返回**，
> **必须看文件 mtime + 元数据，不能看 rc**。
>
> ### 六、编译
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | Springer | **40** | 0 | 0 | 0 |
> | **NC** | **56** | 0 | 0 | 0 |
>
> ### 七、结论
>
> **所有实验数据现在满足**：① 批次统一（128）② seed 数一致（5，VLM 13）
> ③ 论文数字与归档**逐项可复现** ④ 门禁全绿。
>
> **剩投稿类待办**：`paper合` 定刊投出｜A1 转投确认（`Nov 08`）｜两条文献作者。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "完整统计审核" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("完整统计审核", "20/20", "80/80", "5.351741", "-0.087733",
              "同一类错第 3 次", "-0.043013"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
