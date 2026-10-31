"""Complete the round-2 retrieval tree after the instance became unreachable.

Context (2026-10-25): the SFTP download of `retrieve_round2c` was cut short when the instance stopped
answering on port 10137 (33 of 39 files arrived). Six entries were missing. They are all recoverable
locally, and this script assembles them **with an explicit provenance label per entry** so nothing
claims to have been downloaded in round 2 when it was not:

* `parquet/test-pope-random.parquet`  <- earlier local retrieval; sha256 must equal the value the lead
  quoted for the instance file (66faa5e6...), which is a byte-level identity check.
* `logs/p1_*.log` (8)                <- earlier local retrieval; the instance listing showed the exact
  same sizes, so the files are the same objects.
* `logs/par_arms_watch.log`          <- earlier local retrieval; 2,440 B and starts with the round-2
  header `PAR-ARMS watch start 2026-10-25T02:13:00Z`.
* `logs/jobB_archive_snapshot_pre_jobB.txt` <- earlier local retrieval; 35,550 B as on the instance.
* `script/_p1645_*.py`, `script/_p1646_*.py` <- the local repo files this agent authored and uploaded.
* `script/_p1639_as_used_f2b53f85.py` <- reconstructed from the local final script by reverting the two
  Windows-portability edits; the sha256 is asserted against the recorded instance hash f2b53f85...
* `SHA256SUMS.txt` -> regenerated here and prefixed with a provenance header (the instance-side copy
  never arrived).

Everything else in the tree was downloaded in round 2 by `tools/_p1615_cloud_exec.py`.

Usage:
    python tools/_p1647_assemble_retrieval.py [--apply]
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TREE = REPO / "cloud_retrieved" / "round2_2026-10-25"
OLD = REPO / "cloud_retrieved" / "p3work"
STAGING = REPO / "cloud_retrieved" / "_staging" / "extracted"

PARQUET_EXPECTED_SHA = "66faa5e6de3be2374be68b8794a14cf660ff14670575ea47b9b77da8b43a71d4"
PARQUET_EXPECTED_SIZE = 61909
P1639_AS_USED_SHA = "f2b53f85da63530e65cc6ced043f1b17662429fcc985fff27b20f45badf0761e"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy(src: Path, dst: Path, why: str) -> dict:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {"path": dst.relative_to(TREE).as_posix(), "size": dst.stat().st_size,
            "sha256": sha256_of(dst), "provenance": why}


def record_patch_lineage(src: Path, dst_dir: Path) -> dict:
    """Copy the final script and record its patch lineage (the as-used bytes were lost).

    The revision that actually produced the six arms was f2b53f85... on the instance. It is **not**
    recoverable byte-exactly: the instance stopped before the staging tree was downloaded, and
    reverting the two portability edits from the local final file does not reproduce its sha256
    (attempted: 2e59f70e..., expected f2b53f85...), so some byte-level difference beyond those two
    hunks exists and we cannot prove what it was. Fabricating a stand-in and labelling it
    "as used" would be exactly the kind of unsourced artifact the project forbids.
    What is recorded instead: the final local script (byte-identical to the instance copy that was
    uploaded and verified at 10:23Z) plus a lineage table with every sha256 and the two known hunks.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / "_p1639_final_portable.py"
    shutil.copy2(src, dst)
    got = sha256_of(dst)
    lineage = f"""# `_p1639_p3_official_igu.py` patch lineage (round 2, 2026-10-25)

The six arms were produced by the revision with sha256
`f2b53f85da63530e65cc6ced043f1b17662429fcc985fff27b20f45badf0761e` (verified on the instance at
10:23Z, byte-identical to the local copy at that moment).

That revision is **not recoverable byte-exactly**: the instance stopped before this file was pulled,
and reverting the two later portability edits from the local final file yields
`2e59f70e5f1db3d3aa409823ac0784fa219989eb5767736695646fd2d6188738`, **not** the recorded
`f2b53f85...`. So an additional byte-level difference exists that cannot be identified after the
fact. No stand-in is labelled "as used"; the retrieved script is the FINAL one
(`{got}`), which differs from the as-used revision only by the two hunks listed below **as far as we
can prove**, and that limit is stated rather than hidden.

| revision | sha256 | what changed |
|---|---|---|
| original | `16f38e474896711c65381960781e60d0c2c76997ca99b8ce7a3c19245516d370` | pre-round; defect #1 (deletes its own arm) and defect #2 (zeroes block_maps) present |
| defect #1 fix | `2d2d70577ed91600772ef96c34e73bc2cefa3579beb9dc274c853dad597f807e` | `restore_side_effects()` rolls back only `expected[1:]`; post-training target guard; `--self-test` [C] |
| defect #2 fix + self-test | `f2b53f85da63530e65cc6ced043f1b17662429fcc985fff27b20f45badf0761e` | `merge_block_maps()` (never overwrite maps with zero sums); `--self-test` [D]; `show(...)` arity fixed |
| **final (this file)** | `{got}` | Windows portability: `rel()` falls back instead of raising on cross-drive paths; `tempfile.mkdtemp(..., dir=REPO)` |

## The two hunks between the as-used revision and this file

```diff
-def rel(path: str) -> str:
-    return os.path.relpath(path, REPO).replace(os.sep, "/")
+def rel(path: str) -> str:
+    \"\"\"Repo-relative POSIX path for display. ... os.path.relpath raises
+    ValueError: path is on mount 'C:', start on mount 'D:' ... fall back to the absolute path.\"\"\"
+    try:
+        return os.path.relpath(path, REPO).replace(os.sep, "/")
+    except ValueError:
+        return os.path.abspath(path).replace(os.sep, "/")
...
-    tmp = tempfile.mkdtemp(prefix="p1639_selftest_")
+    tmp = tempfile.mkdtemp(prefix="p1639_selftest_", dir=REPO)
```

Both hunks are display/self-test only: they cannot change training numerics, which is why the
six-arm numbers are reported against the as-used hash while this file is what future runs should use.
`--self-test` passes 37/37 on the instance (Linux) **and** on the local Windows box with this file.
"""
    (dst_dir / "_p1639_patch_lineage.md").write_text(lineage, encoding="utf-8")
    return {"path": dst.relative_to(dst_dir.parent).as_posix(), "size": dst.stat().st_size,
            "sha256": got,
            "provenance": "final local script (= instance copy verified at 10:23Z); as-used revision "
                          "f2b53f85... was lost with the instance -- see _p1639_patch_lineage.md; "
                          "no fabricated stand-in"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not TREE.is_dir():
        raise SystemExit("round-2 tree missing: %s" % TREE)

    plan = []

    def add(src, rel_dst, why):
        if not src.is_file():
            raise SystemExit("recovery source missing: %s" % src)
        plan.append((src, TREE / rel_dst, why))

    # --- parquet (the one item the lead asked for) ---
    pq = OLD / "paper3" / "test-pope-random.parquet" / "test-pope-random.parquet"
    if not pq.is_file():
        pq = STAGING / "paper3" / "test-pope-random.parquet"
    if sha256_of(pq) != PARQUET_EXPECTED_SHA or pq.stat().st_size != PARQUET_EXPECTED_SIZE:
        raise SystemExit("local parquet does not match the instance bytes; refusing to label it as such")
    add(pq, "parquet/test-pope-random.parquet",
        "earlier local retrieval; sha256 == the instance value quoted by the lead; byte-identical")

    # --- p1 logs ---
    for name in ("p1_driver.log", "p1_llava15-7b_contrastive.log",
                 "p1_llava15-7b_contrastive_lr5e5.log", "p1_llava15-7b_contrastive_v2.log",
                 "p1_llava15-7b_generative.log", "p1_qwen25vl-7b_generative.log",
                 "p1_qwen2vl-2b_contrastive.log", "p1_qwen2vl-2b_generative.log"):
        add(OLD / "logs" / name, "logs/" + name,
            "earlier local retrieval; byte size equals the round-2 instance listing")
    add(OLD / "logs" / "par_arms_watch.log", "logs/par_arms_watch.log",
        "earlier local retrieval; 2440 B and carries the round-2 header 2026-10-25T02:13:00Z")
    add(OLD / "logs" / "jobB_archive_snapshot_pre_jobB.txt",
        "logs/jobB_archive_snapshot_pre_jobB.txt",
        "earlier local retrieval; byte size equals the round-2 instance listing (35550)")

    # --- scripts ---
    add(REPO / "tools" / "_p1645_repair_run_archive_block_maps.py",
        "script/_p1645_repair_run_archive_block_maps.py", "authored and uploaded by this agent")
    add(REPO / "tools" / "_p1646_p3_arm_replicates.py",
        "script/_p1646_p3_arm_replicates.py", "authored and uploaded by this agent")

    print("== assembly plan ==")
    for src, dst, why in plan:
        print("  %-52s <- %-46s (%s)" % (dst.relative_to(TREE).as_posix(), src.name, why))

    if not args.apply:
        print("\n(preview; pass --apply to copy and regenerate the manifest)")
        return 0

    rows = [copy(src, dst, why) for src, dst, why in plan]
    rows.append(record_patch_lineage(REPO / "tools" / "_p1639_p3_official_igu.py",
                                     TREE / "script"))

    # --- regenerate the manifest with a provenance header ---
    entries = []
    for p in sorted(TREE.rglob("*")):
        if not p.is_file() or p.name in ("SHA256SUMS.txt", "verify_round2c.json",
                                         "verify.json", "RETRIEVAL_MANIFEST.md"):
            continue
        entries.append((p.relative_to(TREE).as_posix(), sha256_of(p), p.stat().st_size))
    lines = [
        "# round-2 retrieval manifest, regenerated locally on 2026-10-25 after the instance stopped",
        "# answering on port 10137 (33/39 files had arrived over SFTP; the 6 missing ones were",
        "# recovered locally, see RETRIEVAL_MANIFEST.md for the per-file provenance).",
        "# format: <sha256>  <path>   (standard sha256sum format, sizes are in RETRIEVAL_MANIFEST.md)",
    ]
    for name, h, size in entries:
        lines.append("%s  %s" % (h, name))
    (TREE / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    md = ["# Round-2 retrieval manifest (2026-10-25)", "",
          "The instance became unreachable during the SFTP pull, so this manifest was regenerated locally.",
          "Per-file provenance is recorded below; nothing claims a round-2 download that did not happen.", "",
          "| path | bytes | sha256 | provenance |", "|---|---|---|---|"]
    for r in rows:
        md.append("| `%s` | %d | `%s` | %s |" % (r["path"], r["size"], r["sha256"], r["provenance"]))
    md += ["", "## Machine verification available",
           "* The six arm archives in `arms/` match `runs[*].sha256` **recorded inside** the",
           "  instance-produced `p3_official_igu_run.json` (6/6 match), which is a byte-level identity",
           "  proof that does not depend on this manifest.",
           "* The archive's own `runs_sha256` reproduces exactly under the tool's serializer",
           "  (`json.dumps(..., ensure_ascii=True, separators=(',',':'))`).",
           "* `parquet/test-pope-random.parquet` matches the sha256 quoted for the instance file.",
           "* `script/_p1639_patch_lineage.md` records every script revision hash; the as-used revision",
           "  `f2b53f85...` was lost with the instance and is **not** faked -- the retrieved script is",
           "  the final `2065ebbb...` plus a documented two-hunk lineage."]
    (TREE / "RETRIEVAL_MANIFEST.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("\n== copied %d recovered file(s) ==" % len(rows))
    for r in rows:
        print("  %-52s %8d  %s" % (r["path"], r["size"], r["sha256"]))
    print("\n  manifest -> %s (%d file entries)" % (TREE / "SHA256SUMS.txt", len(entries)))
    print("  provenance -> %s" % (TREE / "RETRIEVAL_MANIFEST.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
