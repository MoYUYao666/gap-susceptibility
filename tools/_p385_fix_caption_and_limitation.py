# -*- coding: utf-8 -*-
r"""更正 `tab:position_strict` caption 的错误定性 + 加画廊抽样 limitation（2026-10-12）。

## 为什么必须改

我在 caption 里写了"**2 格在归档中无来源**"（`unreproducible from the archive`）。
**画廊噪声量化后**（`outputs/analysis/gallery_noise_cg.json`）：
- **R@1 抽样 sd = 0.00714**（6 次重复，300 对）
- 我观察到的 6 格差异是 **0.0006–0.0064** → **全部在 1 sd 内**

→ **"无来源"的定性过重**，正确表述是"**差异在评测抽样噪声内**"。
**这是我自己定性错误，必须更正。**

## 根因（已在源码层确认）

`src/dataset.py::create_dataloaders` 用 `random_split` 切 Flickr30k，
而 `random_split` 返回的 `Subset` **保留**被包装 `Flickr30kDataset` 的 `transform`，
该对象是以 `split="train"` 建的 → **val/test 画廊继承 `RandomHorizontalFlip(0.5)` + `ColorJitter`**
→ **每次评测是不同抽样**。

    python tools\_p385_fix_caption_and_limitation.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
E = REPO / "paper合" / "sections" / "empirical.tex"
D = REPO / "paper合" / "sections" / "discussion.tex"

CAP_OLD = (
    r"Two cells, CLIP B/32$^\dagger$ both-position ($0.679$) and CLIP B/16$^\dagger$ "
    r"text-only ($0.651$), do not match the strict-freezing archive to the printed precision: "
    r"the recomputed means are $0.6796$ and $0.6502$. An exhaustive scan of the $94$ archived "
    r"groups with at least three runs finds no group whose full-seed mean rounds to $0.651$ or "
    r"to $0.679$. Three-seed subsets of those groups can be found that round to either value, "
    r"but we do not treat that as provenance: of the $4581$ three-seed subsets available, $39$ "
    r"round to $0.651$ and $43$ to $0.679$, so subset matching carries no evidential weight at "
    r"this precision. The comparison this table supports rests on the $\Delta$CG column, which "
    r"reproduces exactly for all twelve cells.")

CAP_NEW = (
    r"The remaining $R@1$ entries differ from the five-seed means by at most $0.0064$, which is "
    r"within the evaluation sampling noise of this protocol: the retrieval gallery inherits the "
    r"training-time random transforms (Section~\ref{sec:discussion}), so repeated evaluation of "
    r"one checkpoint gives $R@1$ a standard deviation of $0.007$ over $300$ pairs while "
    r"$\mathrm{CG}$ varies by only $0.0005$. The comparison this table supports therefore rests "
    r"on the $\Delta$CG column, which reproduces exactly for all twelve cells and whose sampling "
    r"noise is two orders of magnitude below the between-arm differences.")

LIM = (
    "\n\n"
    r"Twelfth, the retrieval gallery used throughout is built by \texttt{random\_split} over a "
    r"dataset object that was constructed with the training split, so the gallery inherits the "
    r"training-time random transforms (horizontal flip and colour jitter); a checkpoint "
    r"re-evaluated on it is therefore a fresh draw rather than a fixed measurement. We "
    r"quantified the consequence: over six repeats of one frozen checkpoint on $300$ pairs, the "
    r"Centroid Gap has a standard deviation of $0.0005$ and $R@1$ a standard deviation of "
    r"$0.007$. The $\Delta\mathrm{CG}$ comparisons this paper rests on are unaffected, because "
    r"the between-arm differences they use are $40$--$100$ times that noise, but $R@1$ "
    r"differences below about $0.007$ should not be interpreted, and the $R@1$ column of "
    r"Table~\ref{tab:position_strict} should be read as one draw from this distribution rather "
    r"than as a reproducible value. Fixing the gallery to a deterministic evaluation transform "
    r"is a change we recommend for future work but have not applied retrospectively, because it "
    r"would alter archived numbers without repairing the archive.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    ok = True

    # ① caption 更正
    t = io.open(E, encoding="utf-8", errors="replace").read()
    n = t.count(CAP_OLD)
    print(f"  caption 旧段命中 {n}")
    if n == 1:
        if a.apply:
            bak = E.with_suffix(".tex.bak_p365")
            if not bak.exists():
                shutil.copy2(E, bak)
            io.open(E, "w", encoding="utf-8", newline="").write(t.replace(CAP_OLD, CAP_NEW))
            print("  ✅ caption 已更正")
    elif "within the evaluation sampling noise of this protocol" in t:
        print("  caption 已更正过")
    else:
        print("  🔴 caption 未命中")
        ok = False

    # ② limitation
    t2 = io.open(D, encoding="utf-8", errors="replace").read()
    if "the retrieval gallery used throughout is built by" in t2:
        print("  limitation 已存在")
    else:
        anchor = r"Tenth, our cross-method comparison is made at one shared learning rate"
        if anchor in t2 and a.apply:
            bak = D.with_suffix(".tex.bak_p365")
            if not bak.exists():
                shutil.copy2(D, bak)
            io.open(D, "w", encoding="utf-8", newline="").write(t2.replace(anchor, LIM.strip() + "\n\n" + anchor, 1))
            print("  ✅ limitation 已加入（Twelfth）")
        elif anchor not in t2:
            print("  🔴 limitation 锚点未命中")
            ok = False

    if not a.apply:
        print("  （预演）")
        return 0
    e3 = io.open(E, encoding="utf-8", errors="replace").read()
    d3 = io.open(D, encoding="utf-8", errors="replace").read()
    checks = {
        "caption 不再说 'no group whose full-seed mean rounds'":
            "no group whose full-seed mean rounds" not in e3,
        "caption 含抽样噪声解释": "within the evaluation sampling noise" in e3,
        "caption 含 0.007": "$0.007$" in e3,
        "limitation 含 gallery 段": "the retrieval gallery used throughout is built by" in d3,
        "limitation 含 40--100 倍": "$40$--$100$" in d3,
    }
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
