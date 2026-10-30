# -*- coding: utf-8 -*-
r"""Record the Paper A pre-submission work in the handoff document.

    python tools/_p695_record_paperhe.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ENT = """> **📄 2026-10-14 18:30 —— Paper A（`paper合/`，目标 Neurocomputing）投稿前核验与修复**
>
> ### 一、操作者意图
>
> > **"改，并根据PR的回复再检查一遍"** —— 改 Data availability，并按 P3 审稿人提出的问题复查 Paper A。
>
> ### 二、🔴 查出并修好的问题
>
> | # | 问题 | 处置 |
> |---|---|---|
> | **1** | **Data availability 过期且自相矛盾**：`main_nc.tex` 写 *"the project repository, **which is currently private and will be made public upon publication**… **No new data were generated that requires deposit in an external repository**"*；而 `sections/conclusion.tex` 另写 *"Data will be made available on request"* | ✅ 两处统一为**公开仓库 URL + Zenodo DOI**；`conclusion.tex` 的矛盾一行式改为指向前置声明 |
> | **2** | **`main_nc.tex` 有中文注释**（`%% 由 tools/_pa_to_elsarticle.py 从…转换`）会随源包交编辑部 | ✅ 改英文 |
> | **3** | **`NC_submission/Highlights.pdf` 印的是旧标题** *"Protect, Don't Perturb: …"*，与稿件标题 *"Adaptation Site and the Modality Gap: …"* 不符 | ✅ 按当前标题重建（P3 同款问题） |
> | **4** | **highlights 的 R² 写错**：txt 写 0.97、`highlights_nc.pdf` 写 0.96 —— **稿件真值是 `mean R² = 0.949`（范围 0.814–0.977）** | ✅ 改为 **`mean R2 of 0.95`** |
> | **5** | **cover letter 的页数字与字数过期**：写 "56 pages"、"246 words" | ✅ 改为 **63 pages**、**236 words**，并补上仓库/DOI |
> | **6** | **`NC_submission/README.md` 同样过期**（56 页 / 246 词 / 最长 61 字符） | ✅ 改为 63 页 / 236 词 / 最长 59 字符 |
> | **7** | **源包副本落后于现行源码** | ✅ `latex_source/` 两份已同步，zip 重打（**55 成员 / 1,989,660 字节**） |
>
> ### 三、✅ 按 P3 审稿人问题复查 Paper A（`tools/_p687` 提取清单，`_p688` 执行）
>
> | P3 被要求撤回/降级的主张 | Paper A 是否也有 |
> |---|---|
> | "architecture-dependent" 读法 | ✅ **无** |
> | 分配规则胜过 uniform 基线 | ✅ **无** |
> | sharp phase transition | ✅ **无** |
> | 未加 R3′ 就声称唯一性 | ✅ **无** |
> | 块可分解 ⇒ 可加性 | ✅ **无** |
> | 30× 方差比当作发现 | ✅ **无** |
> | alignment energy 是下游性能的代理 | ✅ **无 → 反而明确写了"不是代理"** |
>
> **⇒ Paper A 与 P3 的撤回项没有重叠**；两处关键词命中经逐句核验**均非问题**（一处是 `DG*` 作为可微代理的**方法学说明**，一处正是"不是代理"的正面表述）。
>
> ### 四、✅ 完整检查（`tools/_p689`）
>
> | 检查 | 结果 |
> |---|---|
> | 编译 | **63 页 / 0 错误 / 0 未定义引用 / 0 未定义引用** |
> | PDF 内 `??` | **0** |
> | 新 DOI `10.5281/zenodo.23341223` 在 PDF 内 | ✅ |
> | 旧措辞（currently private / upon publication / No new data / on request） | **全部 0** ✅ |
> | 断头命令（`abla`/`oindent`） | 0 |
> | 编码非法 | 0 |
> | 中文字符（交付件） | **0**（已修 main_nc.tex） |
> | 占位符（TODO/TBD/…） | 0 |
> | **摘要字数** | **236 词**（限 250）✅ |
> | 缺失图 | **0** |
> | Springer 版（共享 `sections/`）重编译 | **45 页 / 0 错误** ✅ |
>
> **⚠️ 我在此过程中修正了自己两次误报**：
> ① 摘要一度数出 **260 词** —— 实际是把**页脚通信作者邮箱**与**串栏文字**算进切片（正确值 236）；
> ② 一度以为两处关键词命中是问题 —— 逐句看后**均非问题**。
> **⇒ 教训（再次）：关键词命中必须看整句，数字必须用两种口径交叉。**
>
> ### 五、📤 投稿包现状（`paper合/NC_submission/`）
>
> | 文件 | 大小 | 状态 |
> |---|---|---|
> | `Manuscript.pdf` | 927,072 | ✅ **63 页**，含新 DOI 声明 |
> | `Cover Letter.pdf` | — | ✅ 3 页，63 页/236 词 + DOI |
> | `Highlights.pdf` / `Highlights.txt` | — | ✅ 当前标题，5 条（43–59 字符） |
> | `latex_source.zip` | **1,989,660** | ✅ 55 成员，含新声明 |
> | `README.md` | — | ✅ 数字已更新 |
>
> ### 六、⚠️ 待操作者决定的**两件对外事项**（我不擅自做）
>
> | 项 | 说明 |
> |---|---|
> | **Paper A 的代码/结果归档** | 声明现在指向 **P3 的那个仓库**（`gap-susceptibility`）。**Paper A 是不同稿件** ⇒ 需操作者决定：① 把 Paper A 的 `outputs/`/代码**并入该仓库**（则声明无需改）② **另建仓库并取新 DOI**（则声明要改）③ 不加归档，退回"按请求提供"（**不建议**，与公开数据现状不符） |
> | **投稿时机** | `README_是哪篇.md` 记"投稿时点等 P1 的决定"。**P1 = `PR-D-26-10149` 已被 Pattern Recognition 拒**，Paper A 是 P1+P2 合并稿 ⇒ 这个前置条件**可能已经解除**，需操作者确认可以投 |
>
> ### 七、剩余
>
> ① 决定 Paper A 归档指向（上表第 1 项）② 确认投稿时机（第 2 项）③ 上传 `NC_submission/` 到 Neurocomputing 门户
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
    if "Paper A（`paper合/`，目标 Neurocomputing）投稿前核验与修复" in t:
        print("  already recorded")
        return 0
    i = t.find("# 项目交接文档")
    j = t.find("\n", i)
    io.open(hp, "w", encoding="utf-8", newline="").write(t[:j + 1] + "\n" + ENT + t[j + 1:])
    t2 = io.open(hp, encoding="utf-8").read()
    for k in ("目标 Neurocomputing）投稿前核验与修复", "currently private", "1,989,660",
              "两次误报", "另建仓库并取新 DOI"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    print(f"  HANDOFF lines = {len(t2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
