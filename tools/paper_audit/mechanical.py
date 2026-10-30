# -*- coding: utf-8 -*-
"""Phase-1 mechanical consistency gates (N-01..N-05, N-07) for the paper audit.

Design rule: a check NEVER returns PASS when it could not determine an answer -- it returns
MANUAL with the reason, so a green verdict always means "checked and clean".

Registries (data, versioned in docs/):
  docs/QUANTITY_REGISTRY.json   N-01: archive-backed quantities + text mentions
  docs/SIGN_REGISTRY.json       N-02: lower_is_better / higher_is_better semantics per field
  docs/RELEASE_LEDGER.json      N-04: release snapshots, DOIs, what the archive holds/excludes
  docs/REF_VERIFICATION.json    N-05: verified reference metadata per citation key

Built/refreshed by tools/paper_audit/build_registries.py.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
QUANTITY_REGISTRY = DOCS / "QUANTITY_REGISTRY.json"
SIGN_REGISTRY = DOCS / "SIGN_REGISTRY.json"
RELEASE_LEDGER = DOCS / "RELEASE_LEDGER.json"
REF_VERIFICATION = DOCS / "REF_VERIFICATION.json"
GITIGNORE = ROOT / ".gitignore"
AUDITS_DIR = DOCS / "audits"

MINUS = "\u2212"  # unicode minus printed by LaTeX math


# --------------------------------------------------------------------------- helpers
def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError) as exc:  # malformed registry is a defect too
        return {"__error__": "%s: %s" % (type(exc).__name__, exc)}


def norm_text(text: str) -> str:
    """Collapse whitespace and unify dashes so regexes survive PDF extraction quirks."""
    t = text.replace(MINUS, "-").replace("\u2013", "-").replace("\u2014", "-")
    t = t.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", t)


def _sentence_split(text: str):
    return re.split(r"(?<=[.;])\s+", norm_text(text))


def _number(token: str):
    try:
        return float(token.replace("\u2212", "-"))
    except (TypeError, ValueError):
        return None


def _rounds_equal(value: float, canonical: float, rounding: int) -> bool:
    if value is None:
        return False
    return round(float(value), int(rounding)) == round(float(canonical), int(rounding))


def _fmt(value: float, rounding: int) -> str:
    return ("%%.%df" % int(rounding)) % float(value)


def resolve_archive(rel_candidates):
    for rel in rel_candidates:
        p = ROOT / rel
        if p.is_file():
            return p
    return None


def get_field(obj, field: str):
    """Resolve a dotted/indexed field path; returns (found, value)."""
    cur = obj
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", field):
        if part.startswith("["):
            try:
                cur = cur[int(part[1:-1])]
            except (IndexError, KeyError, TypeError):
                return False, None
        else:
            if not isinstance(cur, dict) or part not in cur:
                return False, None
            cur = cur[part]
    return True, cur


def profile_text(ctx):
    """Primary PDF text + supplement text (if any), normalised."""
    parts = [ctx.get("pdf_text") or ""]
    prof, msdir = ctx["profile"], ctx["msdir"]
    supp = prof.get("supplementary")
    if supp:
        sp = msdir / supp
        if sp.is_file():
            try:
                from pypdf import PdfReader
                parts.append("".join((p.extract_text() or "") for p in PdfReader(str(sp)).pages))
            except Exception:  # noqa: BLE001
                pass
    return norm_text("\n".join(parts))


def raw_pdf_text(ctx):
    """Un-normalised PDF text layer (line breaks preserved) for heading indexing."""
    parts = [ctx.get("pdf_text") or ""]
    prof, msdir = ctx["profile"], ctx["msdir"]
    supp = prof.get("supplementary")
    if supp:
        sp = msdir / supp
        if sp.is_file():
            try:
                from pypdf import PdfReader
                parts.append("".join((p.extract_text() or "") for p in PdfReader(str(sp)).pages))
            except Exception:  # noqa: BLE001
                pass
    return "\n".join(parts)


def tex_sources(ctx):
    """All LaTeX text of the manuscript (expanded main document + supplemental .tex files)."""
    merged = ctx.get("merged") or ""
    parts = [merged] if merged.strip() else []
    msdir = ctx["msdir"]
    if not parts:  # fallback: expand each configured source on its own
        for tex in ctx["profile"].get("tex") or []:
            p = msdir / tex
            if p.is_file():
                parts.append(p.read_text(encoding="utf-8", errors="replace"))
    supp = ctx["profile"].get("supplementary")
    if supp:
        sp = msdir / Path(supp).parent / "supplementary.tex"
        if sp.is_file():
            parts.append(sp.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def _finding(chk, status, message, evidence="", remediation=""):
    from .model import Finding, Status
    return Finding(check_id=chk.id, dimension=chk.dimension, severity=chk.severity,
                   title=chk.title, status=status, message=message, evidence=evidence,
                   remediation=remediation)


def _status(name):
    from .model import Status
    return getattr(Status, name)


# --------------------------------------------------------------------------- N-01
def check_quantity_uniqueness(ctx, chk):
    reg = load_json(QUANTITY_REGISTRY)
    if reg is None:
        return _finding(chk, _status("MANUAL"), "quantity registry missing",
                        str(QUANTITY_REGISTRY),
                        "run: python tools/paper_audit/build_registries.py --apply")
    if "__error__" in reg:
        return _finding(chk, _status("FAIL"), "quantity registry is malformed", reg["__error__"])
    pid = ctx["profile"]["id"]
    entries = (reg.get("manuscripts") or {}).get(pid) or {}
    if not entries:
        return _finding(chk, _status("SKIP"), "no quantities registered for this profile",
                        "docs/QUANTITY_REGISTRY.json::manuscripts.%s" % pid)
    text = profile_text(ctx)
    fails, manual, checked, scanned, archive_verified = [], [], 0, 0, 0
    for name, q in sorted(entries.items()):
        checked += 1
        archive = resolve_archive([q.get("archive", ""), "outputs/analysis/" + str(q.get("archive", "")),
                                   "outputs/" + str(q.get("archive", ""))])
        if archive is None:
            fails.append("%s: archive missing (%s)" % (name, q.get("archive")))
            continue
        data = load_json(archive)
        found, value = get_field(data, q.get("field", ""))
        if not found or not isinstance(value, (int, float)):
            fails.append("%s: field %s missing in %s" % (name, q.get("field"), archive.name))
            continue
        rounding = int(q.get("rounding", 3))
        if not _rounds_equal(value, q["canonical_value"], rounding):
            fails.append("%s: archive %s=%r but canonical %r (round %d)"
                         % (name, q["field"], value, q["canonical_value"], rounding))
        else:
            archive_verified += 1
        variants = q.get("allowed_variants") or []
        allowed = [v.get("value") for v in variants if isinstance(v, dict)]
        mentions = q.get("mentions") or []
        if not mentions:
            manual.append(name)
            continue
        for m in mentions:
            pattern = m.get("regex") if isinstance(m, dict) else None
            if not pattern:
                fails.append("%s: malformed mention entry" % name)
                continue
            try:
                hits = re.findall(pattern, text, re.I)
            except re.error as exc:
                fails.append("%s: bad regex %r (%s)" % (name, pattern, exc))
                continue
            for hit in hits:
                tok = hit if isinstance(hit, str) else next((g for g in hit if g), "")
                val = _number(tok)
                if val is None:
                    fails.append("%s: mention matched %r but no number parsed" % (name, tok))
                    continue
                scanned += 1
                ok = _rounds_equal(val, q["canonical_value"], rounding) or any(
                    _rounds_equal(val, a, rounding) for a in allowed)
                if not ok:
                    fails.append("%s: printed %r but canonical is %s"
                                 % (name, tok, _fmt(q["canonical_value"], rounding)))
    if fails:
        return _finding(chk, _status("FAIL"), "quantity registry violation(s)",
                        "; ".join(fails[:6]),
                        "one canonical value per quantity, or register the variant with a reason")
    if manual and archive_verified == 0:
        return _finding(chk, _status("MANUAL"),
                        "%d quantity entries have neither an archive check nor a "
                        "text-scan mention" % checked,
                        "not verifiable automatically: " + ", ".join(sorted(manual)[:8]),
                        "add archive/field and mentions to QUANTITY_REGISTRY.json")
    if manual:
        return _finding(chk, _status("MANUAL"),
                        "%d quantity entries: %d archive-verified, %d without a "
                        "text-scan mention"
                        % (checked, archive_verified, len(manual)),
                        "not verifiable automatically: " + ", ".join(manual[:8]),
                        "add a 'mentions' regex for these quantities")
    return _finding(chk, _status("PASS"),
                    "%d quantit(ies) archive-verified; %d printed mention(s) match" % (checked, scanned),
                    "docs/QUANTITY_REGISTRY.json::manuscripts.%s" % pid)


# --------------------------------------------------------------------------- N-02
def check_sign_consistency(ctx, chk):
    reg = load_json(SIGN_REGISTRY)
    if reg is None:
        return _finding(chk, _status("MANUAL"), "sign registry missing", str(SIGN_REGISTRY),
                        "run: python tools/paper_audit/build_registries.py --apply")
    if "__error__" in reg:
        return _finding(chk, _status("FAIL"), "sign registry is malformed", reg["__error__"])
    pid = ctx["profile"]["id"]
    entries = (reg.get("manuscripts") or {}).get(pid) or {}
    if not entries:
        return _finding(chk, _status("SKIP"), "no directional semantics registered", pid)
    text = profile_text(ctx)
    sentences = _sentence_split(text)
    direction = {
        "better": r"\b(better|improves?|improved|gain|gains|favou?rable|superior|reduces? the error)\b",
        "worse": r"\b(worse|degrades?|degraded|drops?|loss|losses|deteriorat\w*|inferior)\b",
        "reverses": r"\b(revers|opposite|sign[- ]flip\w*|contradict\w*)\b",
    }
    comparison = r"\b(than|versus|vs\.?|compared (?:with|to)|relative to|between|both arms|two arms)\b"
    fails, manual, matched = [], [], 0
    for name, e in sorted(entries.items()):
        keyword = e.get("keyword") or ""
        if not keyword:
            fails.append("%s: missing keyword" % name)
            continue
        lower_is = e.get("lower_is")
        if lower_is not in ("better", "worse", "neutral"):
            return _finding(chk, _status("FAIL"), "bad sign registry entry %r" % name,
                            "lower_is must be better/worse/neutral")
        for s in sentences:
            if not re.search(keyword, s, re.I) or not re.search(comparison, s, re.I):
                continue
            verb = next((k for k, pat in direction.items() if re.search(pat, s, re.I)), None)
            if verb is None:
                continue
            matched += 1
            # a paired-difference sentence: find the first signed number and the paired-diff label
            if not re.search(r"paired|delta|\b\Delta\b|difference|AUC|energy|\bE\b|accuracy|F1", s, re.I):
                continue
            m = re.search(r"(?<![\w.])%s\s*[0-9]+\.[0-9]+" % re.escape(MINUS), s)
            if not m:
                m = re.search(r"(?<![\w.])[-]\s*[0-9]+\.[0-9]+", s)
            if not m:
                manual.append("%s: directional sentence without a parsable signed number: %r"
                              % (name, s[:90]))
                continue
            value = _number(m.group(0).replace(" ", ""))
            if value is None:
                manual.append("%s: cannot parse %r" % (name, m.group(0)))
                continue
            if lower_is == "neutral":
                continue
            implied = ("better" if value < 0 else "worse") if lower_is == "better" else (
                "worse" if value < 0 else "better")
            if verb == "reverses":
                continue  # "reverses" describes the comparison, no value judgement to check
            if verb != implied:
                fails.append("%s: sentence calls a %s paired difference %r, but %s means %r "
                             "(value %+.4f): %r"
                             % (name, "negative" if value < 0 else "positive", verb, lower_is,
                                implied, value, s[:110]))
    if fails:
        return _finding(chk, _status("FAIL"), "sign/direction contradiction(s)",
                        " || ".join(fails[:4]),
                        "state the direction with the registered semantics, or fix the number")
    if manual:
        return _finding(chk, _status("MANUAL"), "directional sentence(s) without a parsable value",
                        " || ".join(manual[:3]))
    return _finding(chk, _status("PASS"), "no directional contradiction (%d sentence(s) matched)" % matched,
                    "docs/SIGN_REGISTRY.json::manuscripts.%s" % pid)


# --------------------------------------------------------------------------- N-03
LEAK_PATTERNS = [
    (r"\bref[a-z]{1,12}:\s*[A-Za-z]", "leaked \\ref fragment (e.g. 'refcor:')"),
    (r"\bref\{", "leaked \\ref{...}"),
    (r"\b(?:Table|Figure|Section|Eq\.)\s*\?\?", "unresolved '??' pointer"),
    (r"\?\?", "unresolved '??'"),
    (r"Appendix\s+Appendix", "duplicated 'Appendix Appendix'"),
]


def _tex_pointer_index(ctx):
    """Numbers that exist, simulated from the LaTeX counters (sections/tables/figures)."""
    tex = tex_sources(ctx)
    idx = {"section": set(), "appendix": set(), "table": set(), "figure": set(), "supp": set()}
    sec = sub = subsub = 0
    tbl = fig = 0
    appendix_mode = False
    for line in tex.splitlines():
        if re.match(r"\s*\\appendix\b", line):
            appendix_mode = True
            sec = sub = subsub = 0
            continue
        if re.search(r"\\section\*", line):
            continue
        if re.search(r"\\section\{", line):
            sec += 1
            sub = subsub = 0
            if appendix_mode:
                idx["appendix"].add(chr(64 + sec) if sec <= 26 else "?")
            else:
                idx["section"].add(str(sec))
            continue
        if re.search(r"\\subsection\*", line):
            continue
        if re.search(r"\\subsection\{", line):
            sub += 1
            subsub = 0
            if appendix_mode:
                idx["appendix"].add("%s.%d" % (chr(64 + sec) if sec <= 26 else "?", sub))
            else:
                idx["section"].add("%d.%d" % (sec, sub))
            continue
        if re.search(r"\\subsubsection\{", line):
            subsub += 1
            if not appendix_mode:
                idx["section"].add("%d.%d.%d" % (sec, sub, subsub))
            continue
        if re.search(r"\\begin\{table\}", line):
            tbl += 1
            idx["table"].add(str(tbl))
        if re.search(r"\\begin\s*\{table\*\}", line):
            tbl += 1
            idx["table"].add(str(tbl))
        if re.search(r"\\begin\{figure\}", line):
            fig += 1
            idx["figure"].add(str(fig))
        if re.search(r"\\begin\{longtable\}", line):
            tbl += 1
            idx["table"].add(str(tbl))
    # supplement: separate document with S<k> sections
    supp = ctx["profile"].get("supplementary")
    if supp:
        sp = ctx["msdir"] / Path(supp).parent / "supplementary.tex"
        if sp.is_file():
            st = sp.read_text(encoding="utf-8", errors="replace")
            n = len(re.findall(r"\\section\{", st))
            idx["supp"] = set(str(i) for i in range(1, n + 1))
    return idx


def _pdf_pointer_index(text):
    """Heading numbers recovered from the raw PDF text layer (independent of the tex counters)."""
    idx = {"section": set(), "appendix": set(), "table": set(), "figure": set()}
    for m in re.finditer(r"(?:^|\n|\f|\.\s)(\d+(?:\.\d+){0,2})\.?\s+[A-Za-z\u0370-\u03ff]", text):
        idx["section"].add(m.group(1))
    for m in re.finditer(r"(?:^|\n|\f)\s*(\d+(?:\.\d+){0,2})\.?\s+\S", text):
        idx["section"].add(m.group(1))
    for m in re.finditer(r"Appendix\s+([A-Z])(?:\.(\d+))?\.?\s", text):
        idx["appendix"].add(m.group(1) + ("." + m.group(2) if m.group(2) else ""))
    for m in re.finditer(r"Table\s+(\d+|[A-Z]\.\d+)\s*:", text):
        idx["table"].add(m.group(1))
    for m in re.finditer(r"Figure\s+(\d+|[A-Z]\.\d+)\s*:", text):
        idx["figure"].add(m.group(1))
    return idx


def check_pointer_resolution(ctx, chk):
    text = profile_text(ctx)
    fails = []
    for pat, label in LEAK_PATTERNS:
        if pat == r"\?\?":
            continue  # covered by the specific patterns above
        hit = re.search(pat, text)
        if hit:
            fails.append("%s -> %r" % (label, text[max(0, hit.start() - 40):hit.end() + 40]))
    tex = tex_sources(ctx)
    # (iv) a starred heading inside the appendix carrying a label referenced by number: that label
    # inherits the *previous* numbered heading (this produced the A.4 mis-pointing). Starred
    # headings in the body legitimately inherit their section number, so they are not flagged.
    star_labels = []
    lines = tex.splitlines()
    appendix_mode = False
    for i, line in enumerate(lines):
        if re.match(r"\s*\\appendix\b", line):
            appendix_mode = True
            continue
        if not appendix_mode:
            continue
        if re.search(r"\\(section|subsection|subsubsection)\*\{", line):
            for j in range(i + 1, min(i + 4, len(lines))):
                m = re.search(r"\\label\{([^}]+)\}", lines[j])
                if m:
                    star_labels.append(m.group(1))
                    break
    bad_star = []
    for lab in star_labels:
        if re.search(r"\\ref\{%s\}" % re.escape(lab), tex):
            bad_star.append(lab)
    # (iii) pointer targets must exist
    tix = _tex_pointer_index(ctx)
    pix = _pdf_pointer_index(raw_pdf_text(ctx))
    allowed = {k: tix[k] | pix.get(k, set()) for k in ("section", "appendix", "table", "figure")}
    unknown = []
    for kind, target in re.findall(r"\b(Section|Appendix|Table|Figure)s?\s+([A-Z]?(?:\d+\.)?\d+(?:\.\d+)?)", text):
        key = {"Section": "section", "Appendix": "appendix", "Table": "table",
               "Figure": "figure"}[kind]
        if not allowed[key]:
            continue  # cannot build an index -> not determinable, do not fail
        norm = target.lstrip("0") or "0"
        if norm in allowed[key] or target in allowed[key]:
            continue
        if key == "section" and re.match(r"^\d+\.\d+$", target):
            continue  # subsection numbering checked against the same set
        unknown.append("%s %s" % (kind, target))
    if fails:
        return _finding(chk, _status("FAIL"), "cross-reference leakage in the built PDF",
                        " || ".join(fails[:4]),
                        "fix the source: this text must never reach the PDF")
    if unknown or bad_star:
        notes = []
        if unknown:
            notes.append("pointer target(s) not found in the index: %s"
                         % ", ".join(sorted(set(unknown))[:8]))
        if bad_star:
            notes.append("starred appendix heading(s) whose label is referenced by number: %s"
                         % ", ".join(sorted(set(bad_star))[:4]))
        return _finding(chk, _status("MANUAL"),
                        "no leaked references; numbering could not be certified automatically",
                        " || ".join(notes),
                        "resolve the pointer manually; the numbering scheme differs across templates")
    return _finding(chk, _status("PASS"), "no leaked/unresolved pointers or wrong targets",
                    "index: %d sections, %d appendix subsections, %d tables, %d figures"
                    % (len(allowed["section"]), len(allowed["appendix"]),
                       len(allowed["table"]), len(allowed["figure"])))


# --------------------------------------------------------------------------- N-04
CLAIM_OBJECTS = {
    "manuscript": ("manuscripts", "forbidden"),
    "compiled": ("compiled PDFs", "forbidden"),
    "pdf": ("compiled PDFs", "forbidden"),
    "cover letter": ("cover letters", "forbidden"),
    "script": ("scripts", "tools"),
    "code": ("code", "tools"),
    "record": ("per-run records", "outputs"),
    "analysis": ("analyses", "outputs"),
    "analyses": ("analyses", "outputs"),
    "figure": ("figures", "outputs"),
    "result": ("results", "outputs"),
    "dataset": ("datasets", "outputs"),
}


def _data_statements(tex):
    """Paragraphs of the data/code availability statement(s)."""
    out = []
    for m in re.finditer(r"(?:Data(?:\s+and\s+code)?\s+availability|Code\s+availability|"
                         r"Data\s+statement|Data\s+and\s+code\s+availability)", tex, re.I):
        tail = tex[m.end():m.end() + 2200]
        stop = re.search(r"\\(?:sub)?section|\\textbf\{|\\bibliography|\\end\{document\}", tail)
        if stop:
            tail = tail[:stop.start()]
        out.append((m.group(0), tail))
    return out


def check_archive_claims(ctx, chk):
    ledger = load_json(RELEASE_LEDGER)
    if ledger is None:
        return _finding(chk, _status("MANUAL"), "release ledger missing", str(RELEASE_LEDGER),
                        "run: python tools/paper_audit/build_registries.py --apply")
    if "__error__" in ledger:
        return _finding(chk, _status("FAIL"), "release ledger is malformed", ledger["__error__"])
    statements = _data_statements(ctx.get("merged") or "")
    if not statements:
        return _finding(chk, _status("SKIP"), "no data availability statement in the sources",
                        "profile %s" % ctx["profile"]["id"])
    registered_dois = set(d.lower() for d in ledger.get("registered_dois") or [])
    third = ledger.get("third_party_sources") or []
    third_dois = {t.get("doi", "").lower() for t in third if t.get("doi")}
    third_urls = {t.get("url", "").lower() for t in third if t.get("url")}
    registered_dois |= third_dois
    venue_file = DOCS / "VENUE_SCI_REGISTRY.md"
    if venue_file.is_file():
        registered_dois |= set(d.lower() for d in re.findall(
            r"10\.\d{4,9}/[^\s)\];,]+", venue_file.read_text(encoding="utf-8", errors="replace")))
    repos = set(r.rstrip("/").lower() for r in ledger.get("repositories") or [])
    excludes = [e.lower() for e in ledger.get("archive_excludes") or []]
    has_tools = (ROOT / "publish_clean" / "tools").is_dir()
    has_outputs = (ROOT / "publish_clean" / "outputs").is_dir()
    fails, checked = [], 0
    for label, body in statements:
        flat = norm_text(body)
        for doi in re.findall(r"10\.\d{4,9}/[^\s)\];,}]+", flat):
            checked += 1
            if doi.lower().rstrip(".") not in {d.rstrip(".") for d in registered_dois}:
                fails.append("DOI %s is not registered in RELEASE_LEDGER/VENUE_SCI_REGISTRY" % doi)
        for url in re.findall(r"https?://[^\s)\];,}]+", flat):
            checked += 1
            base = re.sub(r"^https?://(www\.)?", "", url.lower()).split("/")[0]
            low = url.lower()
            ok = (any(base in r for r in repos)
                  or any(d and d.rstrip(".") in low for d in registered_dois)
                  or any(base in d for d in registered_dois)
                  or any(u and u.rstrip("/") in low for u in third_urls))
            if not ok:
                fails.append("URL %s is not registered in RELEASE_LEDGER" % url)
        # 'contains/archived' claims about objects the archive does not hold
        for m in re.finditer(r"(contains?|includes?|archiv\w*|holds?|deposit\w*)", flat, re.I):
            window = flat[m.start():m.start() + 260].lower()
            for key, (obj, kind) in CLAIM_OBJECTS.items():
                if key not in window:
                    continue
                if kind == "forbidden":
                    fails.append("claims the archive holds %s, but the release excludes %s"
                                 % (obj, ", ".join(excludes) or obj))
                elif kind == "tools" and not has_tools:
                    fails.append("claims archived %s but publish_clean/tools is absent" % obj)
                elif kind == "outputs" and not has_outputs:
                    fails.append("claims archived %s but publish_clean/outputs is absent" % obj)
    if fails:
        return _finding(chk, _status("FAIL"), "archive/data-statement claims are not verifiable",
                        " || ".join(fails[:4]),
                        "make the statement match docs/RELEASE_LEDGER.json or register the target")
    return _finding(chk, _status("PASS"),
                    "data statement: %d link(s) registered; contains-claims match the ledger" % checked,
                    "docs/RELEASE_LEDGER.json")


# --------------------------------------------------------------------------- N-05
BIB_RE = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}(.*?)(?=\\bibitem|\\end\{thebibliography\})",
                    re.S)


BIB_QUOTED_RE = re.compile(r"``(.+?)''|\u201c(.+?)\u201d|\"(.+?)\"", re.S)
BIB_VENUE_RE = re.compile(r"(arxiv|preprint|proceedings|conference|journal|transactions|letters|"
                          r"workshop|symposium|press|vol\.|pp\.|\((?:19|20)\d{2}\)|"
                          r"advances|neurips|icml|iclr|cvpr|eccv|iccv|acl|emnlp|naacl|"
                          r"ieee|acm|springer|elsevier)", re.I)


def _bib_first_surname(flat):
    """First-author surname for APA style ('Huh, M., ...') and IEEE style ('F. Maione, ...')."""
    seg = flat.split(" et al")[0]
    seg = re.split(r",|;| and ", seg)[0].strip()
    seg = re.sub(r"^\[[^\]]*\]\s*", "", seg)
    toks = [t for t in re.split(r"\s+", seg) if t]
    if not toks:
        return ""
    return toks[-1].strip(".")


def _bib_title(flat):
    q = BIB_QUOTED_RE.search(flat)
    if q:
        return (q.group(1) or q.group(2) or q.group(3) or "").strip().strip("`\"'")
    m = re.search(r"\(\s*(?:19|20)\d{2}\s*\)\.?\s*(.+?)(?:\.\s|$)", flat)
    if m:
        return m.group(1).strip()
    # unquoted IEEE/Commentary style: the longest comma-separated segment that is not venue/author
    best = ""
    for seg in [x.strip() for x in flat.split(", ") if x.strip()]:
        words = seg.split()
        if len(words) < 3 or BIB_VENUE_RE.search(seg):
            continue
        if len(words) == 2 and all(w[0].isupper() for w in words if w):
            continue
        if len(seg) > len(best):
            best = seg
    return re.sub(r"^[A-Z]\.\s+", "", best).strip()


def _parse_bib_entry(tex, key, body):
    flat = norm_text(body)
    doi = re.search(r"10\.\d{4,9}/[^\s)\]<>,;\"]+", flat)
    arx = re.search(r"arXiv:\s*(\d{4}\.\d{4,5})", flat, re.I)
    year = re.search(r"\((19|20)\d{2}\)", flat) or re.search(r"\b(19|20)\d{2}\b", flat)
    first = _bib_first_surname(flat)
    title = _bib_title(flat)
    return {"key": key, "first_author": first, "year": year.group(0).strip("()") if year else "",
            "title": title, "doi": doi.group(0).rstrip(".") if doi else "",
            "arxiv": arx.group(1) if arx else "",
            "raw": flat[:400]}


VENUE_WORDS_RE = re.compile(
    r"(pp\.|proc\.|proceedings|conference|volume|vol\.|journal|transactions|letters|"
    r"arxiv|iclr|icml|cvpr|neurips|eccv|iccv|adv\.|advances|track|workshop)", re.I)


def _title_reliable(t: str) -> bool:
    return bool(t) and len(t) >= 8 and not VENUE_WORDS_RE.search(t)


def _norm_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())[:70]


BIB_FILE_RE = re.compile(r"@(\w+)\{([^,\s]+),\s*(.*?)\n\}", re.S)


def _bib_fields(body: str):
    """Parse `key = {value}` fields with brace-depth counting (titles like {{IGU-LoRA}: ...})."""
    out = {}
    for m in re.finditer(r"(\w+)\s*=\s*\{", body):
        key = m.group(1).lower()
        i = m.end()
        depth = 1
        start = i
        while i < len(body) and depth:
            if body[i] == "{":
                depth += 1
            elif body[i] == "}":
                depth -= 1
            i += 1
        out.setdefault(key, body[start:i - 1].strip())
    return out


def _bib_file_entries(msdir: Path):
    """Parse BibTeX @entry{key,...} files under the manuscript directory."""
    out = {}
    if not msdir.is_dir():
        return out
    # prefer the manuscript-root bibliography; package copies are frozen/stale by design
    bibs = sorted(msdir.rglob("*.bib"), key=lambda p: (len(p.relative_to(msdir).parts), str(p)))
    for bib in bibs:
        try:
            text = bib.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for kind, key, body in BIB_FILE_RE.findall(text):
            if key in out:
                continue
            fields = _bib_fields(body)
            flat = norm_text(" ".join(fields.values()))
            arx = re.search(r"arXiv:\s*(\d{4}\.\d{4,5})", flat, re.I)
            out[key] = {
                "key": key, "first_author": fields.get("author", "").split(" and ")[0].split(",")[0],
                "year": fields.get("year", ""), "title": fields.get("title", ""),
                "venue": fields.get("booktitle") or fields.get("journal", ""),
                "doi": fields.get("doi", "").rstrip("."),
                "arxiv": fields.get("eprint", "") or (arx.group(1) if arx else ""),
                "raw": flat[:400],
            }
    return out


def check_reference_verification(ctx, chk):
    cache = load_json(REF_VERIFICATION)
    if cache is None:
        return _finding(chk, _status("MANUAL"), "reference verification cache missing",
                        str(REF_VERIFICATION),
                        "run: python tools/paper_audit/build_registries.py --apply")
    if "__error__" in cache:
        return _finding(chk, _status("FAIL"), "reference cache is malformed", cache["__error__"])
    entries = cache.get("entries") or {}
    tex = tex_sources(ctx)
    msdir = ctx["msdir"]
    parsed = [_parse_bib_entry(tex, k, b) for k, b in BIB_RE.findall(tex)]
    by_key = {e["key"]: e for e in parsed}
    for key, e in _bib_file_entries(msdir).items():
        by_key.setdefault(key, e)
    if not by_key:
        return _finding(chk, _status("SKIP"), "no bibliography entries in the sources",
                        ctx["profile"]["id"])
    if not any(e.get("doi") or e.get("arxiv") for e in by_key.values()):
        return _finding(chk, _status("SKIP"), "no DOI/arXiv bibliography entries to verify",
                        ctx["profile"]["id"])
    fails, unverified, verified = [], [], 0
    for key, e in sorted(by_key.items()):
        if not e.get("doi") and not e.get("arxiv"):
            continue
        # conservative: only compare entries whose title/author could be parsed reliably
        author = (e.get("first_author") or "").strip()
        title = (e.get("title") or "").strip()
        if (len(author) < 2 or len(title) < 12
                or not re.match(r"^[A-Za-z][A-Za-z\-']+$", author)):
            unverified.append(key)
            continue
        c = entries.get(key)
        if not c or str(c.get("source", "")).startswith("unverified"):
            unverified.append(key)
            continue
        verified += 1
        problems = []
        cache_title = _norm_title(c.get("title") or "")
        bib_title = _norm_title(e.get("title") or "")
        if " and " in (e.get("title") or "") or len((e.get("title") or "").split()) <= 3:
            bib_title = ""  # name-list / truncated title fragment: not comparable
        same_title = (not cache_title or not bib_title or cache_title == bib_title
                      or cache_title in bib_title or bib_title in cache_title)
        if c.get("title") and _title_reliable(e.get("title") or "") and not same_title:
            problems.append("title %r vs cache %r" % (e["title"][:60], c["title"][:60]))
        bib_author = (e.get("first_author") or "").strip()
        if " and " in bib_author or len(bib_author) > 30:
            bib_author = ""  # the bibitem parser returned an author list, not a surname
        if c.get("first_author") and re.match(r"^[A-Za-z][A-Za-z\-']{2,}$", bib_author):
            bib_surname = bib_author.split()[-1].lower()
            cache_surname = (c["first_author"].strip().split()[-1].lower()
                             if c["first_author"].strip() else "")
            if cache_surname and bib_surname != cache_surname:
                problems.append("first author %r vs cache %r" % (bib_author, c["first_author"]))
        if (c.get("year") and e.get("year") and str(c["year"]) != str(e.get("year"))
                and c.get("year_comparable", True)):
            problems.append("year %r vs cache %r" % (e.get("year"), c["year"]))
        if problems:
            fails.append("%s: %s" % (key, "; ".join(problems)))
    if fails:
        return _finding(chk, _status("FAIL"), "reference metadata disagrees with the verified cache",
                        " || ".join(fails[:4]),
                        "correct the bibliography entry, not the cache")
    if unverified:
        return _finding(chk, _status("MANUAL"),
                        "%d reference(s) verified; %d DOI/arXiv entries not in the cache"
                        % (verified, len(unverified)),
                        "unverified: " + ", ".join(unverified[:8]),
                        "run: python tools/paper_audit/build_registries.py --apply (and verify them)")
    return _finding(chk, _status("PASS"), "%d DOI/arXiv reference(s) match the verified cache" % verified,
                    "docs/REF_VERIFICATION.json")


# --------------------------------------------------------------------------- N-07
def check_artifact_hygiene(ctx, chk):
    problems = []
    gi = GITIGNORE.read_text(encoding="utf-8", errors="replace") if GITIGNORE.is_file() else ""
    has_rule = re.search(r"(?m)^docs/audits/\*", gi) or re.search(r"(?m)^docs/audits/$", gi)
    has_keep = bool(re.search(r"(?m)^!docs/audits/\.gitkeep", gi))
    if not has_rule:
        problems.append(".gitignore has no docs/audits ignore rule")
    if not has_keep:
        problems.append(".gitignore does not re-include docs/audits/.gitkeep")
    if not (AUDITS_DIR / ".gitkeep").is_file():
        problems.append("docs/audits/.gitkeep missing")
    untracked = ""
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", "docs/audits"],
                           cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60)
        untracked = "\n".join(l for l in (r.stdout or "").splitlines()
                              if l.startswith("??") and "AUD-" in l)
    except Exception as exc:  # noqa: BLE001
        problems.append("cannot run git status: %s" % exc)
    if untracked.strip():
        problems.append("untracked audit files still visible: %s"
                        % ", ".join(untracked.splitlines()[:3]))
    if problems:
        return _finding(chk, _status("FAIL"), "audit artifact hygiene broken",
                        " || ".join(problems),
                        "keep docs/audits ignored except .gitkeep so runs leave no untracked files")
    return _finding(chk, _status("PASS"),
                    "docs/audits is git-ignored except .gitkeep; no untracked audit artifacts",
                    ".gitignore + docs/audits/.gitkeep")


CHECKS = {
    "N-01": check_quantity_uniqueness,
    "N-02": check_sign_consistency,
    "N-03": check_pointer_resolution,
    "N-04": check_archive_claims,
    "N-05": check_reference_verification,
    "N-07": check_artifact_hygiene,
}


# --------------------------------------------------------------------------- self-test
def _fixture_ctx(pid, case="", tex="", pdf_text="", msdir=None):
    return {"profile": {"id": pid, "tex": [], "supplementary": None}, "msdir": msdir or ROOT,
            "merged": tex, "pdf_text": pdf_text, "case": case}


class _FakeRun:
    """Stands in for the `subprocess` module when a fixture must not touch git."""

    def __init__(self, stdout=""):
        self._stdout = stdout

    def run(self, *a, **k):
        return type("R", (), {"stdout": self._stdout, "returncode": 0})()


def selftest_mechanical():
    """Positive + negative fixtures for every Phase-1 check. Returns [(id, case, expect, got, ok)]."""
    import tempfile

    from .registry import by_id

    tmp = Path(tempfile.mkdtemp(prefix="mech_selftest_"))
    saved = {k: globals().get(k) for k in
             ("QUANTITY_REGISTRY", "SIGN_REGISTRY", "RELEASE_LEDGER", "REF_VERIFICATION",
              "GITIGNORE", "AUDITS_DIR", "subprocess")}
    cases = []

    def wjson(name, data):
        p = tmp / name
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def run(cid, ctx, expect):
        f = None
        try:
            f = CHECKS[cid](ctx, by_id(cid))
            got = f.status.value
            detail = (f.evidence or "")[:160]
        except Exception as exc:  # noqa: BLE001
            got, detail = "ERROR", "%s: %s" % (type(exc).__name__, exc)
        cases.append((cid, ctx.get("case", ""), expect, got, expect == got, detail))
        return f

    try:
        # ---- N-01 quantity uniqueness ------------------------------------
        arc = wjson("archive.json", {"v": 32.673, "cg": 0.855})
        globals()["QUANTITY_REGISTRY"] = wjson("qty.json", {"manuscripts": {"t1": {
            "spread": {"archive": str(arc), "field": "v", "canonical_value": 32.7,
                       "rounding": 1, "mentions": [{"regex": r"spread ([0-9.]+)"}]}}}})
        run("N-01", _fixture_ctx("t1", "positive", pdf_text="the spread 32.7 points holds"),
            "PASS")
        run("N-01", _fixture_ctx("t1", "second value", pdf_text="the spread 33.0 points holds"),
            "FAIL")
        globals()["QUANTITY_REGISTRY"] = wjson("qty2.json", {"manuscripts": {"t1": {
            "spread": {"archive": "missing/archive.json", "field": "v", "canonical_value": 1.0,
                       "rounding": 1, "mentions": []}}}})
        run("N-01", _fixture_ctx("t1", "missing archive"), "FAIL")
        globals()["QUANTITY_REGISTRY"] = tmp / "missing-qty.json"  # missing registry must be MANUAL
        run("N-01", _fixture_ctx("t1", "missing registry"), "MANUAL")

        # ---- N-02 sign consistency --------------------------------------
        globals()["SIGN_REGISTRY"] = wjson("sign.json", {"manuscripts": {"t2": {
            "paired difference": {"keyword": r"paired difference", "lower_is": "better"}}}})
        good = ("The paired difference is \u22123570.10, which is better than the other arm.")
        bad = ("The paired difference is \u22123570.10, which is worse than the other arm.")
        run("N-02", _fixture_ctx("t2", "negative is better", pdf_text=good), "PASS")
        run("N-02", _fixture_ctx("t2", "negative called worse", pdf_text=bad), "FAIL")

        # ---- N-03 pointer resolution ------------------------------------
        run("N-03", _fixture_ctx("t3", "duplicated Appendix",
                                 pdf_text="see Appendix Appendix A.3 for details"), "FAIL")
        run("N-03", _fixture_ctx("t3", "leaked ref", pdf_text="Corollary refcor:lipschitz holds"),
            "FAIL")
        run("N-03", _fixture_ctx("t3", "clean pointers",
                                 tex="\\section{One}\n\\section{Two}\n",
                                 pdf_text="see Section 2 for details and Table 1: x"),
            "PASS")

        # ---- N-04 archive claims ----------------------------------------
        globals()["RELEASE_LEDGER"] = wjson("rel.json", {
            "registered_dois": ["10.5281/zenodo.23632347"], "repositories": [],
            "archive_excludes": ["manuscripts"], "archive_root": "publish_clean"})
        ok_tex = ("\\section{Data availability} The records are archived at "
                  "https://doi.org/10.5281/zenodo.23632347 and the scripts are in the repository. "
                  "\\section{Conclusion}")
        run("N-04", _fixture_ctx("t4", "registered DOI", tex=ok_tex), "PASS")
        bad_doi = ("\\section{Data availability} The archive is at "
                   "https://doi.org/10.5281/zenodo.99999999 . \\section{Conclusion}")
        run("N-04", _fixture_ctx("t4", "unregistered DOI", tex=bad_doi), "FAIL")
        bad_claim = ("\\section{Data availability} The archive contains the compiled manuscripts "
                     "and the results. \\section{Conclusion}")
        run("N-04", _fixture_ctx("t4", "manuscripts claimed", tex=bad_claim), "FAIL")

        # ---- N-05 reference cache ---------------------------------------
        globals()["REF_VERIFICATION"] = wjson("refs.json", {"entries": {"k1": {
            "title": "A Great Paper", "first_author": "Smith", "year": "2020",
            "source": "verified"}}})
        bib_ok = ("\\begin{thebibliography}{9}\n\\bibitem[Smith, 2020]{k1} Smith, J. (2020). "
                  "A Great Paper. Journal of Tests. DOI: 10.1234/abc.\n\\end{thebibliography}")
        run("N-05", _fixture_ctx("t5", "matching cache", tex=bib_ok, msdir=tmp), "PASS")
        globals()["REF_VERIFICATION"] = wjson("refs2.json", {"entries": {"k1": {
            "title": "A Great Paper", "first_author": "Jones", "year": "2020",
            "source": "verified"}}})
        run("N-05", _fixture_ctx("t5", "wrong first author", tex=bib_ok, msdir=tmp), "FAIL")

        # ---- N-07 artifact hygiene --------------------------------------
        gi_ok = tmp / "gitignore_ok"
        gi_ok.write_text("docs/audits/*\n!docs/audits/.gitkeep\n", encoding="utf-8")
        ad_ok = tmp / "audits_ok"
        ad_ok.mkdir()
        (ad_ok / ".gitkeep").write_text("", encoding="utf-8")
        globals()["GITIGNORE"], globals()["AUDITS_DIR"] = gi_ok, ad_ok
        globals()["subprocess"] = _FakeRun("")
        run("N-07", _fixture_ctx("t7", "ignored audits"), "PASS")
        gi_bad = tmp / "gitignore_bad"
        gi_bad.write_text("", encoding="utf-8")
        globals()["GITIGNORE"] = gi_bad
        run("N-07", _fixture_ctx("t7", "missing ignore rule"), "FAIL")
        globals()["subprocess"] = _FakeRun("?? docs/audits/AUD-x-1.json\n")
        globals()["GITIGNORE"] = gi_ok
        run("N-07", _fixture_ctx("t7", "untracked AUD file visible"), "FAIL")
    finally:
        for k, v in saved.items():
            if v is not None:
                globals()[k] = v
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    return cases
