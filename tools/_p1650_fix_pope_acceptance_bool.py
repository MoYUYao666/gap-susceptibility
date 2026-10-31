"""Honesty fix for the POPE aggregate's prepared-parquet acceptance flag (2026-10-25).

Defect: `tools/_p1640_p3_second_downstream.py` computes the row-order check as either a real
`bool` (parquet present) or the sentinel **string**
`"NOT_VERIFIED_LOCALLY (prepared parquet absent on this machine)"` (parquet absent, --allow-missing-prepared).
`aggregate_core()` then stored `bool(match_parquet)`, and `bool(<non-empty string>)` is **True**.
Result: `outputs/analysis/p3_second_downstream.json` recorded
`acceptance.refs_match_prepared_parquet_order: true` for a run in which the check had never been
performed, and the sentinel itself was dropped, so nothing in the archive revealed the gap.

Evidence (local copies, 2026-10-25):
* `cloud_retrieved/round2_2026-10-25/pope/aggregate_before_rerun.json` (sha256 `52e4e7bd...`):
  `"prepared_parquet": "not retrieved locally (see the per-arm meta)"`,
  `"refs_match_prepared_parquet_order": true`, and **no** `NOT_VERIFIED` string anywhere.
* after re-running `--aggregate --strict` with the parquet present
  (`paper3/test-pope-random.parquet`, 61,909 B, sha256 `66faa5e6...`):
  `"prepared_parquet": "paper3/test-pope-random.parquet"`, the flag is a genuinely computed True.

Fix: keep the boolean honest (False when the check is a sentinel) and preserve the sentinel verbatim
in a new companion field `prepared_parquet_order_check`. Non-breaking: the boolean key keeps its type
and its meaning ("was the row order actually verified?").

Idempotent: re-running finds `prepared_parquet_order_check` already present and does nothing.

Usage:
    python tools/_p1650_fix_pope_acceptance_bool.py [--apply]
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools" / "_p1640_p3_second_downstream.py"

OLD = '        "refs_match_prepared_parquet_order": bool(match_parquet),'
NEW = (
    "        # honesty fix (2026-10-25): the not-verified sentinel is a STRING and\n"
    "        # bool(\"NOT_VERIFIED...\") is True, so the archive used to claim a row-order check that\n"
    "        # never ran. Record the boolean honestly (False when unverified) and keep the sentinel.\n"
    '        "refs_match_prepared_parquet_order": (match_parquet if isinstance(match_parquet, bool)\n'
    "                                              else False),\n"
    '        "prepared_parquet_order_check": match_parquet,'
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    text = io.open(TOOL, encoding="utf-8").read()
    if '"prepared_parquet_order_check"' in text:
        print("already patched; nothing to do")
        return 0
    n = text.count(OLD)
    if n != 1:
        print("ERROR: expected exactly 1 occurrence of the target line, found %d" % n)
        return 2
    patched = text.replace(OLD, NEW, 1)
    if not args.apply:
        print("preview: would replace 1 line in %s (%d -> %d bytes)"
              % (TOOL.name, len(text.encode("utf-8")), len(patched.encode("utf-8"))))
        return 0
    io.open(TOOL, "w", encoding="utf-8", newline="\n").write(patched)
    check = io.open(TOOL, encoding="utf-8").read()
    assert 'prepared_parquet_order_check' in check, "patch did not take"
    # the old *coercion inside the archive payload* must be gone; `bool(match_parquet)` legitimately
    # survives one line earlier when it computes `prepared_order_check` for the written report.
    assert '"refs_match_prepared_parquet_order": bool(match_parquet)' not in check, \
        "old coercion still present"
    print("patched %s: %d -> %d bytes" % (TOOL.name, len(text.encode("utf-8")),
                                          len(check.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
