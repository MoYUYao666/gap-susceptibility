# -*- coding: utf-8 -*-
r"""Download the open-access full texts of a curated shortlist and extract their quotable statements.

Deep-reading twelve papers by hand is what makes a survey more than an abstract digest, but the reading has to start from
real text. This script downloads the open-access PDFs that OpenAlex listed for the shortlist, extracts the text, stores it
under `literature/fulltext/`, and writes a fact sheet: for each paper, its abstract, the numeric sentences from the first
two pages and the numeric sentences from the last two pages (where limitations and conclusion claims live).

Outputs
  paper_rsvlm_survey/literature/fulltext/<doi>.txt
  paper_rsvlm_survey/literature/fulltext_facts_<date>.json

Usage
  D:\Anaconda\envs\pytorch\python.exe tools\_p1799_rsvlm_fulltext.py
"""
import io
import json
import os
import re
import time
import urllib.request

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIT = os.path.join("paper_rsvlm_survey", "literature")
OUTDIR = os.path.join(LIT, "fulltext")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"

# the shortlist: datasets/benchmarks, adaptation, evaluation and the two surveys that frame the field
SHORTLIST = [
    "10.1016/j.rse.2023.113856",            # cross-city benchmark
    "10.1016/j.isprsjprs.2021.05.011",      # multimodal land-cover benchmarks
    "10.1016/j.isprsjprs.2025.03.028",      # RSGPT
    "10.1007/s11432-024-4251-x",            # Woodpecker hallucination correction
    "10.1016/j.inffus.2025.103204",         # MM-InstructEval
    "10.1016/j.neunet.2024.106414",         # Hydra low-rank adaptation
    "10.1007/s11263-024-02247-9",           # LSKNet
    "10.1007/s44267-025-00099-6",           # efficient MLLM survey
    "10.1016/j.inffus.2024.102742",         # knowledge distillation in RS survey
    "10.1016/j.isprsjprs.2022.03.012",      # crop mapping from time series
    "10.3390/rs17040719",                   # DDFAV
    "10.3390/rs18142352",                   # Fed-RSAdapter
]


def fetch_pdf(url, dst):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/pdf,*/*"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read()
    if not data.startswith(b"%PDF"):
        raise ValueError("not a PDF (%d bytes, starts %r)" % (len(data), data[:12]))
    io.open(dst, "wb").write(data)
    return len(data)


def extract_text(path):
    from pypdf import PdfReader
    r = PdfReader(path)
    pages = [(p.extract_text() or "") for p in r.pages]
    return pages


def numeric_sentences(text, limit=8):
    out = []
    for sent in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text)):
        if 20 < len(sent) < 320 and re.search(r"\b\d", sent):
            out.append(sent.strip())
        if len(out) >= limit:
            break
    return out


def main() -> int:
    stamp = time.strftime("%Y-%m-%d")
    os.makedirs(OUTDIR, exist_ok=True)
    oa = json.load(io.open(os.path.join(LIT, "oa_locations_2026-10-28.json"), encoding="utf-8"))
    facts, failed = {}, []
    for doi in SHORTLIST:
        rec = oa.get(doi) or {}
        url = rec.get("pdf_url")
        dst = os.path.join(OUTDIR, re.sub(r"[^0-9a-zA-Z]+", "_", doi) + ".pdf")
        txt = os.path.join(OUTDIR, re.sub(r"[^0-9a-zA-Z]+", "_", doi) + ".txt")
        if not url:
            failed.append((doi, "no open-access pdf listed"))
            print("  skip %-34s no pdf url" % doi)
            continue
        try:
            size = fetch_pdf(url, dst)
            pages = extract_text(dst)
            io.open(txt, "w", encoding="utf-8", newline="").write("\n\n=== PAGE BREAK ===\n\n".join(pages))
            first = " ".join(pages[:2])
            last = " ".join(pages[-2:])
            facts[doi] = {"title": rec.get("title"), "pdf_url": url, "pdf_bytes": size, "pages": len(pages),
                          "head_numbers": numeric_sentences(first), "tail_numbers": numeric_sentences(last),
                          "text_path": txt}
            print("  ok   %-34s %7.1f KB, %d pages" % (doi, size / 1024, len(pages)))
        except Exception as e:
            failed.append((doi, str(e)[:140]))
            print("  FAIL %-34s %s" % (doi, str(e)[:100]))
        time.sleep(1.0)
    io.open(os.path.join(LIT, "fulltext_facts_%s.json" % stamp), "w", encoding="utf-8", newline="").write(
        json.dumps({"generated": time.strftime("%Y-%m-%d %H:%M"), "shortlist": SHORTLIST,
                    "n_ok": len(facts), "failed": failed, "facts": facts}, indent=1, ensure_ascii=False))
    print("\nfull texts: %d ok, %d failed" % (len(facts), len(failed)))
    return 0 if facts else 1


if __name__ == "__main__":
    raise SystemExit(main())
