# -*- coding: utf-8 -*-
"""Check execution engine for the paper-audit mode (English-only artifact).

The engine is intentionally boring: every check is a small function that reads
files, compares values, and returns one Finding. No network access is required.
"""
from __future__ import annotations

import json
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .model import Check, Finding, Report, Severity, Status
from .registry import CHECKS, DIMENSIONS, by_id
from . import texutil as tx
from . import mechanical as mech

ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# low-level helpers
# ---------------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_cmd(cmd: list[str], cwd: Path | None = None, timeout: int = 900) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=str(cwd or ROOT), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, "command not found: %s" % cmd[0]
    except subprocess.TimeoutExpired:
        return 124, "timeout after %d s" % timeout


def git(*args: str) -> str:
    rc, out = run_cmd(["git"] + list(args), timeout=60)
    return out.strip() if rc == 0 else ""


def pdfinfo(path: Path) -> dict[str, str]:
    info: dict[str, str] = {}
    if not path.is_file():
        return info
    rc, out = run_cmd(["pdfinfo", str(path)], timeout=60)
    if rc != 0:
        return info
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info[k.strip()] = v.strip()
    return info


def pdftotext(path: Path) -> str:
    if not path.is_file():
        return ""
    rc, out = run_cmd(["pdftotext", "-raw", str(path), "-"], timeout=120)
    return out if rc == 0 else ""


def pdffonts(path: Path) -> str:
    if not path.is_file():
        return ""
    rc, out = run_cmd(["pdffonts", str(path)], timeout=120)
    return out if rc == 0 else ""


def log_stats(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"present": False}
    log = path.read_text(encoding="utf-8", errors="replace")
    return {
        "present": True,
        "errors": len(re.findall(r"(?m)^! ", log)),
        "undef_refs": len(re.findall(r"Reference .*? undefined", log)),
        "undef_cites": len(re.findall(r"Citation .*? undefined", log)),
        "overfull": len(re.findall(r"Overfull \\hbox", log)),
        "underfull": len(re.findall(r"Underfull \\hbox", log)),
        "float_too_large": len(re.findall(r"Float too large", log)),
        "latex_warnings": re.findall(r"(?m)^LaTeX Warning: .*$", log),
        "font_warnings": re.findall(r"(?m)^LaTeX Font Warning: .*$", log),
        "rerun": "Rerun to get" in log,
        "output": re.search(r"Output written on .*?\((\d+) page", log),
        "raw": log,
    }


def parse_pages(info: dict[str, str]) -> int:
    try:
        return int(info.get("Pages", "0"))
    except ValueError:
        return 0


def fmt(value) -> str:
    return json.dumps(value, ensure_ascii=False)


# ---------------------------------------------------------------------------
# context
# ---------------------------------------------------------------------------
def build_context(profile: dict, opts) -> dict:
    msdir = ROOT / profile["manuscript"]
    tex_files = []
    for name in profile["tex"]:
        p = msdir / name
        if p.is_file():
            tex_files.append(p)
    primary = profile["tex"][0] if profile.get("tex") else None
    merged, included = tx.expand_sources(msdir, [primary] if primary else profile["tex"])
    abstract = tx.find_abstract(merged, profile.get("abstract_style", "env"))
    keywords = tx.keyword_items(tx.find_keywords(merged)) or tx.keywords_line(merged)
    title = tx.find_title(merged)

    pdfs = [msdir / p for p in profile["pdfs"]]
    primary_pdf = pdfs[0] if pdfs else None
    pdf_text = pdftotext(primary_pdf) if primary_pdf else ""

    logs = [msdir / p for p in profile["logs"]]
    primary_log = logs[0] if logs else None

    cover_path = msdir / profile["cover_letter"] if profile.get("cover_letter") else None
    cover_tex = tx.read_text(cover_path) if cover_path and cover_path.is_file() else ""
    cover_pdf = cover_path.with_suffix(".pdf") if cover_path else None

    hl_path = msdir / profile["highlights"] if profile.get("highlights") else None
    hl_text = tx.read_text(hl_path) if hl_path and hl_path.is_file() else ""

    package_dir = None
    if profile.get("package"):
        cand = ROOT / profile["package"]
        package_dir = cand if cand.exists() else (msdir / profile["package"])

    source_paths: list[Path] = list(tex_files)
    for name in included:
        p = Path(name)
        if p not in source_paths:
            source_paths.append(p)
    if cover_path and cover_path.is_file():
        source_paths.append(cover_path)
    if hl_path and hl_path.is_file():
        source_paths.append(hl_path)
    for extra in (msdir / "references.bib",):
        if extra.is_file():
            source_paths.append(extra)

    source_parts = []
    for p in source_paths:
        if not p.is_file():
            continue
        raw = tx.read_text(p)
        source_parts.append(tx.strip_comments(raw) if p.suffix.lower() == ".tex" else raw)
    source_text = "\n".join(source_parts)

    build_inputs = list(tex_files) + [Path(n) for n in included] + list(sorted(msdir.glob("*.bib")))

    bib_files = sorted(msdir.glob("*.bib"))
    cite = tx.cite_keys(merged)
    labels = tx.label_keys(merged)
    refs = tx.ref_keys(merged)
    inline_bib = tx.bibitem_keys(merged)
    if bib_files:
        bib_keys = []
        for bf in bib_files:
            bib_keys.extend(tx.bib_file_keys(bf))
    else:
        bib_keys = inline_bib

    env_info = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "pdflatex": (run_cmd(["pdflatex", "--version"], timeout=30)[1].splitlines() or [""])[0],
        "pdfinfo": (run_cmd(["pdfinfo", "-v"], timeout=30)[1].splitlines() or [""])[0],
        "git_commit": git("rev-parse", "HEAD")[:12],
        "git_branch": git("branch", "--show-current"),
    }

    return {
        "profile": profile,
        "root": ROOT,
        "msdir": msdir,
        "tex_files": tex_files,
        "merged": merged,
        "included": included,
        "abstract": abstract,
        "abstract_words": tx.count_words(abstract),
        "keywords": keywords,
        "title": title,
        "pdfs": pdfs,
        "pdf": primary_pdf,
        "pdf_text": pdf_text,
        "logs": logs,
        "log": primary_log,
        "log_stats": log_stats(primary_log) if primary_log else {"present": False},
        "cover_path": cover_path,
        "cover_tex": cover_tex,
        "cover_pdf": cover_pdf,
        "hl_path": hl_path,
        "hl_text": hl_text,
        "package_dir": package_dir,
        "source_paths": source_paths,
        "source_text": source_text,
        "build_inputs": build_inputs,
        "bib_files": bib_files,
        "bib_keys": bib_keys,
        "inline_bib": inline_bib,
        "cite_keys": cite,
        "labels": labels,
        "refs": refs,
        "env": env_info,
        "opts": opts,
        "git_status": git("-c", "core.quotepath=false", "status", "--porcelain"),
    }


# ---------------------------------------------------------------------------
# finding helpers
# ---------------------------------------------------------------------------
def _finding(chk: Check, status: Status, message: str, evidence: str = "",
             remediation: str = "") -> Finding:
    return Finding(check_id=chk.id, dimension=chk.dimension, severity=chk.severity,
                   title=chk.title, status=status, message=message,
                   evidence=evidence, remediation=remediation)


def ok(chk, message="", evidence=""):
    return _finding(chk, Status.PASS, message, evidence)


def fail(chk, message, evidence="", remediation=""):
    return _finding(chk, Status.FAIL, message, evidence, remediation)


def warn(chk, message, evidence="", remediation=""):
    return _finding(chk, Status.WARN, message, evidence, remediation)


def skip(chk, message):
    return _finding(chk, Status.SKIP, message)


def manual(chk, message):
    return _finding(chk, Status.MANUAL, message)


# ---------------------------------------------------------------------------
# handlers: A reproducibility
# ---------------------------------------------------------------------------
def check_A01(ctx, chk):
    if not ctx["tex_files"]:
        return skip(chk, "no LaTeX sources configured")
    msdir = ctx["msdir"].relative_to(ROOT).as_posix()
    lines = [l for l in ctx["git_status"].splitlines() if l[3:].startswith(msdir)]
    if lines:
        return fail(chk, "uncommitted changes under %s" % msdir, "\n".join(lines[:20]),
                    "commit or stash the changes before releasing the manuscript")
    return ok(chk, "working tree clean for %s" % msdir)


def check_A02(ctx, chk):
    e = ctx["env"]
    return ok(chk, "commit %s on %s" % (e["git_commit"], e["git_branch"] or "detached"))


def check_A03(ctx, chk):
    build = ctx["profile"].get("build_command")
    if build:
        return ok(chk, "build command: %s" % " ".join(build))
    if ctx["profile"].get("package") or ctx["pdf"] and ctx["pdf"].is_file():
        return warn(chk, "no explicit build_command in the profile",
                    "document the command in the profile or README")
    return skip(chk, "no build information available")


def check_A04(ctx, chk):
    if not ctx["pdf"] or not ctx["pdf"].is_file() or not ctx["tex_files"]:
        return skip(chk, "pdf or sources missing")
    pdf_m = ctx["pdf"].stat().st_mtime
    src_m = max((p.stat().st_mtime for p in ctx["build_inputs"] if p.is_file()), default=0)
    if pdf_m + 1 < src_m:
        return fail(chk, "PDF is older than its sources",
                    "pdf %s < source %s" % (datetime.fromtimestamp(pdf_m),
                                            datetime.fromtimestamp(src_m)),
                    "rebuild the manuscript")
    return ok(chk, "PDF is up to date")


def check_A05(ctx, chk):
    if not ctx["pdf"] or not ctx["log"]:
        return skip(chk, "pdf or log missing")
    if not ctx["pdf"].is_file() or not ctx["log"].is_file():
        return skip(chk, "pdf or log missing")
    delta = abs(ctx["pdf"].stat().st_mtime - ctx["log"].stat().st_mtime)
    if delta > 120:
        return warn(chk, "log and pdf differ by %.0f s" % delta,
                    "the log may belong to another build")
    return ok(chk, "log and pdf produced together")


def check_A06(ctx, chk):
    return ok(chk, "; ".join("%s=%s" % (k, v) for k, v in ctx["env"].items()))


def check_A07(ctx, chk):
    return manual(chk, "confirm the build command writes only generated artefacts")


def check_A08(ctx, chk):
    if not ctx["tex_files"]:
        return skip(chk, "no sources configured")
    msdir = ctx["msdir"].relative_to(ROOT).as_posix()
    untracked = [l for l in ctx["git_status"].splitlines()
                 if l.startswith("??") and l[3:].startswith(msdir)]
    build_ext = (".aux", ".log", ".out", ".bbl", ".blg", ".fls", ".fdb_latexmk",
                 ".synctex.gz", ".toc", ".lof", ".lot")
    interesting = [l for l in untracked if not l[3:].lower().endswith(build_ext)]
    if interesting:
        return warn(chk, "untracked files under %s" % msdir, "\n".join(interesting[:20]))
    return ok(chk, "no untracked non-build artefacts")


# ---------------------------------------------------------------------------
# handlers: B build
# ---------------------------------------------------------------------------
def check_B01(ctx, chk):
    st = ctx["log_stats"]
    if not st.get("present"):
        return skip(chk, "no build log")
    if st["errors"]:
        return fail(chk, "%d LaTeX errors" % st["errors"], "see %s" % ctx["log"])
    return ok(chk, "no LaTeX errors")


def check_B02(ctx, chk):
    st = ctx["log_stats"]
    if not st.get("present"):
        return skip(chk, "no build log")
    if st["undef_refs"]:
        return fail(chk, "%d undefined references" % st["undef_refs"], "see %s" % ctx["log"],
                    "fix or remove the references")
    return ok(chk, "no undefined references")


def check_B03(ctx, chk):
    st = ctx["log_stats"]
    if not st.get("present"):
        return skip(chk, "no build log")
    if st["undef_cites"]:
        return fail(chk, "%d undefined citations" % st["undef_cites"], "see %s" % ctx["log"],
                    "add the missing bibliography entries")
    return ok(chk, "no undefined citations")


def check_B04(ctx, chk):
    st = ctx["log_stats"]
    if not st.get("present"):
        return skip(chk, "no build log")
    if st["overfull"]:
        return fail(chk, "%d overfull hbox" % st["overfull"], "see %s" % ctx["log"],
                    "reflow the offending paragraph or shorten the token")
    return ok(chk, "no overfull hboxes")


def check_B05(ctx, chk):
    st = ctx["log_stats"]
    if not st.get("present"):
        return skip(chk, "no build log")
    if st["float_too_large"]:
        return fail(chk, "%d floats too large" % st["float_too_large"], "see %s" % ctx["log"])
    return ok(chk, "no oversized floats")


def check_B06(ctx, chk):
    st = ctx["log_stats"]
    if not st.get("present"):
        return skip(chk, "no build log")
    warns = [w for w in st["latex_warnings"] if "float specifier changed" not in w]
    if warns:
        return warn(chk, "%d LaTeX warnings" % len(warns), "\n".join(warns[:15]))
    return ok(chk, "no LaTeX warnings")


def check_B07(ctx, chk):
    st = ctx["log_stats"]
    if not st.get("present"):
        return skip(chk, "no build log")
    if st["rerun"]:
        return fail(chk, "the last build asked for another pass")
    return ok(chk, "build converged")


def check_B08(ctx, chk):
    st = ctx["log_stats"]
    if not st.get("present") or not ctx["pdf"] or not ctx["pdf"].is_file():
        return skip(chk, "log or pdf missing")
    m = st.get("output")
    pages = parse_pages(pdfinfo(ctx["pdf"]))
    if not m:
        return warn(chk, "log has no 'Output written' line; page count not compared",
                    str(ctx["log"]))
    if int(m.group(1)) != pages:
        return fail(chk, "log says %s pages, pdf has %d" % (m.group(1), pages))
    return ok(chk, "log and pdf agree on %d pages" % pages)


def check_B09(ctx, chk):
    st = ctx["log_stats"]
    if not st.get("present"):
        return skip(chk, "no build log")
    warns = st["font_warnings"]
    if warns:
        return warn(chk, "%d font warnings" % len(warns), "\n".join(warns[:10]))
    return ok(chk, "no font warnings")


def check_B10(ctx, chk):
    staged = ctx["opts"].get("staged_result")
    if not staged:
        return skip(chk, "clean-room rebuild not requested (use --staged)")
    # Keep the finding schema stable: message/evidence must be strings.
    if isinstance(staged, dict):
        detail = staged.get("message", "")
    else:
        detail = str(staged)
    return manual(chk, detail)


# ---------------------------------------------------------------------------
# handlers: C structure
# ---------------------------------------------------------------------------
def check_C01(ctx, chk):
    required = ctx["profile"].get("required_sections") or []
    if not required:
        return skip(chk, "no required sections configured")
    titles = " || ".join(tx.section_titles(ctx["merged"]))
    missing = [r for r in required if r.lower() not in titles.lower() and r.lower() not in ctx["merged"].lower()]
    if missing:
        return fail(chk, "missing sections: %s" % ", ".join(missing),
                    "found: %s" % titles[:500], "add the missing sections or update the profile")
    return ok(chk, "%d required sections found" % len(required))


def check_C02(ctx, chk):
    n = len(tx.ABSTRACT_ENV_RE.findall(ctx["merged"]))
    if not ctx["abstract"]:
        return fail(chk, "no abstract found", "expected exactly one abstract")
    if n > 1:
        return fail(chk, "%d abstract environments" % n)
    return ok(chk, "abstract present (%d words)" % ctx["abstract_words"])


def check_C03(ctx, chk):
    if not ctx["keywords"]:
        return fail(chk, "no keyword block found")
    return ok(chk, "%d keywords" % len(ctx["keywords"]))


def check_C04(ctx, chk):
    if ctx["bib_files"] or ctx["inline_bib"] or "\\bibliography{" in ctx["merged"]:
        return ok(chk, "bibliography present")
    return fail(chk, "no bibliography found")


def check_C05(ctx, chk):
    labels = [l for l in ctx["labels"] if l.lower().startswith(("fig:", "tab:"))]
    unused = [l for l in labels if l not in ctx["refs"]]
    if unused:
        return warn(chk, "%d figure/table labels never referenced" % len(unused),
                    ", ".join(sorted(unused)))
    return ok(chk, "%d figure/table labels all referenced" % len(labels))


def check_C06(ctx, chk):
    if not ctx["pdf_text"]:
        return skip(chk, "no pdf text")
    if "??" in ctx["pdf_text"]:
        return fail(chk, "'??' present in the PDF text")
    return ok(chk, "no unresolved reference marker in the PDF")


def check_C07(ctx, chk):
    dead = [l for l in ctx["labels"] if l not in ctx["refs"] and not l.lower().startswith("sec:")]
    if dead:
        return warn(chk, "%d labels never referenced" % len(dead), ", ".join(sorted(dead)[:30]))
    return ok(chk, "no dead labels")


def check_C08(ctx, chk):
    pos = tx.declaration_positions(ctx["merged"], ctx["profile"].get("required_declarations") or [])
    bib = tx.bibliography_position(ctx["merged"])
    found = {k: v for k, v in pos.items() if v >= 0}
    if bib < 0:
        return skip(chk, "no bibliography position found")
    if not found:
        return skip(chk, "no required declaration found")
    bad = {k: v for k, v in found.items() if v > bib}
    if bad:
        return fail(chk, "declarations after the bibliography", fmt(bad),
                    "move the declarations before the bibliography")
    return ok(chk, "all declarations precede the bibliography (bib at %d)" % bib)


def check_C09(ctx, chk):
    required = ctx["profile"].get("required_declarations") or []
    if not required:
        return skip(chk, "no declarations required by this profile")
    low = ctx["merged"].lower()
    missing = [d for d in required if d.lower() not in low]
    if missing:
        return fail(chk, "missing declarations: %s" % ", ".join(missing))
    return ok(chk, "%d declarations present" % len(required))


def check_C10(ctx, chk):
    if not ctx["title"]:
        return fail(chk, "no title found")
    authors = re.search(r"\\author", ctx["merged"]) is not None or "author" in ctx["merged"].lower()
    if not authors:
        return warn(chk, "no author block found")
    return ok(chk, "title present: %s" % ctx["title"][:90])


# ---------------------------------------------------------------------------
# handlers: D compliance
# ---------------------------------------------------------------------------
def check_D01(ctx, chk):
    if not ctx["pdf"] or not ctx["pdf"].is_file():
        return fail(chk, "no PDF to measure", str(ctx["pdf"] or "pdf not configured"))
    pages = parse_pages(pdfinfo(ctx["pdf"]))
    limit = ctx["profile"]["limits"].get("pages_max")
    if limit is None:
        return ok(chk, "%d pages (no hard limit configured)" % pages)
    if pages > int(limit):
        return fail(chk, "%d pages > limit %d" % (pages, int(limit)))
    return ok(chk, "%d pages <= %d" % (pages, int(limit)))


def check_D02(ctx, chk):
    words = ctx["abstract_words"]
    lim = ctx["profile"]["limits"]
    mx = lim.get("abstract_words_max")
    mn = lim.get("abstract_words_min")
    if not ctx["abstract"]:
        return fail(chk, "no abstract to count")
    if mx is not None and words > int(mx):
        return fail(chk, "abstract %d words > %d" % (words, int(mx)))
    if mn is not None and words < int(mn):
        return fail(chk, "abstract %d words < %d" % (words, int(mn)))
    return ok(chk, "abstract %d words" % words)


def check_D03(ctx, chk):
    n = len(ctx["keywords"])
    lim = ctx["profile"]["limits"]
    mn = int(lim.get("keywords_min") or 0)
    mx = int(lim.get("keywords_max") or 99)
    if not n:
        return skip(chk, "no keywords found")
    if n < mn or n > mx:
        return fail(chk, "%d keywords outside [%d, %d]" % (n, mn, mx))
    return ok(chk, "%d keywords within [%d, %d]" % (n, mn, mx))


def check_D04(ctx, chk):
    lim = ctx["profile"]["limits"]
    hmin = lim.get("highlights_min")
    hmax = lim.get("highlights_max")
    cmax = int(lim.get("highlight_chars_max") or 85)
    if hmin is None and hmax is None:
        return skip(chk, "highlights not required by this profile")
    text = ctx["hl_text"]
    if not text:
        return skip(chk, "no highlights file configured or found")
    if ctx["hl_path"] and ctx["hl_path"].suffix.lower() == ".tex":
        items = [m.group(1).strip() for m in re.finditer(r"\\item\s+(.+)", text)]
    else:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        items = [re.sub(r"^[-*]\s*", "", l) for l in lines if l.lower() not in ("highlights",)]
    if not items:
        return fail(chk, "highlights file has no items")
    too_long = [i for i in items if len(i) > cmax]
    n = len(items)
    if hmin is not None and n < int(hmin):
        return fail(chk, "%d highlights < %d" % (n, int(hmin)))
    if hmax is not None and n > int(hmax):
        return fail(chk, "%d highlights > %d" % (n, int(hmax)))
    if too_long:
        return fail(chk, "%d highlights exceed %d characters" % (len(too_long), cmax),
                    "longest=%d" % max(len(i) for i in items))
    return ok(chk, "%d highlights, longest %d chars" % (n, max(len(i) for i in items)))


def check_D05(ctx, chk):
    if not ctx["profile"]["limits"].get("blinded"):
        return skip(chk, "this profile is not blinded")
    name_hits = [k for k in ("Acknowledg", "author") if k.lower() in ctx["merged"].lower()]
    return manual(chk, "confirm author names/affiliations are absent for blinding")


def check_D06(ctx, chk):
    mx = ctx["profile"]["limits"].get("title_chars_max")
    if mx is None:
        return skip(chk, "no title-length limit configured")
    n = len(re.sub(r"\\[a-zA-Z]+|[{}$]", "", ctx["title"]))
    if n > int(mx):
        return fail(chk, "title %d chars > %d" % (n, int(mx)))
    return ok(chk, "title %d chars <= %d" % (n, int(mx)))


def check_D07(ctx, chk):
    sup = ctx["profile"].get("supplementary")
    if not sup:
        return skip(chk, "no supplementary material configured")
    p = ctx["msdir"] / sup
    if not p.is_file():
        p = ROOT / sup
    if not p.is_file():
        return warn(chk, "supplementary file not found: %s" % sup)
    pages = parse_pages(pdfinfo(p))
    return ok(chk, "supplementary has %d pages" % pages)


def check_D08(ctx, chk):
    pkg = ctx["package_dir"]
    expected = ctx["profile"].get("package_expected") or []
    if not pkg or not expected:
        return skip(chk, "no submission package configured")
    if not pkg.is_dir():
        return fail(chk, "package directory missing: %s" % pkg)
    missing = [n for n in expected if not (pkg / n).is_file()]
    if missing:
        return fail(chk, "missing package files: %s" % ", ".join(missing))
    return ok(chk, "%d expected package files present" % len(expected))


def check_D09(ctx, chk):
    if not ctx["cover_tex"]:
        return skip(chk, "no cover letter configured")
    m = re.search(r"abstract of (\d+) words", ctx["cover_tex"], re.I)
    if not m:
        return skip(chk, "no abstract word claim found in the cover letter")
    claimed = int(m.group(1))
    if claimed != ctx["abstract_words"]:
        return fail(chk, "cover letter claims %d abstract words, measured %d"
                    % (claimed, ctx["abstract_words"]))
    return ok(chk, "cover letter abstract claim matches (%d words)" % claimed)


def check_D10(ctx, chk):
    return manual(chk, "review the declaration wording against the venue guide")


# ---------------------------------------------------------------------------
# handlers: E references
# ---------------------------------------------------------------------------
def check_E01(ctx, chk):
    cites = {k for k in ctx["cite_keys"] if not k.startswith("#")}
    missing = sorted(k for k in cites if k not in set(ctx["bib_keys"]))
    if missing:
        return fail(chk, "%d cited keys missing from the bibliography" % len(missing),
                    ", ".join(missing[:20]), "add the missing references")
    return ok(chk, "%d cited keys all resolved" % len(ctx["cite_keys"]))


def check_E02(ctx, chk):
    cited = set(ctx["cite_keys"])
    unused = sorted(k for k in set(ctx["bib_keys"]) if k not in cited)
    if unused:
        return warn(chk, "%d unused bibliography entries" % len(unused),
                    ", ".join(unused[:20]))
    return ok(chk, "no unused bibliography entries")


def check_E03(ctx, chk):
    if not ctx["inline_bib"]:
        return skip(chk, "external bibliography (or no inline bibitems)")
    n_refs = len(ctx["inline_bib"])
    n_cites = len({k for k in ctx["cite_keys"] if not k.startswith("#")})
    if n_refs != n_cites:
        return fail(chk, "%d bibitems but %d distinct cited keys" % (n_refs, n_cites))
    return ok(chk, "%d bibitems match %d cited keys" % (n_refs, n_cites))


def check_E04(ctx, chk):
    return manual(chk, "numeric citation contiguity requires the typeset reference list (heuristic disabled)")


def check_E05(ctx, chk):
    dois = set(tx.doi_strings(ctx["pdf_text"]))
    if not dois:
        return skip(chk, "no DOI strings in the PDF")
    bad = [d for d in dois if not re.match(r"^10\.\d{4,9}/[A-Za-z0-9._;()/:-]+$", d)]
    if bad:
        return fail(chk, "%d malformed DOI strings" % len(bad), ", ".join(sorted(bad)[:10]))
    return ok(chk, "%d DOIs syntactically valid" % len(dois))


def check_E06(ctx, chk):
    return manual(chk, "confirm dataset / software citations carry a URL or DOI")


def check_E07(ctx, chk):
    keys = ctx["inline_bib"] if ctx["inline_bib"] else ctx["bib_keys"]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    if dup:
        return fail(chk, "duplicate bibliography keys: %s" % ", ".join(dup))
    if ctx["bib_files"]:
        blocks = []
        for bf in ctx["bib_files"]:
            blocks.extend(re.split(r"(?m)^@", tx.read_text(bf))[1:])
        seen = {}
        for b in blocks:
            for d in tx.doi_strings(b):
                seen.setdefault(d, []).append(b[:60])
        dup_dois = sorted(d for d, v in seen.items() if len(v) > 1)
        if dup_dois:
            return warn(chk, "DOIs appearing in more than one bibliography entry",
                        ", ".join(dup_dois[:10]))
    return ok(chk, "no duplicate entries detected")


def check_E08(ctx, chk):
    self_keys = ctx["profile"].get("self_keys") or []
    if not self_keys:
        return skip(chk, "no self-citation key list configured")
    cited = sorted(set(self_keys) & ctx["cite_keys"])
    if cited:
        return warn(chk, "self-citations present: %s" % ", ".join(cited))
    return ok(chk, "no self-citations from the configured list")


def check_E09(ctx, chk):
    return manual(chk, "confirm reference ordering matches the venue style")


def check_E10(ctx, chk):
    return manual(chk, "spot-check that every reference item has authors, title, venue and year")


# ---------------------------------------------------------------------------
# handlers: F consistency
# ---------------------------------------------------------------------------
def check_F01(ctx, chk):
    hits = tx.placeholders(ctx["source_text"]) + tx.placeholders(ctx["pdf_text"])
    if hits:
        return fail(chk, "%d placeholder markers" % len(hits), ", ".join(sorted(set(hits))[:20]),
                    "resolve every placeholder before submission")
    return ok(chk, "no placeholders found")


def check_F02(ctx, chk):
    visible = tx.cjk_hits(ctx["merged"])
    if visible:
        return fail(chk, "%d CJK characters in visible manuscript text" % len(visible),
                    "".join(visible[:20]))
    raw_hits = 0
    for p in ctx["tex_files"]:
        raw_hits += len(tx.cjk_hits(tx.read_text(p)))
    if raw_hits:
        return warn(chk, "%d CJK character(s) in source comments (not rendered)" % raw_hits)
    return ok(chk, "no CJK characters in the sources")


def check_F03(ctx, chk):
    tokens = ctx["profile"].get("broken_tokens") or ["⟨abla", "ablaM"]
    text = ctx["pdf_text"]
    hits = [t for t in tokens if t in text]
    if hits:
        return fail(chk, "corrupted token(s) in the PDF: %s" % ", ".join(hits))
    return ok(chk, "no configured corrupted tokens in the PDF")


def _run_profile_commands(ctx):
    """Run profile.commands once and cache the results."""
    if "command_results" in ctx:
        return ctx["command_results"]
    results = []
    for spec in ctx["profile"].get("commands") or []:
        cmd = spec.get("cmd") or []
        if not cmd:
            continue
        rc, out = run_cmd(cmd, timeout=int(ctx["opts"].get("command_timeout", 900)))
        results.append({"name": spec.get("name", " ".join(cmd)), "cmd": " ".join(cmd),
                        "kind": spec.get("kind", "gate"), "expect": spec.get("expect", ""),
                        "rc": rc, "output": out[-4000:]})
    ctx["command_results"] = results
    return results


def check_F04(ctx, chk):
    results = [r for r in _run_profile_commands(ctx) if r["kind"] == "ledger"]
    if not results:
        return skip(chk, "no claim-ledger command configured")
    bad = [r for r in results if r["rc"] != 0 or (r["expect"] and r["expect"] not in r["output"])]
    if bad:
        return fail(chk, "%d claim-ledger command(s) failed" % len(bad),
                    "\n".join("%s: rc=%d" % (r["name"], r["rc"]) for r in bad))
    return ok(chk, "; ".join("%s: %s" % (r["name"], r["expect"]) for r in results))


def check_F05(ctx, chk):
    results = [r for r in _run_profile_commands(ctx) if r["kind"] == "gate"]
    if not results:
        return skip(chk, "no consistency-gate command configured")
    bad = [r for r in results if r["rc"] != 0 or (r["expect"] and r["expect"] not in r["output"])]
    if bad:
        return fail(chk, "%d consistency gate(s) failed" % len(bad),
                    "\n".join("%s: rc=%d %s" % (r["name"], r["rc"], r["output"][-300:]) for r in bad))
    return ok(chk, "; ".join(r["name"] for r in results))


def check_F06(ctx, chk):
    spec = ctx["profile"].get("key_numbers") or {}
    if not spec:
        return skip(chk, "no key-number specification configured")
    missing = []
    for value, paths in spec.items():
        found = False
        for rel in paths:
            p = ROOT / rel
            files = [p] if p.is_file() else ([q for q in p.rglob("*") if q.is_file()]
                                             if p.is_dir() else [])
            for f in files:
                if f.suffix.lower() in (".tex", ".bib", ".md", ".txt", ".json"):
                    if str(value) in tx.read_text(f):
                        found = True
                        break
            if found:
                break
        if not found:
            missing.append(str(value))
    if missing:
        return fail(chk, "key numbers absent from the expected contexts: %s" % ", ".join(missing))
    return ok(chk, "key numbers present: %s" % ", ".join(spec.keys()))


def check_F07(ctx, chk):
    forbid = ctx["profile"].get("forbidden_strings") or []
    if not forbid:
        return skip(chk, "no forbidden strings configured")
    haystacks = {"sources": ctx["source_text"], "pdf": ctx["pdf_text"]}
    hits = []
    for label, text in haystacks.items():
        for s in forbid:
            if s.lower() in text.lower():
                hits.append("%s: %s" % (label, s))
    if hits:
        return fail(chk, "%d stale/forbidden strings" % len(hits), "; ".join(hits[:15]))
    return ok(chk, "no forbidden strings found")


def check_F08(ctx, chk):
    dupes = tx.duplicate_sentences(ctx["merged"])
    if dupes:
        return warn(chk, "%d duplicated sentence(s)" % len(dupes), "\n".join(dupes[:5]))
    return ok(chk, "no duplicated long sentences")


def check_F09(ctx, chk):
    if not ctx["cover_tex"]:
        return skip(chk, "no cover letter configured")
    m = re.search(r"manuscript is (\d+) pages", ctx["cover_tex"], re.I)
    if not m:
        return skip(chk, "no page-count claim found in the cover letter")
    claimed = int(m.group(1))
    pages = parse_pages(pdfinfo(ctx["pdf"])) if ctx["pdf"] else 0
    if claimed != pages:
        return fail(chk, "cover letter claims %d pages, PDF has %d" % (claimed, pages))
    return ok(chk, "cover letter page claim matches (%d)" % claimed)


def check_F10(ctx, chk):
    text = ctx["pdf_text"]
    if not text:
        return skip(chk, "no pdf text")
    bad = len(re.findall(r"\[\?\]|\(\?\)|\?\?", text))
    if bad:
        return fail(chk, "%d question-mark artefacts" % bad)
    n = text.count("?")
    return ok(chk, "no reference artefacts (%d sentence-level question marks)" % n)


# ---------------------------------------------------------------------------
# handlers: G rendering
# ---------------------------------------------------------------------------
def check_G01(ctx, chk):
    hits = re.findall(r"(?m)^\s*\d+(?:\.\d+)*\.\s+\d+(?:\.\d+)*\.\s",
                      ctx["pdf_text"])
    if hits:
        return fail(chk, "%d double-numbered heading(s)" % len(hits), fmt(hits[:5]))
    return ok(chk, "no double-numbered headings")


def check_G02(ctx, chk):
    tokens = ["<scp>", "</scp>", "<i>", "</i>", "<b>", "</b>", "&amp;", "&lt;", "&gt;"]
    hits = [t for t in tokens if t in ctx["pdf_text"]]
    if hits:
        return fail(chk, "HTML/XML artefacts in the PDF: %s" % ", ".join(hits))
    return ok(chk, "no HTML/XML artefacts")


def check_G03(ctx, chk):
    hits = re.findall(r"\\[a-zA-Z]{2,}", ctx["pdf_text"])
    if hits:
        return fail(chk, "%d literal LaTeX command(s) in the PDF" % len(hits),
                    ", ".join(sorted(set(hits))[:10]))
    return ok(chk, "no literal LaTeX commands in the PDF")


def check_G04(ctx, chk):
    out = pdffonts(ctx["pdf"]) if ctx["pdf"] else ""
    if not out:
        return skip(chk, "pdffonts unavailable or no pdf")
    lines = [l for l in out.splitlines() if l.strip()]
    bad = []
    for line in lines[2:]:
        cols = line.split()
        if len(cols) >= 5 and cols[3].lower() == "no":
            bad.append(line.strip())
    if bad:
        return fail(chk, "%d font(s) not embedded" % len(bad), "\n".join(bad[:5]))
    return ok(chk, "all fonts embedded")


def check_G05(ctx, chk):
    info = pdfinfo(ctx["pdf"]) if ctx["pdf"] else {}
    title = info.get("Title", "")
    if not title:
        return warn(chk, "PDF metadata has no title")
    src = re.sub(r"\\[a-zA-Z]+|[{}$]", "", ctx["title"])
    src_n = re.sub(r"\s+", " ", src).strip().lower()
    pdf_n = re.sub(r"\s+", " ", title).strip().lower()
    if src_n and pdf_n[:30] not in src_n and src_n[:30] not in pdf_n:
        return warn(chk, "PDF title differs from the source title",
                    "pdf=%r source=%r" % (title[:60], ctx["title"][:60]))
    return ok(chk, "PDF metadata title matches the source")


def check_G06(ctx, chk):
    if not ctx["pdf"] or not ctx["pdf"].is_file():
        return skip(chk, "no pdf")
    pages = parse_pages(pdfinfo(ctx["pdf"]))
    exceptions = set(ctx["profile"].get("blank_page_exceptions") or [])
    blank = []
    for n in range(1, pages + 1):
        rc, out = run_cmd(["pdftotext", "-f", str(n), "-l", str(n), str(ctx["pdf"]), "-"], timeout=60)
        if rc == 0 and len(out.strip()) < 20 and n not in exceptions:
            blank.append(n)
    if blank:
        return warn(chk, "%d near-empty page(s)" % len(blank), "pages %s" % blank)
    return ok(chk, "no unexpected blank pages")


def check_G07(ctx, chk):
    return manual(chk, "review list / contribution numbering in the PDF")


def check_G08(ctx, chk):
    return manual(chk, "confirm page numbers (and line numbers if required) are present")


# ---------------------------------------------------------------------------
# handlers: H data and ethics
# ---------------------------------------------------------------------------
def _has(ctx, needle):
    return needle.lower() in ctx["merged"].lower()


def check_H01(ctx, chk):
    required = ctx["profile"].get("required_declarations") or []
    required_data = any("data availability" in d.lower() for d in required)
    if not required_data:
        return skip(chk, "data availability not required by this profile")
    if not _has(ctx, "Data availability"):
        return fail(chk, "no Data availability statement", "",
                    "add a statement naming the repository / DOI or the access conditions")
    return ok(chk, "Data availability statement present")


def check_H02(ctx, chk):
    m = re.search(r"Data availability", ctx["merged"], re.I)
    if not m:
        return skip(chk, "no data availability statement")
    tail = ctx["merged"][m.end():m.end() + 4000]
    urls = re.findall(r"https?://[^\s}\)]+", tail)
    dois = tx.doi_strings(tail)
    bad = [u for u in urls if not re.match(r"^https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+$", u)]
    if bad:
        return fail(chk, "malformed URL(s) in the data statement", ", ".join(bad[:5]))
    if not urls and not dois:
        # An explicit no-new-data declaration is a substantive data statement:
        # the values are then quoted from the cited literature, so a repository
        # URL or DOI would be a false pointer (rationale recorded in registry.py).
        if re.search(r"no new (?:data|datasets?|experimental data)", tail, re.I):
            return ok(chk, "explicit no-new-data declaration; values quoted from the cited sources")
        return warn(chk, "data statement contains no URL or DOI")
    return ok(chk, "data statement links: %d URL(s), %d DOI(s)" % (len(urls), len(dois)))


def check_H03(ctx, chk):
    required = ctx["profile"].get("required_declarations") or []
    if not any("generative" in d.lower() or "ai" == d.lower() for d in required):
        return skip(chk, "AI disclosure not required by this profile")
    if not (_has(ctx, "generative") or _has(ctx, "AI-assisted") or _has(ctx, "large language model")):
        return fail(chk, "no generative-AI disclosure")
    return ok(chk, "generative-AI disclosure present")


def check_H04(ctx, chk):
    required = ctx["profile"].get("required_declarations") or []
    if not any("competing" in d.lower() for d in required):
        return skip(chk, "competing-interest declaration not required by this profile")
    if not (_has(ctx, "competing") or _has(ctx, "conflict of interest")):
        return fail(chk, "no competing-interest declaration")
    return ok(chk, "competing-interest declaration present")


def check_H05(ctx, chk):
    required = ctx["profile"].get("required_declarations") or []
    if not any("funding" in d.lower() for d in required):
        return skip(chk, "funding declaration not required by this profile")
    if not _has(ctx, "funding"):
        return fail(chk, "no funding declaration")
    return ok(chk, "funding declaration present")


def check_H06(ctx, chk):
    required = ctx["profile"].get("required_declarations") or []
    if not any("credit" in d.lower() for d in required):
        return skip(chk, "CRediT statement not required by this profile")
    if not (_has(ctx, "CRediT") or _has(ctx, "author contribution")):
        return fail(chk, "no CRediT / author-contribution statement")
    return ok(chk, "CRediT statement present")


def check_H07(ctx, chk):
    return skip(chk, "no human-subject or animal data in this project (N/A)")


# ---------------------------------------------------------------------------
# freeze helpers and I handlers
# ---------------------------------------------------------------------------
def tree_hashes(paths: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in paths:
        p = ROOT / rel
        if not p.exists():
            out[rel + "::MISSING"] = ""
            continue
        if p.is_file():
            out[rel] = sha256_file(p)
        elif p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file():
                    out[f.relative_to(ROOT).as_posix()] = sha256_file(f)
    return out


def freeze_profile(profile: dict) -> Path:
    manifest = ROOT / profile["freeze_manifest"]
    manifest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "profile": profile["id"],
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "paths": profile.get("freeze_paths") or [],
        "entries": tree_hashes(profile.get("freeze_paths") or []),
    }
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def compare_freeze(profile: dict) -> dict:
    manifest = ROOT / profile["freeze_manifest"]
    if not profile.get("freeze_paths"):
        return {"status": "skip", "reason": "no frozen artefacts configured"}
    if not manifest.is_file():
        return {"status": "skip", "reason": "no freeze manifest; run: python -m tools.paper_audit freeze --profile %s --write" % profile["id"]}
    baseline = json.loads(manifest.read_text(encoding="utf-8")).get("entries", {})
    current = tree_hashes(profile["freeze_paths"])
    added = sorted(set(current) - set(baseline))
    removed = sorted(set(baseline) - set(current))
    changed = sorted(k for k in set(baseline) & set(current) if baseline[k] != current[k])
    return {"status": "checked", "added": added, "removed": removed, "changed": changed,
            "n": len(current)}


def check_I01(ctx, chk):
    pkg = ctx["package_dir"]
    if not pkg:
        return skip(chk, "no submission package configured")
    if not pkg.is_dir():
        return fail(chk, "package directory missing: %s" % pkg)
    expected = ctx["profile"].get("package_expected") or []
    missing = [n for n in expected if not (pkg / n).is_file()]
    if missing:
        return fail(chk, "missing package files: %s" % ", ".join(missing))
    return ok(chk, "package present with %d expected files" % len(expected))


def _newest_mtime(path: Path):
    """Newest mtime of a file/dir tree (the package 'snapshot' instant), or None."""
    try:
        if path.is_file():
            return path.stat().st_mtime
        stamps = [p.stat().st_mtime for p in path.rglob("*") if p.is_file()]
        return max(stamps) if stamps else None
    except OSError:
        return None


def _page_count(path: Path):
    try:
        if path.is_file():
            from pypdf import PdfReader
            return len(PdfReader(str(path)).pages)
    except Exception:  # noqa: BLE001
        return None
    return None


def _pdf_fingerprint(path: Path) -> dict:
    """Page count + hash of the whitespace-normalised extracted text.

    This is the I-02 'content mode': it is what makes a rebuild comparable, because pdfTeX
    embeds a creation date and a trailer ID, so two builds of the same source are never
    byte-identical unless the build pins SOURCE_DATE_EPOCH (see docs/gate_structural_fixes).
    """
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    norm = re.sub(r"\s+", " ", text).strip()
    return {"pages": len(reader.pages),
            "text_sha256": hashlib.sha256(norm.encode("utf-8")).hexdigest(),
            "text_chars": len(norm)}


def check_I02(ctx, chk):
    profile = ctx["profile"]
    # D-8 (2026-10-25): a frozen submitted package is NEVER compared byte-wise with the live
    # draft -- the divergence is deliberate. Report it as a NAMED warning (package + snapshot
    # date + page divergence) instead of silently skipping, and point at I-04 for integrity.
    if profile.get("package_frozen"):
        frozen = profile.get("package") or next(
            (p for p in (profile.get("freeze_paths") or []) if p.startswith("SUBMISSION/")), None)
        snap = _newest_mtime(ROOT / frozen) if frozen else None
        snap_s = (datetime.fromtimestamp(snap, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                  if snap else "unknown")
        pkg = ctx["package_dir"]
        base = pkg if pkg else (ROOT / frozen if frozen else None)
        n_files = 0
        if base and base.is_dir():
            n_files = sum(1 for f in base.rglob("*") if f.is_file())
        divergent, same, missing = [], [], []
        for pkg_name, live_name in (profile.get("package_map") or []):
            a = (pkg / pkg_name) if pkg else None
            b = ctx["msdir"] / live_name
            if a is None or not a.is_file() or not b.is_file():
                missing.append("%s or %s missing" % (pkg_name, live_name))
                continue
            if sha256_file(a) == sha256_file(b):
                same.append("%s byte-identical" % pkg_name)
                continue
            p_pages, l_pages = _page_count(a), _page_count(b)
            if p_pages is None or l_pages is None:
                divergent.append("%s differs from live %s" % (pkg_name, live_name))
                continue
            if p_pages != l_pages:
                divergent.append("%s %d pp vs live %s %d pp (page count differs)"
                                 % (pkg_name, p_pages, live_name, l_pages))
                continue
            try:
                fa, fb = _pdf_fingerprint(a), _pdf_fingerprint(b)
                if fa["text_sha256"] == fb["text_sha256"]:
                    divergent.append("%s %d pp, text identical (bytes differ)"
                                     % (pkg_name, p_pages))
                else:
                    divergent.append("%s %d pp = %d pp, text differs"
                                     % (pkg_name, p_pages, l_pages))
            except Exception:  # noqa: BLE001
                divergent.append("%s %d pp (bytes differ)" % (pkg_name, p_pages))
        detail = ("package=%s (%d files) snapshot=%s; deliberately not compared with the live "
                  "draft (the submitted version is frozen while the local draft is revised). "
                  "Integrity is verified by I-04 (frozen hashes)."
                  % (frozen, n_files, snap_s))
        if divergent:
            detail += " Diverged: " + "; ".join(divergent) + "."
        if same:
            detail += " Unchanged: " + "; ".join(same) + "."
        if missing:
            detail += " Missing: " + "; ".join(missing) + "."
        return warn(chk, "frozen submitted package (not compared with the live draft)", detail,
                    "when a NEW submission is prepared, rebuild the package and clear "
                    "package_frozen in profiles.py")
    pkg = ctx["package_dir"]
    pairs = profile.get("package_map") or []
    if not pkg or not pairs:
        return skip(chk, "no package-to-live mapping configured")
    bad, details = [], []
    n_byte = n_content = 0
    for pkg_name, live_name in pairs:
        a, b = pkg / pkg_name, ctx["msdir"] / live_name
        if not a.is_file() or not b.is_file():
            bad.append("%s or %s missing" % (pkg_name, live_name))
            continue
        if sha256_file(a) == sha256_file(b):
            n_byte += 1
            details.append("%s == %s (mode=byte)" % (pkg_name, live_name))
            continue
        # D-6 (2026-10-25): only PDFs get the content mode. A rebuild changes /CreationDate and
        # /ID but not one character of text, so a byte difference here is expected and is not a
        # stale package; a genuine text/page difference still FAILS.
        if a.suffix.lower() != ".pdf" or b.suffix.lower() != ".pdf":
            bad.append("%s != %s (byte difference; content mode applies to PDFs only)"
                       % (pkg_name, live_name))
            continue
        try:
            fa, fb = _pdf_fingerprint(a), _pdf_fingerprint(b)
        except Exception as exc:  # noqa: BLE001
            bad.append("%s: content comparison failed (%s: %s)"
                       % (pkg_name, type(exc).__name__, exc))
            continue
        if fa["pages"] != fb["pages"] or fa["text_sha256"] != fb["text_sha256"]:
            bad.append("%s != %s (CONTENT differs: pages %s vs %s, text sha %s vs %s)"
                       % (pkg_name, live_name, fa["pages"], fb["pages"],
                          fa["text_sha256"][:12], fb["text_sha256"][:12]))
            continue
        size_delta = abs(a.stat().st_size - b.stat().st_size) / max(a.stat().st_size, 1)
        if size_delta > 0.01:
            bad.append("%s != %s (text identical but size differs by %.2f%%: embedded assets may "
                       "have changed; rebuild the package)" % (pkg_name, live_name, size_delta * 100))
            continue
        n_content += 1
        details.append("%s ~= %s (mode=content: %d pp, extracted text identical, size delta %.4f%%)"
                       % (pkg_name, live_name, fa["pages"], size_delta * 100))
    if bad:
        return fail(chk, "package copies differ from live files", "; ".join(bad),
                    "regenerate the package after rebuilding the manuscript")
    if n_content:
        return ok(chk, "%d of %d package copies match (%d byte-equal, %d content-equal; content "
                       "mode is used because pdfTeX embeds a creation date/trailer ID, so a rebuild "
                       "is not byte-stable)" % (len(pairs), len(pairs), n_byte, n_content),
                  "; ".join(details))
    return ok(chk, "%d package copies match the live files (mode=byte)" % len(pairs),
              "; ".join(details))


def check_I03(ctx, chk):
    res = ctx["opts"].get("staged_result")
    if not res:
        return skip(chk, "standalone package compile not requested (use --staged)")
    if res.get("ok"):
        return ok(chk, res.get("message", "staged compile passed"))
    return fail(chk, res.get("message", "staged compile failed"))


def check_I04(ctx, chk):
    res = compare_freeze(ctx["profile"])
    if res["status"] == "skip":
        return skip(chk, res["reason"])
    if res["added"] or res["removed"] or res["changed"]:
        return fail(chk, "frozen artefacts changed",
                    "changed=%s removed=%s added=%s" % (res["changed"][:10],
                                                         res["removed"][:10], res["added"][:10]),
                    "restore the frozen files; the submitted version must not change")
    return ok(chk, "%d frozen files unchanged" % res["n"])


def check_I05(ctx, chk):
    pkg = ctx["package_dir"]
    if not pkg or not pkg.is_dir():
        return skip(chk, "no package directory")
    limit_mb = float(ctx["profile"]["limits"].get("portal_size_mb") or 50)
    bad = []
    for f in pkg.rglob("*"):
        if f.is_file() and f.stat().st_size > limit_mb * 1024 * 1024:
            bad.append("%s (%.1f MB)" % (f.name, f.stat().st_size / 1024 / 1024))
    if bad:
        return fail(chk, "files over the portal limit", ", ".join(bad))
    return ok(chk, "all package files under %.0f MB" % limit_mb)


def check_I06(ctx, chk):
    if ctx["profile"].get("package_frozen"):
        return skip(chk, "frozen submitted package README; not re-checked")
    pkg = ctx["package_dir"]
    if not pkg or not (pkg / "README.md").is_file():
        return skip(chk, "no package README")
    readme = (pkg / "README.md").read_text(encoding="utf-8", errors="replace")
    pages = parse_pages(pdfinfo(ctx["pdf"])) if ctx["pdf"] else 0
    problems = []
    checked = 0
    m = re.search(r"\*\*(\d+)\s*页\*\*", readme) or re.search(r"(\d+)\s*(?:页|pages?)", readme)
    if m and pages:
        checked += 1
        if int(m.group(1)) != pages:
            problems.append("README says %s pages, PDF has %d" % (m.group(1), pages))
    m = re.search(r"\*\*(\d+)\s*词\*\*", readme) or re.search(r"(\d+)\s*(?:词|words)", readme)
    if m and ctx["abstract_words"]:
        checked += 1
        if int(m.group(1)) != ctx["abstract_words"]:
            problems.append("README says %s abstract words, measured %d"
                            % (m.group(1), ctx["abstract_words"]))
    if problems:
        return warn(chk, "package README facts are stale", "; ".join(problems))
    if checked == 0:
        return warn(chk, "package README has no measurable page/word claim",
                    str(pkg / "README.md"))
    return ok(chk, "package README facts match the measurements (%d claim(s))" % checked)


def check_I07(ctx, chk):
    pkg = ctx["package_dir"]
    if not pkg or not pkg.is_dir():
        return skip(chk, "no package directory")
    zips = sorted(pkg.glob("*.zip"))
    if not zips:
        return skip(chk, "no source archive in the package")
    z = zips[0]
    try:
        with zipfile.ZipFile(z) as zf:
            bad = zf.testzip()
            names = zf.namelist()
    except zipfile.BadZipFile:
        return fail(chk, "archive is not a valid zip: %s" % z.name)
    if bad is not None:
        return fail(chk, "corrupt entry in archive", bad)
    src = pkg / "latex_source"
    if src.is_dir():
        n_src = sum(1 for f in src.rglob("*") if f.is_file())
        if len(names) != n_src:
            return warn(chk, "archive has %d entries, source tree has %d" % (len(names), n_src))
    return ok(chk, "archive valid (%d entries)" % len(names))


def check_I08(ctx, chk):
    mirror = ctx["profile"].get("public_mirror")
    if not mirror:
        return skip(chk, "no public mirror configured")
    md = ROOT / mirror
    if not md.is_dir():
        return skip(chk, "public mirror not present: %s" % mirror)
    leaks = []
    pattern = re.compile(
        r"^(main|cover[_-]?letter|highlights?|declaration|manuscript|title[_-]?page|"
        r"abstract|graphical[_-]?abstract|supplementary|response|rebuttal)"
        r"([_-][A-Za-z0-9]+)*\.(tex|pdf|bib|docx|zip)$", re.I)
    for f in md.rglob("*"):
        if not f.is_file() or ".git" in f.parts:
            continue
        if f.suffix.lower() not in (".tex", ".pdf", ".bib", ".docx", ".zip"):
            continue
        if pattern.match(f.name.lower()):
            leaks.append(f.relative_to(ROOT).as_posix())
    if leaks:
        return fail(chk, "%d manuscript-like files in the public mirror" % len(leaks),
                    "\n".join(leaks[:10]))
    return ok(chk, "no manuscript files in the public mirror")


def check_J01(ctx, chk):
    idx = ROOT / "outputs" / "analysis"
    if not idx.is_dir():
        return skip(chk, "no outputs/analysis directory")
    ledgers = sorted(idx.glob("claim_ledger*.json"))
    if not ledgers:
        return skip(chk, "no claim-ledger JSON found")
    newest = max(p.stat().st_mtime for p in ledgers)
    src = max((p.stat().st_mtime for p in ctx["tex_files"]), default=0)
    names = ", ".join(p.name for p in ledgers)
    if src > newest:
        return warn(chk, "claim-ledger evidence older than the manuscript sources", names)
    return ok(chk, "claim-ledger evidence current: %s" % names)


def check_J02(ctx, chk):
    out = ROOT / "docs" / "audits"
    reports = sorted(out.glob("AUD-%s-*.json" % ctx["profile"]["id"])) if out.is_dir() else []
    if reports:
        return ok(chk, "archived report present: %s" % reports[-1].name,
                  reports[-1].relative_to(ROOT).as_posix())
    return warn(chk, "no archived report yet for this profile", out.as_posix())


def check_J03(ctx, chk):
    return manual(chk, "confirm HANDOFF.md and 文件地图.md record the current status")


def check_J04(ctx, chk):
    fixes = sorted(ctx["msdir"].glob("FIXES_*.md"))
    if fixes:
        return ok(chk, "fix evidence present: %s" % ", ".join(p.name for p in fixes[-3:]))
    return skip(chk, "no FIXES_*.md in the manuscript directory")


def check_J05(ctx, chk):
    env = ctx["env"]
    required = ("python", "platform", "pdflatex", "pdfinfo", "git_commit", "git_branch")
    missing = [k for k in required if not env.get(k)]
    if missing:
        return fail(chk, "environment fields missing: %s" % ", ".join(missing))
    n_cmd = len(_run_profile_commands(ctx))
    return ok(chk, "environment recorded; %d profile command(s) listed" % n_cmd,
              "; ".join("%s=%s" % (k, env[k]) for k in required))


# ---------------------------------------------------------------------------
# dispatch and entry point
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# mechanical gates (N-*, Phase 1 2026-10-25) -- thin wrappers over mechanical.py
# ---------------------------------------------------------------------------
def check_N01(ctx, chk):
    return mech.check_quantity_uniqueness(ctx, chk)


def check_N02(ctx, chk):
    return mech.check_sign_consistency(ctx, chk)


def check_N03(ctx, chk):
    return mech.check_pointer_resolution(ctx, chk)


def check_N04(ctx, chk):
    return mech.check_archive_claims(ctx, chk)


def check_N05(ctx, chk):
    return mech.check_reference_verification(ctx, chk)


def check_N07(ctx, chk):
    return mech.check_artifact_hygiene(ctx, chk)


selftest_mechanical = mech.selftest_mechanical


# ---------------------------------------------------------------------------
# dispatch and entry point
# ---------------------------------------------------------------------------
HANDLERS = {
    "A-01": check_A01, "A-02": check_A02, "A-03": check_A03, "A-04": check_A04,
    "A-05": check_A05, "A-06": check_A06, "A-07": check_A07, "A-08": check_A08,
    "B-01": check_B01, "B-02": check_B02, "B-03": check_B03, "B-04": check_B04,
    "B-05": check_B05, "B-06": check_B06, "B-07": check_B07, "B-08": check_B08,
    "B-09": check_B09, "B-10": check_B10,
    "C-01": check_C01, "C-02": check_C02, "C-03": check_C03, "C-04": check_C04,
    "C-05": check_C05, "C-06": check_C06, "C-07": check_C07, "C-08": check_C08,
    "C-09": check_C09, "C-10": check_C10,
    "D-01": check_D01, "D-02": check_D02, "D-03": check_D03, "D-04": check_D04,
    "D-05": check_D05, "D-06": check_D06, "D-07": check_D07, "D-08": check_D08,
    "D-09": check_D09, "D-10": check_D10,
    "E-01": check_E01, "E-02": check_E02, "E-03": check_E03, "E-04": check_E04,
    "E-05": check_E05, "E-06": check_E06, "E-07": check_E07, "E-08": check_E08,
    "E-09": check_E09, "E-10": check_E10,
    "F-01": check_F01, "F-02": check_F02, "F-03": check_F03, "F-04": check_F04,
    "F-05": check_F05, "F-06": check_F06, "F-07": check_F07, "F-08": check_F08,
    "F-09": check_F09, "F-10": check_F10,
    "G-01": check_G01, "G-02": check_G02, "G-03": check_G03, "G-04": check_G04,
    "G-05": check_G05, "G-06": check_G06, "G-07": check_G07, "G-08": check_G08,
    "H-01": check_H01, "H-02": check_H02, "H-03": check_H03, "H-04": check_H04,
    "H-05": check_H05, "H-06": check_H06, "H-07": check_H07,
    "I-01": check_I01, "I-02": check_I02, "I-03": check_I03, "I-04": check_I04,
    "I-05": check_I05, "I-06": check_I06, "I-07": check_I07, "I-08": check_I08,
    "J-01": check_J01, "J-02": check_J02, "J-03": check_J03, "J-04": check_J04,
    "J-05": check_J05,
    "N-01": check_N01, "N-02": check_N02, "N-03": check_N03,
    "N-04": check_N04, "N-05": check_N05, "N-07": check_N07,
}


def run_audit(profile: dict, opts: dict) -> Report:
    ctx = build_context(profile, opts)
    findings = []
    for chk in CHECKS:
        handler = HANDLERS.get(chk.id)
        try:
            if handler is None:
                findings.append(manual(chk, chk.method))
            else:
                findings.append(handler(ctx, chk))
        except Exception as exc:  # keep auditing: one broken check must not stop the rest
            findings.append(_finding(chk, Status.ERROR, "%s: %s" % (type(exc).__name__, exc)))
    artifacts = {}
    for p in ctx["pdfs"]:
        if p.is_file():
            artifacts[p.relative_to(ROOT).as_posix()] = sha256_file(p)
    log = ctx["log_stats"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    audit_id = "AUD-%s-%s" % (profile["id"], stamp)
    report = Report(
        audit_id=audit_id,
        profile=profile["id"],
        profile_label=profile["label"],
        manuscript=profile["manuscript"],
        generated_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        git_commit=ctx["env"]["git_commit"],
        git_branch=ctx["env"]["git_branch"],
        git_dirty=bool(ctx["git_status"]),
        environment=ctx["env"],
        findings=findings,
        checks=CHECKS,
        artifacts=artifacts,
        commands=[r["cmd"] for r in _run_profile_commands(ctx)],
    )
    return report
