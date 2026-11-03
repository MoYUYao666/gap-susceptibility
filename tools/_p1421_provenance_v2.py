# -*- coding: utf-8 -*-
r"""Provenance map v2: repo-wide script search for figures and numeric-token verification for tables.

Output: outputs/analysis/provenance_map_v2.json  (per float: script, archive candidates, verification)

    python tools/_p1421_provenance_v2.py --apply
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "outputs", "analysis", "provenance_map_v2.json")
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
EXCLUDE = (".git", ".tmp_deepinfer", "publish_clean", "backups", "node_modules")


def collect_tex(path: str, seen=None) -> list:
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


def py_sources() -> dict:
    out = {}
    for f in glob.glob(os.path.join(REPO, "**", "*.py"), recursive=True):
        if any(x in f.replace("\\", "/") for x in EXCLUDE):
            continue
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


def score_archive(text: str, toks: list) -> int:
    return sum(1 for t in toks if re.search(r"(?<![\d.])" + re.escape(t) + r"(?![\d.])", text))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    pys = py_sources()
    arches = json_archives()
    draft = {}
    for name, files in MANUSCRIPTS.items():
        items = []
        for rel in files:
            for tex in collect_tex(os.path.join(REPO, rel)):
                for m in FLOAT_RE.finditer(tex):
                    body = m.group(2)
                    label = LABEL_RE.search(body)
                    capm = CAPTION_RE.search(body)
                    caption = re.sub(r"\s+", " ", capm.group(1)) if capm else ""
                    entry = {"kind": m.group(1), "label": label.group(1) if label else None,
                             "caption": caption[:220], "scripts": [], "archive": None,
                             "archive_score": 0, "tokens": []}
                    if m.group(1) == "figure":
                        gs = GRAPHICS_RE.findall(body)
                        base = os.path.splitext(os.path.basename(gs[0]))[0] if gs else None
                        if base:
                            holders = [f for f, t in pys.items() if base in t]
                            holders.sort(key=lambda x: (0 if "/tools/" in x.replace("\\", "/") else 1, len(x)))
                            entry["scripts"] = [os.path.relpath(f, REPO) for f in holders[:2]]
                            if holders:
                                gen = pys[holders[0]]
                                arcs = sorted(set(re.findall(r"outputs/[\w./-]+\.json", gen)))
                                toks = [t for t in NUM_RE.findall(caption) if len(t) >= 2][:6]
                                entry["tokens"] = toks
                                best = [(score_archive(arches.get(os.path.join(REPO, x), ""), toks), x) for x in arcs]
                                best.sort(reverse=True)
                                if best:
                                    entry["archive_score"], entry["archive"] = best[0]
                    else:
                        toks = [t for t in NUM_RE.findall(caption) if len(t) >= 2][:8]
                        entry["tokens"] = toks
                        scored = []
                        for f, t in arches.items():
                            s = score_archive(t, toks)
                            if s >= 2:
                                scored.append((s, os.path.relpath(f, REPO)))
                        scored.sort(reverse=True)
                        if scored:
                            entry["archive_score"], entry["archive"] = scored[0]
                    items.append(entry)
        draft[name] = items
        n_ok = sum(1 for i in items if i["archive"])
        print(f"  {name}: {len(items)} floats; archive candidates: {n_ok}; figure scripts: "
              f"{sum(1 for i in items if i['scripts'])}")
    if a.apply:
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(draft, indent=1))
        print("  wrote", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
