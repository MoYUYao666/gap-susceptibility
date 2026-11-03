# -*- coding: utf-8 -*-
r"""Draft a provenance map (float -> generating script -> result archive) for the manuscript floats.

Figures are matched through their \includegraphics basenames: the generator script is the tools/*.py file that mentions the
basename, and the result archive is the outputs/*.json path mentioned inside that generator. Tables have no filename, so the
script proposes candidate archives by exact numeric-token matching and marks them for review.

Output: outputs/analysis/provenance_map_draft.json

    python tools/_p1420_build_provenance_map.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "provenance_map_draft.json")
MANUSCRIPTS = {
    "paperA": ["paper合/main_nc.tex"],
    "A1": ["paper_a1/main.tex"],
    "P3": ["paper3/paper_ieee/main.tex"],
    "A23": ["paper_a2/main_ieee.tex"],
}
FLOAT_RE = re.compile(r"\\begin\{(table|figure)\*?\}(.*?)\\end\{\1\*?\}", re.S)
LABEL_RE = re.compile(r"\\label\{([^}]+)\}")
CAPTION_RE = re.compile(r"\\caption\{(.*?)\}", re.S)
GRAPHICS_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
NUM_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])")


def collect_tex(path: str, seen=None) -> list:
    """Return the source text of a manuscript plus all recursively \\input files."""
    if seen is None:
        seen = set()
    path = os.path.abspath(path)
    if path in seen or not os.path.exists(path):
        return []
    seen.add(path)
    tex = io.open(path, encoding="utf-8", errors="ignore").read()
    parts = [tex]
    for inc in re.finditer(r"\\input\{([^}]+)\}", tex):
        cand = os.path.join(os.path.dirname(path), inc.group(1) + ".tex")
        parts += collect_tex(cand, seen)
    return parts


def tool_files() -> dict:
    out = {}
    for f in glob.glob(os.path.join(REPO, "tools", "*.py")):
        try:
            out[f] = io.open(f, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
    return out


def json_archives() -> dict:
    out = {}
    for pat in ("outputs/*.json", "outputs/analysis/*.json", "outputs/*/*.json"):
        for f in glob.glob(os.path.join(REPO, pat)):
            try:
                out[f] = io.open(f, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    tools = tool_files()
    arches = json_archives()
    draft = {}
    for name, files in MANUSCRIPTS.items():
        items = []
        for rel in files:
            for tex in collect_tex(os.path.join(REPO, rel)):
                for m in FLOAT_RE.finditer(tex):
                    body = m.group(2)
                    label = LABEL_RE.search(body)
                    caption = re.sub(r"\s+", " ", CAPTION_RE.search(body).group(1)) if CAPTION_RE.search(body) else ""
                    entry = {"kind": m.group(1), "label": label.group(1) if label else None,
                             "caption": caption[:240], "script": None, "archives": [], "candidates": []}
                    if m.group(1) == "figure":
                        gs = GRAPHICS_RE.findall(body)
                        base = os.path.splitext(os.path.basename(gs[0]))[0] if gs else None
                        if base:
                            holders = [f for f, t in tools.items() if base in t]
                            if holders:
                                entry["script"] = os.path.relpath(min(holders, key=len), REPO)
                                gen = tools[holders[0]]
                                entry["archives"] = sorted(set(re.findall(r"outputs/[\w./-]+\.json", gen)))[:4]
                    else:
                        toks = [x for x in NUM_RE.findall(caption) if len(x) >= 2][:8]
                        scored = []
                        for f, tt in arches.items():
                            score = sum(1 for tok in toks
                                        if re.search(r"(?<![\d.])" + re.escape(tok) + r"(?![\d.])", tt))
                            if score >= 2:
                                scored.append((score, os.path.relpath(f, REPO)))
                        scored.sort(reverse=True)
                        entry["candidates"] = scored[:3]
                    items.append(entry)
        draft[name] = items
        print(f"  {name}: {len(items)} floats; figures with script: {sum(1 for i in items if i['script'])}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(draft, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
