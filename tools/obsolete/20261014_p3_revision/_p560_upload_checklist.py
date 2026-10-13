# -*- coding: utf-8 -*-
r"""生成「提交上传清单」并落账（2026-10-13）。

## 依据

- **原投稿包**（`SUBMISSION/P3_PRL/`）：7 个 PDF/DOCX + `latex_source/` + zip
- **PRL Guide 硬要求**：源文件必须上传；Authorship Confirmation 以 item type `Cover Letter` 上传；
  双栏 ≤7 页；Data statement 必须有（**Option C：deposit 数据 + 引用链接**）
- **本次修订新增**：补充材料（新）、33 条回复（新）、更新后的稿件/封面信/标题页

    python tools\_p560_upload_checklist.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD_CHECKLIST.md"
D = REPO / "SUBMISSION" / "P3_PRL_revision"

CHECKLIST = """# 提交上传清单（PRL `PRLETTERS-D-26-02378`，Revise）

> 生成：2026-10-13｜**截止 2026-11-02**
> 依据：`docs/guides/_prl_guide.txt`（官方 Guide）

## 一、要上传的文件（EM 的 `Attach Files`）

| # | item type | 文件 | 状态 | 说明 |
|---|---|---|---|---|
| 1 | **Manuscript** | `manuscript/main.pdf` | 🔄 **重新上传**（替换旧版） | 10 页；作者块已去院系；Data statement 已改；33 条意见对应的修改全部改入 |
| 2 | **Supplementary Material** | `manuscript/supplementary.pdf` | 🆕 **新上传** | 5 页；公理推导、完整证明、协议细节、逐 run 表、表与图 |
| 3 | **LaTeX Source** | `manuscript/latex_source/`（12 个 tex + bib） | 🔄 **重新上传** | Guide：**"must upload source files"**；只交 PDF 会延误 |
| 4 | **Cover Letter** | `../P3_PRL/Cover letter.pdf`（**先更新**） | 🔄 **需改后重传** | 必须补：① 篇幅 vs Guide 的 7 页说明；② 本稿已投 PRL 的 Revise 语境 |
| 5 | **Cover Letter**（表单） | `Authorship Confirmation` | 🔄 **随 cover letter 重传** | Guide 第 4 条：**必须作为 item type `Cover Letter` 上传，未照办 = AUTOMATIC REJECTION** |
| 6 | **Title Page** | `../P3_PRL/Title page with declarations.pdf`（**先更新**） | 🔄 **需改后重传** | 院系已从标题页源去掉；需重新生成 PDF |
| 7 | **Highlights** | `../P3_PRL/highlights.pdf` | ⚠️ **建议更新** | 现版基于旧摘要（含 $30\\times$ 等已撤回主张）⇒ **须重做** |
| 8 | **Response to Reviewers** | **在 EM 表单里逐条/逐审稿人填写** | 🆕 | **三个回复框**，用 `response/P3_RESPONSE_Reviewer{1,2,3}_plain.txt` |

### ❌ 不需要上传的

| 文件 | 原因 |
|---|---|
| `manuscript/main_full.pdf`（13 页完整版） | **非投稿件**；仅供回复信引用与审稿人索取 |
| `response/P3_RESPONSE_LETTER.md`（33 条完整存档） | 内部存档；EM 用三份分审稿人版本 |
| `evidence/*` | 内部证据链；审稿人索取时再提供 |
| `reviews/*` | 编辑部已有 |

## 二、LaTeX 压缩包要不要上传？

**要 —— 但按编辑部要求的形式：**

| 选项 | 建议 |
|---|---|
| **上传 `latex_source/` 的**源文件**（.tex/.bib）** | ✅ **推荐**（EM 有专门的 LaTeX source 上传口，逐文件或 zip 都接受） |
| 上传 zip | ✅ 可以（`../P3_PRL/latex_source.zip` 是上次的做法） |
| 只交 PDF | ❌ **Guide 明确不接受**：*"A PDF is not an acceptable source file"* |

**⇒ 建议**：把 `manuscript/latex_source/` 打成一个 zip 上传（**命名 `P3_latex_source_revision.zip`**），
与上次投稿的 `latex_source.zip` 区分开。**注意**：补充材料也要**单独上传 PDF**（EM 的 Supplementary 口）。

## 三、⚠️ 必须解决的两个合规缺口（**都不是格式问题，是实质要求**）

### 缺口 1：**数据 deposited 到仓库**（Guide 的 Option C）

Guide 原文：*"For this journal, **Option C** … you are **required** to: **Deposit your research
data in a relevant data repository.** Cite and link to this dataset in your article. If this is
not possible, make a statement explaining why research data cannot be shared."*

**现状**：Data statement 已如实写明"派生数据在私有仓库、接受后公开归档"，但**尚未真正 deposit**。
**⇒ 建议（按代价排序）**：
- **(a) 最省事**：把 `outputs/` 的结果 JSON + `tools/` 的分析脚本 **打成一个 zip 上传到 Zenodo**
  （免费、给 DOI）⇒ 拿到 DOI 后**填进 Data statement 并给出链接**，完全满足 Option C
- (b) 用 **Mendeley Data** 或 **Figshare**（Elsevier 自家，与 EM 流程集成）
- (c) 若都不做：**保持现措辞**（说明为何暂不能共享）—— Guide 允许，但说服力弱

### 缺口 2：**GitHub 仓库目前是私有**

Guide 没要求"必须开 GitHub"，但**它要求数据可获取**。若选 (a)，**GitHub 公开与否就不重要了**。
**若想让 GitHub 也公开**：仓库可见性未核实，需操作者确认后公开（`.gitignore` 已保证稿件类不进库）。

## 四、提交前自检（可重跑）

```bash
python tools/_p497_scan_contradictions.py       # 矛盾扫描：要求「需处理 0 处」
python tools/_p556_scan_all_severed.py          # 断头命令：要求 0 处
python tools/_p503_fix_literal_n_correct.py     # 字面 \\n：要求 0
python tools/_p530_verify_response_letter.py    # 回复覆盖：33/33
python tools/_p550_check_plain_readability.py   # 三份纯文本可读性
cd paper3/paper_ieee && pdflatex main.tex       # 10 页 / 0 错 / 0 未定义
```


## 五、逐条意见 → 稿件修改对照（抽查 33/33 已核）

| 意见 | 稿件修改 | 状态 |
|---|---|---|
| R1.5 / R3.3（证明缺口） | **新增 R3$'$ 公理 + 反例 $\\|\\nabla E\\|^2$ + Lemma** | ✅ |
| R2.2 / R3.9 / R3.21 | **真逐块 Γ 引导分配**，57 run 逐位同预算 $7{,}237{,}632$；**优势撤回** | ✅ |
| R2.3 / R3.15 / R3.16 | **下游检验否证**（$R@1$ 对照 + 分层相关 + 配对检验） | ✅ |
| R2.4 / R3.9 | **AdaLoRA 同预算 + 对称 lr 扫描**；**如实承认其更优** | ✅ |
| R3.12 | **逐块 Γ + rank 表**（CLIP / LLaVA / Qwen2-VL） | ✅ |
| R3.13 / R3.14 / R3.23 | **blank 非中性**：论文操作点 $3.09\\times$ | ✅ |
| R3.17 / R3.19 | **降级为 bracketed** + CI + 置换 $p=0.100$ + 功效 11–28 | ✅ |
| R3.18 | **跨环境可复现性分析** + 两端初始能量 + 设备不变性 | ✅ |
| R2.1 / R3.10 | **零样本约束**：分配决策不含目标模型梯度 | ✅ |
| R3.7 | **$\\beta$ 来源更正**（`ode_ledger.json::runs[90]`，median 0.072 over 96 fits） | ✅ |
| R3.8 | **为何用 $|\\Gamma|$** 的解释 | ✅ |
| R1.4 / R3.11 | **架构依赖撤回**（token 预算伪影） | ✅ |
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  （预演）")
        return 0
    io.open(OUT, "w", encoding="utf-8", newline="").write(CHECKLIST)

    # 打包 latex source
    import zipfile
    zp = D / "manuscript" / "P3_latex_source_revision.zip"
    src = D / "manuscript" / "latex_source"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(src))
    print(f"  ✅ {OUT.relative_to(REPO)}")
    print(f"  ✅ {zp.relative_to(REPO)}（{zp.stat().st_size:,} B）")
    with zipfile.ZipFile(zp) as z:
        print(f"     内含 {len(z.namelist())} 个文件；testzip = {z.testzip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
