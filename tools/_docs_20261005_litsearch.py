# -*- coding: utf-8 -*-
r"""记录 2026-10-05 每周文献检索的结果与改稿（阶段收尾）。

    python tools\_docs_20261005_litsearch.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENTRY = r"""> **📚 2026-10-05 —— 每周文献检索（首次执行）：加 3 条引用 + 一段辨析**
>
> 调度 `schedule-7342612c` 首次触发。按清单跑完 7 条检索式 + 追踪 9 位已有作者。
> **bib 先核对**（当时 41 条），避免把已有引用误报为新论文。
>
> ### 发现（逐条读过摘要，非凭标题）
>
> | key | 出处 | 关系 | 行动 |
> |---|---|---|---|
> | `sharma2026readout` | [arXiv:2609.36101](https://arxiv.org/abs/2609.36101)，Sharma & Saxena，2026-09-28 | **支持**：在 CLIP **与 SigLIP** 上发现改间隙的效果**依任务而异**（降间隙利于零样本；移除间隙结构损害检索） | **加引用** |
> | `yaras2026explaining` | [arXiv:2412.07909](https://arxiv.org/abs/2412.07909)（v2 2026-02），Yaras et al. | **需辨析**：用**梯度流**做间隙动力学（与本文同一工具），称"关间隙改善图文检索" | **加引用 + 写辨析** |
> | `chen2026dominance` | [ACL 2026 long, pp. 36666–36678](https://aclanthology.org/2026.acl-long.1699/)，**DOI 10.18653/v1/2026.acl-long.1699** | **背景/呼应**："Text Space as Anchor"——对齐是视觉特征向刚性文本流形的**非对称投影**，视觉侧调整是破坏源 | **加引用** |
>
> ### 辨析的实质（不是措辞回避）
>
> `yaras2026explaining` 与本稿**表面冲突**（它称关间隙改善检索，本稿称二者可分离）。写入正文的划分：
>
> - 它研究**预训练**阶段间隙**如何产生**（不匹配数据对 + 可学习温度），其干预在**两个编码器一起训练时**施加；
> - 本稿研究**微调**阶段：编码器已固定，只有适配器在变——**阶段不同**；
> - `sharma2026readout` 在**下游阶段**独立得出与本文同向的结论；
> - **三者合起来支持一个更一般的说法**：不存在单一的"间隙目标"能同时优化所有检索设定。
>
> ### 改稿与核验
>
> - bib **41 → 44 条**；cites 44 / bib 44 全匹配、无未使用（`tools/audit/check_paperA.py`）；
> - NC 版 **41 → 42 页**（Springer 31 页）、0 错误、0 未定义引用；
> - 摘要仍 **244 词**（未动）；
> - 投稿包已重建，`tools/_pa_final_check_nc.py` **全绿**。
>
> 脚本：`tools/_pa_add_litsearch_20261005.py`（带断言，可重跑）。
>
> ### 核实纪律的执行
>
> - 3 条**全部读过摘要**后才判断关系（未凭标题）；
> - **未使用** arXiv DOI（登记中），改用 `eprint` 字段；ACL 那条有正式 DOI，照录；
> - 未写入任何无法从官方页核实的字段。

"""


def main() -> int:
    apply = "--apply" in sys.argv
    p = REPO / "HANDOFF.md"
    t = io.open(p, encoding="utf-8").read()
    if "每周文献检索（首次执行）" in t:
        print("  已记录，跳过")
        return 0
    anchor = "> **🔬 2026-10-05 凌晨"
    i = t.find(anchor)
    if i < 0:
        print("  ⚠ 未找到锚点")
        return 1
    if apply:
        io.open(p, "w", encoding="utf-8", newline="").write(t[:i] + ENTRY + t[i:])
        t2 = io.open(p, encoding="utf-8").read()
        for k in ("2609.36101", "2412.07909", "10.18653/v1/2026.acl-long.1699", "41 → 44 条"):
            assert k in t2, f"断言失败：缺 {k}"
        print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
