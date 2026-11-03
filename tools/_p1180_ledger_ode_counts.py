# -*- coding: utf-8 -*-
r"""Point the claim ledger at the per-run ODE archive instead of the mixed 215-fit audit.

The ledger asserted three numbers that the manuscript no longer quotes (`215` fits, `196` negative, `19` exceptions)
against `outputs/analysis/alpha_stats_current.json`, which is a **sum of five archives**: ledger 96 + LOCO 33 + LOCO2
33 (the same 33 configurations twice) + Adapter 50 + BitFit 3. That is both double-counted and a different
population from the per-run fits the paper now relies on.

After the 2026-10-17 simplification the paper states 96 fits / 92 negative / 4 exceptions, all of which are
recomputable from `outputs/analysis/ode_ledger.json`. This patch swaps the assertions accordingly and rewrites the
`383 = 221 + 162` arithmetic record as `317 = 221 + 96`, sourced from the same file.

    python tools/_p1180_ledger_ode_counts.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "tools" / "_claim_ledger_paperA.py"

OLD_FITS = '''    cur = j("outputs/analysis/alpha_stats_current.json")
    record("fits archived (paper, after the correction)", 215, cur["total"],
           "outputs/analysis/alpha_stats_current.json :: total "
           "[= ledger 96 + loco 33 + loco2 33 + adapter 50 + bitfit 3]",
           cur["total"] == 215, f"[the 2026-10-05 audit recorded {tot_aud}]")
    record("fits with negative alpha", 196, cur["negative"],
           "outputs/analysis/alpha_stats_current.json :: negative",
           cur["negative"] == 196)
    record("non-negative exceptions", 19, cur["exceptions"],
           "outputs/analysis/alpha_stats_current.json :: exceptions",
           cur["exceptions"] == 19)
'''

NEW_FITS = '''    # 2026-10-17 (operator decision A): the paper quotes the per-run ODE ledger, not the mixed audit. The old
    # alpha_stats_current.json summed ledger 96 + LOCO 33 + LOCO2 33 (the same 33 twice) + Adapter 50 + BitFit 3,
    # which is double-counted and is a different population from the per-run fits; it is kept on disk as history.
    od = j("outputs/analysis/ode_ledger.json")
    od_runs = od["runs"]
    od_neg = sum(1 for r in od_runs if r["alpha"] < 0)
    od_pos_fams = sorted({r["family"] for r in od_runs if r["alpha"] >= 0})
    od_pos_n = sum(1 for r in od_runs if r["alpha"] >= 0)
    lora_runs = [r for r in od_runs if r["family"] == "lora"]
    lora_neg = sum(1 for r in lora_runs if r["alpha"] < 0)
    record("ODE fits archived", 96, len(od_runs),
           "outputs/analysis/ode_ledger.json :: n_runs_total", len(od_runs) == 96,
           f"[the 2026-10-05 mixed audit recorded {tot_aud}]")
    record("ODE fits with negative alpha", 92, od_neg,
           "outputs/analysis/ode_ledger.json :: runs[].alpha < 0 (recomputed)", od_neg == 92)
    record("ODE fits with non-negative alpha", 4, od_pos_n,
           "outputs/analysis/ode_ledger.json :: runs[].alpha >= 0 (recomputed)", od_pos_n == 4)
    record("all non-negative fits are Adapter", "adapter", od_pos_fams,
           "outputs/analysis/ode_ledger.json :: family of the non-negative fits",
           od_pos_fams == ["adapter"])
    record("LoRA fits all negative", f"{len(lora_runs)}/{len(lora_runs)}", f"{lora_neg}/{len(lora_runs)}",
           "outputs/analysis/ode_ledger.json :: runs[family=lora].alpha",
           lora_neg == len(lora_runs) == 55)
'''

OLD_383 = '''    # the paper's 383 = catalogue 221 + 162 ODE fits
    record("validation experiments = 221 + ODE fits", 383, 221 + 162,
           "HANDOFF L10192: 'catalogue + ODE = 221 + 162 = 383'", 221 + 162 == 383)
'''

NEW_383 = '''    # 2026-10-17: 317 = catalogue 221 + the 96 per-run ODE fits actually archived (the old 162 had no archive)
    record("validation experiments = catalogue + ODE fits", 317, 221 + int(od["n_runs_total"]),
           "supplement.tex::tab:full_experiments Total (221) + ode_ledger.json::n_runs_total (96)",
           221 + int(od["n_runs_total"]) == 317)
'''

OLD_NOTE = '''        print("     稿件已按 215 / 196 改写，并保留「19 个例外」不变（实测仍为 19）。")'''
NEW_NOTE = '''        print("     ⚠️ 2026-10-17 已改为按逐 run ODE 台账：96 fits / 92 negative / 4 exceptions（全为 Adapter）；")
        print("        旧的 215/196/19 来自 alpha_stats_current.json 的五档求和（含 LOCO 重复计 33），已作废。")'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(P, encoding="utf-8").read()
    if "the paper quotes the per-run ODE ledger" in t:
        print("  already patched")
        return 0
    for old, new, label in ((OLD_FITS, NEW_FITS, "fits block"), (OLD_383, NEW_383, "383 record"),
                            (OLD_NOTE, NEW_NOTE, "historical note")):
        n = t.count(old)
        print(f"  {label}: occurrences {n}")
        if n != 1:
            print("  !! expected exactly one occurrence")
            return 1
        t = t.replace(old, new, 1)
    ast.parse(t)
    print("  patched block parses")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(P, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
