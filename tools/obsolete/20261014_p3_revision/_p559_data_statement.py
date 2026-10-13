# -*- coding: utf-8 -*-
r"""改 Data statement：符合 PRL 的 Option C（2026-10-13）。

## PRL 的硬要求（Guide 原文）

> **Research data deposit, citation and linking** — *For this journal, **Option C** …
> you are **required** to:*
> - ***Deposit your research data in a relevant data repository.***
> - ***Cite and link to this dataset in your article.***
> - *If this is not possible, make a statement explaining why research data cannot be shared.*
>
> **Data statement** — *you are **required** to state the availability of any data at submission.*

## 现稿的问题

现 Data statement：*"…archived in the project repository, **which is currently private** and will be
made public upon publication; they are available to the reviewers on request."*

**⚠️ 不对应 Option C**：Option C 要求**存入数据仓库并引用链接**（或说明为何不能）。
"仓库现在私有、发表后公开"**既没链接也没说明不能共享的原因**。

## 改法（**如实**：写清"哪些是公共数据、哪些是我们产出的、现在怎么拿到"）

**⚠️ 关键纪律**：**不得写成"已存入仓库并给出 DOI"** —— 因为我们**还没做**。
只能写**当前的实际情况 + 明确的承诺**，并把这个缺口标出来交给操作者决定。

    python tools\_p559_data_statement.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAIN = REPO / "paper3" / "paper_ieee" / "main.tex"

OLD_RE = re.compile(r"\\section\*\{Data statement\}\s*(.*?)(?=\\section\*|\\bibliographystyle)", re.S)

NEW = r"""\section*{Data statement}
All datasets and pre-trained models used in this study are public: Alpaca, ShareGPT,
MS-COCO, Flickr30k and an ImageNet subset, together with the released weights of CLIP
ViT-B/32, LLaVA-1.5-7B, Qwen2-VL-7B and Qwen2-VL-2B. The derived data this paper relies
on---the per-run result records, the analysis scripts that compute every reported
statistic, and the training configurations---are archived in the project repository. That
repository is private while the manuscript is under review; a public archive with a
persistent identifier, linked from the published article, will be deposited on acceptance,
and the material is available to the editor and reviewers on request. We note that the
analysis does not require any non-public data: every number in the paper can be recomputed
from the public datasets and models above.

"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAIN, encoding="utf-8", errors="replace").read()
    m = OLD_RE.search(t)
    if not m:
        print("  🔴 未找到 Data statement")
        return 1
    old = m.group(1)
    print(f"  旧（{len(old)} 字符）：")
    print("    " + " ".join(old.split())[:330])
    print()
    print(f"  新（{len(NEW)} 字符）：")
    print("    " + " ".join(NEW.split())[:420])
    print()
    if not a.apply:
        print("  （预演）")
        return 0
    bak = MAIN.with_suffix(".tex.bak_p559")
    if not bak.exists():
        shutil.copy2(MAIN, bak)
    t2 = OLD_RE.sub(lambda _m: NEW, t, count=1)
    io.open(MAIN, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(MAIN, encoding="utf-8", errors="replace").read()
    checks = {
        "提到公共数据集": "are public" in t3,
        "提到我们产出的派生数据": "derived data this paper relies" in t3,
        "明确当前私有": "private while the manuscript is under review" in t3,
        "承诺公开归档 + 持久标识": "persistent identifier" in t3,
        "可向编辑与审稿人索取": "available to the editor and reviewers" in t3,
        "声明无需非公开数据": "does not require any non-public data" in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    print()
    print("  ⚠️ **未写「已存入仓库并给出 DOI」** —— 因为**尚未做**；")
    print("     若要完全满足 Option C，操作者需先真正 deposit（见收尾说明）。")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
