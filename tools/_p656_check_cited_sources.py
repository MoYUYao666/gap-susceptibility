# -*- coding: utf-8 -*-
r"""Do the source files the responses cite actually exist in the public archive?

The responses say, repeatedly, "Every number can be traced to a script and an archived
field", and the Data statement now points reviewers at a public repository and a Zenodo DOI.
Before the repository was public that promise was uncheckable; now a reviewer can follow it.
So every file path cited in the three response boxes has to resolve somewhere the reviewer
can reach: the published repository (at the archived tag) or the supplementary material.

    python tools/_p656_check_cited_sources.py [--apply]
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
RESP = REPO / "SUBMISSION" / "P3_PRL_revision" / "response"
PUB = REPO / "publish_clean"
OUT = REPO / "outputs" / "analysis" / "cited_sources.json"

# file paths the responses mention: outputs/... .json, tools/... .py, docs/... .md
PATH_RE = re.compile(r"\b((?:outputs|tools|docs|src|exp|experiments|paper3)[\w./*\-]*\.(?:json|py|md|txt|tex|zip|bib))")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    cited: dict[str, set[str]] = {}
    for p in sorted(RESP.glob("*_plain.txt")):
        t = io.open(p, encoding="utf-8", errors="replace").read()
        for m in PATH_RE.finditer(t):
            cited.setdefault(m.group(1), set()).add(p.name)
    print(f"  distinct file paths cited in the response boxes: {len(cited)}")
    print()

    # what the reviewer can reach
    r = subprocess.run(["git", "ls-files"], cwd=str(PUB), capture_output=True)
    published = set(r.stdout.decode("utf-8", errors="replace").splitlines())
    supp = REPO / "SUBMISSION" / "P3_PRL_revision" / "manuscript" / "supplementary.pdf"

    rows = []
    ok = missing = wildcards = 0
    for path, files in sorted(cited.items()):
        if "*" in path:
            # a glob: check that at least one match is published
            prefix = path.split("*")[0]
            hits = [x for x in published if x.startswith(prefix)]
            status = f"glob -> {len(hits)} match(es) in archive"
            wildcards += 1
        elif path in published:
            status = "published"
            ok += 1
        elif (REPO / path).exists():
            status = "**NOT in the published archive** (exists only in the workspace)"
            missing += 1
        else:
            status = "MISSING EVERYWHERE"
            missing += 1
        rows.append({"path": path, "status": status, "cited_in": sorted(files)})
        flag = "OK " if "published" in status or "glob" in status else "GAP"
        print(f"  {flag} {path:<62} {status[:60]}")
        if flag == "GAP":
            print(f"        cited in: {', '.join(sorted(files))}")

    print()
    print(f"  resolved: {ok + wildcards}  |  gaps: {missing}")
    if missing:
        print()
        print("  These paths are cited to the reviewer but are NOT in the archive the Data")
        print("  statement points at. Either publish them or drop the citation.")
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(
            {"rows": rows, "resolved": ok + wildcards, "gaps": missing},
            ensure_ascii=False, indent=1))
        print()
        print(f"  Wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
