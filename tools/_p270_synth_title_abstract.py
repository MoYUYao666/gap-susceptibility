# -*- coding: utf-8 -*-
r"""PR 改稿合成·第一批：标题收窄（R2.1）+ 摘要补统计限制（R1.2/R3.2）（2026-10-12）。

## 决定（操作者"全改对"，由 Lead 定）

- **标题 = T1**：*Adaptation Site and the Modality Gap: Empirical Regularities and a
  Gradient-Flow Theory for PEFT of Contrastive Dual-Encoders*
  （去掉祈使句的处方暗示；把模型族写进标题；两半贡献都保留）
- **摘要补统计限制**：把"204 个实验"改成"204 archived runs drawn from 6 dataset × backbone
  cells"，并给出聚类后的区间——直接回应 R1.2/R3.2。

## 标题只改"本文自己的标题"
**不动** `cover_letter*.tex:78` —— 那里引的是**前任稿 P1** 的标题，属披露信息。

    python tools\_p270_synth_title_abstract.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

OLD_TITLE = ("Protect, Don't Perturb: From Empirical Regularities to a Dynamical Theory of "
             "Cross-Modal Alignment under PEFT")
NEW_TITLE = ("Adaptation Site and the Modality Gap: Empirical Regularities and a "
             "Gradient-Flow Theory for PEFT of Contrastive Dual-Encoders")
OLD_SHORT = r"\title[Protect, Don't Perturb]{"
NEW_SHORT = r"\title[Adaptation Site and the Modality Gap]{"

TITLE_TARGETS = [
    "paper合/main_nc.tex",
    "paper合/NC_submission/latex_source/main_nc.tex",
    "paper合/main_springer.tex",
    "paper合/highlights_nc.tex",
    "paper合/cover_letter.tex",
    "paper合/cover_letter_nc.tex",
]

# 摘要：把"204 个独立实验"的措辞改为带聚类限制的版本
ABS_OLD = (r"Over $n=204$ archived experiments")
ABS_NEW = (r"Over $n=204$ archived runs drawn from six dataset $\times$ backbone cells "
           r"(so the effective sample size is far smaller than $204$)")

ADD_LIMIT = (
    "\n\n"
    r"The gap--retrieval association is reported with cluster-robust inference: under "
    r"dataset $\times$ backbone clustering the slope is $-1.05$ with a CR1 standard error of "
    r"$0.29$ ($p=0.016$), and the family-clustered bootstrap 95\% interval is $[-0.89,-0.62]$."
)


def sha(p: Path) -> str:
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 92)
    print("① 标题（6 处；跳过 cover_letter*:78 的披露）")
    print("=" * 92)
    for rel in TITLE_TARGETS:
        p = REPO / rel
        if not p.exists():
            print(f"  ❌ 缺 {rel}")
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n_long = t.count(OLD_TITLE)
        n_short = t.count(OLD_SHORT)
        # 披露行保护：若某次出现位于 "predecessor" 附近则不动
        guarded = 0
        if n_long:
            idx, keep = 0, []
            while True:
                i = t.find(OLD_TITLE, idx)
                if i < 0:
                    break
                ctx = t[max(0, i - 300):i]
                if "predecessor" in ctx.lower():
                    guarded += 1
                    keep.append(i)
                idx = i + 1
            if keep:
                print(f"  ⚠️ {rel}: 有 {guarded} 处位于 'predecessor' 披露语境 → 保留")
        print(f"  {rel}: 长标题 {n_long} 处（保护 {guarded}）｜ 短标题 {n_short} 处")
        if not a.apply:
            continue
        if n_long == 0 and n_short == 0:
            continue
        # 逐处替换，跳过披露
        out, idx = [], 0
        while True:
            i = t.find(OLD_TITLE, idx)
            if i < 0:
                out.append(t[idx:])
                break
            ctx = t[max(0, i - 300):i]
            if "predecessor" in ctx.lower():
                out.append(t[idx:i + len(OLD_TITLE)])
            else:
                out.append(t[idx:i] + NEW_TITLE)
            idx = i + len(OLD_TITLE)
        t2 = "".join(out)
        if n_short:
            t2 = t2.replace(OLD_SHORT, NEW_SHORT)
        bak = p.with_suffix(p.suffix + ".bak_p270")
        if not bak.exists():
            shutil.copy2(p, bak)
        io.open(p, "w", encoding="utf-8", newline="").write(t2)

    print()
    print("=" * 92)
    print("② 摘要：统计限制")
    print("=" * 92)
    for rel in ("paper合/main_nc.tex", "paper合/NC_submission/latex_source/main_nc.tex",
                "paper合/main_springer.tex"):
        p = REPO / rel
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        n = t.count(ABS_OLD)
        has_limit = "cluster-robust inference" in t
        print(f"  {rel}: 锚点 {n} ｜ 已有统计限制段 {'✅' if has_limit else '❌'}")
        if not a.apply or n == 0:
            continue
        t = t.replace(ABS_OLD, ABS_NEW)
        if not has_limit:
            # 插在 abstract 结束前
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
    for rel in TITLE_TARGETS:
        p = REPO / rel
        if not p.exists():
            continue
        t = io.open(p, encoding="utf-8", errors="replace").read()
        old_n = t.count(OLD_TITLE)
        new_n = t.count(NEW_TITLE)
        disc = t.count("Protect, Don't Perturb: Cross-Modal Alignment under PEFT")
        print(f"  {rel}: 旧长标题 {old_n}（应=披露数）｜ 新标题 {new_n} ｜ 披露 {disc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
