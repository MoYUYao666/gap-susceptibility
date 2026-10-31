# -*- coding: utf-8 -*-
r"""落账：实验 ④ 已写入论文（2026-10-08 22:00）。

    python tools\_docs_vlm_in_paper.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📝 2026-10-08 22:00 —— 实验 ④ 已写入论文（scope 缺口已补）**
>
> ### 改了两处
>
> | 文件 | 改动 |
> |---|---|
> | **`discussion.tex`** Limitation 第二条 | 把 *"limited to contrastive dual-encoder architectures … remains open"* → **改为已测一个解码器 VLM**（含三点初步性说明），并保留"generation-oriented objectives remains untested" |
> | **`supplement.tex`** 新增 **E 节**（`\\label{sec:vlm}`） | 三臂完整表 + 协议 + **为何用 4-bit** + **为何用相对降幅** |
>
> ### 写进论文的表述（要点）
>
> - **框架不限于双塔**：解码器 VLM 上 `DG*` 同样指数衰减，
>   且**视觉侧单独适配再次最差**（移动 11%，另两臂为 74% 与 84%）；
> - **最优位置不同**：此模型上 `both` 最优，而三个对比式双塔骨干是 `text_only`
>   —— **正是主文已有的"排序稳定、最优位置随配置而变"的结论**，**跨架构族边界再次观察到**；
> - **初步性（三点，如实写明）**：**单模型、单 seed**；**三臂全用 4-bit**
>   （为内部可比）；**规模小**（400 样本 3 epoch，足以定排序，**不足以报最终性能**）。
>
> ### 编译与门禁
>
> | 项 | 结果 |
> |---|---|
> | NC | **53 页** ｜ 0 错误 ｜ **0 未定义引用** ｜ 0 Overfull |
> | Springer | **39 页** ｜ 0 错误 ｜ **0 未定义引用** ｜ 0 Overfull |
> | **门禁** `_claim_ledger.py` | **40/40 通过**（新增 7 条：3 相对降幅 + 1 起点比 + 3 n_trainable） |
>
> ### 顺带：`\\ref{sec:vlm}` 跨文件引用已解析（0 未定义）
>
> `discussion.tex` 引用 `supplement.tex` 的 `\\label{sec:vlm}` —— 实测**编译后 0 未定义引用**，
> 故该 label 在最终文档中可达。
>
> ### 写稿过程踩的一处坑
>
> 脚本里一段**多行 raw 字符串漏了闭合引号** → `SyntaxError: unterminated string literal`。
> **已修**（这类错误在本仓库已多次出现：长字符串跨行拼接易漏引号）。
"""


def main() -> int:
    apply = "--apply" in sys.argv
    if not apply:
        print("  （预演）")
        return 0
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "实验 ④ 已写入论文" in t:
        print("  已记录，跳过")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("实验 ④ 已写入论文", "53 页", "40/40 通过", "单模型、单 seed",
              "unterminated string literal"):
        assert k in t2, f"断言失败：缺 {k}"
    print(f"  ✅ HANDOFF 已追加（{len(t2.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
