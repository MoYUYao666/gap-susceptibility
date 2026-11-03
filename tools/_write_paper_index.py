# -*- coding: utf-8 -*-
r"""生成"**哪篇是哪篇**"速查表（2026-10-06）。

## 为什么需要

操作者："**你整理一下文件夹，太乱了，哪个是哪篇的我分不清了**"。
根目录有 **9 个 `paper*`**，命名无统一规则；且部分目录**内含多个版本**
（`paper3/` 有 3 个、`paper_a2/` 有 3 个）。

**不重命名**：有 14+ 个脚本按字面相对路径打开这些目录，改名会大面积失效。
改为在根目录放一份**核对过实测**的速查表。

## 设计教训（本脚本第一版踩的坑）

第一版用 `glob('**/main*.pdf')` 自动取 PDF → **取到了子目录里的副本**
（`paper3/paper/main.pdf`、`paper_a2/main_ieee.pdf`），导致页数对不上。
**故本版改为显式列出每个目录的主 PDF 路径**——不猜。

    python tools\_write_paper_index.py [--apply]
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# (目录, 是哪篇, 主 tex（相对目录）, 主 PDF（相对目录）, 身份/状态, 其他版本)
PAPERS = [
    ("paper", "**P1** — Protect, Don't Perturb", "main_nn.tex", "main_nn.pdf",
     "Pattern Recognition ｜ 稿号 **`PR-D-26-10149`** ｜ **Required Reviews Completed**（2026-10-04）"
     "｜⚠️ **它出决定前 `paper合` 不投**", ""),
    ("paper2", "**P2**", "main.tex", "main.pdf",
     "已与 P1 合并为 `paper合/`；本目录为单独版（`cas-sc` 模板）", ""),
    ("paper3", "**P3** — Gradient Structure Laws…", "paper_ieee/main.tex", "paper_ieee/main.pdf",
     "Pattern Recognition Letters ｜ 稿号 **`PRLETTERS-D-26-02378`** ｜ **Under Review**"
     "（2026-09-26 投）", "另有 `paper/main.pdf`(12页)、`paper_ICLR_backup/main.pdf`(12页)"),
    ("paper_a1", "**A1** — The Modality Gap Is Not a Universal Health Metric",
     "main.tex", "main.pdf",
     "**Neurocomputing** ｜ 稿号 **`NEUCOM-D-26-20952`** ｜ **With Editor**"
     "（2026-09-16 投；前身 `PRLETTERS-D-26-01941` 于 09-14 被 PRL 拒）"
     "｜⚠️ **与 `paper合/` 同刊（Neurocomputing），见索引末尾的冲突提示**",
     "`main_zh.pdf`(22页) 中文版"),
    ("paper_a2", "**A2 / A23** — 海洋·声呐", "main.tex", "main.pdf",
     "IEEE JOE ｜ 稿号 **`26-0663`**", "`main_ieee.pdf`(64页, IEEEtran)、`main_zh.pdf`(46页)"),
    ("paper_review", "**PRL Commentary**（评论/综述）", None, None,
     "Pattern Recognition Letters ｜ 稿号 **`PRLETTERS-D-26-02402`** ｜ **Under Review**"
     "（2026-09-28 投）", "本目录为工作版，PRL 格式版见 `paper_review_prl/`"),
    ("paper_review_prl", "**PRL Commentary 的 PRL 格式版**", "main_prl.tex", "main_prl.pdf",
     "7 页（上限 7）｜`UPLOAD/` 6 件 + Authorship Confirmation 表", ""),
    ("paper合", "**Paper A = P1+P2 合并稿** ⭐ **当前在编主稿**", "main_nc.tex", "main_nc.pdf",
     "目标 **Neurocomputing**（Elsevier `elsarticle`）｜投稿包 `NC_submission/` **已就绪**"
     "｜⏳ 投稿时点等 P1 决定", "`main_springer.pdf`(33页) Springer 版"),
]

OTHER = [
    ("备选", "备选/归档稿件（含 `备选/06_归档稿件/`）"),
    ("SUBMISSION", "各刊投稿材料归档"),
    ("publish_clean", "**GitHub 发布用独立仓库**（只放代码与结果，**不放论文**）"),
    ("outputs", "**全部论文数字的来源**（JSON，**勿动**）"),
    ("models", "本地模型权重（CLIP / OpenCLIP / SigLIP / BioCLIP / BLIP 等）"),
    ("data` / `coco` / `flickr30k", "数据集"),
    ("src", "核心库（trainer / lora / dataset / gap_susceptibility 等）"),
    ("experiments", "实验脚本（严格冻结对照、SigLIP 等）"),
    ("exp", "云端补实验（llava-hf / Qwen2-VL）"),
    ("tools", "**分析与审计脚本**（`_pa_*` / `_exp*` / `audit/`）+ 各阶段报告生成器"),
    ("docs", "决策、审计、图来源、阶段报告（`*.md`）"),
    ("backups", "全量快照 zip + sha256（约 14 GB）"),
]


def pdf_pages(p: Path) -> int | None:
    if not p.exists():
        return None
    r = subprocess.run(["pdfinfo", str(p)], capture_output=True)
    m = re.search(rb"Pages:\s+(\d+)", r.stdout)
    return int(m.group(1)) if m else None


def main() -> int:
    apply = "--apply" in sys.argv
    L = ["# 哪篇是哪篇（Pick your paper）", "",
         "> 由 `tools/_write_paper_index.py` 生成，**页数为实测**。最后更新 **2026-10-06**。",
         "> **目录不改名**——有 14+ 个脚本按字面相对路径打开它们，改名会大面积失效。", "",
         "## 一、根目录里的 8 个 `paper*`", "",
         "| 目录 | 是哪篇 | 主文件 | 身份 / 投稿状态 | 页数（实测） |",
         "|---|---|---|---|---|"]
    problems = []
    for d, who, tex, pdf, status, extra in PAPERS:
        dp = REPO / d
        if not dp.exists():
            problems.append(f"目录不存在：{d}")
            continue
        if tex and not (dp / tex).exists():
            problems.append(f"{d}/{tex} 不存在")
        if pdf and not (dp / pdf).exists():
            problems.append(f"{d}/{pdf} 不存在")
        pg = pdf_pages(dp / pdf) if pdf else None
        L.append(f"| `{d}/` | {who} | `{tex or '—'}` | {status} | {pg if pg else '—'} |")
        if extra:
            L.append(f"| | | ⌞ 其他版本 | {extra} | |")

    L += ["", "## 二、⚠️ 一个需要你决定的冲突", "",
          "**A1（`paper_a1/`）已在 Neurocomputing 在审（With Editor），而 `paper合/` 的目标期刊也是 Neurocomputing。**", "",
          "同一作者向同一期刊投两篇相关稿（都做 PEFT 下的 modality gap、都测零样本），编辑可能视为重复发表或自我竞争。", "",
          "**两篇的理论构件不重叠**（A1 用 Order Preservation / gap surgery；`paper合` 用 Gap Susceptibility / ODE），但主题与实验场景重叠。", "",
          "→ **需要决定**：换刊 ／ 在投稿信中说明区别 ｜ 等 A1 决定。", "",
          "## 三、⭐ 三句话记住", "",
          "1. **要投的是 `paper合/`**（Paper A = P1+P2，目标 Neurocomputing）——**当前唯一在编主稿**。",
          "2. **`paper/` 是 P1**（Pattern Recognition 在审）：**它出决定前 `paper合` 不投**。",
          "3. **`paper3/` 是 P3**（PRL 在审）。", "",
          "4. **`paper_ap3/`（P1+P2+P3 合并稿）已归档**到 `备选/06_归档稿件/paper_ap3/`——"
          "**不可投**（含 P3，与 PRL 在审稿重叠）。", "",
          "## 四、在审稿号一览", "",
          "| 稿号 | 期刊 | 是哪篇 | 状态 |", "|---|---|---|---|",
          "| `PR-D-26-10149` | Pattern Recognition | **P1**（`paper/`） | Required Reviews Completed（2026-10-04） |",
          "| `NEUCOM-D-26-20952` | **Neurocomputing** | **A1**（`paper_a1/`） | **With Editor**（09-16 投） |",
          "| `PRLETTERS-D-26-02378` | Pattern Recognition Letters | **P3**（`paper3/`） | Under Review（09-26 投） |",
          "| `PRLETTERS-D-26-02402` | Pattern Recognition Letters | **Commentary**（`paper_review/`） | Under Review（09-28 投） |",
          "", "## 五、其余目录", "", "| 目录 | 作用 |", "|---|---|"]
    for d, desc in OTHER:
        L.append(f"| `{d}` | {desc} |")

    text = "\n".join(L) + "\n"
    print(f"  生成 {len(L)} 行；核对发现 {len(problems)} 处问题")
    for p in problems:
        print("    ⚠ " + p)
    if apply:
        out = REPO / "哪篇是哪篇.md"
        io.open(out, "w", encoding="utf-8", newline="").write(text)
        t = io.open(out, encoding="utf-8").read()
        # ap3 已于 2026-10-06 归档（见 备选/06_归档稿件/），故索引里不再有 "不可投" 一项
        for k in ("paper合", "PR-D-26-10149", "NEUCOM-D-26-20952", "PRLETTERS-D-26-02378",
                  "PRLETTERS-D-26-02402", "With Editor", "一个需要你决定的冲突"):
            assert k in t, f"断言失败：缺 {k}"
        print(f"  ✅ 已写 哪篇是哪篇.md（{len(t.splitlines())} 行）")
        assert not problems, f"仍有 {len(problems)} 处不一致，速查表不可信"
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
