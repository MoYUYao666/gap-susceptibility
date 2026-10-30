# -*- coding: utf-8 -*-
"""List exactly what N-05 counts as 'not in the cache', with the reason, per profile."""
import json
import sys
from pathlib import Path

REPO = Path(r"D:\Realdesktop\Wan\Important\New")
sys.path.insert(0, str(REPO))
from tools.paper_audit import checks as C  # noqa: E402
from tools.paper_audit import mechanical as M  # noqa: E402
from tools.paper_audit.profiles import get_profile  # noqa: E402

CACHE = json.loads((REPO / "docs" / "REF_VERIFICATION.json").read_text(encoding="utf-8"))["entries"]
rows = []
for pid in ("a23_joe", "paperA_nc", "p3_prl", "a1_paa", "prl_commentary"):
    ctx = C.build_context(get_profile(pid), {"staged_result": None, "command_timeout": 60})
    tex = M.tex_sources(ctx)
    parsed = [M._parse_bib_entry(tex, k, b) for k, b in M.BIB_RE.findall(tex)]
    by_key = {e["key"]: e for e in parsed}
    for key, e in M._bib_file_entries(ctx["msdir"]).items():
        by_key.setdefault(key, e)
    for key, e in sorted(by_key.items()):
        if not (e.get("doi") or e.get("arxiv")):
            continue
        author = (e.get("first_author") or "").strip()
        title = (e.get("title") or "").strip()
        reason = ""
        import re as _re
        if (len(author) < 2 or len(title) < 12
                or not _re.match(r"^[A-Za-z][A-Za-z\-']+$", author)):
            reason = "parse-weak (author=%r title=%r)" % (author[:20], title[:30])
        else:
            c = CACHE.get(key)
            if not c:
                reason = "no cache entry"
            elif str(c.get("source", "")).startswith("unverified"):
                reason = "cache source=unverified"
        if reason:
            rows.append((pid, key, e.get("doi") or ("arXiv:" + e.get("arxiv", "")), author, title, reason))
print("total:", len(rows))
for pid, key, ident, author, title, reason in rows:
    print("%-16s %-28s %-34s %s" % (pid, key[:28], ident[:34], reason))
    print("      title=%r" % title[:90])
(REPO / "docs" / "_n05_missing.json").write_text(
    json.dumps([{"profile": p, "key": k, "identifier": i, "author": a, "title": t, "reason": r}
                for p, k, i, a, t, r in rows], indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote docs/_n05_missing.json")
