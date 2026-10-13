"""Query Crossref for the A23 bibliography entries that carry no DOI.
Prints candidate matches for HUMAN verification. It never writes a DOI into
the manuscript: fabrication risk is unacceptable, so this only reports.

Network: api.crossref.org (no key needed). Polite: mailto in the query.
"""
import json
import time
import urllib.parse
import urllib.request

MAILTO = "contact@example.com"

# key -> (query string, what we expect, current locator in the manuscript)
TARGETS = [
    ("liang2022", "Mind the gap understanding the modality gap in multi-modal contrastive representation learning", "NeurIPS 2022"),
    ("levi2025", "The double-ellipsoid geometry of CLIP", "ICML 2025"),
    ("mistretta2025", "Cross the gap exposing the intra-modal misalignment in CLIP via modality inversion", "ICLR 2025"),
    ("yamaguchi2025", "Post-pre-training for modality alignment in vision-language foundation models", "CVPR 2025"),
    ("sofer2025", "Pull it together reducing the modality gap in contrastive learning", "Interspeech 2025"),
    ("chowers2026", "Is the modality gap a bug or a feature A robustness perspective", "CVPR 2026"),
    ("grassucci2026", "Closing the modality gap aligns group-wise semantics", "ICLR 2026"),
    ("wortsman2022", "Robust fine-tuning of zero-shot models", "CVPR 2022"),
    ("biderman2024", "LoRA learns less and forgets less", "TMLR 2024"),
    ("radford2021", "Learning transferable visual models from natural language supervision", "ICML 2021"),
]


def query(q):
    url = ("https://api.crossref.org/works?rows=3&select=DOI,title,type,issued,"
           "container-title,event&mailto=" + urllib.parse.quote(MAILTO)
           + "&query.bibliographic=" + urllib.parse.quote(q))
    req = urllib.request.Request(url, headers={"User-Agent": f"A23-doi-audit/1.0 (mailto:{MAILTO})"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))


def shorten(s, n=92):
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "\u2026"


out = []
for key, q, expect in TARGETS:
    out.append("=" * 100)
    out.append(f"{key}   expected venue: {expect}")
    out.append(f"  query: {q}")
    try:
        data = query(q)
        items = data.get("message", {}).get("items", [])
        if not items:
            out.append("  NO CANDIDATES RETURNED")
        for it in items:
            title = (it.get("title") or ["<no title>"])[0]
            cont = (it.get("container-title") or ["<none>"])[0]
            year = ""
            try:
                year = it["issued"]["date-parts"][0][0]
            except Exception:
                pass
            out.append(f"  - DOI: {it.get('DOI')}")
            out.append(f"      title: {shorten(title)}")
            out.append(f"      type={it.get('type')}  year={year}  container={shorten(cont, 70)}")
    except Exception as e:
        out.append(f"  QUERY FAILED: {type(e).__name__}: {e}")
    time.sleep(0.6)

report = "\n".join(out)
with open(r"D:\Realdesktop\Wan\Important\New\outputs\_a23_doi_candidates.txt", "w", encoding="utf-8") as f:
    f.write(report)
print(report)
