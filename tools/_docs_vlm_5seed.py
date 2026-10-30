# -*- coding: utf-8 -*-
r"""落账：解码器 VLM 的 **5-seed** 结果（2026-10-10 晚）。

    python tools\_docs_vlm_5seed.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **🔬 2026-10-10 晚 —— 解码器 VLM 补到 **5 seed**：`vision_only` 最弱**稳了**，两强臂**仍不可分辨****
>
> 操作者要求"试试 5 seed"。幂等 driver 只补了 5 个新 run（seed 789/1011 × 3 臂，跳过已有 9 个），
> **全部成功**（seed 42/123/456/789/1011 × 3 臂 = **15/15**）。
>
> ### 一、5-seed 结果（bf16，主指标 = $DG^*$ 相对变化）
>
> | 臂 | n | 均值 | 逐 seed | 种子范围 |
> |---|---|---|---|---|
> | `text_only` | 5 | $+67.4\\pm7.3\\%$ | 59.4 / 70.0 / 71.1 / 60.3 / 76.3 | 59.4--76.3 |
> | `vision_only` | 5 | $+15.8\\pm10.4\\%$ | 17.7 / 11.0 / 8.6 / **33.0** / 8.5 | **8.5--33.0** |
> | `both` | 5 | $+86.5\\pm8.1\\%$ | 73.1 / 87.5 / 95.1 / 89.7 / 87.3 | 73.1--95.1 |
>
> ### 二、两个结论（**一个稳、一个不稳**）
>
> | 结论 | 证据 | 判定 |
> |---|---|---|
> | **`vision_only` 最弱** | 其**最大值 33.0%** 仍**低于**另两臂的**最小值**（59.4% / 73.1%）→ **分布完全不重叠** | ✅ **稳**（任何 seed 都成立） |
> | **`text_only` vs `both` 谁更好** | 种子范围**完全重叠**；CG 尺度差 $0.62$ sd | 🔴 **不可分辨**（5 seed 也不够） |
>
> **CG 尺度的对照**（`vision_only` 起始值高 $3.7$–$8.8$ 倍，故 CG 对它不敏感）：
> `text_only` vs `vision_only` = $1.18$ sd（边缘）｜`text_only` vs `both` = $0.62$ sd（不显著）｜
> `vision_only` vs `both` = $0.21$ sd（不显著）
>
> ### 三、3 seed → 5 seed 的变化（**说明为什么必须多种子**）
>
> | 量 | 3 seed | 5 seed |
> |---|---|---|
> | `text_only` | $+66.8\\pm6.5\\%$ | $+67.4\\pm7.3\\%$ |
> | `vision_only` | $+12.4\\pm4.7\\%$ | $+15.8\\pm10.4\\%$（**sd 翻倍**，因新增 seed 789 达 33.0%） |
> | `both` | $+85.2\\pm11.2\\%$ | $+86.5\\pm8.1\\%$ |
> | **CG 尺度排序** | `text_only` < `both` < `vision_only` | **同**（但 `vision_only` 的 sd 从 0.064 变 0.090） |
>
> ### 四、论文改动（3 seed → 5 seed）
>
> | 文件 | 改动 |
> |---|---|
> | `supplement.tex` | `tab:vlm` 换成 5-seed 数字（$+86.5\\pm8.1$ / $+67.4\\pm7.3$ / $+15.8\\pm10.4\\%$）；判读段改写为"**`vision_only` 最弱由每个 seed 支持**；两强臂不可分辨"；协议段 three→**five** seeds；收尾段同步 |
> | `discussion.tex` | Second limitation 同步 5-seed 数字与"种子范围完全重叠" |
>
> **备份**：`supplement.tex.bak_vlm5`｜`discussion.tex.bak_vlm5`
>
> ### 五、编译与门禁
>
> | 稿 | 页数 | 错误 | 未定义 | Overfull |
> |---|---|---|---|---|
> | Springer | **40** | 0 | 0 | 0 |
> | **NC** | **56** | 0 | 0 | 0 |
>
> **门禁：80/80 通过**（①g 区块按 5-seed 归档值同步，14 条断言）｜退出码 0
> **残留检查**：旧 3-seed 数字 **0 命中** ✅
>
> ### 六、C3 的最终状态
>
> | 项 | 状态 |
> |---|---|
> | 模型数 | **1**（未变，已如实标注） |
> | **seed 数** | **5** ✅（与论文其余统计验证的 5-seed 口径一致） |
> | 精度 | **bf16**（逐位可复现）✅ |
> | 规模 | 400 样本 / 3 epoch（未变，已标注） |
> | 结论 | **`vision_only` 最弱（稳）；两强臂不可分辨（如实报告）** |
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "补到 **5 seed**" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("补到 **5 seed**", "80/80", "+15.8", "33.0", "分布完全不重叠", "15/15"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
