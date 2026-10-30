# -*- coding: utf-8 -*-
r"""同步三件文档到 2026-10-05 实测状态（报状态前的收尾，按项目规则）。

## 不同步之处（实测发现）

| 文档 | 问题 |
|---|---|
| `docs/PAPERA_PREFLIGHT_AUDIT.md` | 仍写 **42 页 / 31 页**，实测 **43 / 32**；且未含本日的计数更正、图重绘、最终确认 |
| `docs/PAPERA_REVISION_SPEC.md` | 最后修改 **2026-10-03**，缺 10-04/05 的全部改动 |
| `文件地图.md` | 缺 **212**（目录表合计）这一计数 |

    python tools\_sync_docs_20261005.py [--apply]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SPEC_SECTION = r"""
### 7.7 2026-10-04 ~ 10-05 追加：`k` 修正、跨骨干实验、计数更正、图重绘、投稿前审核

**全部改动均由 `tools/` 下带断言的幂等脚本完成，可重跑复核。**

#### 7.7.1 `k = 0.043` 从全稿清除（5 处）

重测（both 臂，严格冻结，3 seeds/rank，$r\in[1,64]$）：$\|g_v\|$ 极差 **10%**（12.75–14.09），
而 $\sqrt r$ 预测应变化 **8 倍**。**线性拟合给 0.257，且相邻区间局部斜率正负交替**
（−0.20/+0.89/−0.35/+1.39/−0.40）→ **无可辨趋势，斜率不应报**。
改为"**区间 10% vs $\sqrt r$ 预测 8 倍**"。详见 `docs/K043_INVESTIGATION.md`。

- 脚本：`tools/_pa_fix_k_slope.py`、`tools/_pa_fix_k_slope2.py`
- 数据：`outputs/analysis/k_remeasured_both.json`（`tools/_pa_remeasure_k.py`）

#### 7.7.2 跨骨干严格冻结实验完成（95 个 run）

three backbones × 双 rank × 各臂。**权威分析** `tools/_pa_rank_analysis.py`（配对检验）：

| 骨干 | 臂 | r8−r4 | t | 方向 |
|---|---|---|---|---|
| CLIP | text_only | −0.0192 | −7.96 | r8 更小 |
| CLIP | both | −0.0065 | −2.88 | r8 更小 |
| OpenCLIP | text_only | −0.0112 | −5.86 | r8 更小 |
| **OpenCLIP** | **both** | **+0.0042** | **+1.09** | 例外（**不显著**） |
| SigLIP | text_only | −0.0166 | −3.79 | r8 更小 |
| SigLIP | both | −0.0204 | −2.57 | r8 更小 |

→ **5/6 同向且显著**。**位置排序按骨干分组**：CLIP 6/6、OpenCLIP 2/2 为 `text_only` 更小，
**SigLIP 2/2 相反** → 8/10。

#### 7.7.3 实验计数更正（**两轮**）

| 口径 | 值 |
|---|---|
| 附录目录（13 类机理 + XIV 类严格冻结） | **212** |
| ODE 拟合 | 162 |
| **全文合计** | **374** |

- **第一轮**：补上先前**完全未计入**的 95 个严格冻结对照 —— 而那正是位置效应结论的**唯一可靠依据**
  （legacy 约定下 text-only 臂实际训练约 1.45 亿参数）。
- **第二轮（最终确认时发现）**：目录表 `Total` 一度被改成全文字口径 **374**，**与表内求和 212 不符**；
  且附录说明把严格冻结**既算进目录又单列（重复计数）**。**已修正为 212**，说明改为
  "212 catalogued here + 162 in Section~\ref{sec:validation} = 374 in total"。
- **另修**：两版 `main*.tex` **摘要**里残留的旧计数 **278**（第一轮只改了 `sections/*.tex`，漏了主文件）。
- 核算脚本：`tools/_check_catalog_sum.py`（**断言"求和 = Total"**）、`tools/_verify_experiment_counts.py`

#### 7.7.4 图来源重绘（9 张，**12/12 现全部可溯源**）

先前审计：12 张里仅 3 张可溯源，其余 9 张由 **2026-08-22 已不存在的脚本**产出。
现已全部重绘，每张有仓库内脚本 + 明确源 JSON。详见 `docs/PAPERA_FIGURE_PROVENANCE.md`。

**重绘捕获 2 处主张与数据不符**（这才是重绘的价值）：

| 图 | 原主张 | 数据 | 处置 |
|---|---|---|---|
| `fig12` | "all fine-tuned variants within **0.8 pp**" | Food101/both **0.87 pp** | 改为分变体（text-only ≤0.1、both ≤0.9） |
| `fig14` | "**reaches frozen-level CG**"；图题"Text-only Also Preserves Alignment" | Adapter text-only CG **+0.250**、R@1 **0.06**；both +0.503、0.005 | 图注与图题改为如实陈述；**保留**原图注中正确的两点披露 |

**工作方式**：每个重绘脚本**先断言正文主张、再画图**——数据不符即报错。

#### 7.7.5 投稿前审核（`docs/PAPERA_PREFLIGHT_AUDIT.md`）

- 修 **1 项实质缺陷**：`introduction.tex` 残留无条件声称"text-only **overwhelmingly preserves** …
  **117 experiments on five architectures**"（正文已记录 SigLIP 反转；且那 117 个多在 legacy 约定下）。
  改为"holds where the comparison isolates the adaptation site, **but not universally**"。
  **发现方式**：新增的**范围词扫描** `tools/_extract_claims.py`（288 句命中 76 条）。
- 修 **4 项审计工具自身缺陷**：终检脚本引用计数只认数字制（在 44 条文献上报"0 处"）、
  preflight 把 `(fig|tab)` 一起数、漏数 `longtable`、以及**我自己的三次快速断言**。

#### 7.7.6 本阶段我自己的错误（如实记录，供复查）

| # | 错误 | 发现方式 |
|---|---|---|
| 1 | 把 CLIP 的"更负"与 SigLIP 的"更小"当成**相反方向** | 配对检验 |
| 2 | 仅凭 2 个骨干断言"rank 效应**跨骨干成立**"（**曾写入正文**） | OpenCLIP 跑完后推翻 |
| 3 | 断言"OpenCLIP 两臂都与另两个骨干相反" | 其中一臂 **t=+1.09 不显著** |
| 4 | 给 `fig10` 设断言时**臆想了正文没有的主张** | 断言失败，回读正文 |
| 5 | 把 `Overfull \hbox` 误判为"重绘的图太宽" | 目视 page 10 + `pdftotext -bbox` 实测：**无越界** |

**共同根因**：数据未齐/未读原文就下结论。**对策**：分析固化脚本 + 配对检验 + 先读正文再设断言。

#### 7.7.7 最终确认（全绿）

| 项 | 结果 |
|---|---|
| 编译（从零，两版） | NC **43 页** / Springer **33 页**，**0 错误、0 未定义引用** |
| 引用 | cites **44** = bib **44**，缺失 0、未使用 0；PDF 中作者-年份引用 **51 处** |
| 结构 | 悬空 `\ref` **0**、重复 label **0**、占位符 **0**、图文件缺 **0**、图 12/12、表 8/8 |
| 摘要 | **244 词** ≤250，两版一致 |
| 声明 | 5 节齐备且位于参考文献之前 ｜ Highlights 5 条、最长 59 字符 |
| 核心主张复算 | 严格冻结 5-seed 方向+排序 ✅；`R² > 0.96` ✅ |
| 图来源 | **12/12** ✅ ｜ `k=0.043` 残留 **0** ✅ |
| 投稿包 | 已重建，`tools/_pa_final_check_nc.py` **全绿** |

#### 7.7.8 复核入口（本阶段新增）

```powershell
python tools\_check_catalog_sum.py           # 目录表求和 = Total（带断言）
python tools\_verify_experiment_counts.py    # 三段口径核算
python tools\_count_strictfreeze_runs.py     # 严格冻结 run 盘点
python tools\_pa_rank_analysis.py            # 三骨干 rank 配对检验
python tools\_pa_rank_matrix.py              # 骨干 × rank 矩阵
python tools\_extract_claims.py --apply      # 主张提取（措辞审核）
python tools\_audit_paperA_preflight.py      # 新面审计
python tools\_pa_rebuild_figs_rest.py --dry  # 图主张核对（不写图）
python tools\_write_figure_provenance.py --apply
```
"""

MAP_NOTE = r"""
> **🔄 2026-10-05 状态更新（`paper合/`）**：NC 版 **43 页**、Springer 版 **33 页**、0 错误、0 未定义引用。
> 引用 **44** 条全匹配；实验计数 **374**（附录目录 **212** + ODE 拟合 162）；
> 图来源 **12/12** 可溯源；`k=0.043` 已清除。审核报告 `docs/PAPERA_PREFLIGHT_AUDIT.md`，
> 图清单 `docs/PAPERA_FIGURE_PROVENANCE.md`，本阶段改动 `docs/PAPERA_REVISION_SPEC.md` §7.7。
> **唯一未决变量：P1（`PR-D-26-10149`）的决定**（2026-10-04 状态日期，Required Reviews Completed）。
"""


def main() -> int:
    apply = "--apply" in sys.argv

    # ① PREFLIGHT_AUDIT：页数 42→43、31→32，并追加"最终确认"段
    p1 = REPO / "docs" / "PAPERA_PREFLIGHT_AUDIT.md"
    t1 = io.open(p1, encoding="utf-8").read()
    n1 = 0
    for old, new in (("**42 页**", "**43 页**"), ("NC 42 页", "NC 43 页"),
                     ("Springer 31 页", "Springer 33 页"), ("**31 页**", "**33 页**")):
        if old in t1:
            t1 = t1.replace(old, new)
            n1 += 1
    add = ("\n\n## 七、最终确认（2026-10-05，本文件撰写后）\n\n"
           "本报告初稿完成后又做了三轮复核，**发现并修正 3 处真问题**"
           "（两版 `main*.tex` 摘要残留旧计数 278；目录表 `Total` 误用全文字口径 374 而与表内求和 212 不符；"
           "附录说明把严格冻结重复计数），并**重绘全部 9 张来源不明的图**"
           "（`docs/PAPERA_FIGURE_PROVENANCE.md`）。**当前实测**：NC **43 页**、Springer **33 页**、"
           "0 错误、0 未定义引用、cites 44 = bib 44、目录表求和 = Total = **212**、全文 **374**、"
           "图来源 **12/12**。详见 `docs/PAPERA_REVISION_SPEC.md` §7.7。\n")
    if "## 七、最终确认" not in t1:
        t1 = t1.rstrip() + add
        n1 += 1

    # ② REVISION_SPEC：追加 §7.7
    p2 = REPO / "docs" / "PAPERA_REVISION_SPEC.md"
    t2 = io.open(p2, encoding="utf-8").read()
    n2 = 0
    if "### 7.7 2026-10-04" not in t2:
        t2 = t2.rstrip() + "\n" + SPEC_SECTION
        n2 = 1

    # ③ 文件地图：追加状态更新
    p3 = REPO / "文件地图.md"
    t3 = io.open(p3, encoding="utf-8").read()
    n3 = 0
    if "2026-10-05 状态更新（`paper合/`）" not in t3:
        t3 = t3.rstrip() + "\n" + MAP_NOTE
        n3 = 1

    print(f"  ① PAPERA_PREFLIGHT_AUDIT.md: {n1} 处")
    print(f"  ② PAPERA_REVISION_SPEC.md:   {n2} 处（新增 §7.7）")
    print(f"  ③ 文件地图.md:               {n3} 处")

    if apply:
        for p, t, keys in ((p1, t1, ["**43 页**", "## 七、最终确认"]),
                           (p2, t2, ["### 7.7", "212", "374", "+1.09"]),
                           (p3, t3, ["43 页", "**374**", "**212**", "PR-D-26-10149"])):
            io.open(p, "w", encoding="utf-8", newline="").write(t)
            s = io.open(p, encoding="utf-8").read()
            for k in keys:
                assert k in s, f"{p.name} 断言失败：缺 {k}"
        print("  ✅ 三件文档已同步并断言通过")
    else:
        print("  （预演）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
