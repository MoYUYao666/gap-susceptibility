# -*- coding: utf-8 -*-
r"""Reorganise SUBMISSION/: current packages at the root, everything superseded under _archive/.

Nothing is deleted. Every moved tree is hashed before and after the move and the two manifests must agree, so a
half-copied package cannot slip through. `_archive/MOVED_2026-10-18.tsv` records old -> new for every top-level item.

Layout after this script:
  SUBMISSION/
    PaperA_Neurocomputing/          <- paper合/NC_submission  (current, 70 pp)
    A1_PatternAnalysisApplications/ <- paper_a1/PAA_submission (current)
    P3_PRL_revision/  A23_JOE/  Review_PRL/   (under review; frozen, untouched)
    _archive/                       <- superseded and rejected packages
    README.md                       (rewritten separately)

    python tools/_p1242_reorganize_submission.py [--apply]
"""
from __future__ import annotations

import argparse
import hashlib
import io
import os
import shutil

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUB = os.path.join(REPO, "SUBMISSION")
ARCH = os.path.join(SUB, "_archive")

MOVES = [
    # within SUBMISSION: old versions into the archive
    (os.path.join(SUB, "_old"), os.path.join(ARCH, "_old")),
    (os.path.join(SUB, "_superseded_P3_PRL_revision"), os.path.join(ARCH, "_superseded_P3_PRL_revision")),
    (os.path.join(SUB, "_superseded_P3_PRL_submitted_2026-09-26"),
     os.path.join(ARCH, "_superseded_P3_PRL_submitted_2026-09-26")),
    (os.path.join(SUB, "A1_NeuralNetworks"), os.path.join(ARCH, "A1_NeuralNetworks_rejected_2026-10-18")),
    (os.path.join(SUB, "PaperA_Neurocomputing"), os.path.join(ARCH, "PaperA_Neurocomputing_2026-10-12_60pp")),
    # current packages installed from their build locations
    (os.path.join(REPO, "paper合", "NC_submission"), os.path.join(SUB, "PaperA_Neurocomputing")),
    (os.path.join(REPO, "paper_a1", "PAA_submission"), os.path.join(SUB, "A1_PatternAnalysisApplications")),
    # stray helper scripts that belong with the archive
    (os.path.join(SUB, "_p820_llava_sites.py"), os.path.join(ARCH, "scripts", "_p820_llava_sites.py")),
    (os.path.join(SUB, "cloud_p3_setup.sh"), os.path.join(ARCH, "scripts", "cloud_p3_setup.sh")),
]


def tree_hashes(root: str) -> dict[str, str]:
    out = {}
    if os.path.isfile(root):
        h = hashlib.sha256(open(root, "rb").read()).hexdigest()
        return {os.path.basename(root): h}
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, root)
            out[rel] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    os.makedirs(ARCH, exist_ok=True)

    planned = []
    vacated = {os.path.normcase(src) for src, _ in MOVES}
    for src, dst in MOVES:
        if not os.path.exists(src):
            print(f"  SKIP (absent) {os.path.relpath(src, REPO)}")
            continue
        if os.path.exists(dst) and os.path.normcase(dst) not in vacated:
            print(f"  !! destination exists, refusing: {os.path.relpath(dst, REPO)}")
            return 1
        n = len(tree_hashes(src))
        planned.append((src, dst, n))
        print(f"  {os.path.relpath(src, REPO):52s} -> {os.path.relpath(dst, REPO):58s} ({n} files)")

    if not a.apply:
        print("  (dry run)")
        return 0

    rows, bad = [], 0
    for src, dst, n in planned:
        before = tree_hashes(src)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        after = tree_hashes(dst)
        ok = before == after
        bad += 0 if ok else 1
        print(f"  moved {os.path.relpath(dst, REPO)}: {n} files, hashes {'OK' if ok else 'MISMATCH'}")
        rows.append((os.path.relpath(src, REPO), os.path.relpath(dst, REPO), str(n), "OK" if ok else "MISMATCH"))

    tsv = os.path.join(ARCH, "MOVED_2026-10-18.tsv")
    with io.open(tsv, "w", encoding="utf-8", newline="") as fh:
        fh.write("old\tnew\tfiles\tverify\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print(f"\n  wrote {os.path.relpath(tsv, REPO)} ({len(rows)} entries)")
    if bad:
        print(f"  !! {bad} tree(s) failed the hash comparison")
        return 1
    print("  all moves hash-verified")

    print("\n  === SUBMISSION/ now ===")
    for name in sorted(os.listdir(SUB)):
        p = os.path.join(SUB, name)
        print(f"    {name:36s} {'[dir]' if os.path.isdir(p) else os.path.getsize(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
