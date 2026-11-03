# -*- coding: utf-8 -*-
r"""Bibliometric analysis of the survey corpus for the GRSM rewrite.

Reads the archived literature records (verified/de-duplicated harvests, screened core, abstracts and the disclosure
audit) and writes `paper_rsvlm_survey/analysis/trends_2026-11.json` plus two figures used by the rewritten survey:

  fig_trends_volume.pdf   - publications per year by task theme, 2019-2026
  fig_trends_datasets.pdf - dataset reuse counts in the screened abstracts and the audit compliance profile

Every number quoted in the rewritten sections comes from this script's JSON output; nothing is typed by hand.

Usage
  python paper_rsvlm_survey/scripts/analyse_corpus_trends.py
"""
import io
import json
import os
import re
import statistics

import matplotlib as mpl
mpl.use("Agg")
mpl.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "axes.unicode_minus": False,
    "font.size": 9,
})
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIT = os.path.join(ROOT, "literature")
OUT = os.path.join(ROOT, "analysis")
FIG = os.path.join(ROOT, "figures")

THEMES = {
    "retrieval": ("retrieval", "image-text", "cross-modal retrieval", "text-image"),
    "captioning": ("caption", "description generation"),
    "vqa/instruction": ("question answering", "vqa", "instruction", "grounding", "grounded"),
    "pretraining": ("clip", "pre-training", "pretraining", "contrastive"),
    "datasets/benchmarks": ("dataset", "benchmark", "corpus"),
    "general VLM": ("vision-language", "vision language", "multimodal", "foundation"),
}


def load(name):
    p = os.path.join(LIT, name) if not name.startswith("screening") else os.path.join(ROOT, name)
    return json.loads(io.open(p, encoding="utf-8").read())


def theme_of(record):
    """Assign each record the theme that matches the most of its harvest queries (ties by declaration order)."""
    queries = [q.lower() for q in (record.get("found_by") or [])]
    scores = {}
    for theme, keys in THEMES.items():
        scores[theme] = sum(1 for q in queries if any(k in q for k in keys))
    best = max(scores.values())
    if best == 0:
        return "other"
    for theme in THEMES:
        if scores[theme] == best:
            return theme
    return "other"


def volume_by_year(records):
    out = {}
    for r in records.values():
        y = r.get("year")
        if not isinstance(y, int) or y < 2019:
            continue
        out.setdefault(y, {}).setdefault(theme_of(r), 0)
        out[y][theme_of(r)] += 1
    return out


def venue_distribution(records, top=10):
    counts = {}
    for r in records.values():
        v = (r.get("venue") or "").strip() or "unknown"
        counts[v] = counts.get(v, 0) + 1
    return sorted(counts.items(), key=lambda kv: -kv[1])[:top]


def citation_profile(records):
    by_year = {}
    allc = []
    for r in records.values():
        c = r.get("cited_by") or 0
        allc.append(c)
        y = r.get("year")
        if isinstance(y, int):
            by_year.setdefault(y, []).append(c)
    med = {str(y): statistics.median(v) for y, v in sorted(by_year.items())}
    allc.sort(reverse=True)
    top10_share = sum(allc[: max(1, len(allc) // 10)]) / max(1, sum(allc))
    return {"median_by_year": med, "top10_share_of_citations": round(top10_share, 3),
            "records": len(allc), "total_citations": sum(allc)}


DATASET_PATTERNS = {
    "RSICD": r"rsicd",
    "RSITMD": r"rsitmd",
    "NWPU-Captions": r"nwpu[- ]?captions?",
    "UCM-Captions": r"ucm[- ]?captions?",
    "Sydney-Captions": r"sydney[- ]?captions?",
    "AID": r"\baid\b",
    "DIOR": r"\bdior\b",
    "RS5M": r"rs5m",
    "RSICap": r"rsicap",
    "LEVIR-CC": r"levir",
}


def dataset_reuse(abstracts):
    counts = {k: 0 for k in DATASET_PATTERNS}
    matched = 0
    for rec in abstracts.values():
        text = ((rec.get("title") or "") + " " + (rec.get("abstract") or "")).lower()
        hit = False
        for name, pat in DATASET_PATTERNS.items():
            if re.search(pat, text):
                counts[name] += 1
                hit = True
        if hit:
            matched += 1
    return {"n_abstracts": len(abstracts), "n_with_dataset_mention": matched, "counts": counts}


def audit_profile():
    d = load("disclosure_audit_2026-10-28.json")
    items = ["repeated runs", "dispersion", "compute disclosure", "cross-region evaluation"]
    counts = {it: sum(1 for p in d["papers"] if p["items"][it]["verdict"]) for it in items}
    return {"n_papers": d["n_papers"], "reported": counts}


def figure_volume(vol, path):
    years = sorted(vol)
    themes = ["retrieval", "captioning", "vqa/instruction", "pretraining", "datasets/benchmarks", "general VLM", "other"]
    colors = {"retrieval": "#264653", "captioning": "#2a9d8f", "vqa/instruction": "#e9c46a",
              "pretraining": "#f4a261", "datasets/benchmarks": "#e76f51", "general VLM": "#8d99ae", "other": "#bbbbbb"}
    fig, ax = plt.subplots(figsize=(6.4, 3.0), dpi=300)
    bottom = [0] * len(years)
    for t in themes:
        vals = [vol[y].get(t, 0) for y in years]
        ax.bar([str(y) for y in years], vals, bottom=bottom, color=colors[t], label=t, width=0.72)
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_ylabel("records in the verified corpus")
    ax.legend(fontsize=7, ncol=2, frameon=False, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout(pad=0.3)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def figure_datasets(reuse, audit, path):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8), dpi=300, gridspec_kw={"width_ratios": [1.5, 1]})
    ax = axes[0]
    items = sorted(reuse["counts"].items(), key=lambda kv: -kv[1])
    names = [k for k, v in items if v > 0]
    vals = [v for k, v in items if v > 0]
    ax.barh(names[::-1], vals[::-1], color="#2a9d8f")
    ax.set_xlabel("abstracts mentioning the dataset")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("(a) dataset reuse in screened abstracts", fontsize=8, loc="left")
    ax = axes[1]
    items = list(audit["reported"].items())
    ax.bar([i.replace(" ", "\n") for i, _ in items], [v for _, v in items], color="#e76f51")
    ax.set_ylim(0, audit["n_papers"])
    ax.set_ylabel("papers reporting the item")
    ax.set_title("(b) disclosure audit of %d papers" % audit["n_papers"], fontsize=8, loc="left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", labelsize=6.5)
    fig.tight_layout(pad=0.3)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(FIG, exist_ok=True)
    verified = load("verified_2026-10-27.json")
    dedup = load("dedup_2026-10-27.json")
    abstracts = load("abstracts_2026-10-27.json")
    screening = load("screening/core_2026-10-27.json")

    vol = volume_by_year(verified)
    venues = venue_distribution(verified)
    cites = citation_profile(verified)
    reuse = dataset_reuse(abstracts)
    audit = audit_profile()
    screened = {k: len(v) for k, v in screening.items()}

    result = {
        "generated": "2026-11-02",
        "source_records": {"verified": len(verified), "deduplicated": len(dedup), "abstracts": len(abstracts)},
        "volume_by_year_theme": {str(y): vol[y] for y in sorted(vol)},
        "year_totals": {str(y): sum(vol[y].values()) for y in sorted(vol)},
        "top_venues": [{"venue": v, "records": n} for v, n in venues],
        "citations": cites,
        "dataset_reuse": reuse,
        "disclosure_audit": audit,
        "screened_core": screened,
        "notes": "Themes assigned from the harvest queries recorded in found_by; a record may match several themes and "
                 "is assigned the first match in the order retrieval, captioning, vqa/instruction, pretraining, "
                 "datasets/benchmarks.",
    }
    io.open(os.path.join(OUT, "trends_2026-11.json"), "w", encoding="utf-8", newline="").write(
        json.dumps(result, indent=1))
    figure_volume(vol, os.path.join(FIG, "fig_trends_volume.pdf"))
    figure_datasets(reuse, audit, os.path.join(FIG, "fig_trends_datasets.pdf"))
    # era shares for the trends text
    early, late = {}, {}
    for y, themes in vol.items():
        target = early if int(y) <= 2022 else late
        for k, v in themes.items():
            target[k] = target.get(k, 0) + v
    def share(d, key):
        tot = sum(d.values()) or 1
        return 100.0 * d.get(key, 0) / tot
    era = {"early": early, "late": late}

    # macro file consumed by the rewritten survey sections
    yr = result["year_totals"]
    ven = result["top_venues"]
    lines = [
        "% Generated by paper_rsvlm_survey/scripts/analyse_corpus_trends.py - do not edit by hand.",
        r"\newcommand{\trrecords}{%d}" % len(verified),
        r"\newcommand{\trdedup}{%d}" % len(dedup),
        r"\newcommand{\trabstracts}{%d}" % len(abstracts),
        r"\newcommand{\tryearfirst}{%s}" % min(yr, key=lambda k: int(k)),
        r"\newcommand{\trvolfirst}{%d}" % yr[min(yr, key=lambda k: int(k))],
        r"\newcommand{\trvolpeak}{%d}" % max(yr.values()),
        r"\newcommand{\trvolpeakyear}{%s}" % max(yr, key=lambda k: yr[k]),
        r"\newcommand{\trvoltwentyfour}{%d}" % yr.get("2024", 0),
        r"\newcommand{\trvoltwentysix}{%d}" % yr.get("2026", 0),
        r"\newcommand{\trtopvenue}{%s}" % ven[0]["venue"].replace("&", "\&"),
        r"\newcommand{\trtopvenuerecords}{%d}" % ven[0]["records"],
        r"\newcommand{\trsecondvenue}{%s}" % ven[1]["venue"].replace("&", "\&"),
        r"\newcommand{\trsecondvenuerecords}{%d}" % ven[1]["records"],
        r"\newcommand{\trtopshare}{%.1f}" % (100 * cites["top10_share_of_citations"]),
        r"\newcommand{\trcitations}{%s}" % "{:,}".format(cites["total_citations"]).replace(",", "{,}"),
        r"\newcommand{\trauditpapers}{%d}" % audit["n_papers"],
        r"\newcommand{\trauditrepeat}{%d}" % audit["reported"]["repeated runs"],
        r"\newcommand{\trauditdispersion}{%d}" % audit["reported"]["dispersion"],
        r"\newcommand{\trauditcompute}{%d}" % audit["reported"]["compute disclosure"],
        r"\newcommand{\trauditregion}{%d}" % audit["reported"]["cross-region evaluation"],
        r"\newcommand{\trrsicd}{%d}" % reuse["counts"]["RSICD"],
        r"\newcommand{\trrsitmd}{%d}" % reuse["counts"]["RSITMD"],
        r"\newcommand{\trnwpu}{%d}" % reuse["counts"]["NWPU-Captions"],
        r"\newcommand{\trucm}{%d}" % reuse["counts"]["UCM-Captions"],
        r"\newcommand{\traid}{%d}" % reuse["counts"]["AID"],
        r"\newcommand{\trdatasetabstracts}{%d}" % reuse["n_abstracts"],
        r"\newcommand{\trdatasetmentions}{%d}" % reuse["n_with_dataset_mention"],
        r"\newcommand{\trcaptionearly}{%.0f}" % share(early, "captioning"),
        r"\newcommand{\trcaptionlate}{%.0f}" % share(late, "captioning"),
        r"\newcommand{\trvqaearly}{%.0f}" % share(early, "vqa/instruction"),
        r"\newcommand{\trvqalate}{%.0f}" % share(late, "vqa/instruction"),
        r"\newcommand{\trgeneralearly}{%.0f}" % share(early, "general VLM"),
        r"\newcommand{\trgenerallate}{%.0f}" % share(late, "general VLM"),
        r"\newcommand{\trpretrainearly}{%.0f}" % share(early, "pretraining"),
        r"\newcommand{\trpretrainlate}{%.0f}" % share(late, "pretraining"),
        r"\newcommand{\trotherlate}{%.0f}" % share(late, "other"),
    ]
    macros_dir = os.path.join(ROOT, "grrsm")
    os.makedirs(macros_dir, exist_ok=True)
    io.open(os.path.join(macros_dir, "trends_numbers.tex"), "w", encoding="utf-8", newline="").write("\n".join(lines) + "\n")
    print("wrote analysis/trends_2026-11.json, two figures and grrsm/trends_numbers.tex")
    print("year totals:", result["year_totals"])
    print("top venue:", venues[0] if venues else None)
    print("dataset reuse:", reuse["counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
