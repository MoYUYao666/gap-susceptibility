# -*- coding: utf-8 -*-
"""Record the Paper A figure-font (Type 3 -> CID TrueType) fix round."""
import io
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

entry = """> **🔤 2026-10-24 14:35 —— Paper A 17 张 Type 3 图全部修完；五份主稿 0 个 Type 3**
>
> - **根因**：`tools/figure_style.py::apply_style()` 只设了字体族（Times + STIX），**没设 `pdf.fonttype`** ⇒ matplotlib 默认 **Type 3**；
>   凡经 `figure_style.save()` 出图的 PDF 全是 Type 3（Paper A 18 张里 17 张中招；A1/评论稿是另一条出图路径所以没事）；
> - **修法**：给 `apply_style()` 加 `pdf.fonttype=42` / `ps.fonttype=42`，再按"权威生成脚本"重出各图（`tools/_p1581_fix_paperA_figure_fonts.py --apply`，幂等、带逐图校验）：
>   `_pa_rebuild_figs_rest.py --apply`（fig1/fig1_ode_fits/fig3/fig2_v5_falsification/fig4_effective_rank）、
>   `_pa_split_appendix_figs.py --apply`（fig8a/b/c、fig9a/b/c）、`_pa_rebuild_fig12.py --apply`、`_pa_fig10_tall.py --apply`、
>   `_pa_fig14_tall.py`、`_p860_fig_stratified.py --apply`，以及单独的两张：
>   **fig2** = `_pa_fig2_corr.py`（它写 Paper A 的 fig2，且经 `save()` 同时写 PDF）、
>   **fig4** = `_pa_rebuild_fig4_crossmethod.py --apply`（`_pa_rebuild_figs_rest.py` 里 fig4 分支已停用）；
> - **旧图已归档**：`_archive/paperA_figures_pre_fontfix_2026-10-24/`（PDF+PNG 全部原件）；
> - **校验**：17/17 图 `pdffonts` **Type 3 = 0**，字体仅 TimesNewRoman*/STIX*；两份主稿重编译后
>   `paper合/main_nc.pdf` **74 页**、`main_springer.pdf` **53 页**（页数未变），均 **0 error / 0 undefined / 0 overfull**；
>   五份主稿（NC、Springer、A1、A23、Commentary）`pdffonts` **Type 3 全为 0**、无 DejaVu/Arial/Helvetica；
> - **包**：`tools/_p1576_refresh_a1_papera_packages.py --apply` 重刷（Manuscript 74 页、摘要 242 词；zip 45 条=树 45）；
> - **门禁**：六 profile **READY(A)、0 fail / 0 warn**；台账 96/96、A1 216/216、Paper A 88/88；`final_verification` **ALL PASS**；
> - **已知坏脚本（勿用）**：`tools/_pa_fix_fig8c_fig14.py` 有语法错误（第 48 行未闭合字符串），其功能已被 `_pa_split_appendix_figs.py` + `_pa_fig14_tall.py` 覆盖。
>
"""

h = io.open("HANDOFF.md", encoding="utf-8").read()
if "Paper A 17 张 Type 3 图全部修完" not in h:
    i = h.find("# 项目交接文档")
    j = h.find("\n", i)
    h = h[:j + 1] + "\n" + entry + h[j + 1:]
    io.open("HANDOFF.md", "w", encoding="utf-8", newline="").write(h)
    print("handoff updated")

m = io.open("文件地图.md", encoding="utf-8").read()
row = ("159. 🔤 **2026-10-24 14:35 —— Paper A 图字体 Type 3 全清**：根因 `figure_style.apply_style` 缺 `pdf.fonttype`；"
       "17/17 图重出为 CID TrueType；两份主稿 74/53 页 0/0/0；脚本 `tools/_p1581_fix_paperA_figure_fonts.py`。\n")
if "Paper A 图字体 Type 3 全清" not in m:
    i = m.find("158. 🔤 **2026-10-24 14:20")
    e = m.find("\n", i)
    m = m[:e + 1] + row + m[e + 1:]
    io.open("文件地图.md", "w", encoding="utf-8", newline="").write(m)
    print("map updated")
print("done")