# -*- coding: utf-8 -*-
r"""Paper A 整改 · 第 6 项：[M11] 相关性主张改为可复现口径（主 n=204 + 稳健性 n=98）。

## 操作者决策（2026-10-01）

"**两套都报（主 + 稳健性）**"——主结果用 n=204 全归档集，n=98 聚类 bootstrap 作稳健性检验。

## 数据来源（实测，非推算）

**A. 主结果** `outputs/analysis/dg_r1_reproducible.json`（脚本 `tools/p1_dg_r1_recompute.py`）
- `rule`：every `outputs/**/results.json` with finite CG/DG/R@1；一行一实验目录；
  排除路径含 `figures/comparison/strict_freeze/smoke/_void/old/backup`
- `supersedes`：**the n=81 subset used in Table 5 / Fig. 2 / the abstract, whose selection rule was lost**
- n=204 ｜ DG vs R@1 **−0.7142** ｜ CG vs R@1 **−0.5939** ｜ partial DG|CG **−0.5814** ｜ DG~CG **+0.9451**
- DG p = 0.0 ｜ CG p = 0.0 ｜ CGΔ r = **+0.1898**, p = **0.006554**（**显著**）
- 12 簇 cluster bootstrap：DG mean **−0.738**, CI **[−0.8885, −0.6128]**, frac≥0 = 0.0

**B. 稳健性** `outputs/clustered_bootstrap_dg_r1.json`（`tools/audit_clustered_bootstrap.py`）
- 输入 `outputs/master_results.json` :: `experiments[*].dg_init` vs `.R1`
- **98 experiments / 14 clusters**（cluster = 顶层实验目录）｜ naive Pearson **−0.8572**
- 10,000 重采样：r_mean **−0.8474**, CI95 **[−0.936, −0.709]**, frac≥0 = **0.0004**
- 该文件 note 明写：*replaces the earlier reported −0.819 / 94 experiments / 79 clusters figure,
  which had no local source*

## 因此必须同时修正的"旧数字错误"

旧文（`empirical.tex:97`、`conclusion.tex:5`）写的是 **−0.819、94 experiments、79 clusters、CI[−0.867,−0.759]**，
而源文件明确说那是**无本地来源的旧值**。本次一并改为 98/14/−0.8474/[−0.936,−0.709]。

    python tools\_pa_fix_correlation.py            # 预演
    python tools\_pa_fix_correlation.py --apply
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
S = REPO / "paper合" / "sections"

EDITS: list[tuple[str, str, str, str]] = [
    # ---- empirical.tex ----
    ("empirical.tex",
     "A key statistical discovery is that the Distribution Gap strongly predicts retrieval performance. "
     "Across the $n=81$ complete experiments spanning different methods, architectures, and datasets, "
     "DG achieves $r = -0.827$ with R@1, substantially outperforming CG ($r = -0.683$). "
     "Figure~\\ref{fig:corr} visualizes this relationship.",
     "A key statistical discovery is that the Distribution Gap strongly predicts retrieval performance. "
     "Across the $n=204$ archived experiments spanning different methods, architectures, and datasets, "
     "DG achieves $r = -0.714$ with R@1, substantially outperforming CG ($r = -0.594$); both are "
     "significant at $p < 0.001$. Figure~\\ref{fig:corr} visualizes this relationship. "
     "The subset is defined by an explicit reproducible rule (every archived \\texttt{results.json} with "
     "finite CG, DG and R@1), stated in the released analysis script.",
     "主结果 n=204"),
    ("empirical.tex",
     "\\caption{DG vs.\\ CG as retrieval predictors. DG achieves $r=-0.827$, substantially stronger than CG ($r=-0.683$).}",
     "\\caption{DG vs.\\ CG as retrieval predictors over the $n=204$ archived experiments. "
     "DG achieves $r=-0.714$, substantially stronger than CG ($r=-0.594$).}",
     "图注同步"),
    ("empirical.tex",
     "Controlling for CG via partial correlation, DG retains $r = -0.807$ ($p < 0.001$), confirming that DG "
     "captures distributional shape information beyond first-order centroid shift. In contrast, CG change "
     "(CG$\\Delta$) has no significant predictive power ($r = 0.012$, $p = 0.915$).",
     "Controlling for CG via partial correlation, DG retains $r = -0.581$ ($p < 0.001$), confirming that DG "
     "captures distributional shape information beyond first-order centroid shift. In contrast, the "
     "\\emph{change} in CG (CG$\\Delta$) is a weak predictor on its own ($r = 0.190$, $p = 0.007$), an order "
     "of magnitude less than DG's association with R@1.",
     "partial + CGΔ 同步（CGΔ 由 n.s. 变为显著，须如实改）"),
    ("empirical.tex",
     "To address potential concerns about non-independence among experiments sharing configurations, "
     "we performed a clustered bootstrap with configuration as the cluster unit (94 experiments, 79 clusters, "
     "10,000 resamples). The cluster-adjusted correlation is $r = -0.819$ (95\\% CI: $[-0.867, -0.759]$, "
     "$p < 0.0001$), with zero of 10,000 bootstrap samples yielding $r \\geq 0$. The DG--retrieval association "
     "is robust to within-configuration dependence; the cluster adjustment does not attenuate the correlation "
     "($-0.819$ vs.\\ the naive Pearson $-0.815$ over the same $n=94$ sample; the $n=81$ Pearson is $-0.827$).",
     "To address potential concerns about non-independence among experiments sharing configurations, we "
     "performed two resampling checks. On the $n=204$ subset, a clustered bootstrap over 12 experiment "
     "families gives $r = -0.738$ (95\\% CI: $[-0.889, -0.613]$). Independently, on the initial-state "
     "measurement set (98 experiments over 14 clusters), a 10,000-resample clustered bootstrap gives "
     "$r = -0.847$ (95\\% CI: $[-0.936, -0.709]$), with 4 of 10,000 resamples reaching $r \\geq 0$. Both "
     "checks show the DG--retrieval association surviving within-family dependence; neither attenuates it "
     "toward zero. A six-variant sensitivity analysis over sample definition (all rows, R@1 $\\geq 0.01$, "
     "legacy keyword filter, Flickr30k only) preserves the ordering DG $>$ CG in every variant.",
     "聚类 bootstrap：改 98/14/−0.8474 + 补 n=204 的 12 簇结果 + 敏感性"),
    # ---- empirical.tex 表格 ----
    ("empirical.tex",
     "\\caption{Pearson correlation between gap metrics and R@1 ($n=81$).}",
     "\\caption{Pearson correlation between gap metrics and R@1, over the $n=204$ archived experiments.}",
     "表注 n=204"),
    ("empirical.tex",
     "DG        & $\\mathbf{-0.827}$ & $\\mathbf{-0.807}$ & $<0.001$ \\\\\n"
     "CG        & $-0.683$ & --- & $<0.001$ \\\\\n"
     "CG$\\Delta$ & $+0.012$ & --- & $0.915$ (n.s.) \\\\",
     "DG        & $\\mathbf{-0.714}$ & $\\mathbf{-0.581}$ & $<0.001$ \\\\\n"
     "CG        & $-0.594$ & --- & $<0.001$ \\\\\n"
     "CG$\\Delta$ & $+0.190$ & --- & $0.007$ \\\\",
     "表内三行数值（CGΔ 由 n.s. 改为显著）"),
    # ---- introduction.tex ----
    ("introduction.tex",
     "predicts retrieval performance at $r = -0.827$, far outperforming the commonly reported Centroid Gap",
     "predicts retrieval performance at $r = -0.714$ over $n=204$ experiments, far outperforming the "
     "commonly reported Centroid Gap",
     "引言正文同步"),
    ("introduction.tex",
     "DG-based retrieval prediction ($r=-0.827$)",
     "DG-based retrieval prediction ($r=-0.714$ over $n=204$ experiments)",
     "引言贡献列表同步"),
    # ---- theory.tex ----
    ("theory.tex",
     "\\textbf{DG as a retrieval predictor.} The empirical finding that DG predicts R@1 at $r=-0.827$ "
     "(partial $r=-0.807$ controlling for CG) follows naturally from the ODE:",
     "\\textbf{DG as a retrieval predictor.} The empirical finding that DG predicts R@1 at $r=-0.714$ "
     "(partial $r=-0.581$ controlling for CG) follows naturally from the ODE:",
     "理论章引用同步"),
    # ---- conclusion.tex ----
    ("conclusion.tex",
     "that the Distribution Gap predicts retrieval performance ($r = -0.827$ over $n=81$ experiments; "
     "clustered-bootstrap estimate $r = -0.819$, 95\\% CI: $[-0.867, -0.759]$)",
     "that the Distribution Gap predicts retrieval performance ($r = -0.714$ over $n=204$ experiments; "
     "clustered-bootstrap estimates $r = -0.738$, 95\\% CI: $[-0.889, -0.613]$, and independently "
     "$r = -0.847$, 95\\% CI: $[-0.936, -0.709]$)",
     "结论同步"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    n = 0
    for fname, old, new, why in EDITS:
        p = S / fname
        t = io.open(p, encoding="utf-8").read()
        c = t.count(old)
        if c == 1:
            print(f"  ✅ {fname}: {why}")
            if apply:
                io.open(p, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
            n += 1
        elif c == 0:
            print(f"  ⚠ {fname}: 未命中（{why}）")
        else:
            print(f"  ⚠ {fname}: 命中 {c} 次（预期 1），拒绝改动")
    print(f"\n{n}/{len(EDITS)} 处{'已改' if apply else '可改'}")
    if apply:
        # 断言：旧数字清零
        bad = []
        for f in S.glob("*.tex"):
            tt = io.open(f, encoding="utf-8").read()
            for pat in ("-0.827", "-0.683", "-0.807", "0.915", "94 experiments", "79 clusters", "-0.819", "n=81"):
                if pat in tt:
                    bad.append(f"{f.name}:{pat}")
        assert not bad, f"仍有旧值残留：{bad}"
        print("✅ 断言通过：旧相关性数字已全部清除")
    else:
        print("（预演，加 --apply 生效）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
