# -*- coding: utf-8 -*-
r"""Verify that the public repository really holds the data Paper A's statement promises.

The statement now says the derived data "are openly available in a public repository at
github.com/MoYUYao666/gap-susceptibility and in a versioned snapshot archived on Zenodo under
DOI 10.5281/zenodo.23341223", naming the per-epoch monitoring trajectories, the strict-freezing
controls and the cross-architecture sweeps. The operator confirms the data are in that
repository. Verify it, because a data statement that points at material which is not there is
worse than a vaguer one.

    python tools/_p696_verify_paperhe_in_repo.py [--apply]
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
NC = REPO / "paper合" / "NC_submission"
OUT = REPO / "outputs" / "analysis" / "paperhe_in_repo.json"

# artifact families Paper A's statement and results depend on
FAMILIES = {
    "per-epoch / monitoring trajectories": r"monitor|epoch|traj",
    "strict-freezing controls": r"strict_freeze|strictfreeze|freeze",
    "cross-architecture sweeps": r"clip|siglip|openclip|blip",
    "ODE fits": r"ode|fit",
    "LoRA rank / allocation sweeps": r"rank|alloc",
    "dataset-gap measurements": r"gap",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    r = subprocess.run(["git", "ls-files", "outputs"], cwd=str(PUB), capture_output=True)
    tracked = [x for x in r.stdout.decode("utf-8", errors="replace").splitlines() if x.strip()]
    print(f"  repository tracks {len(tracked)} files under outputs/")
    print()

    print("=" * 104)
    print("1. artifact families Paper A relies on, present in the public repository?")
    print("=" * 104)
    report = {}
    for label, pat in FAMILIES.items():
        hits = [f for f in tracked if re.search(pat, f, re.I)]
        print(f"  {label:<36} {len(hits):>5} file(s)")
        for h in hits[:3]:
            print(f"        {h}")
        report[label] = len(hits)

    print()
    print("=" * 104)
    print("2. the exact figures and controls named in Paper A")
    print("=" * 104)
    named = {
        "strict-freeze": r"strict_freeze",
        "COCO sweeps": r"coco",
        "Flickr30k": r"flickr",
        "SigLIP": r"siglip",
        "OpenCLIP": r"openclip|oclip",
        "effective rank": r"rank",
        "downstream retrieval": r"retriev|zs_|zeroshot",
        "random pool": r"random",
        "power / seeds": r"seed|power",
    }
    for label, pat in named.items():
        hits = [f for f in tracked if re.search(pat, f, re.I)]
        flag = "OK " if hits else "none"
        print(f"  {flag} {label:<26} {len(hits):>5}")
        report[f"named/{label}"] = len(hits)

    print()
    print("=" * 104)
    print("3. are the numbers Paper A quotes traceable to a tracked file?")
    print("=" * 104)
    # a few distinctive values from Paper A
    values = ["0.949", "0.943", "0.922", "204", "383", "60.69", "60.87", "0.814", "0.977"]
    # search the tracked JSONs for each
    import zipfile
    found = {v: [] for v in values}
    jsons = [f for f in tracked if f.endswith(".json")]
    print(f"  scanning {len(jsons)} tracked JSON files for {len(values)} values")
    for f in jsons:
        p = PUB / f
        if not p.exists():
            continue
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for v in values:
            if v in t and len(found[v]) < 3:
                found[v].append(f)
    for v in values:
        print(f"  {'OK ' if found[v] else 'not found':<10} {v:<8} "
              f"{found[v][0] if found[v] else ''}")
        report[f"value/{v}"] = found[v][:3]

    print()
    print("=" * 104)
    print("4. does the published README claim cover this paper too?")
    print("=" * 104)
    rd = PUB / "README.md"
    if rd.exists():
        t = io.open(rd, encoding="utf-8", errors="replace").read()
        for k in ("Adaptation Site", "Modality Gap", "Paper 3", "gap-susceptibility"):
            print(f"  {'yes' if k in t else 'no '} mentions {k!r}")
        print(f"  README length: {len(t):,} characters")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(report, ensure_ascii=False, indent=1))
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
