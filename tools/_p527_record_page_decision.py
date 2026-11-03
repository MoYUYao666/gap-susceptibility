# -*- coding: utf-8 -*-
r"""落账：操作者选定篇幅档 ①（10 页）；停止压缩，转收尾（2026-10-13）。

    python tools\_p527_record_page_decision.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PI = REPO / "paper3" / "paper_ieee"

ENT = """> **✅ 2026-10-13 19:20 —— 操作者选定篇幅**档 ①（10 页）**；停止压缩，转收尾**
>
> ### 一、操作者决定
>
> 面对我给出的三档（`tools/_p524`/`_p525` 量化后）：
>
> | 档 | 页数 | 代价 |
> |---|---|---|
> | **① 现状** | **10 页** | 超出 Guide 的 7 页，但**答复最完整** |
> | ② 折中 | 8–9 页 | 移出下游检验 + 逐块表 |
> | ③ 严格 7 页 | 7 页 | **必须牺牲 5 项证据之一**（对应 9 条意见） |
>
> **⇒ 操作者选 ①：10 页。** 依据：
> - **原投稿 11 页且进了外审** ⇒ PRL 实践上已在 11 页放行；
> - **10 页比投稿时更短**（压缩了 appendix→补充、proof→补充、细节→补充）；
> - 33 条意见中 **9 条**直接依赖将被 ③ 牺牲的证据 ⇒ **③ 代价大于收益**。
>
> ### 二、因此本次修订的篇幅状态
>
> | 构建 | 页数 | 用途 |
> |---|---|---|
> | **`main.tex`** | **10 页** | **投稿件（本次修订提交）** |
> | **`main_full.tex` + `sections_full/`** | **13 页** | **完整版存档**（回复信引用、审稿人索取） |
> | **`supplementary/supplementary.tex`** | — | **补充材料**（推导/证明/协议细节/逐 run 表/表图） |
>
> **⚠️ 必须在 cover letter 里主动说明篇幅与 Guide 的关系，请编辑裁定** —— 已列为收尾必办项。
>
> ### 三、压缩工作的最终交付（`task-12` 关闭）
>
> `writing-hardener` 的 `task-12` 目标（四节 ≤12,600 字符）**因内容约束未达标**，
> 且它给出了**关键反证**（四节整节删光也只到 ≈6.3 页）—— **我采纳该判断并关闭任务**。
>
> **本轮实际压缩总量**：
>
> | 动作 | 脚本 | 省 |
> |---|---|---|
> | `appendix` 整节 → 补充 | `_p490` | 8,520 |
> | 3 个 `proof` → 补充 | `_p492` | 2,501 |
> | 四节压缩（成员） | `_p513` | 7,883 |
> | 6 块细节 → 补充 | `_p511` | 8,165 |
> | experiments 散文 | `_p521` + `_p523` | 1,026 |
> | **合计** | | **≈28,100 字符（≈4.6 页）** |
>
> **12 页 → 10 页**（另 14 页的旧版）。
>
> ### 四、收尾清单（剩余三件）
>
> 1. **cover letter 增补篇幅说明**（主动向编辑说明 10 页 vs Guide 的 7 页）
> 2. **33 条回复信正式文本**（`docs/P3_REVIEW_RESPONSE.md` → 正式英文逐条回复）
> 3. **修订包重新生成**（`SUBMISSION/P3_PRL_revision/`，含 10 页稿 + 补充材料 + 回复信）
>
> ### 五、状态
>
> - **投稿件**：**10 页 / 0 错误 / 0 未定义 / 断头命令 0**
> - **完整版**：13 页（冻结）
> - **累计修订 44 处**；`_p497` 矛盾扫描 **0 处需处理**
>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    # 冻结 10 页版为 main_10pp
    src = PI / "main.tex"
    dst = PI / "main_10pp.tex"
    if src.exists() and not dst.exists():
        shutil.copy2(src, dst)
        print(f"  ✅ 已冻结 10 页版为 {dst.name}")
    hp = REPO / "HANDOFF.md"
    t = io.open(hp, encoding="utf-8").read()
    if "操作者选定篇幅" in t:
        print("  已记录")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("操作者选定篇幅", "档 ①：10 页", "≈28,100 字符", "cover letter 增补篇幅说明", "main_full.tex"):
        print(f"  {'✅' if k in t2 else '🔴'} {k}")
    print(f"  HANDOFF 行数 = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
