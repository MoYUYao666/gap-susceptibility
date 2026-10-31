"""Append the Chinese task-17 section to docs/p3_cloud_round2_notes.md (UTF-8, no rewriting).

The target file already carries another session's English record (its 369 lines document the POPE
round and the shutdown). Project rule for handover documents is **append, never rewrite**, and Chinese
must be written through Python with an explicit encoding (PowerShell text append on Windows has
corrupted UTF-8 in this repo before).

Usage:
    python tools/_p1649_append_round2_zh.py [--apply]
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "docs" / "p3_cloud_round2_notes.md"
SECTION = REPO / "docs" / "_tmp_round2_igu_section.md"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not TARGET.is_file() or not SECTION.is_file():
        print("ERROR: missing %s or %s" % (TARGET, SECTION))
        return 2
    existing = TARGET.read_text(encoding="utf-8")
    marker = "官方 IGU-LoRA 六臂轮次（task-17"
    if marker in existing:
        print("section already present; nothing to do")
        return 0
    section = SECTION.read_text(encoding="utf-8")
    merged = existing.rstrip("\n") + "\n" + section
    if not args.apply:
        print("preview: would append %d bytes (%d lines) to %s"
              % (len(section.encode("utf-8")), len(section.splitlines()), TARGET))
        print("target currently %d bytes / %d lines"
              % (len(existing.encode("utf-8")), len(existing.splitlines())))
        return 0
    # explicit UTF-8 write; verify the result decodes strictly and keeps the original prefix intact
    with io.open(TARGET, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(merged)
    check = TARGET.read_text(encoding="utf-8")
    assert check.startswith(existing.rstrip("\n")), "original content was altered"
    assert marker in check, "appended section missing"
    TARGET.read_bytes().decode("utf-8")          # strict decode: no mixed encoding
    print("appended: %s now %d bytes / %d lines"
          % (TARGET, TARGET.stat().st_size, len(check.splitlines())))
    SECTION.unlink()
    print("removed staging file %s" % SECTION.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
