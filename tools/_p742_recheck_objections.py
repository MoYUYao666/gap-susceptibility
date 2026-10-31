# -*- coding: utf-8 -*-
r"""Re-check the Pattern Recognition objections that the first pass flagged, with better patterns.

The first pass used narrow regexes, so several "TODO" markers may be false alarms (the paper may
write "mixed model" rather than "mixed-effects"). This checks each remaining objection against the
actual wording, and reports what still looks unanswered after reading the context.

    python tools/_p742_recheck_objections.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PA = REPO / "paper合"
OUT = REPO / "outputs" / "analysis" / "pr_objections_recheck.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    parts = [("main_nc.tex", io.open(PA / "main_nc.tex", encoding="utf-8", errors="replace").read())]
    for p in sorted((PA / "sections").glob("*.tex")):
        parts.append((p.name, io.open(p, encoding="utf-8", errors="replace").read()))
    all_text = "\n".join(t for _, t in parts)

    def find(label, pattern, window=230, limit=6):
        print("=" * 108)
        print(f"{label}")
        print(f"  pattern: /{pattern}/")
        print("=" * 108)
        total = 0
        for name, t in parts:
            for m in re.finditer(pattern, t, re.I):
                total += 1
                if total > limit:
                    break
                ln = t[:m.start()].count("\n") + 1
                seg = " ".join(t[max(0, m.start() - 120):m.start() + window].split())
                print(f"  {name}:{ln}")
                print(f"     ...{seg[:300]}...")
            if total > limit:
                break
        if not total:
            print("  NO MATCH")
        print()
        return total

    print()
    r = {}
    r["mixed_model"] = find("R1-W2 / R3-2  mixed / hierarchical model",
                            r"mixed[- ]?model|random[- ]intercept|hierarch\w+ model", limit=4)
    r["held_out"] = find("R3-2  held-out validation of the association",
                         r"held[- ]?out|hold[- ]?out|leave[- ]one[- ](?:config|family|cell|design)|"
                         r"out[- ]of[- ]sample", limit=5)
    r["early_stopping"] = find("R1-W5 / R2-5  DG-guided early stopping positioning",
                               r"early stopping|DG-ES|early[- ]stop", limit=5)
    r["route_d"] = find("R1-W1  Route D / config-hash disclosure",
                        r"Route~?D|route_d|configuration hash|config hash|"
                        r"target modules|q_?proj|v_?proj", limit=5)
    r["stratified"] = find("R1  stratified DG-R@1 by model or dataset",
                           r"stratified|within[- ](?:family|dataset|model|cell)|"
                           r"group[- ](?:wise|level)|per[- ](?:family|dataset|model)",
                           limit=5)
    r["compaction"] = find("R2-2  compact presentation of figures and tables",
                           r"consolidat|compact|Appendix~?[A-Z]|supplementar", limit=4)

    print("=" * 108)
    print("counts")
    print("=" * 108)
    for k, v in r.items():
        print(f"  {k:<18} {v}")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(r, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
