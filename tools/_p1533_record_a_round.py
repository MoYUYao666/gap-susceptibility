# -*- coding: utf-8 -*-
"""Finalise the three-environment text and record the A-round outcomes."""
import io
import json
import os

SUPP = "paper3/paper_ieee/supplementary/supplementary.tex"
HANDOFF = "HANDOFF.md"
MAP = "文件地图.md"
GAPS = "docs/P3_REMAINING_GAPS_2026-10-22.md"
AUD = "docs/P3_RESUBMISSION_AUDIT_2026-10-21.md"


def main() -> int:
    t = io.open(SUPP, encoding="utf-8").read()
    old = ("The protocol is repeated on a second machine: RTX 4080 SUPER, torch 2.12.1+cu130, CUDA 13.0 (the local runs use\n"
           "torch 2.9.1+cu130 on an RTX 4060 Laptop). Table~\\ref{tab:envcloud} compares the two.")
    new = ("The protocol is repeated in three environments: RTX 4060 Laptop with torch 2.9.1+cu130, RTX 4080 SUPER with\n"
           "torch 2.12.1+cu130, and RTX 4060 Laptop with torch 2.4.1+cu121 (CUDA 12.1). Table~\\ref{tab:envcloud} compares\n"
           "them.")
    if old in t:
        t = t.replace(old, new, 1)
        io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
        print("S29 intro updated")
    h = io.open(HANDOFF, encoding="utf-8").read()
    entry = """> **🧩 2026-10-22 23:00 —— A 组（官方基线 / VQA 规模 / 环境矩阵）本地部分完成；云端留最后**
>
> | A 项 | 结果 |
> |---|---|
> | **A1 官方基线** | IGU-LoRA 官方仓库已克隆（`external/igulora`）；其发布的剪枝流程基于 SVD-LoRA 文本 LLM 管线，**不能直接嵌入 4-bit LLaVA**，故按其论文 Eq.4–7 实现分配（vision 13/1/1/1）并训练 arm：**ΔE +227.0 (+5.8%)**。HALoRA（AAAI-26 页面无代码链接）与 ShapLoRA（论文称"将开源"）**官方代码不可得**，如实记录。 |
> | **A3 环境矩阵** | 三个环境跑完：torch 2.9/cu130 → r5 **−10.5**、r6 **+115.0**；torch 2.12/cu130（云 4080）→ r5 **−33.5**、r6 **+81.5**；torch 2.4/cu121（本地新建 env）→ r5 **+41.0**、r6 **+89.0**。**r6 恒正；r5 在 torch 2.4/CUDA 12.1 下翻转** → 交叉点对环境敏感。 |
> | **A2 VQA 规模** | 云脚本 `cloud_p3/run_cloud_final.sh` 已备好（完整 VQA-RAD 1793 训练对、per-step、eval 200 + 额外 seed）；**需先重启 AutoDL 实例**（端口会变）才能执行。 |
>
> 论文更新：**S29 改为三环境矩阵**（含 r5 翻转的诚实结论）；S27 增 IGU 方程 arm；S17 环境行改为"not supported（r5 符号随 torch/CUDA 翻转）"；discussion 限制 (6) 同步。
> 当前：正文 10 页、补充 12 页（S1–S29）；本地冒烟全部通过。
>

"""
    if "A 组（官方基线 / VQA 规模 / 环境矩阵）本地部分完成" not in h:
        i = h.find("# 项目交接文档")
        j = h.find("\n", i)
        io.open(HANDOFF, "w", encoding="utf-8", newline="").write(h[: j + 1] + "\n" + entry + h[j + 1:])
        print("handoff updated")
    m = io.open(MAP, encoding="utf-8").read()
    row = ("149. 🧩 **A 组本地完成（2026-10-22 23:00）** —— A1 IGU 官方仓库+方程 arm（+227）；A3 三环境矩阵"
           "（r5 在 torch2.4/cu121 翻转）；A2 云脚本就绪待实例。\n")
    if "A 组本地完成" not in m:
        i = m.find("148. ☁️ **云端结果 + 清理")
        assert i >= 0
        end = m.find("\n", i)
        m = m[: end + 1] + row + m[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(m)
        print("map updated")
    g = io.open(GAPS, encoding="utf-8").read()
    add = """

## 十一、A 组状态（2026-10-22 23:00）

- A1：IGU-LoRA 官方仓库已获取，但其发布管线只支持 SVD-LoRA 文本 LLM；按其方程实现的分配 arm 已训练（+227.0）。
  HALoRA / ShapLoRA 官方代码不可得；S27 已更新并如实说明。
- A3：三环境矩阵完成，r6 恒正、r5 在 torch 2.4/CUDA 12.1 下翻转（+41.0），S29/S17/discussion 已同步。
- A2：完整 VQA-RAD（1793 训练对）云端脚本就绪，**等实例重启**。
"""
    if "## 十一、A 组状态" not in g:
        io.open(GAPS, "w", encoding="utf-8", newline="").write(g.rstrip() + add)
        print("gaps updated")
    a = io.open(AUD, encoding="utf-8").read()
    if "A 组收尾" not in a:
        a = a.rstrip() + "\n\n## 十三、A 组收尾（2026-10-22 23:00）\n\nS29 三环境矩阵（r5 在 torch2.4/cu121 翻转）、S27 IGU 方程 arm；A2 云脚本待实例。\n"
        io.open(AUD, "w", encoding="utf-8", newline="").write(a)
        print("audit updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
