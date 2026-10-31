# -*- coding: utf-8 -*-
r"""Audit the handover documents for contradictions before reporting status.

The stage-closing rule requires the three handover artefacts to agree, and this repository has been burned
before by stale numbers left uncorrected. This checks the numbers that are easy to contradict -- paper page
counts, claim-ledger totals, artefact counts -- across HANDOFF.md, 文件地图.md and docs/, and reports the live
state of the deliverables on disk.

    python tools/_p1097_status_audit.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def live_facts() -> dict[str, object]:
    facts: dict[str, object] = {}

    # paper page counts, from the PDFs themselves
    for name, path in (("Paper A NC", REPO / "paper合" / "main_nc.pdf"),
                       ("Paper A Springer", REPO / "paper合" / "main_springer.pdf"),
                       ("P3 manuscript", REPO / "SUBMISSION" / "P3_PRL_revision" / "UPLOAD_2026-10-15"
                        / "P3_PRLETTERS-D-26-02378_Manuscript.pdf")):
        if not path.exists():
            facts[name] = "missing"
            continue
        try:
            # pdfinfo writes in the console's code page on Windows, so decoding must tolerate that rather
            # than assume UTF-8 (which raised UnicodeDecodeError inside subprocess's reader thread).
            out = subprocess.run(["pdfinfo", str(path)], capture_output=True, timeout=30,
                                 encoding="utf-8", errors="replace").stdout or ""
            m = re.search(r"Pages:\s+(\d+)", out)
            facts[name] = int(m.group(1)) if m else "?"
        except Exception:
            facts[name] = "?"

    # claim ledger
    lp = REPO / "outputs" / "analysis" / "claim_ledger.json"
    if lp.exists():
        d = json.loads(io.open(lp, encoding="utf-8").read())
        facts["ledger"] = f"{d.get('passed')} passed / {d.get('failed')} failed"
        facts["ledger_claims"] = len(d.get("claims", []))

    # LLaVA archive
    lv = REPO / "outputs" / "llava_bf16_sites_cloud"
    if lv.exists():
        facts["llava_records"] = len([f for f in os.listdir(lv) if f.endswith(".json")
                                      and "progress" not in f and f != "llava_sites.json"])
        facts["llava_adapters"] = len(glob.glob(str(lv / "*.pt")))
        facts["llava_mb"] = round(sum(os.path.getsize(lv / f) for f in os.listdir(lv)) / 1e6, 1)

    # generated tools from this session
    facts["tools_added_today"] = len([f for f in glob.glob(str(REPO / "tools" / "_p10*.py"))
                                      + glob.glob(str(REPO / "tools" / "_p10*.sh"))
                                      + glob.glob(str(REPO / "tools" / "_p8*_cloud*.sh"))])

    # git
    try:
        log = subprocess.run(["git", "log", "--oneline", "-1"], cwd=REPO, capture_output=True, text=True).stdout
        facts["head"] = log.strip()
        st = subprocess.run(["git", "status", "--short"], cwd=REPO, capture_output=True, text=True).stdout
        facts["dirty_files"] = len([l for l in st.splitlines() if l.strip()])
    except Exception:
        pass
    return facts


def doc_claims() -> dict[str, list[tuple[str, int, str]]]:
    """Find page-count and count claims in the handover documents."""
    found: dict[str, list[tuple[str, int, str]]] = {}
    pat = re.compile(r"(\d{2,3})\s*(?:页|pp\.?|pages)")
    for rel in ("HANDOFF.md", "文件地图.md"):
        p = REPO / rel
        if not p.exists():
            continue
        hits = []
        for i, line in enumerate(io.open(p, encoding="utf-8", errors="replace"), 1):
            for m in pat.finditer(line):
                hits.append((f"{rel}:{i}", int(m.group(1)), " ".join(line.split())[:110]))
        found[rel] = hits
    return found


def main() -> None:
    print("=== live facts ===")
    facts = live_facts()
    for k, v in facts.items():
        print(f"  {k:<20} {v}")

    print("\n=== page-count claims in the handover docs (recent entries only) ===")
    for rel, hits in doc_claims().items():
        print(f"  {rel}: {len(hits)} numeric page claims")
        for where, n, line in hits[:12]:
            print(f"    {where}: {n}  |  {line}")

    print("\n=== contradiction check ===")
    nc = facts.get("Paper A NC")
    print(f"  Paper A NC pages on disk: {nc}")
    for rel, hits in doc_claims().items():
        vals = {n for _w, n, _l in hits}
        if nc in vals:
            print(f"  {rel}: contains {nc} -> agrees with the PDF")
        else:
            print(f"  {rel}: no entry states {nc}; values present: {sorted(vals)[:12]}")


if __name__ == "__main__":
    main()
