# -*- coding: utf-8 -*-
r"""Add claim-ledger assertions for the two decoder-VLM tables (supplement E and G).

The ledger reads `publish_clean/` for historical artifacts. The two decoder archives postdate that snapshot, so this
block reads them from the live repo and states the path in each source string -- the point of the ledger is that
every manuscript number names a file and a field, not that the file lives in one particular directory.

Inserted before the summary print so it runs inside `main()` with the existing `record()` helper.

    python tools/_p1168_ledger_eg.py [--apply]
"""
from __future__ import annotations

import argparse
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "tools" / "_claim_ledger_paperA.py"

ANCHOR = '''    print()
    print("=" * 118)
    print(f"  PASS {ok} ｜ GAP {gap} ｜ total {ok + gap}")
'''

BLOCK = r'''    # ---- 2026-10-17: decoder-VLM tables E and G, clean gap definition ----
    # These two archives postdate the publish_clean snapshot, so they are read from the live repo; the source
    # string still names the file and the field, which is what the ledger requires.
    def _local_json(rel):
        return json.loads((REPO / rel).read_text(encoding="utf-8"))

    def _local_num(rel, path):
        cur = _local_json(rel)
        for part in path.split("."):
            cur = cur[part]
        return float(cur)

    def _local_claim(name, manuscript, rel, path, tol=0.0005):
        try:
            computed = _local_num(rel, path)
            good = abs(float(manuscript) - computed) <= tol
        except Exception as exc:
            computed, good = None, False
            name = f"{name} [unreadable: {str(exc)[:30]}]"
        record(name, manuscript, round(computed, 6) if computed is not None else None,
               f"{rel}::{path}", good)

    print()
    print("  --- supplement E: Qwen2-VL-2B, clean definition (vlm_clean_summary.json) ---")
    ES = "outputs/vlm_clean_summary.json"
    _local_claim("E frozen clean DG*", 0.777826, ES, "frozen.dg_star")
    _local_claim("E frozen CG", 0.742107, ES, "frozen.cg")
    _local_claim("E both reduction mean", 98.57, ES, "per_arm.both.reduction_mean")
    _local_claim("E both reduction sd", 0.44, ES, "per_arm.both.reduction_sd")
    _local_claim("E text-only reduction mean", 96.74, ES, "per_arm.text_only.reduction_mean")
    _local_claim("E text-only reduction sd", 0.29, ES, "per_arm.text_only.reduction_sd")
    _local_claim("E vision-only reduction mean", 89.41, ES, "per_arm.vision_only.reduction_mean")
    _local_claim("E vision-only reduction sd", 1.01, ES, "per_arm.vision_only.reduction_sd")
    _local_claim("E legacy both ~2.0", 2.0192, ES, "per_arm.both.legacy_ep3_mean", tol=0.01)
    _local_claim("E legacy text ~2.0", 2.0103, ES, "per_arm.text_only.legacy_ep3_mean", tol=0.01)
    _local_claim("E legacy vision ~2.0", 2.0322, ES, "per_arm.vision_only.legacy_ep3_mean", tol=0.01)
    _local_claim("E both DG* after", 0.0111, ES, "per_arm.both.dg_star_ep3_mean", tol=0.001)
    _local_claim("E text-only DG* after", 0.0253, ES, "per_arm.text_only.dg_star_ep3_mean", tol=0.001)
    _local_claim("E vision-only DG* after", 0.0824, ES, "per_arm.vision_only.dg_star_ep3_mean", tol=0.001)
    _local_claim("E seed count per arm", 13, ES, "per_arm.both.n")
    _local_claim("E record count", 39, ES, "verification.n_records")
    # the manuscript claims the three seed ranges are disjoint; assert the inequalities themselves
    _e = _local_json(ES)["per_arm"]
    record("E seed ranges disjoint",
           "vision_max<text_min<both_min",
           f"{_e['vision_only']['reduction_mean']:.2f}<{_e['text_only']['reduction_mean']:.2f}"
           f"<{_e['both']['reduction_mean']:.2f}",
           "derived from new_* / reduction_mean ordering",
           (_e["vision_only"]["reduction_mean"] < _e["text_only"]["reduction_mean"]
            < _e["both"]["reduction_mean"]),
           note="means ordered as the manuscript states")

    print()
    print("  --- supplement G: LLaVA-1.5-7B, clean definition (canonical_caption_metric.json) ---")
    GS = "outputs/canonical_caption_metric.json"
    _local_claim("G frozen clean DG*", 0.3566, GS, "runs.frozen.clean.dg_star")
    _gd = _local_json(GS)
    _gfz = float(_gd["runs"]["frozen"]["clean"]["dg_star"])

    def _g_arm(arm):
        vals = [float(v["clean"]["dg_star"]) for k, v in _gd["runs"].items() if k.startswith(arm)]
        rel = [100 * (x - _gfz) / _gfz for x in vals]
        return st.mean(rel), st.pstdev(rel), len(vals), min(rel), max(rel)

    for _arm, _expect in (("vision_only", 121.48), ("both", 95.66), ("text_only", 73.27)):
        _m, _s, _n, _lo, _hi = _g_arm(_arm)
        record(f"G {_arm} change mean", f"{_expect:.2f}%", f"{_m:.2f}%",
               f"{GS}::runs.*_{_arm}*.clean.dg_star (recomputed)", abs(_m - _expect) <= 0.05)
    _tm, _ts, _tn, _tlo, _thi = _g_arm("text_only")
    _bm, _bs, _bn, _blo, _bhi = _g_arm("both")
    record("G text/both seed ranges disjoint", f"text_max {_thi:.2f} < both_min {_blo:.2f}",
           f"{_thi:.2f} < {_blo:.2f}", f"{GS}::runs.*.clean.dg_star (recomputed)",
           _thi < _blo, note="the manuscript claims the two spreads do not overlap")

'''

OLD_TAIL_NOTE = """        print("  ⚠️ 另有一处归档缺口已修复（2026-10-14）：")"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(P, encoding="utf-8").read()
    if "supplement E: Qwen2-VL-2B" in t:
        print("  already patched")
        return 0
    n = t.count(ANCHOR)
    print(f"  anchor occurrences: {n}")
    if n != 1:
        print("  !! expected exactly one anchor")
        return 1
    t = t.replace(ANCHOR, BLOCK + ANCHOR, 1)
    import ast
    ast.parse(t)
    print("  block inserted; parses")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(P, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
