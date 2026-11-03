# -*- coding: utf-8 -*-
"""Small, dependency-free LaTeX helpers used by the paper-audit checks.

The helpers are deliberately conservative: they scan text, they do not try to
be a TeX parser. Every heuristic records what it did so the report stays honest.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

CITE_RE = re.compile(r"\\cite[a-zA-Z]*\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}")
REF_RE = re.compile(r"\\(?:ref|eqref|autoref|cref|Cref|pageref|nameref)\{([^}]*)\}")
LABEL_RE = re.compile(r"\\label\{([^}]*)\}")
SECTION_RE = re.compile(r"\\(?:section|subsection|subsubsection)\*?\{")
BIBITEM_RE = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}")
BIB_KEY_RE = re.compile(r"@[a-zA-Z]+\s*\{\s*([^,\s]+)\s*,")
INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]*)\}")
TITLE_RE = re.compile(r"\\title\{")
AUTHOR_RE = re.compile(r"\\author\{")
ABSTRACT_ENV_RE = re.compile(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", re.S)
KEYWORD_ENVS = ("keyword", "keywords", "IEEEkeywords", "IEEEkeyword")
MATH_INLINE_RE = re.compile(r"\$[^$]*\$")
CMD_RE = re.compile(r"\\[a-zA-Z]+\*?")
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def strip_comments(tex: str) -> str:
    out = []
    for line in tex.splitlines():
        if line.lstrip().startswith("%"):
            out.append("")
            continue
        out.append(re.sub(r"(?<!\\)%.*$", "", line))
    return "\n".join(out)


def balanced_group(text: str, open_pos: int) -> tuple[str, int]:
    """Return the contents of the brace group starting at text[open_pos] == '{'."""
    depth = 0
    for i in range(open_pos, len(text)):
        ch = text[i]
        if ch == "{" and (i == 0 or text[i - 1] != "\\"):
            depth += 1
        elif ch == "}" and (i == 0 or text[i - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return text[open_pos + 1:i], i + 1
    return text[open_pos + 1:], len(text)


def command_arg(tex: str, cmd: str) -> str:
    m = re.search(r"\\" + re.escape(cmd) + r"\*?", tex)
    if not m:
        return ""
    i = tex.find("{", m.end())
    if i < 0:
        return ""
    return balanced_group(tex, i)[0]


def expand_sources(msdir: Path, tex_names: list[str]) -> tuple[str, list[str]]:
    """Concatenate the named sources plus recursively included files."""
    seen: list[str] = []
    parts: list[str] = []

    def visit(rel: str):
        p = (msdir / rel).resolve()
        if not p.is_file():
            return
        key = str(p)
        if key in seen:
            return
        seen.append(key)
        raw = read_text(p)
        tex = strip_comments(raw)
        parts.append("\n%% ---- %s ----\n" % rel)
        parts.append(tex)
        for m in INPUT_RE.finditer(tex):
            inc = m.group(1).strip()
            for cand in (inc, inc + ".tex"):
                if (msdir / cand).is_file():
                    visit(cand)
                    break

    for name in tex_names:
        visit(name)
    return "\n".join(parts), seen


def find_abstract(tex: str, style: str = "env") -> str:
    if style == "command" or not ABSTRACT_ENV_RE.search(tex):
        body = command_arg(tex, "abstract")
        if body:
            return body
    m = ABSTRACT_ENV_RE.search(tex)
    return m.group(1) if m else ""


def find_keywords(tex: str) -> str:
    for env in KEYWORD_ENVS:
        m = re.search(r"\\begin\{" + env + r"\}(.*?)\\end\{" + env + r"\}", tex, re.S)
        if m:
            return m.group(1)
    body = command_arg(tex, "keywords")
    return body


def keyword_items(text: str) -> list[str]:
    text = text.replace("\\sep", ";")
    flat = re.sub(r"\\[a-zA-Z]+\*?[\[{][^}\]]*[\]}]", " ", text)
    flat = flat.replace("{", " ").replace("}", " ").replace("\\", " ")
    parts = re.split(r"[;,]\s*", flat)
    return [re.sub(r"\s+", " ", p).strip() for p in parts if p.strip()]


def count_words(text: str, math_as_one: bool = True) -> int:
    t = text
    if math_as_one:
        t = MATH_INLINE_RE.sub(" MATH ", t)
        t = re.sub(r"\\\[.*?\\\]", " MATH ", t, flags=re.S)
        t = re.sub(r"\\\(.*?\\\)", " MATH ", t, flags=re.S)
    else:
        t = MATH_INLINE_RE.sub(" ", t)
    t = CMD_RE.sub(" ", t)
    t = re.sub(r"[{}~]", " ", t)
    words = [w for w in t.split() if any(ch.isalnum() for ch in w)]
    return len(words)


def find_title(tex: str) -> str:
    i = tex.find("\\title")
    if i < 0:
        return ""
    j = tex.find("{", i)
    return balanced_group(tex, j)[0].strip() if j >= 0 else ""


def cite_keys(tex: str) -> set[str]:
    keys: set[str] = set()
    for m in CITE_RE.finditer(tex):
        for k in m.group(1).split(","):
            k = k.strip()
            if k:
                keys.add(k)
    return keys


def ref_keys(tex: str) -> set[str]:
    return {m.group(1).strip() for m in REF_RE.finditer(tex) if m.group(1).strip()}


def label_keys(tex: str) -> set[str]:
    return {m.group(1).strip() for m in LABEL_RE.finditer(tex) if m.group(1).strip()}


def bibitem_keys(tex: str) -> list[str]:
    return [m.group(1).strip() for m in BIBITEM_RE.finditer(tex)]


def bib_file_keys(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [m.group(1).strip() for m in BIB_KEY_RE.finditer(read_text(path))]


def section_titles(tex: str) -> list[str]:
    out = []
    for m in SECTION_RE.finditer(tex):
        i = tex.find("{", m.end() - 1)
        body = balanced_group(tex, i)[0]
        body = CMD_RE.sub(" ", body)
        body = re.sub(r"[{}]", " ", body)
        out.append(re.sub(r"\s+", " ", body).strip())
    return out


def declaration_positions(tex: str, declarations: list[str]) -> dict[str, int]:
    low = tex.lower()
    return {d: low.find(d.lower()) for d in declarations}


def bibliography_position(tex: str) -> int:
    positions = [p for p in (tex.find("\\begin{thebibliography}"),
                             tex.find("\\bibliography{"), tex.find("\\printbibliography"))
                 if p >= 0]
    return min(positions) if positions else -1


def placeholders(text: str) -> list[str]:
    hits = []
    for pat in (r"\bTODO\b", r"\bTBD\b", r"\bFIXME\b", r"\bXXX\b", r"\[\?\]",
                r"\(\?\)", r"\?\?", r"lorem ipsum", r"待补", r"待填", r"占位"):
        hits.extend(m.group(0) for m in re.finditer(pat, text, re.I))
    return hits


def cjk_hits(text: str) -> list[str]:
    return [m.group(0) for m in CJK_RE.finditer(text)]


def duplicate_sentences(text: str, min_words: int = 15) -> list[str]:
    t = CMD_RE.sub(" ", text)
    t = re.sub(r"[{}$]", " ", t)
    t = re.sub(r"\s+", " ", t)
    sentences = re.split(r"(?<=[.!?])\s+", t)
    seen: dict[str, int] = {}
    dupes = []
    for s in sentences:
        words = s.split()
        if len(words) < min_words:
            continue
        norm = re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()
        norm = re.sub(r"\s+", " ", norm)
        if not norm:
            continue
        seen[norm] = seen.get(norm, 0) + 1
        if seen[norm] == 2:
            dupes.append(s.strip()[:160])
    return dupes


def strip_tex_for_text(text: str) -> str:
    """Plain-ish text used for claim comparisons (not for PDF checks)."""
    t = strip_comments(text)
    t = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", t)
    t = t.replace("{", " ").replace("}", " ").replace("$", " ")
    return re.sub(r"\s+", " ", t)


def keywords_line(tex: str) -> list[str]:
    m = re.search(r"(?im)^\s*\\noindent\s*\\textbf\{Keywords:?\}\s*(.+)$", tex)
    if not m:
        m = re.search(r"(?i)\bKeywords?\b\s*[:---]\s*(.+)", tex)
    if not m:
        return []
    line = m.group(1)
    line = re.sub(r"\\\\\s*$", "", line).strip()
    parts = re.split(r"[;,]\s*", line.replace("\\\\sep", ";"))
    return [re.sub(r"\s+", " ", p).strip() for p in parts if p.strip()]


DOI_RE = re.compile(r"10\.\d{4,9}/[^\s,;\]\)\}\\]+")


def doi_strings(text: str) -> list[str]:
    out = []
    for m in DOI_RE.finditer(text):
        d = m.group(0).rstrip(".,;")
        out.append(d)
    return out
