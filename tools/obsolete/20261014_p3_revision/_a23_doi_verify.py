"""1) Re-query Crossref for wortsman2022 with a title-scoped search.
   2) Verify resolvability of every DOI planned for the final bibliography.
Prints a table; writes nothing into the manuscript."""
import json
import urllib.error
import urllib.parse
import urllib.request

MAILTO = "hw4c24@soton.ac.uk"
UA = {"User-Agent": f"A23-doi-verify/1.0 (mailto:{MAILTO})"}


def crossref_title(q, rows=5):
    url = ("https://api.crossref.org/works?rows=%d&select=DOI,title,type,issued,container-title"
           "&mailto=%s&query.title=%s" % (rows, urllib.parse.quote(MAILTO), urllib.parse.quote(q)))
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())["message"]["items"]


print("### STEP 1: targeted re-query for wortsman2022")
for q in ["Robust fine-tuning of zero-shot models",
          "Robust fine-tuning of zero-shot models Wortsman Ilharco"]:
    print(f"\n-- query.title = {q!r}")
    try:
        for it in crossref_title(q):
            t = (it.get("title") or ["?"])[0]
            c = (it.get("container-title") or ["?"])[0]
            y = ""
            try:
                y = it["issued"]["date-parts"][0][0]
            except Exception:
                pass
            print(f"   {it.get('DOI')}\n     {t[:95]}\n     type={it.get('type')} year={y} cont={c[:60]}")
    except Exception as e:
        print("   FAILED:", e)

PLANNED = [
    ("chen2025", "10.1145/3759243"),
    ("jian2024", "10.1007/s44295-024-00023-6"),
    ("qin2022", "10.3390/rs14153794"),
    ("aquaticclip2026", "10.1109/TNNLS.2026.3657138"),
    ("marinegpt2023", "10.48550/arXiv.2310.13596"),
    ("oceangpt2023", "10.18653/v1/2024.acl-long.184"),
    ("liang2022", "10.52202/068431-1280"),
    ("yi2025", "10.48550/arXiv.2510.03268"),
    ("yamaguchi2025", "10.1109/CVPR52734.2025.00402"),
    ("sofer2025", "10.21437/Interspeech.2025-1664"),
    ("christensen2026", "10.1016/j.oceaneng.2026.124646"),
    ("maione2026", "10.1016/j.oceaneng.2026.127078"),
    ("uatd2022", "10.1038/s41597-022-01854-w"),
    ("s3simulator2024", "10.1007/978-3-031-78444-6_15"),
    ("sonarsurvey2025", "10.48550/arXiv.2510.03353"),
    ("aubard2025", "10.1109/JOE.2025.3531933"),
]

print("\n\n### STEP 2: DOI resolvability check (HEAD https://doi.org/<doi>)")
for key, doi in PLANNED:
    url = "https://doi.org/" + urllib.parse.quote(doi)
    status = "?"
    final = ""
    try:
        req = urllib.request.Request(url, headers=UA, method="HEAD")
        with urllib.request.urlopen(req, timeout=35) as r:
            status = r.status
            final = r.geturl()
    except urllib.error.HTTPError as e:
        status = f"HTTP{e.code}"
        final = getattr(e, "url", "")
    except Exception as e:
        status = f"{type(e).__name__}"
    ok = "OK " if str(status) in ("200", "302", "303") else "!! "
    print(f"{ok}{key:20s} {doi:38s} {status}  -> {final[:78]}")
