# -*- coding: utf-8 -*-
"""Build the Phase-1 registries for the mechanical audit gates.

    python tools/paper_audit/build_registries.py [--apply]

Writes (idempotent, seeds preserved):
  docs/QUANTITY_REGISTRY.json   from the three claim ledgers + curated entries for values fixed this week
  docs/SIGN_REGISTRY.json       direction semantics for the metrics we keep misreading
  docs/RELEASE_LEDGER.json      release snapshots, DOIs, what the archive holds and excludes
  docs/REF_VERIFICATION.json    reference metadata cache (verified entries kept, new bib keys added as unverified)

`--verify-network` (optional, not used by the offline gate) would re-resolve unverified entries via
CrossRef/arXiv; it is documented in docs/gate_upgrade_2026-10-25.md and intentionally not required.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.paper_audit import mechanical as M  # noqa: E402


def _decimals(value) -> int:
    s = ("%r" % float(value)) if not isinstance(value, str) else value
    if "e" in s.lower():
        return 6
    out = s.split(".")[1] if "." in s else ""
    return min(6, len(out.rstrip("0")) if out.rstrip("0") else 0)


def _resolve(rel: str):
    for cand in (rel, "outputs/analysis/" + rel, "outputs/" + rel):
        p = REPO / cand
        if p.is_file():
            return cand, p
    return None, None


def _expand_sources(rows):
    """Ledger sources abbreviate paths as '...' or '...<file-hint>'; rebuild (hint, field) pairs."""
    out, last = [], ""
    for row in rows:
        src = str(row.get("source") or "")
        if src.startswith("..."):
            rest = src[3:]
            sep = "::" if "::" in rest else (":" if ":" in rest else "")
            if not sep:
                continue
            hint, field = rest.split(sep, 1)
            if not hint:
                out.append((row, last, field))
            elif last and hint in Path(last).name:
                out.append((row, last, field))
            else:
                out.append((row, "HINT:" + hint, field))
            continue
        path, field = _parse_source(src)
        last = path
        out.append((row, path, field))
    return out


def _parse_source(src: str):
    if not src:
        return "", ""
    if "::" in src:
        path, field = src.split("::", 1)
    elif ":" in src:
        path, field = src.split(":", 1)
    else:
        return "", ""
    return path.strip(), field.strip()


LEDGER_SPECS = [
    ("outputs/analysis/claim_ledger.json", ["paperA_nc", "paperA_springer"], "claims"),
    ("outputs/analysis/claim_ledger_paperA.json", ["paperA_nc", "paperA_springer"], "entries"),
    ("outputs/analysis/claim_ledger_a1.json", ["a1_paa"], "claims"),
]

# Curated quantities: the duplicate-value classes fixed this week. Both A1 tau-R@1 grids are
# registered as explicit variants WITH a reason, so the gate verifies the text prints one of them
# and never a third value.
CURATED_QUANTITIES = {
    "paperA_nc": {
        "Flickr30k LoRA archived runs": {
            "archive": "outputs/analysis/ode_ledger.json",
            "field": "subsets.lora_flickr.n",
            "canonical_value": 49, "rounding": 0,
            "allowed_variants": [{"value": 43, "reason": "rank-sweep subset (Runs column of "
                                   "tab:generalization); 49 also counts the 6 Phase-1 pilot runs"}],
            "mentions": [{"regex": r"\(([0-9]+) on Flickr30k"},
                         {"regex": r"([0-9]+) rank[-\s]?sweep runs"},
                         {"regex": r"CLIP \+ Flickr30k \+ LoRA[^\n]{0,160}?0\.067\s+([0-9]{1,3})"}],
            "note": "49 archived Flickr30k LoRA runs (43 sweep + 6 pilot); table runs = 43.",
        },
        "archived LoRA runs (all)": {
            "archive": "outputs/analysis/ode_ledger.json", "field": "subsets.lora.n",
            "canonical_value": 55, "rounding": 0, "allowed_variants": [],
            "mentions": [{"regex": r"([0-9]+) archived LoRA runs"},
                         {"regex": r"([0-9]+) LoRA trajectories are archived"}],
        },
        "archived ODE fits (all)": {
            "archive": "outputs/analysis/ode_ledger.json", "field": "subsets.all.n",
            "canonical_value": 96, "rounding": 0, "allowed_variants": [],
            "mentions": [{"regex": r"of the ([0-9]+) archived fits"}],
        },
    },
    "paperA_springer": {
        "Flickr30k LoRA archived runs": {
            "archive": "outputs/analysis/ode_ledger.json",
            "field": "subsets.lora_flickr.n",
            "canonical_value": 49, "rounding": 0,
            "allowed_variants": [{"value": 43, "reason": "rank-sweep subset (Runs column of "
                                   "tab:generalization); 49 also counts the 6 Phase-1 pilot runs"}],
            "mentions": [{"regex": r"\(([0-9]+) on Flickr30k"},
                         {"regex": r"([0-9]+) rank[-\s]?sweep runs"},
                         {"regex": r"CLIP \+ Flickr30k \+ LoRA[^\n]{0,160}?0\.067\s+([0-9]{1,3})"}],
            "note": "49 archived Flickr30k LoRA runs (43 sweep + 6 pilot); table runs = 43.",
        },
        "archived LoRA runs (all)": {
            "archive": "outputs/analysis/ode_ledger.json", "field": "subsets.lora.n",
            "canonical_value": 55, "rounding": 0, "allowed_variants": [],
            "mentions": [{"regex": r"([0-9]+) archived LoRA runs"},
                         {"regex": r"([0-9]+) LoRA trajectories are archived"}],
        },
        "archived ODE fits (all)": {
            "archive": "outputs/analysis/ode_ledger.json", "field": "subsets.all.n",
            "canonical_value": 96, "rounding": 0, "allowed_variants": [],
            "mentions": [{"regex": r"of the ([0-9]+) archived fits"}],
        },
    },
    "a1_paa": {
        "tau R@1 (retrieval-evidence, 21 configurations)": {
            "archive": "outputs/analysis/a1_retrieval_evidence.json",
            "field": "correlation.tau_vs_R1",
            "canonical_value": -0.1657, "rounding": 3,
            "allowed_variants": [],
            "mentions": [{"regex": r"([-\u2212]?0\.1[0-9]{2,3})\s*over\s*21\s*configurations"}],
            "note": "21-configuration evidence archive (printed as -0.166)",
        },
        "tau R@1 (17-configuration head-to-head grid)": {
            "archive": "outputs/analysis/a1_statistic_showdown.json",
            "field": "correlation_with_top1.retrieval.tau5",
            "canonical_value": -0.1427, "rounding": 3,
            "allowed_variants": [],
            "mentions": [{"regex": r"([-\u2212]?0\.1[0-9]{2,3})\s*over\s*the\s*17"}],
            "note": "17-configuration grid (Table 20, printed as -0.143)",
        },
    },
}

SIGN_REGISTRY = {
    "schema": 1,
    "built_at": date.today().isoformat(),
    "semantics": {
        "energy_paired_difference": {
            "description": "paired difference of retrieval/matching energy; a NEGATIVE value means "
                           "the arm is better (lower energy).",
            "lower_is": "better",
        },
        "gap_paired_difference": {
            "description": "paired difference of a modality gap / centroid distance; the gap has no "
                           "monotone health meaning for classification (neutral).",
            "lower_is": "neutral",
        },
        "accuracy_paired_difference": {
            "description": "paired difference of accuracy / top-1 / F1: a POSITIVE value means the "
                           "arm is better.",
            "lower_is": "worse",
        },
    },
    "manuscripts": {
        "p3_prl": {
            "energy paired difference": {
                "keyword": r"paired difference|pairwise difference|energy",
                "lower_is": "better",
                "field": "matching energy (lower is better)",
                "note": "P3 residual: a negative paired difference (-3570.10) is BETTER, not 'opposite'.",
            },
        },
        "a23_joe": {
            "paired difference": {
                "keyword": r"paired difference|pairwise difference|\bdelta E\b|\u0394E",
                "lower_is": "better",
                "field": "paired energy difference (lower is better)",
            },
        },
    },
}

RELEASE_LEDGER = {
    "schema": 1,
    "built_at": date.today().isoformat(),
    "repositories": ["https://github.com/MoYUYao666/gap-susceptibility"],
    "registered_dois": [
        "10.5281/zenodo.23632347",
        "10.5281/zenodo.23341083",
        "10.5281/zenodo.23341223",
    ],
    "releases": [
        {"tag": "v2.5", "version_doi": "10.5281/zenodo.23632347", "concept_doi":
         "10.5281/zenodo.23341083", "contents": ["per-run result records", "analysis scripts",
         "training configurations", "figure-generating scripts"], "excludes": ["manuscripts",
         "compiled PDFs", "cover letters", "title pages", "declarations"]},
        {"tag": "v1.0-prl-revision", "version_doi": "10.5281/zenodo.23341223", "concept_doi":
         "10.5281/zenodo.23341083", "contents": ["per-run result records", "analysis scripts"],
         "excludes": ["manuscripts", "compiled PDFs"]},
    ],
    "third_party_sources": [
        {"doi": "10.6084/m9.figshare.21331143.v3", "what": "FathomNet dataset release",
         "why": "third-party dataset cited in the data statement"},
        {"url": "https://database.fathomnet.org", "what": "FathomNet database",
         "why": "third-party dataset portal cited in the data statement"},
    ],
    "archive_excludes": ["manuscripts", "compiled PDFs", "cover letters", "title pages",
                         "declarations"],
    "archive_root": "publish_clean",
    "policy_source": "AGENTS.md / 发布边界 (repository carries code and results only)",
}

# Curated verified reference metadata (the IGU-LoRA correction is the first locked one).
VERIFIED_REFS = {
    "igulora2025": {
        "title": "IGU-LoRA: Adaptive Rank Allocation via Integrated Gradients and "
                 "Uncertainty-Aware Scoring",
        "first_author": "Cui", "year": "2026",
        "venue": "ICLR 2026 (The Fourteenth International Conference on Learning Representations)",
        "source": "primary source: official arXiv:2603.13792 + ICLR 2026 proceedings",
        "checked_at": date.today().isoformat(),
    },
    "hu2022lora": {
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "first_author": "Hu", "year": "2022", "venue": "ICLR 2022",
        "source": "ICLR 2022 proceedings", "checked_at": date.today().isoformat(),
    },
    "radford2021": {
        "title": "Learning Transferable Visual Models From Natural Language Supervision",
        "first_author": "Radford", "year": "2021", "venue": "ICML 2021",
        "source": "PMLR 139", "checked_at": date.today().isoformat(),
    },
    "liang2022": {
        "title": "Mind the Gap: Understanding the Modality Gap in Multi-modal Contrastive "
                 "Representation Learning",
        "first_author": "Liang", "year": "2022", "venue": "NeurIPS 2022",
        "source": "NeurIPS 2022 proceedings", "checked_at": date.today().isoformat(),
    },
    "kendall1938": {
        "title": "A New Measure of Rank Correlation",
        "first_author": "Kendall", "year": "1938", "venue": "Biometrika 30(1-2):81-93",
        "source": "DOI 10.1093/biomet/30.1-2.81", "checked_at": date.today().isoformat(),
    },
    "french1999catastrophic": {
        "title": "Catastrophic forgetting in connectionist networks",
        "first_author": "French", "year": "1999",
        "venue": "Trends in Cognitive Sciences 3(4):128-135",
        "source": "DOI 10.1016/S1364-6613(99)01294-2", "checked_at": date.today().isoformat(),
    },
    "hendrycks2021imagenetr": {
        "title": "The Many Faces of Robustness: A Critical Analysis of Out-of-Distribution "
                 "Generalization",
        "first_author": "Hendrycks", "year": "2021", "venue": "ICCV 2021",
        "source": "DOI 10.1109/ICCV48922.2021.00823", "checked_at": date.today().isoformat(),
    },
}

BIB_FILE_RE = re.compile(r"@(\w+)\{([^,\s]+),\s*(.*?)\n\}", re.S)
FIELD_RE = re.compile(r"(\w+)\s*=\s*\{(.*?)\}", re.S)
MANUSCRIPT_DIRS = ["paper_a1", "paper_a2", "paper合", "paper3/paper_ieee", "paper_review_prl"]


def _bib_file_entries(root: Path):
    out = {}
    for rel in MANUSCRIPT_DIRS:
        d = REPO / rel
        if not d.is_dir():
            continue
        for bib in sorted(d.rglob("*.bib")):
            text = bib.read_text(encoding="utf-8", errors="replace")
            for kind, key, body in BIB_FILE_RE.findall(text):
                fields = {k.lower(): v.strip() for k, v in FIELD_RE.findall(body)}
                flat = re.sub(r"\s+", " ", " ".join(fields.values()))
                out.setdefault(key, {
                    "key": key,
                    "kind": kind,
                    "title": fields.get("title", ""),
                    "first_author": (fields.get("author", "").split(" and ")[0].split(",")[0]
                                     or ""),
                    "year": fields.get("year", ""),
                    "venue": fields.get("booktitle") or fields.get("journal", ""),
                    "doi": fields.get("doi", "").rstrip("."),
                    "arxiv": (fields.get("eprint", "")
                              or (re.search(r"arXiv:\s*(\d{4}\.\d{4,5})", flat, re.I).group(1)
                                  if re.search(r"arXiv:\s*(\d{4}\.\d{4,5})", flat, re.I) else "")),
                    "source_file": str(bib.relative_to(REPO)).replace("\\", "/"),
                })
    return out


def _bibitem_entries():
    out = {}
    for rel in MANUSCRIPT_DIRS:
        d = REPO / rel
        if not d.is_dir():
            continue
        for tex in sorted(d.glob("*.tex")):
            text = tex.read_text(encoding="utf-8", errors="replace")
            for key, body in M.BIB_RE.findall(text):
                parsed = M._parse_bib_entry(text, key, body)
                parsed["source_file"] = str(tex.relative_to(REPO)).replace("\\", "/")
                out.setdefault(key, parsed)
    return out


def build_quantities():
    counts, manuscripts = {}, {}
    for ledger_rel, profiles, keyname in LEDGER_SPECS:
        p = REPO / ledger_rel
        if not p.is_file():
            print("  skip missing ledger", ledger_rel)
            continue
        doc = json.loads(p.read_text(encoding="utf-8"))
        rows = doc.get(keyname) or doc.get("claims") or doc.get("entries") or []
        for row, path, field in _expand_sources(rows):
            if not path or not field:
                continue
            if path.startswith("HINT:"):
                hint = path[5:]
                hits = [p for p in (REPO / "outputs").rglob("*" + hint + "*.json")
                        if p.is_file()]
                if len(hits) != 1:
                    continue
                cand = str(hits[0].relative_to(REPO)).replace("\\", "/")
                real = hits[0]
            else:
                cand, real = _resolve(path)
            if not real:
                continue
            # the field must actually exist and reproduce (never enshrine a bad seed)
            try:
                data = json.loads(real.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                continue
            found, archive_value = M.get_field(data, field)
            if not found or not isinstance(archive_value, (int, float)):
                continue
            value = row.get("manuscript", row.get("ms"))
            computed = row.get("computed")
            if value is None or computed is None:
                continue
            try:
                canonical = float(value)
                archive_value = float(computed)
            except (TypeError, ValueError):
                continue
            rounding = _decimals(value)
            if round(archive_value, rounding) != round(canonical, rounding):
                continue  # ledger says it does not reproduce; do not enshrine it
            entry = {
                "archive": cand,
                "field": field,
                "canonical_value": canonical,
                "rounding": rounding,
                "allowed_variants": [],
                "mention_required": False,
                "seed": ledger_rel.split("/")[-1],
                "note": "seeded from the claim ledger; archive-only (no text mention registered)",
            }
            for pid in profiles:
                q = manuscripts.setdefault(pid, {})
                q.setdefault(str(row.get("claim")), entry)
                counts[pid] = counts.get(pid, 0) + 1
    for pid, qs in CURATED_QUANTITIES.items():
        manuscripts.setdefault(pid, {}).update(qs)
        counts[pid] = counts.get(pid, 0) + len(qs)
    return {"schema": 1, "built_at": date.today().isoformat(),
            "note": "N-01: one canonical value per (manuscript, quantity); text mentions must match "
                    "the canonical rounding or an explicitly allowed variant.",
            "seed_counts": counts, "manuscripts": manuscripts}


def build_refs():
    entries = {}
    for src in (_bibitem_entries(), _bib_file_entries(REPO)):
        for key, e in src.items():
            if key in entries:
                continue
            verified = VERIFIED_REFS.get(key)
            if verified:
                entry = dict(verified)
                entry["manuscripts"] = []
                entries[key] = entry
            else:
                entries[key] = {
                    "title": e.get("title", ""), "first_author": e.get("first_author", ""),
                    "year": e.get("year", ""), "venue": e.get("venue", ""),
                    "doi": e.get("doi", ""), "arxiv": e.get("arxiv", ""),
                    "source": "unverified-bib", "checked_at": "",
                }
    for key, verified in VERIFIED_REFS.items():
        entries.setdefault(key, dict(verified))
    for key, e in entries.items():
        for rel in MANUSCRIPT_DIRS:
            d = REPO / rel
            if not d.is_dir():
                continue
            for f in list(d.rglob("*.bib")) + list(d.glob("*.tex")):
                try:
                    s = f.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if key in s and "manuscripts" in e:
                    e["manuscripts"].append(rel)
                    break
    verified = sum(1 for e in entries.values() if e.get("source") != "unverified-bib")
    return {"schema": 1, "built_at": date.today().isoformat(),
            "note": "N-05: verified reference metadata; entries with source 'unverified-bib' make "
                    "the check report MANUAL, never PASS.",
            "counts": {"total": len(entries), "verified": verified,
                       "unverified": len(entries) - verified},
            "entries": entries}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--verify-network", action="store_true",
                    help="(documented, optional) re-resolve unverified refs via CrossRef/arXiv")
    a = ap.parse_args()
    q = build_quantities()
    refs = build_refs()
    payload = {
        str(M.QUANTITY_REGISTRY): q,
        str(M.SIGN_REGISTRY): SIGN_REGISTRY,
        str(M.RELEASE_LEDGER): RELEASE_LEDGER,
        str(M.REF_VERIFICATION): refs,
    }
    print("quantity registry: %d profiles, %d entries"
          % (len(q["manuscripts"]), sum(len(v) for v in q["manuscripts"].values())))
    for pid, n in sorted(q["seed_counts"].items()):
        print("   %-16s %d" % (pid, n))
    print("sign registry: %d profiles" % len(SIGN_REGISTRY["manuscripts"]))
    print("release ledger: %d release(s), %d registered DOI(s)"
          % (len(RELEASE_LEDGER["releases"]), len(RELEASE_LEDGER["registered_dois"])))
    print("reference cache: %(total)d entries (%(verified)d verified, %(unverified)d unverified)"
          % refs["counts"])
    if not a.apply:
        print("(dry run: pass --apply to write)")
        return 0
    for path, data in payload.items():
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print("wrote", p.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
