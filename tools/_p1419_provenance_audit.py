# -*- coding: utf-8 -*-
r"""Provenance audit: every table/figure that reports our own results must name its generating script and JSON archive.

Scans the five manuscripts, extracts float environments (table/figure) with captions and labels, and checks whether a
source path (tools/... or outputs/...json) appears in the caption or in the surrounding text.

Output: outputs/analysis/provenance_audit.json + a readable summary printed to stdout.

    python tools/_p1419_provenance_audit.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "provenance_audit.json")
MANUSCRIPTS = {
    "paperA": ["paper合/main_nc.tex", "paper合/main_springer.tex"],
    "A1": ["paper_a1/main.tex"],
    "P3": ["paper3/paper_ieee/main.tex"],
    "A23": ["paper_a2/main_ieee.tex"],
}
SOURCE_RE = re.compile(r"(tools/_p?\w+|outputs/[\w\\/.%-]+?\.json|outputs/\\(\w| )+?)")
FLOAT_RE = re.compile(r"\\begin\{(table|figure)\*?\}(.*?)\\end\{\1\*?\}", re.S)
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
CAPTION_RE = re.compile(r"\\caption\{(.*?)\}\s*$", re.S)


def scan_file(path: str) -> list:
    text = io.open(path, encoding="utf-8", errors="ignore").read()
    # include \input files so captions from sections are covered
    parts = [text]
    for inc in re.finditer(r"\\input\{([^}]+)\}", text):
        cand = os.path.join(REPO, os.path.dirname(path), inc.group(1) + ".tex")
        if os.path.exists(cand):
            parts.append(io.open(cand, encoding="utf-8", errors="ignore").read())
    items = []
    for part in parts:
        for m in FLOAT_RE.finditer(part):
            body = m.group(2)
            label = LABEL_RE.search(body)
            capt = CAPTION_RE.search(body)
            caption = re.sub(r"\s+", " ", capt.group(1)) if capt else ""
            has_script = bool(re.search(r"tools/_p?\w+", body))
            has_json = bool(re.search(r"\.json", body))
            items.append({"kind": m.group(1),
                          "label": label.group(1) if label else None,
                          "caption": caption[:300],
                          "has_script": has_script,
                          "has_json": has_json,
                          "source_in_body": bool(SOURCE_RE.search(body))})
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}
    for name, files in MANUSCRIPTS.items():
        items = []
        for f in files:
            p = os.path.join(REPO, f)
            if os.path.exists(p):
                items += scan_file(p)
        # dedupe by label
        seen, uniq = set(), []
        for it in items:
            k = it["label"] or it["caption"][:60]
            if k in seen:
                continue
            seen.add(k)
            uniq.append(it)
        missing = [it for it in uniq if not (it["has_script"] and it["has_json"])]
        report[name] = {"n_floats": len(uniq), "n_missing_provenance": len(missing),
                        "missing": [{"kind": it["kind"], "label": it["label"], "caption": it["caption"][:160]}
                                    for it in missing]}
        print(f"  {name}: {len(uniq)} floats, {len(missing)} without full provenance")
        for it in missing[:12]:
            print(f"    - {it['kind']} {it['label']}: {it['caption'][:90]}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(report, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
