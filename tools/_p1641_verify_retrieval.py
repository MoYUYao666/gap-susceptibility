"""Verify a retrieved file set against a sha256 manifest produced on the cloud instance.

The cloud round rules require every retrieved file to be checked for size and sha256 before the
instance is shut down. The manifest is produced remotely with `sha256sum *` and retrieved together
with the payload, so the comparison is between the instance's bytes and the local copy.

Usage:
    python tools/_p1641_verify_retrieval.py \
        --manifest cloud_retrieved/round2_2026-10-25/pope/POPE_SHA256.txt \
        --dir      cloud_retrieved/round2_2026-10-25/pope \
        [--report cloud_retrieved/round2_2026-10-25/pope/verify.json]

Exit code 0 only when every listed file is present, non-empty, and byte-identical.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_manifest(manifest: Path) -> list[tuple[str, str]]:
    rows = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):   # tolerate comment/header lines
            continue
        # `sha256sum` output is "<hash>  <name>"; tolerate one space as well.
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise SystemExit("malformed manifest line: %r" % line)
        digest, name = parts
        rows.append((name.lstrip("*"), digest.lower()))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dir", required=True, dest="directory")
    ap.add_argument("--report", default=None, help="optional JSON report path")
    args = ap.parse_args()

    manifest = Path(args.manifest)
    directory = Path(args.directory)
    if not manifest.is_file():
        print("ERROR: manifest not found: %s" % manifest)
        return 2
    if not directory.is_dir():
        print("ERROR: directory not found: %s" % directory)
        return 2

    rows = parse_manifest(manifest)
    results = []
    failures = 0
    print("== retrieval verification: %d file(s) ==" % len(rows))
    for name, expected in rows:
        target = directory / name
        if not target.is_file():
            print("  [FAIL] %-46s MISSING" % name)
            results.append({"file": name, "status": "missing"})
            failures += 1
            continue
        size = target.stat().st_size
        actual = sha256_of(target)
        ok = actual == expected and size > 0
        print("  [%s] %-46s size=%-9d sha256=%s" % ("OK  " if ok else "FAIL", name, size,
                                                    "match" if actual == expected else "MISMATCH"))
        results.append({"file": name, "size": size, "sha256": actual,
                        "sha256_expected": expected, "status": "ok" if ok else "mismatch"})
        if not ok:
            failures += 1

    # Files present locally but absent from the manifest are reported, not failed: the manifest is
    # authoritative for what the instance staged.
    extra = sorted(p.name for p in directory.iterdir()
                   if p.is_file() and p.name not in {n for n, _ in rows}
                   and p.resolve() != manifest.resolve())
    if extra:
        print("  note: %d local file(s) not listed in the manifest: %s" % (len(extra), extra))

    report = {"manifest": str(manifest), "directory": str(directory),
              "n_files": len(rows), "n_failures": failures, "files": results,
              "extra_local_files": extra}
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=1), encoding="utf-8")
        print("  report -> %s" % args.report)

    print("\n== %d/%d verified ==" % (len(rows) - failures, len(rows)))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
