# -*- coding: utf-8 -*-
"""Record the Commentary figure font fix and the remaining Paper A figure-font gap."""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

entry = """> **🔤 2026-10-24 14:20 —— Commentary Fig.1 字体已修；发现 Paper A 仍有 17 张 Type 3 图（待处理）**
>
> - **已修**：`paper_review_prl/figures/fig1_decision_space.pdf` 原为 **DejaVuSans + Type 3**（违反"图内文字 Times New Roman、嵌入须 CID TrueType"规则）。
>   在 `tools/_make_prl_figure.py` 注入统一 style 块（`font.family=serif` → Times New Roman、`mathtext.fontset=stix`、`pdf.fonttype=42`）后重生成：
>   `pdffonts` 现为 **TimesNewRomanPSMT / TimesNewRomanPS-ItalicMT（CID TrueType）**；
>   `python tools/_build_prl_tex.py` 重建（7 页、0 error、0 undefined、0 overfull），`tools/_final_check_prl.py` 全过，审计 **READY(A) 57/0/0**；
>   重建使 `main_prl.tex` 变新 → J-01 曾报 "claim-ledger evidence older" → 用 `--apply` 重写三份台账（96/96、A1 216/216、Paper A 88/88）后消除；
> - **未处理（已知合规缺口）**：Paper A 18 张图里 **17 张仍嵌入 Type 3**（图名：fig1、fig1_ode_fits、fig2、fig2_v5_falsification、fig3、fig4、fig4_effective_rank、fig8a/8b/8c、fig9a/9b/9c、fig10_layered_ft、fig12_zeroshot_more、fig14_adapter_layered、fig15_stratified_dg_r1），
>   字体名是 TimesNewRoman/STIX 但嵌入类型为 Type 3；需按 `_make_prl_figure.py` 的方式给各生成脚本注入 style 块后重生成（生成脚本尚未全部定位）；**A1（11 图）、A23（图内 PDF 为 0）无此问题**；
> - 复核：六 profile 全部 **READY(A)、0 fail / 0 warn**；`final_verification` **ALL PASS**。
>
"""

h = io.open("HANDOFF.md", encoding="utf-8").read()
if "Commentary Fig.1 字体已修" not in h:
    i = h.find("# 项目交接文档")
    j = h.find("\n", i)
    h = h[:j + 1] + "\n" + entry + h[j + 1:]
    io.open("HANDOFF.md", "w", encoding="utf-8", newline="").write(h)
    print("handoff updated")

m = io.open("文件地图.md", encoding="utf-8").read()
row = ("158. 🔤 **2026-10-24 14:20 —— 图字体合规**：Commentary Fig.1 由 DejaVu+Type3 修为 TimesNewRoman CID TrueType"
       "（重建 7 页、审计 READY）；**Paper A 17/18 图仍为 Type 3，待重生成**；A1/A23 无问题。\n")
if "图字体合规" not in m:
    i = m.find("157. 💾 **2026-10-24 14:10")
    e = m.find("\n", i)
    m = m[:e + 1] + row + m[e + 1:]
    io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m)
    print("map updated")
print("done")