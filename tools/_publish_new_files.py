# -*- coding: utf-8 -*-
"""List files that exist on one side of the live/publish split but not the other.

_publish_live_drift.py only walks paths already tracked in publish/main HEAD, so brand-new
files (a fresh tool, a fresh JSON) are invisible to it.  This prints them, restricted to the
extensions that the publish convention actually carries, so the commit cannot silently miss
an artefact.  Run it BEFORE git add.
"""
import os

LIVE = r"D:\Realdesktop\Wan\Important\New"
PUB = os.path.join(LIVE, ".worktrees", "publish-main")
# 2026-09-20: "paper_ap3" (and the other paper_* trees) were missing from this list, so the tool
# was blind to exactly the directory where a copy was then silently dropped (paper_ap3/scripts/
# plot_fig_corr.py).  Keep every published manuscript tree here.
DIRS = ["tools", "docs", "paper", "paper_a1", "paper_a2", "paper3",   # 2026-10-06: paper_ap3 已归档（不可投），从发布列表移除
        "outputs", "experiments", "src"]
EXTS = {".py", ".json", ".tex", ".pdf", ".png", ".bbl", ".md", ".txt", ".csv", ".svg"}
SKIP_DIRS = {"__pycache__", ".git", ".ipynb_checkpoints", "_superseded_2026", ".worktrees"}
# build byproducts and local-only trees that the convention does not publish
SKIP_FILES = {"_build1.log", "_build2.log", "_build3.log", "_bibtex.log", "_cl_build.log"}


def walk(base):
    out = set()
    for d in DIRS:
        root_dir = os.path.join(base, d)
        if not os.path.isdir(root_dir):
            continue
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
            for f in files:
                if os.path.splitext(f)[1].lower() not in EXTS or f in SKIP_FILES:
                    continue
                rel = os.path.relpath(os.path.join(root, f), base).replace("\\", "/")
                out.add(rel)
    return out


live, pub = walk(LIVE), walk(PUB)
new_live = sorted(live - pub)
new_pub = sorted(pub - live)
print("live-only  (must be copied + added): %d" % len(new_live))
for p in new_live:
    print("    + %s" % p)
print("\npublish-only (exists only in the publish worktree): %d" % len(new_pub))
for p in new_pub:
    print("    - %s" % p)
