# -*- coding: utf-8 -*-
r"""Add the rank-rerun assertions to the Paper A claim ledger.

The paper now cites the rerun's numbers (dCG +0.0135 at rank 2 falling to +0.0021 at rank 64, R@1
0.6071 to 0.6122, adapters of 196,608 r/8 parameters), so each of them has to be asserted against
outputs/analysis/rank_rerun.json the way every other number in the paper is.

    python tools/_p810_ledger_rank.py --apply
"""
from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LEDGER = REPO / "tools" / "_claim_ledger_paperA.py"

ANCHOR = '    print()\n    print("  --- §6：逐方法调参后的零样本准确率 ---")'

BLOCK = '''    print()
    print("  --- §4：rank 消融重跑（真 LoRA，冻结基座）---")
    rr = j("outputs/analysis/rank_rerun.json")
    by_rank = {r["rank"]: r for r in rr["runs"]}
    record("adapter size scales as 196,608 x r/8 (rank 8)", 196608,
           by_rank[8]["n_trainable_params"],
           "outputs/analysis/rank_rerun.json :: rank 8 n_trainable_params",
           by_rank[8]["n_trainable_params"] == 196608)
    record("rank 2 adapter holds 49,152", 49152, by_rank[2]["n_trainable_params"],
           "outputs/analysis/rank_rerun.json :: rank 2 n_trainable_params",
           by_rank[2]["n_trainable_params"] == 49152)
    record("rank 64 adapter holds 1,572,864", 1572864, by_rank[64]["n_trainable_params"],
           "outputs/analysis/rank_rerun.json :: rank 64 n_trainable_params",
           by_rank[64]["n_trainable_params"] == 1572864)
    record("dCG at rank 2 (paper states +0.0135)", 0.0135, round(by_rank[2]["dCG"], 4),
           "outputs/analysis/rank_rerun.json :: rank 2 dCG",
           abs(by_rank[2]["dCG"] - 0.0135) <= 0.0001)
    record("dCG at rank 64 (paper states +0.0021)", 0.0021, round(by_rank[64]["dCG"], 4),
           "outputs/analysis/rank_rerun.json :: rank 64 dCG",
           abs(by_rank[64]["dCG"] - 0.0021) <= 0.0001)
    record("R@1 at rank 2 (paper states 0.6071)", 0.6071, round(by_rank[2]["R@1"], 4),
           "outputs/analysis/rank_rerun.json :: rank 2 R@1",
           abs(by_rank[2]["R@1"] - 0.6071) <= 0.0001)
    record("R@1 at rank 16 (paper states 0.6122)", 0.6122, round(by_rank[16]["R@1"], 4),
           "outputs/analysis/rank_rerun.json :: rank 16 R@1",
           abs(by_rank[16]["R@1"] - 0.6122) <= 0.0001)

'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(LEDGER, encoding="utf-8").read()
    if "rank 消融重跑（真 LoRA，冻结基座）" in t:
        print("  already present")
        return 0
    if ANCHOR not in t:
        print("  !! anchor not found")
        return 1
    if not a.apply:
        print("  (dry run) anchor found, would insert 7 assertions")
        return 0
    bak = LEDGER.with_suffix(".py.bak_p810")
    if not bak.exists():
        shutil.copy2(LEDGER, bak)
    io.open(LEDGER, "w", encoding="utf-8", newline="").write(t.replace(ANCHOR, BLOCK + ANCHOR, 1))
    print("  inserted")
    t2 = io.open(LEDGER, encoding="utf-8").read()
    for k in ("rank 消融重跑（真 LoRA，冻结基座）", "196,608 x r/8", "dCG at rank 64"):
        print(f"  {'OK ' if k in t2 else 'BAD'} {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
