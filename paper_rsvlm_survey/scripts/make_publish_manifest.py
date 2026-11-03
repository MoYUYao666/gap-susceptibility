# -*- coding: utf-8 -*-
r"""Write PUBLISHING_MANIFEST.json for the survey reference corpus.

Reads the archived literature records and records the counts that the review quotes (harvested, de-duplicated,
DOI-carrying, verified) together with the file sizes of the published subset.

Usage
  python paper_rsvlm_survey/scripts/make_publish_manifest.py
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name):
    p = os.path.join(ROOT, "literature", name)
    return json.loads(io.open(p, encoding="utf-8").read()) if os.path.exists(p) else None


def count_records(obj):
    if isinstance(obj, list):
        return len(obj)
    if isinstance(obj, dict):
        return len(obj)
    return 0


def main():
    raw = load("raw_2026-10-27.json")
    dedup = load("dedup_2026-10-27.json")
    verified = load("verified_2026-10-27.json")
    summary = load("summary_2026-10-27.json")
    verify_summary = load("verify_summary_2026-10-27.json")
    audit = load("disclosure_audit_2026-10-28.json")
    screening = json.loads(io.open(os.path.join(ROOT, "screening", "core_2026-10-27.json"),
                                  encoding="utf-8").read())

    raw_total = sum(count_records(v) for v in raw.values()) if isinstance(raw, dict) else count_records(raw)
    doi_carrying = sum(1 for k in (dedup or {}) if str(k).startswith("10.")) if isinstance(dedup, dict) else 0

    files = []
    for base in (os.path.join(ROOT, "literature"), os.path.join(ROOT, "screening"), os.path.join(ROOT, "scripts")):
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            p = os.path.join(base, name)
            if os.path.isfile(p) and os.path.splitext(name)[1] in (".json", ".md", ".csv", ".bib", ".py"):
                files.append({"path": os.path.relpath(p, ROOT).replace("\\", "/"), "bytes": os.path.getsize(p)})

    manifest = {
        "generated": "2026-10-31",
        "purpose": "machine-readable record counts for the reference corpus of the RS-VLM review",
        "harvest": {
            "source": "OpenAlex",
            "queries": (summary.get("n_queries")
                        if isinstance(summary, dict) and isinstance(summary.get("n_queries"), int)
                        else (len(summary.get("per_query", {}))
                              if isinstance(summary, dict) and isinstance(summary.get("per_query"), (list, dict))
                              else None)),
            "raw_records": raw_total,
        },
        "dedup_records": count_records(dedup),
        "doi_carrying_records": doi_carrying,
        "verified_records": count_records(verified),
        "verification": verify_summary if isinstance(verify_summary, dict) else {},
        "screened_core_records": count_records(screening),
        "disclosure_audit_papers": audit.get("n_papers") if isinstance(audit, dict) else None,
        "published_files": files,
        "excluded": ["full-text PDFs and extracted text (publisher content)"],
    }
    out = os.path.join(ROOT, "PUBLISHING_MANIFEST.json")
    io.open(out, "w", encoding="utf-8", newline="").write(json.dumps(manifest, indent=1) + "\n")
    print("wrote", out)
    print("raw", raw_total, "| dedup", count_records(dedup), "| doi", doi_carrying,
          "| verified", count_records(verified), "| audit papers", manifest["disclosure_audit_papers"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
