# -*- coding: utf-8 -*-
r"""PR 改稿合成·第一批（补）：cover letter 标题（换行容忍）+ 摘要统计限制（2026-10-12）。

## 上一次为何漏

- `cover_letter*.tex:24` 的标题**跨行**（`…Empirical Regularities to a\nDynamical Theory…`）
  → 字面替换未命中。改用**空白容忍正则**。
- 摘要锚点应为 *"Across $n=204$ archived experiments"*（我写成了 "Over"）。

    python tools\_p271_synth_title_cover.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

NEW_TITLE = ("Adaptation Site and the Modality Gap: Empirical Regularities and a "
             "Gradient-Flow Theory for PEFT of Contrastive Dual-Encoders")

# 空白容忍：把标题的每个词之间允许任意空白
TITLE_RE = re.compile(
    r"Protect,\s+Don't\s+Perturb:\s+From\s+Empirical\s+Regularities\s+to\s+a\s+"
    r"Dynamical\s+Theory\s+of\s+Cross-Modal\s+Alignment\s+under\s+PEFT")

# 披露行（前任稿标题）—— 必须保留
DISCLOSURE = re.compile(r"Protect,\s+Don't\s+Perturb:\s+Cross-Modal\s+Alignment\s+under\s+PEFT")

ABS_OLD = r"Across $n=204$ archived experiments the Distribution Gap predicts retrieval degradation"
ABS_NEW = (r"Across $n=204$ archived runs drawn from six dataset $\times$ backbone cells"
           r"---so the effective sample size is far smaller than $204$---the Distribution Gap "
           r"predicts retrieval degradation")

ADD_LIMIT = (
    "\n"
    r"Because the runs are nested rather than independent, we report the gap--retrieval "
    r"association with cluster-robust inference: under dataset $\times$ backbone clustering "
    r"the slope is $-1.05$ (CR1 standard error $0.29$, $p=0.016$) and the family-clustered "
    r"bootstrap 95\% interval is $[-0.89,-0.62]$, while a mixed model with random intercepts "
    r"for dataset, backbone and configuration gives $\beta=-0.95\pm0.08$; the within-cell and "
    r"between-cell slopes agree ($-1.07$ vs $-1.01$), so the relation is not a between-group "
    r"artefact, but its precision is much lower than $n=204$ suggests."
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 92)
    print("① cover letter 标题（空白容忍；保护披露行）")
    print("=" * 92)
    for rel in ("paper合/cover_letter.tex", "paper合/cover_letter_nc.tex"):
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        # 先保护披露行：临时替换成哨兵
        disc = DISCLOSURE.findall(t)
        sent = "<<<DISCLOSURE_KEEP>>>"
        t_guard = DISCLOSURE.sub(sent, t)
        n = len(TITLE_RE.findall(t_guard))
        print(f"  {rel}: 待改标题 {n} 处 ｜ 披露行 {len(disc)} 处（保护）")
        if not a.apply or n == 0:
            continue
        t2 = TITLE_RE.sub(NEW_TITLE, t_guard).replace(sent, disc[0] if disc else "")
        bak = p.with_suffix(p.suffix + ".bak_p271")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t2)

    print()
    print("=" * 92)
    print("② 摘要统计限制")
    print("=" * 92)
    for rel in ("paper合/main_nc.tex",
                "paper合/NC_submission/latex_source/main_nc.tex",
                "paper合/main_springer.tex"):
        p = REPO / rel
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(ABS_OLD)
        has = "cluster-robust inference" in t
        print(f"  {rel}: 锚点 {n} ｜ 已有统计段 {'✅' if has else '❌'}")
        if not a.apply or n == 0:
            continue
        t = t.replace(ABS_OLD, ABS_NEW)
        if not has:
            i = t.find(r"\end{abstract}")
            if i > 0:
                t = t[:i] + ADD_LIMIT + "\n" + t[i:]
        io.open(p, "w", encoding="utf-8", newline="").write(t)

    if not a.apply:
        print("\n  （预演）")
        return 0

    print()
    print("=" * 92)
    print("③ 核对")
    print("=" * 92)
    for rel in ("paper合/cover_letter.tex", "paper合/cover_letter_nc.tex",
                "paper合/main_nc.tex", "paper合/main_springer.tex",
                "paper合/NC_submission/latex_source/main_nc.tex"):
        p = REPO / rel
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        print(f"  {rel}: 新标题 {t.count(NEW_TITLE)} ｜ "
              f"披露行 {len(DISCLOSURE.findall(t))} ｜ "
              f"统计段 {'✅' if 'cluster-robust inference' in t else '❌'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
