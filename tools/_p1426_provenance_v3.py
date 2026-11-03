# -*- coding: utf-8 -*-
r"""Provenance v3: figure generator matching with suffix stripping, plus claim-ledger matching for tables.

Figures: strip common suffixes (_crop, _v2, etc.) and search every .py in the repo for the base name; the generator's
`outputs/...json` references become archive candidates.
Tables: match caption numbers to the curated claim ledger entries (which carry verified archive paths).

Output: outputs/analysis/provenance_v3.json

    python tools/_p1426_provenance_v3.py --apply
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "provenance_v3.json")
DRAFT = os.path.join(REPO, "outputs", "analysis", "provenance_map_v2.json")
LEDGERS = {
    "paperA": ["outputs/analysis/claim_ledger_paperA.json", "outputs/analysis/claim_ledger.json"],
    "A1": ["outputs/analysis/claim_ledger_a1.json"],
    "P3": [],
    "A23": [],
}
NUM_RE = re.compile(r"(?<![\w.])(-?\d+\.\d+|\d{2,})(?![\w.])")
YEAR_RE = re.compile(r"^(19|20)\d{2}$")
JSON_RE = re.compile(r"outputs/[\w./-]+\.json")
EXCLUDE = (".git", ".tmp_deepinfer", "publish_clean", "backups")


def py_texts():
    out = {}
    for f in glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True):
        if any(x in f.replace("\\", "/") for x in EXCLUDE):
            continue
        try:
            out[f] = io.open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
    return out


def ledger_entries(name):
    rows = []
    for rel in LEDGERS.get(name, []):
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            continue
        d = json.load(io.open(p, encoding="utf-8"))
        items = d.get("entries") or d.get("claims") or []
        for it in items:
            val = it.get("manuscript")
            src = it.get("source") or ""
            rows.append((val, src, it.get("claim", "")))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    draft = json.load(io.open(DRAFT, encoding="utf-8"))
    pys = py_texts()
    out = {}
    for name, items in draft.items():
        led = ledger_entries(name)
        rows = []
        for it in items:
            cap = it.get("caption", "")
            entry = {"kind": it["kind"], "label": it["label"], "caption": cap[:180],
                     "scripts": [], "archives": [], "ledger_hits": []}
            if it["kind"] == "figure":
                gs = it.get("scripts") or []
                if not gs:
                    # try base names from caption-free scan: reuse draft tokens only
                    pass
                # strip _crop and look again
                bases = []
                for s in gs:
                    b = os.path.splitext(os.path.basename(s))[0]
                    bases += [b, b.replace("_crop", "")]
                holders = set()
                for b in set(bases):
                    for f, t in pys.items():
                        if os.path.basename(b) and b in t:
                            holders.add(f)
                ranked = sorted(holders, key=lambda x: (0 if "/tools/" in x.replace("\\", "/") else 1, len(x)))
                entry["scripts"] = [os.path.relpath(f, REPO) for f in ranked[:2]]
                for f in ranked[:1]:
                    entry["archives"] += sorted(set(JSON_RE.findall(pys[f])))[:5]
            else:
                toks = [t for t in NUM_RE.findall(cap) if not YEAR_RE.match(t)]
                for val, src, claim in led:
                    if val is None:
                        continue
                    for t in toks:
                        try:
                            if abs(float(val) - float(t)) < 1e-6 or (
                                    abs(float(val)) >= 1 and abs(round(float(val)) - float(t)) < 1e-9):
                                entry["ledger_hits"].append({"token": t, "claim": claim, "source": src})
                                break
                        except Exception:
                            continue
                seen = set()
                for h in entry["ledger_hits"]:
                    arch = h["source"].split("::")[0]
                    if arch not in seen:
                        seen.add(arch)
                        entry["archives"].append(arch)
            rows.append(entry)
        out[name] = rows
        solved = sum(1 for r in rows if r["archives"])
        print(f"  {name}: {len(rows)} floats; with candidate archive: {solved}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(out, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
