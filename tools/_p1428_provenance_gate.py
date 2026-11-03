# -*- coding: utf-8 -*-
r"""Provenance gate: every results table/figure must have a verified script + archive entry in the manifest.

The manuscript floats are collected with the same recursive scanner used by the provenance audit. For each float the
manifest must contain an entry with status "verified" (script and archive both exist) or "exempt" (with a note). The gate
fails on any missing or pending float, so it can be wired into paper_audit.

    python tools/_p1428_provenance_gate.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
SOURCES = {
    "paperA": ["paper合/main_nc.tex"],
    "A1": ["paper_a1/main.tex"],
    "P3": ["paper3/paper_ieee/main.tex"],
    "A23": ["paper_a2/main_ieee.tex"],
}
FLOAT_RE = re.compile(r"\\begin\{(table|figure)\*?\}(.*?)\\end\{\1\*?\}", re.S)
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")


def collect_tex(path, seen=None):
    if seen is None:
        seen = set()
    path = os.path.abspath(path)
    if path in seen or not os.path.exists(path):
        return []
    seen.add(path)
    tex = io.open(path, encoding="utf-8", errors="ignore").read()
    parts = [tex]
    for inc in re.finditer(r"\\input\{([^}]+)\}", tex):
        parts += collect_tex(os.path.join(os.path.dirname(path), inc.group(1) + ".tex"), seen)
    return parts


def manuscript_floats(name):
    out = set()
    for rel in SOURCES[name]:
        for tex in collect_tex(os.path.join(REPO, rel)):
            for m in FLOAT_RE.finditer(tex):
                lab = LABEL_RE.search(m.group(2))
                if lab:
                    out.add(lab.group(1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    manifest = json.load(io.open(MANIFEST, encoding="utf-8"))["manuscripts"]
    total_missing = 0
    for name, cfg in SOURCES.items():
        floats = manuscript_floats(name)
        entries = {e["label"]: e for e in manifest.get(name, {}).get("floats", [])}
        missing = sorted(f for f in floats if f not in entries)
        pending = sorted(k for k, e in entries.items() if e.get("status") not in ("verified", "exempt"))
        bad = []
        for label, e in entries.items():
            if e.get("status") == "exempt":
                continue
            for key in ("script", "archive"):
                p = e.get(key)
                if not p or not os.path.exists(os.path.join(REPO, p)):
                    bad.append((label, key, p))
        total_missing += len(missing) + len(pending) + len(bad)
        print(f"  {name}: floats={len(floats)} manifest={len(entries)} "
              f"missing={len(missing)} pending={len(pending)} broken_paths={len(bad)}")
        if missing:
            print("    missing:", ", ".join(missing[:10]), "..." if len(missing) > 10 else "")
        if bad:
            print("    broken:", bad[:5])
    print("  gate:", "PASS" if total_missing == 0 else f"FAIL ({total_missing} items)")
    return 0 if total_missing == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
