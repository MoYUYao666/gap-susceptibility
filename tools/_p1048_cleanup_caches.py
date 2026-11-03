# -*- coding: utf-8 -*-
r"""Remove the two caches approved on top of the earlier cleanup: HF datasets and ModelScope.

Approved 2026-10-16 (H and I):

* `~\.cache\huggingface\datasets` -- 33.35 GB of dataset cache, re-downloadable;
* `~\.cache\modelscope\hub` -- 6.62 GB of model cache, re-downloadable from ModelScope.

Explicitly **not** touched: `~\.cache\huggingface\hub` (15.09 GB, holds the LLaVA weights the local runs use),
`~\.cache\codex-runtimes` and `~\.cache\huggingface\modules` (harness runtime), and anything under `models/`
in the repository.

Each removal is guarded: the path must exist, must be the exact cache directory, and must not be a symlink to
somewhere else. Sizes are printed before and after so the reclaim is measured.

    python tools/_p1048_cleanup_caches.py            # report only
    python tools/_p1048_cleanup_caches.py --apply
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOME = Path(os.path.expanduser("~"))
LOG = REPO / "docs" / "cleanup_2026-10-16_caches.md"

TARGETS = [
    (HOME / ".cache" / "huggingface" / "datasets", "H: HuggingFace dataset cache, re-downloadable"),
    (HOME / ".cache" / "modelscope" / "hub", "I: ModelScope model cache, re-downloadable"),
]
KEEP = [
    HOME / ".cache" / "huggingface" / "hub",
    HOME / ".cache" / "codex-runtimes",
    HOME / ".cache" / "huggingface" / "modules",
]


def dir_size(p: Path) -> int:
    if not p.exists():
        return 0
    if p.is_file():
        return p.stat().st_size
    total = 0
    for root, _d, files in os.walk(p):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def human(n: int) -> str:
    return f"{n / 1024 ** 3:.2f} GB" if n >= 1024 ** 3 else f"{n / 1024 ** 2:.1f} MB"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    lines: list[str] = []
    freed = 0

    print("=== kept (not touched) ===")
    for p in KEEP:
        print(f"  {human(dir_size(p)):>10}  {p}")

    print("=== planned removals ===")
    total = 0
    for p, why in TARGETS:
        s = dir_size(p)
        total += s
        print(f"  {human(s):>10}  {p}  [{why}]")
    print(f"  {'-' * 10}\n  total: {human(total)}")

    if not a.apply:
        print("\n  (dry run: nothing removed)")
        return 0

    print("\n=== removing ===")
    for p, why in TARGETS:
        if not p.exists():
            lines.append(f"SKIP {p}: does not exist")
            print(f"  SKIP {p}")
            continue
        if p.is_symlink():
            lines.append(f"SKIP {p}: it is a symlink; removing it would not free the real data")
            print(f"  SKIP {p}: symlink")
            continue
        before = dir_size(p)
        try:
            shutil.rmtree(p)
            freed += before
            lines.append(f"REMOVED {human(before)}  {p}  [{why}]")
            print(f"  REMOVED {human(before):>10}  {p}")
        except OSError as exc:
            lines.append(f"FAILED {p}: {exc}")
            print(f"  FAILED {p}: {exc}")

    print(f"\n=== reclaimed: {human(freed)} ===")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with io.open(LOG, "w", encoding="utf-8", newline="") as fh:
        fh.write("# Cleanup of C-drive caches, 2026-10-16\n\n")
        fh.write("Approved: H (HuggingFace dataset cache), I (ModelScope cache).\n")
        fh.write("Kept: `~/.cache/huggingface/hub` (LLaVA weights), `~/.cache/codex-runtimes`, "
                 "`~/.cache/huggingface/modules`.\n\n")
        for line in lines:
            fh.write(f"- {line}\n")
        fh.write(f"- TOTAL reclaimed: {human(freed)}\n")
    print(f"  wrote {LOG.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
