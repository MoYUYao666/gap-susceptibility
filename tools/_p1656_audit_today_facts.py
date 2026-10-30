#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1656_audit_today_facts.py -- task-21 independent audit, repository-fact collector.

Read-only. Gathers the machine-checkable side of the hand-off claims so the audit notes can
cite exact files/lines/commands. Writes outputs/analysis/audit_docs_rules_facts.json.
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = ROOT / "outputs/analysis/audit_docs_rules_facts.json"
TODAY = date(2026, 10, 25)


def sh(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=str(cwd or ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def pdf_pages(p):
    if not p.exists():
        return None
    code, out, _ = sh(["pdfinfo", str(p)])
    if code != 0:
        return None
    m = re.search(r"^Pages:\s+(\d+)", out, re.M)
    return int(m.group(1)) if m else None


def log_pages(p):
    if not p.exists():
        return None
    t = p.read_text(encoding="utf-8", errors="replace")
    m = None
    for mm in re.finditer(r"Output written on .*?\((\d+) pages?,", t):
        m = mm
    return int(m.group(1)) if m else None


def mt(p):
    return (datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")
            if p.exists() else None)


F = {}
F["generated"] = datetime.now().isoformat(timespec="seconds")
F["today"] = TODAY.isoformat()

# ---- A. page counts vs hand-off claims
CLAIMED = {"paper_a1/main.pdf": 64, "paper合/main_nc.pdf": 79, "paper合/main_springer.pdf": 56,
           "paper3/paper_ieee/main.pdf": 10, "paper3/paper_ieee/supplementary/supplementary.pdf": 26,
           "paper_a2/main_ieee.pdf": 73, "paper_review_prl/main_prl.pdf": 7}
pages = {}
for rel, claimed in CLAIMED.items():
    p = ROOT / rel
    pages[rel] = {"claimed": claimed, "pdf_pages": pdf_pages(p),
                  "pdf_mtime": mt(p),
                  "log_pages": None, "log": None, "log_mtime": None,
                  "match": None}
    # find the sibling .log the profile tracks
    logcand = []
    if "paper3/paper_ieee/supplementary" in rel:
        logcand = [p.parent / "supplementary.log"]
    elif rel.endswith("main_ieee.pdf"):
        logcand = [p.parent / "main_ieee.log"]
    elif rel.endswith("main_prl.pdf"):
        logcand = [p.parent / "main_prl.log"]
    elif rel.endswith("main_nc.pdf"):
        logcand = [p.parent / "main_nc.log"]
    elif rel.endswith("main_springer.pdf"):
        logcand = [p.parent / "main_springer.log"]
    elif rel.endswith("main.pdf"):
        logcand = [p.parent / "main.log"]
    for lp in logcand:
        if lp.exists():
            pages[rel]["log"] = str(lp.relative_to(ROOT))
            pages[rel]["log_pages"] = log_pages(lp)
            pages[rel]["log_mtime"] = mt(lp)
    pages[rel]["match"] = (pages[rel]["pdf_pages"] == claimed)
F["page_counts"] = pages

# ---- B. P3 supplement structure
supp = ROOT / "paper3/paper_ieee/supplementary/supplementary.tex"
st = supp.read_text(encoding="utf-8")
F["p3_supplement"] = {
    "path": str(supp.relative_to(ROOT)),
    "pages": pdf_pages(ROOT / "paper3/paper_ieee/supplementary/supplementary.pdf"),
    "n_sections": len(re.findall(r"\\section\{", st)),
    "n_table_floats": len(re.findall(r"\\begin\{table\*?\}", st)),
    "n_begin_table": len(re.findall(r"\\begin\{table\}", st)),
    "mtime": mt(supp),
}

# ---- C. A23 next-revision package: candidate dirs
cands = []
for base in ("SUBMISSION", "paper_a2", "docs"):
    b = ROOT / base
    if not b.exists():
        continue
    for dp, dn, fn in os.walk(b):
        low = dp.lower()
        if "revision" in low or "next" in low:
            rel = os.path.relpath(dp, ROOT)
            cands.append({"dir": rel, "n_files": len(fn),
                          "files": sorted(fn)[:40]})
F["a23_revision_package_candidates"] = cands[:20]

# ---- D. two cloud jobs executed
def jload(rel):
    p = ROOT / rel
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

igu = jload("outputs/analysis/p3_official_igu_run.json")
vs = jload("outputs/analysis/p3_official_vs_reimpl.json")
rep = jload("outputs/analysis/p3_official_igu_replicates.json")
pope = jload("outputs/analysis/p3_second_downstream.json")
F["cloud_jobs"] = {
    "official_igu_run": {
        "exists": igu is not None,
        "n_runs": len(igu.get("runs", [])) if isinstance(igu, dict) else None,
        "path": "outputs/analysis/p3_official_igu_run.json",
        "mtime": mt(ROOT / "outputs/analysis/p3_official_igu_run.json")},
    "official_vs_reimpl": {
        "exists": vs is not None,
        "keys": sorted(vs.keys()) if isinstance(vs, dict) else None,
        "path": "outputs/analysis/p3_official_vs_reimpl.json",
        "mtime": mt(ROOT / "outputs/analysis/p3_official_vs_reimpl.json")},
    "replicates": {
        "exists": rep is not None,
        "keys": sorted(rep.keys()) if isinstance(rep, dict) else None,
        "path": "outputs/analysis/p3_official_igu_replicates.json",
        "mtime": mt(ROOT / "outputs/analysis/p3_official_igu_replicates.json")},
    "pope": {
        "exists": pope is not None,
        "sha256_prefix": None,
        "path": "outputs/analysis/p3_second_downstream.json",
        "mtime": mt(ROOT / "outputs/analysis/p3_second_downstream.json")},
    "cloud_retrieved_dir": (ROOT / "cloud_retrieved/round2_2026-10-25").exists(),
}
if (ROOT / "outputs/analysis/p3_second_downstream.json").exists():
    import hashlib
    F["cloud_jobs"]["pope"]["sha256_prefix"] = hashlib.sha256(
        (ROOT / "outputs/analysis/p3_second_downstream.json").read_bytes()).hexdigest()[:16]

# ---- E. publish / tags / remaining items
code, tags, _ = sh(["git", "tag", "--list", "--sort=-creatordate"])
F["git"] = {
    "head": sh(["git", "log", "--oneline", "-1"])[1],
    "n_tags": len([x for x in tags.split("\n") if x.strip()]),
    "tags_tail": [x for x in tags.split("\n") if x.strip()][:12],
    "v25_exists": "v2.5" in [x.strip() for x in tags.split("\n")],
}
# tag creation dates for today's tags
tag_dates = {}
for t in [x.strip() for x in tags.split("\n") if x.strip()][:15]:
    code, out, _ = sh(["git", "log", "-1", "--format=%cI", t])
    if code == 0:
        tag_dates[t] = out
F["git"]["tag_dates"] = tag_dates
F["git"]["tags_created_today"] = [t for t, d in tag_dates.items() if d.startswith("2026-10-25")]
# reflog for tag refs (catch any moved tag: reflog of refs/tags would show updates)
reflog = []
proot = ROOT / ".git"
if proot.exists():
    for dp, dn, fn in os.walk(proot / "logs"):
        for f in fn:
            p = Path(dp) / f
            if "tag" in str(p):
                reflog.append(str(p.relative_to(ROOT)))
F["git"]["tag_reflog_files"] = reflog[:10]

pc = ROOT / "publish_clean"
if (pc / ".git").exists():
    F["publish_clean"] = {"head": sh(["git", "-C", str(pc), "log", "--oneline", "-1"])[1],
                          "n_status": len([x for x in sh(["git", "-C", str(pc), "status", "--porcelain"])[1].split("\n") if x.strip()]),
                          "mtime": mt(pc / ".git")}

# remaining-item evidence: A23 cover letter, DOI backfill
cover = []
for pat in ("*cover*letter*", "CoverLetter*"):
    cover += [str(p.relative_to(ROOT)) for p in ROOT.rglob(pat) if "paper_a2" in str(p) or "A23" in str(p)]
F["remaining_items"] = {"a23_cover_letter_candidates": sorted(set(cover))[:12]}
# DOI backfill state: look for zenodo DOI mentions in RELEASE_NOTES / README
doi_files = []
for name in ("README.md", "RELEASE_NOTES_v2.5.md", "RELEASE_NOTES_v2.4.md"):
    p = ROOT / name
    if p.exists():
        t = p.read_text(encoding="utf-8", errors="replace")
        doi_files.append({"file": name, "zenodo_dois": sorted(set(re.findall(r"10\.5281/zenodo\.\d+", t)))})
F["remaining_items"]["doi_files"] = doi_files

# ---- F. upload filenames: underscores under staged revision packages
staged = [p for p in ROOT.glob("SUBMISSION/**/*") if p.is_file()]
staged += [p for p in ROOT.glob("paper合/NC_submission/**/*") if p.is_file()]
under = [str(p.relative_to(ROOT)) for p in staged if "_" in p.name]
F["upload_filenames"] = {
    "n_files_scanned": len(staged),
    "n_with_underscore": len(under),
    "examples": under[:20],
    "note": "rule applies to upload filenames; local source/script names are exempt",
}

# ---- G. fonts on figures produced today
figs = []
for base in ("paper3/paper_ieee/figures", "paper合/figures", "paper_a1/figures",
             "paper_a2/figures", "paper_review_prl/figures"):
    b = ROOT / base
    if b.exists():
        for p in b.rglob("*.pdf"):
            if datetime.fromtimestamp(p.stat().st_mtime).date() == TODAY:
                figs.append(p)
font_rows = []
for p in figs[:20]:
    code, out, _ = sh(["pdffonts", str(p)])
    rows = [ln for ln in out.split("\n")[2:] if ln.strip()]
    types = sorted({ln.split()[-1] if ln.split() else "" for ln in rows})
    names = sorted({ln.split()[0] for ln in rows if ln.split()})
    font_rows.append({"fig": str(p.relative_to(ROOT)), "mtime": mt(p),
                      "fonts": names[:8], "types": types,
                      "type3": any("Type 3" in ln for ln in rows),
                      "only_times": all(("Times" in n or "STIX" in n) for n in names) if names else None})
F["figures_today"] = {"n": len(figs), "rows": font_rows}

# ---- H. language rule: CJK scan of today's archives + scripts
def cjk_hits(t):
    return len(re.findall(r"[\u4e00-\u9fff]", t))

today_files = []
for base in ("outputs/analysis", "tools", "docs"):
    b = ROOT / base
    if not b.exists():
        continue
    for p in b.rglob("*"):
        if not p.is_file():
            continue
        if datetime.fromtimestamp(p.stat().st_mtime).date() != TODAY:
            continue
        today_files.append(p)

lang = {"archives_today": [], "scripts_today_with_cjk": []}
for p in today_files:
    if p.suffix != ".json":
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    n = cjk_hits(t)
    if n:
        lang["archives_today"].append({"file": str(p.relative_to(ROOT)), "cjk_chars": n})
for p in today_files:
    if p.suffix != ".py" or not str(p).startswith(str(ROOT / "tools")):
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    n = cjk_hits(t)
    if n:
        lang["scripts_today_with_cjk"].append({"file": str(p.relative_to(ROOT)), "cjk_chars": n})
F["language_rule"] = lang

# ---- I. SCI venue registry
reg = ROOT / "docs/VENUE_SCI_REGISTRY.md"
if reg.exists():
    t = reg.read_text(encoding="utf-8")
    F["sci_registry"] = {"exists": True, "mtime": mt(reg),
                         "mentions": {v: t.count(v) for v in
                                      ("Neurocomputing", "Pattern Analysis and Applications",
                                       "Pattern Recognition Letters", "IEEE Journal of Oceanic",
                                       "SCIE")},
                         "n_date_tokens": len(re.findall(r"2026-1\d-\d\d", t))}
else:
    F["sci_registry"] = {"exists": False}

# ---- J. inventory: docs/ and tools/ created or modified today
inv = {"docs": [], "tools": []}
for base in ("docs", "tools"):
    b = ROOT / base
    for p in b.rglob("*"):
        if not p.is_file():
            continue
        m = datetime.fromtimestamp(p.stat().st_mtime)
        if m.date() != TODAY:
            continue
        inv[base].append({"file": str(p.relative_to(ROOT)), "size": p.stat().st_size,
                          "mtime": m.isoformat(timespec="seconds")})
for k in inv:
    inv[k].sort(key=lambda r: r["mtime"])
F["inventory_today"] = {"n_docs": len(inv["docs"]), "n_tools": len(inv["tools"]),
                        "docs": inv["docs"], "tools": inv["tools"]}

OUT.write_text(json.dumps(F, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote", OUT)
print("\nPAGE COUNTS (claimed vs pdfinfo):")
for rel, r in F["page_counts"].items():
    print("  %-62s claimed=%-3s pdf=%-3s log=%-3s match=%s" %
          (rel, r["claimed"], r["pdf_pages"], r["log_pages"], r["match"]))
print("\nP3 supplement:", F["p3_supplement"])
print("\ncloud jobs:", {k: (v if not isinstance(v, dict) else {kk: v[kk] for kk in v if kk in ("exists", "n_runs")})
                        for k, v in F["cloud_jobs"].items()})
print("\ngit tags:", F["git"]["n_tags"], "v2.5:", F["git"]["v25_exists"],
      "today:", F["git"]["tags_created_today"])
print("inventory: docs=%d tools=%d" % (F["inventory_today"]["n_docs"], F["inventory_today"]["n_tools"]))
print("uploads scanned=%d with_underscore=%d" % (F["upload_filenames"]["n_files_scanned"],
                                                 F["upload_filenames"]["n_with_underscore"]))
print("figures today=%d" % F["figures_today"]["n"])
print("CJK archives today=%d scripts=%d" % (len(F["language_rule"]["archives_today"]),
                                            len(F["language_rule"]["scripts_today_with_cjk"])))
