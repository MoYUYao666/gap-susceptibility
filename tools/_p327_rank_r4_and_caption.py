# -*- coding: utf-8 -*-
r"""查 `strict_freeze_rank/r4/both` 到底是哪 3 个 run；并定稿 caption（2026-10-12）。

## 已验证（`tools/_p325`、`_p326`）

| # | 主张 | 核实 |
|---|---|---|
| ① | OpenCLIP 行 ΔCG 来自 `strict_freeze_oclip/r4`（rank4）、R@1 来自 `strict_freeze_openclip`（rank8） | ✅ **成立**（r4 R@1=0.6366/0.6818/0.6698；rank8 R@1=**0.6428/0.6798/0.6724** → 发表 0.643/0.680/0.672） |
| ② | `CLIP B/32 r4 text_only` 的 0.621 来自**非严格冻结**的 `flickr30k_seeds/rq2_text_only` | ✅ **成立**（5-seed 均值 **0.6210**，`n_trainable = 145,170,177` ≠ 98,304） |
| ③ | `CLIP B/32 r4 both = 0.679`、`CLIP B/16 r4 text_only = 0.651` 无来源 | ✅ **成立**（容差扫描 94 个 n≥3 组；0.679 只有一个 mixed-config 巧合组；0.651 **一个都没有**） |

    python tools\_p327_rank_r4_and_caption.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
F = REPO / "paper合" / "sections" / "empirical.tex"

# 旧的（我上一版）措辞 —— 归因不准，要替换
OLD = (
    r"All twelve $\Delta$CG cells reproduce exactly from the archived per-seed JSON "
    r"(\texttt{outputs/strict\_freeze*}, $4$-decimal precision). The $R@1$ cells reproduce "
    r"exactly for CLIP B/32 and for five of the nine remaining cells; for the other four the "
    r"value printed here differs from the recomputed five-seed mean by at most $0.0064$ "
    r"(OpenCLIP text-only: $0.643$ printed against $0.6366$ recomputed). We report the "
    r"recomputed means in the archive and flag the discrepancy rather than adjust either "
    r"figure, because the archived \texttt{experiment} field does not distinguish the two "
    r"OpenCLIP runs we hold (rank-$4$ versus a larger target-module set), so the published "
    r"$R@1$ may come from a seed set we can no longer reconstruct. The $\Delta$CG column, "
    r"which is what the table's argument uses, is unaffected.")

NEW = (
    r"All twelve $\Delta$CG cells reproduce exactly from the archived per-seed JSON at "
    r"$4$-decimal precision, and the $\Delta$CG column is what the table's argument uses. The "
    r"$R@1$ column does not reproduce uniformly, and we state its provenance rather than "
    r"silently adjust it. Six cells reproduce exactly. Three cells of the OpenCLIP row "
    r"($0.643$, $0.680$, $0.672$) come from the rank-$8$ OpenCLIP archive "
    r"(\texttt{strict\_freeze\_openclip}) while that row's $\Delta$CG comes from the rank-$4$ "
    r"archive (\texttt{strict\_freeze\_oclip/r4}), so the two halves of that row were not "
    r"measured on the same configuration. One cell, CLIP B/32$^\dagger$ text-only ($0.621$), "
    r"equals the non-strict \texttt{flickr30k\_seeds/rq2\_text\_only} five-seed mean "
    r"($0.6210$, $145{,}170{,}177$ trainable parameters) rather than the strict-freezing mean "
    r"for that cell ($0.6222$, $98{,}304$ trainable parameters). Two cells, CLIP B/32$^\dagger$ "
    r"both-position ($0.679$) and CLIP B/16$^\dagger$ text-only ($0.651$), do not match the "
    r"strict-freezing archive to the printed precision: the recomputed means are $0.6796$ and "
    r"$0.6502$. An exhaustive scan of the $94$ archived groups with at least three runs finds "
    r"no group whose mean rounds to $0.651$; the only group whose mean rounds to $0.679$ is a "
    r"three-seed subset (\texttt{strict\_freeze\_rank/r4/both}, seeds $42$/$123$/$456$, "
    r"$0.6797$), which is not the five-seed cell this row reports. We therefore flag both "
    r"$R@1$ entries as not reproducible from the archive at the printed precision and give the "
    r"recomputed value in the text beside it.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    print("=" * 100)
    print("① strict_freeze_rank/r4/both 的 3 个 run 是什么")
    print("=" * 100)
    for f in sorted(glob.glob(str(REPO / "outputs" / "strict_freeze_rank" / "r4" / "both"
                                  / "**" / "results.json"), recursive=True)):
        d = json.loads(io.open(f, encoding="utf-8", errors="replace").read())
        print(f"  seed={d.get('seed')}  R@1={(d.get('final_task_metrics') or {}).get('R@1')}  "
              f"n_tr={d.get('n_trainable_params')}  {Path(f).relative_to(REPO)}")

    print()
    print("=" * 100)
    print("② 替换 caption 里的归因段")
    print("=" * 100)
    t = io.open(F, encoding="utf-8", errors="replace").read()
    n = t.count(OLD)
    print(f"  旧段命中 {n}")
    if n != 1:
        print("  🔴 未命中，需人工处理")
        return 1
    t2 = t.replace(OLD, NEW)
    if not a.apply:
        print("  （预演）")
        return 0
    bak = F.with_suffix(".tex.bak_p327")
    if not bak.exists():
        shutil.copy2(F, bak)
    io.open(F, "w", encoding="utf-8", newline="").write(t2)
    t3 = io.open(F, encoding="utf-8", errors="replace").read()
    checks = {
        "新段在": "unreproducible from the archive" in t3,
        "旧段已去": OLD not in t3,
        "含 rank-8 归因": "rank-$8$ OpenCLIP archive" in t3,
        "含非严格冻结归因": "145{,}170{,}177" in t3,
    }
    ok = True
    for k, v in checks.items():
        print(f"  {'✅' if v else '🔴'} {k}")
        ok = ok and v
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
