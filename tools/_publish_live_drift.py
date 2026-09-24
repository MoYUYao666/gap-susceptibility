# -*- coding: utf-8 -*-
"""Drift check using git's own blob hashing (line-ending/filter safe)."""
import os
import subprocess

LIVE = r"D:\Realdesktop\Wan\Important\New"
PUB = os.path.join(LIVE, ".worktrees", "publish-main")
# NOTE 2026-09-20: this list previously omitted "paper", "tools", "experiments", "outputs" and
# "src", so manuscript/source drift was invisible (it reported 1 changed file while the
# manuscript's supplementary.tex demonstrably differed). Keep it in sync with what is published.
PREFIXES = ["paper", "paper_a1", "paper_a2", "paper_ap3", "paper3", "docs", "tools",
            "experiments", "outputs", "src", "HANDOFF.md", "AGENTS.md"]


def sh(args, cwd):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout.strip()


tracked = sh(["git", "ls-tree", "-r", "HEAD", "--name-only"], PUB).splitlines()
sel = [p for p in tracked
       if any(p == pre or p.startswith(pre + "/") for pre in PREFIXES)]
print("tracked files scanned: %d" % len(sel))

live_diff, pub_diff = [], []
for rel in sel:
    want = sh(["git", "rev-parse", "HEAD:%s" % rel], PUB)
    lp = os.path.join(LIVE, rel.replace("/", os.sep))
    pp = os.path.join(PUB, rel.replace("/", os.sep))
    lh = sh(["git", "hash-object", "--path=%s" % rel, lp], LIVE) if os.path.exists(lp) else "MISSING"
    ph = sh(["git", "hash-object", "--path=%s" % rel, pp], PUB) if os.path.exists(pp) else "MISSING"
    if lh != want:
        live_diff.append((rel, "MISSING" if lh == "MISSING" else "modified"))
    if ph != want:
        pub_diff.append((rel, "MISSING" if ph == "MISSING" else "modified"))

print("\n[A] live copy differs from publish/main HEAD: %d" % len(live_diff))
for r, w in live_diff:
    print("    %-56s %s" % (r, w))
print("\n[B] publish worktree copy differs from HEAD: %d" % len(pub_diff))
for r, w in pub_diff:
    print("    %-56s %s" % (r, w))

print("\n[C] do live and publish copies agree with each other?")
for rel in sel:
    lp = os.path.join(LIVE, rel.replace("/", os.sep))
    pp = os.path.join(PUB, rel.replace("/", os.sep))
    if not (os.path.exists(lp) and os.path.exists(pp)):
        print("    %-56s one side missing" % rel)
        continue
    lh = sh(["git", "hash-object", "--path=%s" % rel, lp], LIVE)
    ph = sh(["git", "hash-object", "--path=%s" % rel, pp], PUB)
    if lh != ph:
        print("    %-56s DIFFER" % rel)
print("    (paths not listed above are byte-identical)")

print("\n[D] tracked submission/package paths:")
allp = sh(["git", "ls-tree", "-r", "HEAD", "--name-only"], PUB).splitlines()
hits = [p for p in allp if p.lower().startswith("submission") or "/submission" in p.lower()]
print("    " + ("\n    ".join(hits) if hits else "(none)"))
print("\n[E] top-level tracked dirs:")
tops = sorted({p.split("/")[0] for p in allp})
print("    " + ", ".join(tops))
