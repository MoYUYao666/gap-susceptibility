"""Verify the exact release file set and replay all published summaries offline."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import subprocess
import sys

GROUPS = {"alignment_dynamics", "order_preservation", "acoustic_protocols", "text_provenance",
          "readout_validity", "rank_allocation", "checkpoint_selection", "reference_metadata"}

def strict_json(raw, name):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"Duplicate JSON key in {name}: {key}")
            out[key] = value
        return out
    def reject(value):
        raise ValueError(f"Nonfinite JSON value in {name}: {value}")
    def number(value):
        result = float(value)
        if not math.isfinite(result):
            reject(value)
        return result
    return json.loads(raw.decode("utf-8-sig"),object_pairs_hook=pairs,parse_constant=reject,parse_float=number)

def integrity(root: Path) -> int:
    root = root.resolve()
    manifest = strict_json((root/"MANIFEST.json").read_bytes(), "MANIFEST.json")
    listed = manifest["files"]
    for name in listed:
        p = PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts or "\\" in name or name != p.as_posix():
            raise ValueError(f"Unsafe manifest path: {name}")
    found = set()
    for p in root.rglob("*"):
        name = p.relative_to(root).as_posix()
        if ".git" in p.relative_to(root).parts:
            continue
        if p.is_symlink():
            raise ValueError(f"Unsafe symlink: {name}")
        if p.is_file():
            found.add(name)
    allowed = set(listed)|{"MANIFEST.json"}
    if allowed-found:
        raise ValueError(f"Missing release files: {sorted(allowed-found)[:10]}")
    if found-allowed:
        raise ValueError(f"Unexpected release files: {sorted(found-allowed)[:10]}")
    for name, row in listed.items():
        raw = (root/name).read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"Hash mismatch: {name}")
        if name.endswith(".json"):
            strict_json(raw, name)
        elif name.endswith(".py"):
            ast.parse(raw.decode("utf-8-sig"), filename=name)
    return len(listed)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integrity-only", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    count = integrity(root)
    print(f"PASS: exact release inventory and SHA-256 for {count} files", flush=True)
    if not args.integrity_only:
        replays = sorted((root/"results").glob("*/replay.py"))
        if {p.parent.name for p in replays} != GROUPS:
            raise ValueError("The exact eight replay group identities are required")
        for script in replays:
            print(f"REPLAY: {script.parent.name}", flush=True)
            subprocess.run([sys.executable,"-B","-X","utf8",str(script)],cwd=script.parent,check=True)
        print("PASS: all eight evidence groups replayed; no training or network required")

if __name__ == "__main__":
    main()
