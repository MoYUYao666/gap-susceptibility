# -*- coding: utf-8 -*-
r"""Record the figure-library audit: fonts, scale, references, and the two stale PDF exports.

Three defects were found and fixed on 2026-10-15, and one property was confirmed:

* **fonts**: every figure PDF embeds Times New Roman (with STIXGeneral for maths), 17/17. The figure
  added this session had been drawn with matplotlib's default DejaVu Sans and was regenerated through
  `tools/figure_style.py`; `tools/_p867_figure_audit.py` now fails on any fallback font so this cannot
  come back unnoticed.
* **stale PDF exports**: `fig2_v5_falsification` and `fig4_effective_rank` were written with a bare
  `fig.savefig(..., .png)` call, so their PNGs were current while the PDFs that LaTeX actually includes
  were months old (`2026-08-02`). The rebuild script now uses the shared `save()`, which writes both.
* **scale drift**: two figures were drawn at a width other than the one LaTeX requested, so LaTeX
  scaled them (1.05x and 1.18x) and their internal text no longer matched the other figures.
  `tools/_p868_figure_scale.py` measures this; all 17 are now 1.00x.

    python tools/_p870_record_figure_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HANDOFF = REPO / "HANDOFF.md"
MAP = REPO / "文件地图.md"
PROV = REPO / "docs" / "PAPERA_FIGURE_PROVENANCE.md"
MARK = "图库整理：字体、缩放、引用与两份陈旧 PDF 导出"

ENT = """> **🖼️ 2026-10-15 13:30 —— 图库整理：字体、缩放、引用与两份陈旧 PDF 导出**
>
> 操作者指令：**「整理图库，所有文字都是times new roman」**。
>
> ### 一、✅ 字体：**17/17 张图全部 Times New Roman**（实测 `pdffonts`）
>
> | 图 | 内嵌字体 |
> |---|---|
> | 16 张既有图 | `TimesNewRomanPSMT`（部分含 **STIXGeneral** 数学字形，与 Times 同源）|
> | `fig15_stratified_dg_r1`（本轮新增）| **原先为 DejaVu Sans** ⇒ 已改走 `tools/figure_style.py`（Times + STIX）重出 |
>
> **稿件 PDF 实测**：文本 `TimesNewRomanPSMT`/`-BoldMT`，图内 `STIXGeneral`，**无 DejaVu/Liberation 回退**。
> （`CMMI/CMSY/SFRM` 等来自 elsarticle 的模板与数学字体，非本稿正文所述内容。）
>
> ### 二、✅ 修掉两份**陈旧 PDF 导出**（本轮发现的真缺陷）
>
> `fig2_v5_falsification` 与 `fig4_effective_rank` 用的是裸 `fig.savefig(..., .png)`——
> **PNG 是新的，而 LaTeX 实际引用的 PDF 停在 `2026-08-02`**。
> ⇒ 二者相差数月，读者看到的矢量图与数据源不一致。
> 已改为共享 `save()`（同时写 PNG + PDF），并重出两张 PDF（`20,732` / `25,346` 字节）。
>
> ### 三、✅ 缩放漂移已归零：**17/17 张 1.00×**（`tools/_p868_figure_scale.py` 实测）
>
> | 图 | 原自然宽 | LaTeX 要求 | 原缩放 | 处理 |
> |---|---|---|---|---|
> | `fig15_stratified_dg_r1` | 7.043 in | 0.95\\textwidth = 4.522 in | **0.64×** | 画布改为最终尺寸（4.189 in）+ 引用改回 0.88 |
> | `fig2_v5_falsification` | 3.552 in | 0.88\\textwidth = 4.189 in | **1.18×** | 按最终宽重绘 |
> | `fig4_effective_rank` | 3.551 in | 0.88\\textwidth = 4.189 in | **1.18×** | 按最终宽重绘（0.78→0.88 的历史错配）|
>
> **⇒ 全库现在 1.00×**：图内文字与正文同号，不再有的图大、有的图小。
>
> ### 四、✅ 引用与孤儿检查（`tools/_p867_figure_audit.py`，0 problem）
>
> | 检查 | 结果 |
> |---|---|
> | `\\includegraphics` 引用的图都存在 | **17/17**（工作副本 + `NC_submission` 两处都查）|
> | `figures/` 内无未被引用的图 | **0 孤儿**（34 个文件 = 17 图 × PDF+PNG）|
> | PDF/PNG 成对 | **34/34**（本轮为 `fig15` 补了 PNG）|
> | 字体 | **17/17** 全 Times/STIX |
> | **NC 副本与工作副本逐个 SHA-256 比对** | **34/34 一致** |
>
> ### 五、⛔ 一处**有意不动**，留待操作者定夺
>
> **正文数学字体仍是 Computer Modern**（`CMMI/CMSY/CMEX`）。要全稿统一为 Times 数学，
> 需 `\\usepackage{newtxtext,newtxmath}`（或 `mathptmx`）——**这会改变全稿数学排版与行宽，
> 可能使页数变化并影响已接受的版面**。**图内数学已是 STIX（Times 同源）**，故当前图—文数学风格仍属接近。
> 需要我加 `newtx` 的话说一声，我改完会重编并复核页数与溢出。
>
> ### 六、脚本（全部幂等，可重跑）
>
> | 脚本 | 作用 |
> |---|---|
> | `tools/_p867_figure_audit.py` | 引用/孤儿/成对/字体 四项检查（`--apply` 可把孤儿移入 `_superseded/`）|
> | `tools/_p868_figure_scale.py` | 逐图比对**自然宽 vs 要求宽**，报出缩放倍率 |
> | `tools/_p869_align_figure_widths.py` | 对齐两处 `\\includegraphics` 宽度 |
> | `tools/_p860_fig_stratified.py` | 图 15 生成（Times/STIX + 最终尺寸 + PNG/PDF）|
> | `tools/_pa_rebuild_figs_rest.py` | 修掉裸 `savefig`（PNG-only）⇒ 共享 `save()` |
>
> **编译复核**：**61 页 / 0 错误 / 0 未定义引用**（页数由 60→61 系 `fig2_v5` 改宽后重排）。
>

"""

PROV_APPEND = """

---

## 2026-10-15 追加：字体与缩放全库复核（操作者：「整理图库，所有文字都是times new roman」）

**结论：17 张图（含本轮新增的 `fig15_stratified_dg_r1`）全部 Times New Roman + STIX 数学，
缩放全部 1.00×，无孤儿图，工作副本与 `NC_submission` 副本逐个 SHA-256 一致。**

### 本轮修掉的三处

| # | 缺陷 | 证据 | 修法 |
|---|---|---|---|
| ① | 新增的 `fig15_stratified_dg_r1` 用 matplotlib 默认 **DejaVu Sans** | `pdffonts` 显示 `DejaVuSans` / `DejaVuSans-Oblique` | 改走 `tools/figure_style.py`（Times + STIX）重出 |
| ② | `fig2_v5_falsification`、`fig4_effective_rank` 的 **PDF 是 8 月的**（PNG 是新的）| 脚本用裸 `fig.savefig(..., .png)`，PDF 从未随之重写；时间戳 `2026-08-02` vs PNG `2026-10-06` | 改用共享 `save()`（PNG + PDF），重出两张 PDF |
| ③ | 两张图**按错误宽度绘制**，LaTeX 需缩放 1.05× / 1.18× | `tools/_p868_figure_scale.py`：自然宽 3.552 / 3.551 in vs 要求 3.713 / 4.189 in | `fig2_v5` 按最终宽重绘；`fig4_effective_rank` 的 LaTeX 宽度由 0.78 改 0.88 |

### 复核工具（新增，幂等）

```powershell
python tools\\_p867_figure_audit.py      # 引用 / 孤儿 / PDF-PNG 成对 / 字体
python tools\\_p868_figure_scale.py      # 自然宽 vs 要求宽 → 缩放倍率
python tools\\_p869_align_figure_widths.py   # 对齐 includegraphics 宽度
```

### 遗留（有意未动）

正文**数学**字体仍为 Computer Modern（`CMMI/CMSY/CMEX`）。统一为 Times 数学需
`newtxtext`+`newtxmath`，会改变全稿数学排版与行宽 ⇒ **先问操作者**。
图内数学已是 STIX（Times 同源）。
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    hp = io.open(HANDOFF, encoding="utf-8").read()
    if MARK in hp:
        print("  already recorded")
        return 0
    if not a.apply:
        print("  (dry run)")
        return 0

    i = hp.find("# 项目交接文档")
    j = hp.find("\n", i)
    hp = hp[: j + 1] + "\n" + ENT + hp[j + 1:]
    io.open(HANDOFF, "w", encoding="utf-8", newline="").write(hp)

    pv = io.open(PROV, encoding="utf-8").read()
    if "2026-10-15 追加：字体与缩放全库复核" not in pv:
        io.open(PROV, "w", encoding="utf-8", newline="").write(pv.rstrip() + PROV_APPEND)

    mp = io.open(MAP, encoding="utf-8").read()
    row = ("15. 🖼️ **图库复核（2026-10-15）** —— 17/17 图 **Times New Roman + STIX**、缩放 **全 1.00×**、"
           "**0 孤儿**、PDF/PNG **34/34 成对**、`NC_submission` 副本 **34/34 SHA-256 一致**。"
           "查图三件套：`tools/_p867_figure_audit.py`、`_p868_figure_scale.py`、`_p869_align_figure_widths.py`。"
           "⛔ 正文**数学**字体仍为 CM（图内已是 STIX）；统一需 `newtx`，**待操作者决定**。"
           "详见 `HANDOFF.md` 顶部 2026-10-15 13:30 条目与 `docs/PAPERA_FIGURE_PROVENANCE.md`。\n")
    anchor = "14. 🛠️ **PR 拒稿信剩 5 条已做 4 条（2026-10-15）**"
    idx = mp.find(anchor)
    if idx >= 0:
        end = mp.find("\n", idx)
        mp = mp[: end + 1] + row + mp[end + 1:]
        io.open(MAP, "w", encoding="utf-8", newline="").write(mp)
    else:
        print("  WARN: map item 14 not found; map not updated")

    h2 = io.open(HANDOFF, encoding="utf-8").read()
    for k in ("17/17 张图全部 Times New Roman", "fig2_v5_falsification", "1.00×", "newtx", "61 页"):
        print(f"  {'OK ' if k in h2 else 'BAD'} handoff::{k}")
    print(f"  HANDOFF lines = {len(h2.splitlines())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
