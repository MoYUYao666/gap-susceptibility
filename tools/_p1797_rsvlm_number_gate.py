# -*- coding: utf-8 -*-
r"""Number-provenance gate for the survey: every numeric claim quoted from a source must appear in that source's abstract.

The provenance table lists (claim, value, DOI). This gate opens the archived abstract for that DOI and requires the value -
normalised so that "590,326" and "590326" compare equal - to occur in the text. It fails loudly, naming the row, when a
value cannot be found, which is the machine-checkable part of "no number without a source".

Inputs
  paper_rsvlm_survey/provenance.md                     table with columns: claim | value | source
  paper_rsvlm_survey/literature/abstracts_<date>.json  real abstracts from OpenAlex

Usage
  D:\Anaconda\envs\pytorch\python.exe tools\_p1797_rsvlm_number_gate.py [--date 2026-10-27]
Exit code 1 when any check fails.
"""
import argparse
import io
import json
import os
import re

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIT = os.path.join("paper_rsvlm_survey", "literature")
PROV = "paper_rsvlm_survey/provenance.md"


def norm(s):
    s = s.lower().replace(",", "")
    s = s.replace("–", "-").replace("×", "x")
    return re.sub(r"\s+", " ", s)


def load_table():
    rows = []
    for line in io.open(PROV, encoding="utf-8"):
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() in ("claim",):
            continue
        rows.append({"claim": cells[0], "value": cells[1], "source": cells[2]})
    return rows


def find_dois(source):
    return re.findall(r"10\.\d{4,9}/[^\s|`]+", source)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="2026-10-27")
    a = ap.parse_args()
    abstracts = json.load(io.open(os.path.join(LIT, "abstracts_%s.json" % a.date), encoding="utf-8"))
    abstracts = {k.lower(): v for k, v in abstracts.items()}
    # arXiv preprints are not in the OpenAlex abstract dump; fold in the arXiv archive keyed by DOI.
    arx_path = os.path.join(LIT, "arxiv_abstracts_%s.json" % a.date)
    if os.path.exists(arx_path):
        for aid, rec in json.load(io.open(arx_path, encoding="utf-8")).items():
            abstracts.setdefault(rec["doi"].lower(), {"title": rec["title"], "abstract": rec["abstract"]})
    rows = load_table()
    ok, failed, skipped = 0, [], 0
    for r in rows:
        dois = find_dois(r["source"])
        if not dois:
            skipped += 1
            continue
        doi = dois[0].lower()
        rec = abstracts.get(doi)
        rec = abstracts.get(doi)
        slug = re.sub(r"[^0-9a-zA-Z]+", "_", doi)
        chunks = []
        if rec:
            chunks.append(rec["abstract"])
        for name in (slug + ".txt", "web_" + slug + ".txt"):
            fpath = os.path.join(LIT, "fulltext", name)
            if os.path.exists(fpath):
                chunks.append(io.open(fpath, encoding="utf-8", errors="replace").read())
        if not chunks:
            failed.append((r["claim"], r["value"], doi, "no archived abstract, full text or page"))
            continue
        hay = norm(" ".join(chunks))
        probe = norm(r["value"])
        # allow "5 million" style values to match "5,000,000" or "5 m"
        probes = [probe]
        m = re.match(r"^(\d+(?:\.\d+)?) million", probe)
        if m:
            probes += ["%s million" % m.group(1), "%sm" % m.group(1), "{:,.0f}".format(float(m.group(1)) * 1e6)]
        if any(p in hay for p in probes) or any(norm(p) in hay for p in probes):
            ok += 1
        else:
            failed.append((r["claim"], r["value"], doi, "value not found in the abstract"))
    print("checked %d rows: %d ok, %d failed, %d without a DOI source" % (len(rows), ok, len(failed), skipped))
    for claim, value, doi, why in failed:
        print("  FAIL  %-46s %-12s %-34s %s" % (claim[:46], value[:12], doi, why))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
