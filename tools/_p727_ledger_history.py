# -*- coding: utf-8 -*-
r"""Find out why ode_ledger.json went from 103 runs (the audit) to 96 (now).

The audit recorded n = 103 for this file with 4 non-negative entries; the file now holds 96 with
the same 4 non-negative values (max 0.010505). So seven runs disappeared, and the paper's 222
depends on which version is authoritative.

This walks the file's git history, reading its run count at each revision, and identifies which
runs were dropped by comparing the last 103-run revision with the current 96-run one.

    python tools/_p727_ledger_history.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PUB = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "ledger_history.json"


def git(*args):
    r = subprocess.run(["git"] + list(args), cwd=str(PUB), capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    rel = "outputs/analysis/ode_ledger.json"
    rc, out = git("log", "--format=%H %ad %s", "--date=short", "--", rel)
    revs = [l for l in out.splitlines() if l.strip()]
    print(f"  {len(revs)} revisions of {rel}")
    print()
    print(f"  {'commit':<10} {'date':<12} {'runs':>5} {'n_runs_total':>13}  subject")
    history = []
    for line in revs:
        commit = line.split()[0]
        rc, blob = git("show", f"{commit}:{rel}")
        if rc != 0:
            continue
        try:
            d = json.loads(blob)
        except Exception:
            continue
        runs = d.get("runs") or []
        date = line.split()[1]
        subj = " ".join(line.split()[2:])[:60]
        print(f"  {commit[:9]:<10} {date:<12} {len(runs):>5} {str(d.get('n_runs_total')):>13}  {subj}")
        history.append({"commit": commit, "date": date, "runs": len(runs),
                        "n_runs_total": d.get("n_runs_total"), "subject": subj})
    print()
    # find the last revision with 103 and compare confs with now
    cur = json.loads((PUB / rel).read_text(encoding="utf-8", errors="ignore"))
    cur_confs = [r.get("conf") for r in (cur.get("runs") or [])]
    for h in history:
        if h["runs"] == 103:
            rc, blob = git("show", f"{h['commit']}:{rel}")
            d = json.loads(blob)
            old_confs = [r.get("conf") for r in (d.get("runs") or [])]
            from collections import Counter
            co, cc = Counter(old_confs), Counter(cur_confs)
            dropped = {k: co[k] - cc.get(k, 0) for k in co if co[k] > cc.get(k, 0)}
            added = {k: cc[k] - co.get(k, 0) for k in cc if cc[k] > co.get(k, 0)}
            print(f"  comparing {h['commit'][:9]} (103 runs) with HEAD (96 runs):")
            print(f"     configs dropped: {dropped}")
            print(f"     configs added  : {added}")
            break
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(history, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
