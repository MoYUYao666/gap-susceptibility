# -*- coding: utf-8 -*-
r"""Mark the last stale page-count line in 文件地图.md as superseded.

Line 88 states the NC submission package is "60 页已同步". That was true on 2026-10-13; after supplement
Section F was added on 2026-10-16 the built manuscript is 67 pages, and the submission package has not been
refreshed. The line is annotated rather than rewritten, per the rule about not silently overwriting history.

    python tools/_p1099_mark_stale.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAP = REPO / "文件地图.md"

PAT = re.compile(r"^(>?\s*)摘要 \*\*250 词\*\*；.*$", re.M)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(MAP, encoding="utf-8").read()
    m = PAT.search(t)
    if not m:
        print("  target line not found")
        return 0
    print("  current:", m.group(0).strip()[:120])
    if "已过期" in m.group(0):
        print("  already marked")
        return 0
    new = (m.group(1) + "摘要 **250 词**；⚠️ **此处的投稿包页数为 2026-10-13 记录、已过期**："
           "`NC_submission/Manuscript.pdf` 当时 60 页，而**该包尚未同步 2026-10-16 的补充 F 节改动**——"
           "现行 `paper合/main_nc.pdf` 为 **67 页**（Springer 49 页）；")
    t = t[: m.start()] + new + t[m.end():]
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(MAP, "w", encoding="utf-8", newline="").write(t)
    print("  marked as superseded")
    check = io.open(MAP, encoding="utf-8").read()
    for needle in ("NC 67｜Springer 49", "已过期"):
        print(f"  contains {needle!r}: {needle in check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
