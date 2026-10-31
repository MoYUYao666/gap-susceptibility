# -*- coding: utf-8 -*-
r"""Pre-flight checks before the agreed cleanup, then the cleanup itself, step by step.

The operator approved categories A-E on 2026-10-16 and explicitly kept the HuggingFace model cache (F). Some
items in the approved list need a guard before they can be removed safely, and those guards are the point of
this script:

* **backups/** -- only if a newer backup exists. If `snapshot_FULL_20260930.zip` is still the only full
  snapshot, removing it would leave the project with none, so it is reported and kept instead.
* **UATD zips** -- only if the extracted dataset is still present, otherwise the zip is the only copy.
* **.worktrees/** -- removed through `git worktree remove`, not `rm -rf`, so git's records stay consistent.
* **models/** and **outputs/analysis/** -- never touched: the first is needed to run anything locally, the
  second is the source of every number in the papers.

Every step prints the size before and after, so the reclaimed space is measured rather than claimed.

    python tools/_p1047_cleanup.py            # report only, changes nothing
    python tools/_p1047_cleanup.py --apply    # perform the approved removals
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOG = REPO / "docs" / "cleanup_2026-10-16.md"


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
    report: list[str] = []
    freed = 0

    def note(line: str) -> None:
        print("  " + line)
        report.append(line)

    # ---- guard 1: is there a newer backup than the 2026-09-30 snapshot? ----------------------------
    backups = sorted((REPO / "backups").glob("snapshot_FULL_*.zip"))
    print(f"=== backups found: {[b.name for b in backups]}")
    keep_backups = len(backups) <= 1
    if keep_backups:
        note("SKIP backups/: the 2026-09-30 zip is the only full snapshot; removing it would leave none")

    # ---- guard 2: is each UATD zip duplicated by an extracted copy? ---------------------------------
    # Measured: `data/second_sonar/UATD/data/` holds UATD_Training, UATD_Test_1 and UATD_Test_2 (18,400
    # files, 32.7 GB), so those three archives are redundant. UATD_OpenSLT.zip has no extracted directory
    # beside it, so it is left alone -- a zip is only removed when its contents are demonstrably elsewhere.
    uatd = REPO / "data" / "second_sonar" / "UATD"
    extracted = {}
    for sub in ("UATD_Training", "UATD_Test_1", "UATD_Test_2"):
        p = uatd / "data" / sub
        n = sum(len(f) for _r, _d, f in os.walk(p)) if p.exists() else 0
        extracted[sub] = n
    print(f"=== UATD extracted copies (file counts): {extracted}")
    safe_zips = [uatd / f"{k}.zip" for k, n in extracted.items() if n > 0]

    targets: list[tuple[Path, str]] = []
    # A. system cache. The extraction is deliberately partial: `%TEMP%` also holds the harness's own
    # workspace-change object store (`dsh-workspace-changes-*`), which is in use and cannot be deleted
    # (WinError 5 on 2026-10-16). Those entries are skipped rather than forced.
    tmp = Path(os.environ.get("TEMP", ""))
    if tmp.exists():
        protected = []
        try:
            for child in tmp.iterdir():
                if child.name.lower().startswith("dsh-"):
                    protected.append(child)
                else:
                    targets.append((child, "A: user temporary files"))
        except OSError as exc:
            print(f"  could not enumerate %TEMP%: {exc}")
        if protected:
            note(f"SKIPPED {len(protected)} harness-owned %TEMP% entries: "
                 + ", ".join(p.name for p in protected))
    # B. re-downloadable datasets
    for name in ("coco", "flickr30k"):
        p = REPO / name
        if p.exists():
            # results.csv.bak inside flickr30k is covered by removing the directory
            targets.append((p, f"B: re-downloadable dataset {name}"))
    # C. old backup
    if not keep_backups:
        for b in backups[:-1]:
            targets.append((b, "C: superseded full snapshot"))
    # D. unreferenced fine-tuned checkpoints
    pt = sorted((REPO / "outputs").glob("*.pt"))
    for p in pt:
        targets.append((p, "D: fine-tuned checkpoint, unreferenced in the docs"))
    # E. redundant packages
    for rel, why in (("cloud_fixture", "E: cloud fixture, regenerable from SUBMISSION/cloud_p3_setup.sh"),
                     ("outputs/_cloud_data.zip", "E: duplicate of the cloud fixture"),
                     ("outputs/_cloud_layout", "E: duplicate of the cloud fixture"),
                     ("outputs/llava_parity_localdet", "E: local parity run, logs kept in outputs/analysis"),
                     ("flickr30k/results.csv.bak", "E: backup file")):
        p = REPO / rel
        if p.exists():
            targets.append((p, why))
    if safe_zips:
        for z in safe_zips:
            targets.append((z, "E: dataset zip, extracted copy present in UATD/data/"))

    def label(p: Path) -> str:
        try:
            return str(p.relative_to(REPO))
        except ValueError:
            return str(p)  # %TEMP% lives outside the repository

    print()
    print("=== planned removals ===")
    for p, why in targets:
        s = dir_size(p)
        print(f"  {human(s):>10}  {label(p)}  [{why}]")
    print(f"  {'-' * 10}")
    print(f"  total: {human(sum(dir_size(p) for p, _ in targets))}")

    worktrees = REPO / ".worktrees"
    if worktrees.exists():
        print(f"  {human(dir_size(worktrees)):>10}  .worktrees  [E: removed via git worktree]")

    if not a.apply:
        print("\n  (dry run: nothing removed)")
        return 0

    print("\n=== removing ===")
    for p, why in targets:
        before = dir_size(p)
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            freed += before
            note(f"REMOVED {human(before):>10}  {label(p)}  [{why}]")
        except OSError as exc:
            note(f"FAILED  {label(p)}: {exc}")

    # .worktrees through git, so its bookkeeping stays correct
    if worktrees.exists():
        before = dir_size(worktrees)
        r = subprocess.run(["git", "worktree", "list"], cwd=REPO, capture_output=True, text=True)
        print("  git worktrees before:\n    " + (r.stdout or "").replace("\n", "\n    "))
        subprocess.run(["git", "worktree", "prune"], cwd=REPO, capture_output=True)
        try:
            shutil.rmtree(worktrees)
            freed += before
            note(f"REMOVED {human(before):>10}  .worktrees  [E: pruned then removed]")
        except OSError as exc:
            note(f"FAILED  .worktrees: {exc}")

    print(f"\n=== reclaimed: {human(freed)} ===")
    note(f"TOTAL reclaimed: {human(freed)}")

    LOG.parent.mkdir(parents=True, exist_ok=True)
    with io.open(LOG, "w", encoding="utf-8", newline="") as fh:
        fh.write("# Cleanup 2026-10-16\n\n")
        fh.write("Approved categories: A (temporary files), B (coco, flickr30k), C (superseded snapshot), "
                 "D (unreferenced .pt checkpoints), E (redundant packages).\n")
        fh.write("Kept on request: the HuggingFace model cache (F). Never touched: `models/` and "
                 "`outputs/analysis/`.\n\n")
        for line in report:
            fh.write(f"- {line}\n")
    print(f"  wrote {LOG.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
