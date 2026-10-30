#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""_p1659_audit_rules.py -- task-21 standing-rule + package/label checks.

Covers: (a) upload filenames in staged packages, (b) fonts on figures produced today,
(c) language rule on today's new artefacts, (d) SCI registry, (e) tag/Release freeze,
plus: A23 next-revision package contents, cloud retrieval zero-byte files, publish_clean refs,
and the Source-script existence check for the traced numbers.
"""
import json
import os
import re
import subprocess
from datetime import date, datetime
from pathlib import Path

ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = ROOT / "outputs/analysis/audit_rules_facts.json"
TODAY = date(2026, 10, 25)


def sh(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=str(cwd or ROOT), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


R = {}

# ---- (a) upload filenames in STAGED packages only
PKG_DIRS = [p for p in ROOT.glob("SUBMISSION/*_next*")] + \
           [p for p in ROOT.glob("SUBMISSION/_venue_builds/*_next*")] + \
           [p for p in ROOT.glob("paper合/NC_submission") if p.exists()]
UPLOAD_EXT = {".pdf", ".docx", ".zip", ".txt"}
INTERNAL = {"README.md", "SHA256SUMS.txt", "EM_FIELDS.md", "PORTAL_TEXT.md"}
rows = []
for d in PKG_DIRS:
    for p in sorted(d.iterdir()):
        if not p.is_file():
            continue
        if p.name in INTERNAL or p.suffix.lower() not in UPLOAD_EXT:
            continue
        rows.append({"package": str(d.relative_to(ROOT)), "file": p.name,
                     "underscore_in_upload_name": "_" in p.name})
R["a_upload_names"] = {
    "n_packages": len(PKG_DIRS),
    "packages": [str(d.relative_to(ROOT)) for d in PKG_DIRS],
    "upload_files": rows,
    "n_upload_files": len(rows),
    "n_with_underscore": sum(1 for r in rows if r["underscore_in_upload_name"]),
    "violations": [r for r in rows if r["underscore_in_upload_name"]],
    "scope_note": ("checked only the staged upload packages; internal packaging notes "
                   "(README/SHA256SUMS/EM_FIELDS) and legacy source dirs are not uploads"),
}

# ---- (b) figures produced today (any directory)
figs = []
for p in ROOT.rglob("*.pdf"):
    if any(x in str(p) for x in (".worktrees", "publish_clean", "backups", "_archive")):
        continue
    if datetime.fromtimestamp(p.stat().st_mtime).date() == TODAY:
        rel = str(p.relative_to(ROOT))
        if "figure" in rel.lower() or "fig" in p.name.lower():
            figs.append(p)
font_rows = []
for p in figs[:15]:
    code, out, _ = sh(["pdffonts", str(p)])
    names = sorted({ln.split()[0] for ln in out.split("\n")[2:] if ln.strip() and ln.split()})
    type3 = any("Type 3" in ln for ln in out.split("\n")[2:])
    font_rows.append({"fig": str(p.relative_to(ROOT)), "mtime": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
                      "fonts": names[:8], "type3": type3,
                      "only_times_or_stix": all(("Times" in n or "STIX" in n) for n in names) if names else None})
R["b_figures_today"] = {"n": len(figs), "rows": font_rows,
                        "verdict": "NOT_EXERCISED" if not figs else "checked"}

# ---- (c) language rule: today's NEW files (git untracked) vs modified
code, status, _ = sh(["git", "status", "--porcelain"])
untracked = [ln[3:].strip().strip('"') for ln in status.split("\n")
             if ln.startswith("?? ")]
cjk_new, cjk_modified = [], []
for rel in untracked:
    p = ROOT / rel
    if not p.is_file() or p.suffix.lower() not in (".json", ".py", ".md"):
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    n = len(re.findall(r"[\u4e00-\u9fff]", t))
    if n:
        cjk_new.append({"file": rel, "cjk_chars": n, "kind": p.suffix})
# modified tracked files touched today with CJK
code, mods, _ = sh(["git", "status", "--porcelain"])
modified = [ln[3:].strip().strip('"') for ln in mods.split("\n")
            if ln[:2].strip() in ("M", "A", "R")]
for rel in modified:
    p = ROOT / rel
    if not p.is_file() or p.suffix.lower() not in (".json", ".py"):
        continue
    if datetime.fromtimestamp(p.stat().st_mtime).date() != TODAY:
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    n = len(re.findall(r"[\u4e00-\u9fff]", t))
    if n:
        cjk_modified.append({"file": rel, "cjk_chars": n, "kind": p.suffix})
R["c_language"] = {"untracked_with_cjk": cjk_new[:40], "n_untracked_with_cjk": len(cjk_new),
                   "modified_today_with_cjk": cjk_modified[:40],
                   "n_modified_today_with_cjk": len(cjk_modified),
                   "tracked_json_archives_in_outputs_with_cjk_today": None}

# ---- (d) SCI registry
reg = ROOT / "docs/VENUE_SCI_REGISTRY.md"
if reg.exists():
    t = reg.read_text(encoding="utf-8")
    venues = ["Neurocomputing", "Pattern Analysis and Applications",
              "Pattern Recognition Letters", "IEEE Journal of Oceanic", "SCIE"]
    R["d_sci_registry"] = {
        "path": "docs/VENUE_SCI_REGISTRY.md", "size": reg.stat().st_size,
        "mtime": datetime.fromtimestamp(reg.stat().st_mtime).isoformat(timespec="seconds"),
        "venue_mentions": {v: t.count(v) for v in venues},
        "verification_dates": sorted(set(re.findall(r"2026-\d\d-\d\d", t))),
        "has_doi_or_issn": bool(re.search(r"ISSN|doi", t, re.I)),
    }
else:
    R["d_sci_registry"] = {"exists": False}

# ---- (e) tag / Release freeze
pc = ROOT / "publish_clean"
R["e_tags"] = {
    "live_repo_tags": sh(["git", "tag", "--list"])[1].split("\n"),
    "live_repo_tags_today": [],
    "publish_clean_head": sh(["git", "-C", str(pc), "log", "--oneline", "-1"])[1] if (pc / ".git").exists() else None,
    "publish_clean_tags": sh(["git", "-C", str(pc), "tag", "--list"])[1].split("\n") if (pc / ".git").exists() else [],
    "publish_clean_refs": sh(["git", "-C", str(pc), "show-ref"])[1][:1200] if (pc / ".git").exists() else None,
    "publish_clean_log_top": sh(["git", "-C", str(pc), "log", "--oneline", "-8"])[1].split("\n") if (pc / ".git").exists() else [],
}
# tag reflogs anywhere (a moved tag would leave a reflog under .git/logs/refs/tags)
taglogs = []
for base in (ROOT / ".git", pc / ".git"):
    if not base.exists():
        continue
    for p in base.rglob("*"):
        if "logs" in p.parts and "tags" in str(p):
            taglogs.append(str(p))
R["e_tags"]["tag_reflog_paths"] = taglogs
# local commit dates for the tags that exist
R["e_tags"]["tag_dates"] = {}
for t in [x for x in R["e_tags"]["live_repo_tags"] if x]:
    R["e_tags"]["tag_dates"][t] = sh(["git", "log", "-1", "--format=%cI", t])[1]

# ---- A23 next-revision package contents
pkg = ROOT / "SUBMISSION/A2_JOE_next_revision"
R["a23_next_revision_package"] = {
    "path": "SUBMISSION/A2_JOE_next_revision",
    "exists": pkg.exists(),
    "files": [{"name": p.name, "size": p.stat().st_size,
               "mtime": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")}
              for p in sorted(pkg.iterdir())] if pkg.exists() else [],
    "has_cover_letter": any("cover" in p.name.lower() for p in pkg.iterdir()) if pkg.exists() else None,
}
venue_a23 = ROOT / "SUBMISSION/_venue_builds/A23_JOE_next"
R["a23_next_revision_package"]["venue_build_dir"] = {
    "path": "SUBMISSION/_venue_builds/A23_JOE_next",
    "files": [{"name": p.name, "size": p.stat().st_size,
               "mtime": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")}
              for p in sorted(venue_a23.iterdir())] if venue_a23.exists() else [],
}

# ---- cloud retrieval: zero-byte / truncated files
ret = ROOT / "cloud_retrieved/round2_2026-10-25"
zero = []
if ret.exists():
    for p in ret.rglob("*"):
        if p.is_file() and p.stat().st_size == 0:
            zero.append(str(p.relative_to(ROOT)))
    sizes = [p.stat().st_size for p in ret.rglob("*") if p.is_file()]
R["cloud_retrieval"] = {"dir": "cloud_retrieved/round2_2026-10-25",
                        "n_files": len(sizes), "zero_byte_files": zero,
                        "total_bytes": sum(sizes)}

# ---- Source-script existence for the traced numbers
TR = json.loads((ROOT / "outputs/analysis/audit_traceability.json").read_text(encoding="utf-8"))
missing_scripts = []
for row in TR["checked"]:
    for s in row.get("source_scripts_nearby", []):
        if not (ROOT / s).exists():
            missing_scripts.append({"id": row["id"], "script": s})
R["source_script_existence"] = {"n_missing": len(missing_scripts), "missing": missing_scripts}
# archive meta.script agreement where present
agree, disagree = [], []
for row in TR["checked"]:
    p = ROOT / row["archive"]
    if not p.exists():
        continue
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        continue
    meta = d.get("meta", {}) if isinstance(d, dict) else {}
    mscript = (meta.get("script") or d.get("script") if isinstance(d, dict) else None) or ""
    near = row.get("source_scripts_nearby", [])
    if mscript and near:
        base = os.path.basename(mscript)
        if any(os.path.basename(n) == base for n in near):
            agree.append({"id": row["id"], "script": base})
        else:
            disagree.append({"id": row["id"], "archive_meta_script": mscript,
                             "near_scripts": near})
R["source_script_existence"]["meta_script_agree"] = agree
R["source_script_existence"]["meta_script_disagree"] = disagree

OUT.write_text(json.dumps(R, indent=1, ensure_ascii=False), encoding="utf-8")
print("== upload names ==", R["a_upload_names"]["n_upload_files"], "files,",
      R["a_upload_names"]["n_with_underscore"], "with underscore")
for v in R["a_upload_names"]["violations"]:
    print("   VIOLATION", v)
print("== figures today ==", R["b_figures_today"]["n"], R["b_figures_today"]["verdict"])
print("== language ==", "untracked+new with CJK:", R["c_language"]["n_untracked_with_cjk"],
      "| modified-today with CJK:", R["c_language"]["n_modified_today_with_cjk"])
for x in R["c_language"]["untracked_with_cjk"][:12]:
    print("   ", x)
print("== SCI registry ==", json.dumps(R["d_sci_registry"], ensure_ascii=False)[:400])
print("== tags ==", "live:", R["e_tags"]["live_repo_tags"], "pc_head:", R["e_tags"]["publish_clean_head"])
print("   pc tags:", R["e_tags"]["publish_clean_tags"][:10])
print("== A23 pkg ==", "has_cover:", R["a23_next_revision_package"]["has_cover_letter"],
      "files:", [f["name"] for f in R["a23_next_revision_package"]["files"]])
print("== cloud retrieval ==", json.dumps(R["cloud_retrieval"])[:300])
print("== source scripts ==", R["source_script_existence"]["n_missing"],
      "missing; meta agree:", len(R["source_script_existence"]["meta_script_agree"]),
      "disagree:", len(R["source_script_existence"]["meta_script_disagree"]))
print("wrote", OUT)
