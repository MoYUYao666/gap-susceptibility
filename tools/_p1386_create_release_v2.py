# -*- coding: utf-8 -*-
r"""Create the v2.0 tag and GitHub release for the public mirror, once everything else is done.

Guards:
  * working tree of the main repo and of publish_clean must be clean;
  * publish_clean file boundary: no manuscript-like paths, no file above 100 MB;
  * tag v2.0 must not exist (the frozen v1.0-prl-revision tag is never touched);
  * release v2.0 must not exist.

Zenodo will archive the new release as a new version of the same concept DOI and mint a new version DOI; that DOI has to
be recorded in HANDOFF / 文件地图 after the record appears (the GitHub integration is asynchronous).

    python tools/_p1386_create_release_v2.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIRROR = os.path.join(REPO, "publish_clean")
NOTES = os.path.join(REPO, "RELEASE_NOTES_v2.0.md")
TAG = "v2.0"


def run(cmd, cwd=REPO, check=False):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise SystemExit("command failed: %s\n%s\n%s" % (" ".join(cmd), r.stdout[-800:], r.stderr[-800:]))
    return r


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    dirty_main = run(["git", "status", "--porcelain"]).stdout.strip()
    dirty_mirror = run(["git", "-C", MIRROR, "status", "--porcelain"]).stdout.strip()
    tags = set(run(["git", "-C", MIRROR, "tag", "--list"]).stdout.split())
    rel = run(["gh", "release", "list", "--repo", "MoYUYao666/gap-susceptibility", "--limit", "10"]).stdout
    print("  main dirty:", bool(dirty_main), "| mirror dirty:", bool(dirty_mirror), "| v2.0 tag exists:", TAG in tags)
    assert not dirty_main, "main repository has uncommitted changes"
    assert not dirty_mirror, "publish_clean has uncommitted changes"
    assert TAG not in tags, "tag v2.0 already exists; refusing to move it"
    if not a.apply:
        print("  (dry run; nothing pushed, no tag, no release)")
        return 0
    # 1. refresh mirror from the live staging list
    run([sys.executable, "tools/_p1284_prepare_public_mirror.py", "--apply"], check=True)
    out = run(["git", "-C", MIRROR, "status", "--porcelain"]).stdout.splitlines()
    paper = [l for l in out if any(k in l.lower() for k in ("main.tex", "main_nc", "main_springer", "paper_a1",
                                                             "paper_a2", "paper3", "paper_review", "cover_letter",
                                                             "declaration", "title_page", "highlights"))]
    big = []
    for l in out:
        p = l[3:].strip()
        f = os.path.join(MIRROR, p)
        if os.path.isfile(f) and os.path.getsize(f) > 100 * 1024 * 1024:
            big.append(p)
    print("  mirror changed:", len(out), "| manuscript-like:", len(paper), "| >100MB:", len(big))
    assert not paper, "manuscript files would be published"
    assert not big, "files above 100 MB would be published"
    # 2. commit and push mirror
    run(["git", "-C", MIRROR, "add", "-A"], check=True)
    msg = "Release v2.0: local upgrade round (P3 re-run curve, A1 monitoring baselines, A23 tau/UATD controls, commentary compliance)"
    r = run(["git", "-C", MIRROR, "commit", "-m", msg])
    if r.returncode != 0:
        print("  mirror commit:", (r.stdout or r.stderr).strip()[-300:])
    run(["git", "-C", MIRROR, "push", "ssh-origin", "main"], check=True)
    print("  mirror pushed")
    # 3. tag v2.0 and push it
    run(["git", "-C", MIRROR, "tag", "-a", TAG, "-m", "v2.0 - analysis addendum for the five-manuscript round"], check=True)
    run(["git", "-C", MIRROR, "push", "ssh-origin", TAG], check=True)
    print("  tag", TAG, "pushed")
    # 4. GitHub release
    r = run(["gh", "release", "create", TAG, "--repo", "MoYUYao666/gap-susceptibility",
             "--title", "v2.0 - analysis addendum (P3 re-run, A1 monitoring, A23 controls, commentary)",
             "--notes-file", NOTES])
    if r.returncode != 0:
        print("  release creation failed:", (r.stdout + r.stderr)[-600:])
        return 1
    print("  release created:", (r.stdout or "").strip()[-200:])
    print("\n  Zenodo will archive the new release as a new version under the same concept DOI and mint a new version\n"
          "  DOI; record that DOI in HANDOFF.md and 文件地图.md when it appears. The frozen v1.0-prl-revision tag and the\n"
          "  v1.0 version DOI 10.5281/zenodo.23341223 stay untouched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
