# -*- coding: utf-8 -*-
r"""Render docs/PROVENANCE_MANIFEST_2026-10-20.md from docs/provenance_manifest.json.

    python tools/_p1433_render_provenance_manifest.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON = os.path.join(REPO, "docs", "provenance_manifest.json")
MD = os.path.join(REPO, "docs", "PROVENANCE_MANIFEST_2026-10-20.md")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    d = json.load(io.open(JSON, encoding="utf-8"))
    lines = ["# Provenance manifest (2026-10-20)", "",
             "Rule: every table/figure that reports our own results must name its generating script and its result JSON",
             "archive. Literature tables and schematic diagrams are exempt but listed explicitly.",
             "Gate: `python tools/_p1428_provenance_gate.py` (must print PASS).", ""]
    total = verified = exempt = pending = 0
    for name, cfg in d["manuscripts"].items():
        floats = cfg.get("floats", [])
        total += len(floats)
        verified += sum(1 for e in floats if e["status"] == "verified")
        exempt += sum(1 for e in floats if e["status"] == "exempt")
        pending += sum(1 for e in floats if e["status"] not in ("verified", "exempt"))
        lines += [f"## {name} ({cfg.get('source', '')})", "", "| item | script | archive | status |",
                  "|---|---|---|---|"]
        for e in sorted(floats, key=lambda x: x["label"]):
            sc = e.get("script") or "-"
            ar = e.get("archive") or (", ".join(e.get("archives") or []) if e.get("archives") else "-")
            lines.append(f"| `{e['label']}` | `{sc}` | `{ar}` | {e['status']} |")
        lines.append("")
    lines += [f"Totals: {total} floats; verified {verified}; exempt {exempt}; pending {pending}.", ""]
    print(f"  totals: {total} floats, verified {verified}, exempt {exempt}, pending {pending}")
    if a.apply:
        io.open(MD, "w", encoding="utf-8", newline="").write("\n".join(lines))
        print("  wrote", os.path.relpath(MD, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
