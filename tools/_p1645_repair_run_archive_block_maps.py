"""Repair the per-block maps inside outputs/analysis/p3_official_igu_run.json.

Why this exists: on 2026-10-25 the competing agent's `--stage train` invocation (pre-fix code)
overwrote `block_maps` with an all-zero rank sum, which `allocate_from_sums` turned into a uniform
[4,4,4,4]. The pinned corrected allocation is [11,1,2,2], so every later `--stage train` refused to
run ("the run archive's corrected allocation ... differs from the pinned").

The repair is **deterministic and offline**: it rebuilds the maps from the `allocation_stage` block
that the official allocator already wrote at 09:20 (96 per-module ranks), using the same
`merge_block_maps()` helper that the patched `--stage train` uses. No GPU, no new allocation run,
so there is no non-determinism to worry about and no archive is re-derived from scratch.

Guards:

* the rebuilt allocations must equal the pinned values, otherwise exit 3 and write nothing;
* the `runs[]` list must be preserved byte-for-byte (same length and identical JSON), else exit 4;
* before/after sha256 of the whole archive are printed so the change is auditable.

Usage:
    python tools/_p1645_repair_run_archive_block_maps.py [--apply]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE = os.path.join(REPO, "outputs", "analysis", "p3_official_igu_run.json")
TOOL = os.path.join(REPO, "tools", "_p1639_p3_official_igu.py")


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_tool():
    spec = importlib.util.spec_from_file_location("p1639", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # module-level constants only; no side effects
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(ARCHIVE):
        print("ERROR: archive not found: %s" % ARCHIVE)
        return 2
    tool = load_tool()
    before_hash = sha256_of(ARCHIVE)
    with open(ARCHIVE, encoding="utf-8") as fh:
        archive = json.load(fh)

    runs_before = json.dumps(archive.get("runs") or [], sort_keys=True)
    print("== before ==")
    print("  sha256      %s" % before_hash)
    print("  n_runs      %d" % len(archive.get("runs") or []))
    for name in ("archived", "corrected"):
        m = (archive.get("block_maps") or {}).get(name) or {}
        print("  %-10s allocation=%s sums=%s" % (name, m.get("allocation"), m.get("block_rank_sum")))

    stage = archive.get("allocation_stage") or {}
    if not (stage.get("module_ranks")):
        print("ERROR: allocation_stage.module_ranks is missing/empty; cannot rebuild deterministically")
        return 5

    merged = tool.merge_block_maps(archive, dict(archive))
    print("\n== after (rebuilt from allocation_stage.module_ranks) ==")
    for name in ("archived", "corrected"):
        m = merged["block_maps"][name]
        print("  %-10s allocation=%s sums=%s" % (name, m.get("allocation"), m.get("block_rank_sum")))
        if m["allocation"] != tool.ARCHIVED_ALLOCATIONS[name]:
            print("ERROR: rebuilt %s allocation %s != pinned %s -- refusing to write"
                  % (name, m["allocation"], tool.ARCHIVED_ALLOCATIONS[name]))
            return 3
        if any(abs(float(m["block_rank_sum"][b]) - float(tool.ARCHIVED_MODULE_SUMS[name][b])) > 1e-9
               for b in tool.BLOCKS):
            print("ERROR: rebuilt %s block sums differ from the archived sums" % name)
            return 3
    if json.dumps(merged.get("runs") or [], sort_keys=True) != runs_before:
        print("ERROR: runs[] changed during the repair -- refusing to write")
        return 4

    if not args.apply:
        print("\n(preview; pass --apply to write)")
        return 0
    tmp = ARCHIVE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, ARCHIVE)
    after_hash = sha256_of(ARCHIVE)
    print("\n== written ==")
    print("  sha256      %s -> %s" % (before_hash, after_hash))
    print("  n_runs      %d (unchanged)" % len(merged.get("runs") or []))
    return 0


if __name__ == "__main__":
    sys.exit(main())
