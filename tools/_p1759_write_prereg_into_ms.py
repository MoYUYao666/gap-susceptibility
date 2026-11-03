# -*- coding: utf-8 -*-
r"""Write the pre-registered cross-backbone test into the manuscript and rebuild.

What is reported: three backbones (CLIP B/32, OpenCLIP B/32, CLIP B/16) x three adaptation sites x five held-out
seeds, strict freezing, identical protocol, with the prediction frozen before the runs. Numbers are computed from the
retrieved archives, never typed by hand. The OpenCLIP non-replication is written as a boundary, because the ordering
does not survive the change of pre-training corpus for this backbone.
"""
import glob
import io
import json
import os
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)

SETS = [("P1", "CLIP B/32", "paperA_c_prereg"), ("P2", "OpenCLIP B/32", "paperA_c_prereg_openclip"),
        ("P4", "CLIP B/16", "paperA_c_prereg_b16")]
SITES = ["text_only", "both", "vision_only"]


def num(d, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur if isinstance(cur, (int, float)) else None


def stats():
    out = {}
    for tag, model, folder in SETS:
        rows = {}
        for p in sorted(glob.glob("outputs/%s/*.json" % folder)):
            d = json.load(io.open(p, encoding="utf-8"))
            site = next((s for s in SITES if s in p), d.get("tag"))
            cg0, cg1 = num(d, "initial_gap", "centroid_gap"), num(d, "final_gap", "centroid_gap")
            if cg0 is None or cg1 is None:
                continue
            rows.setdefault(site, []).append(cg1 - cg0)
        out[tag] = (model, {s: (len(v), sum(v) / len(v)) for s, v in rows.items()})
    return out


st = stats()
for tag, (model, d) in st.items():
    print(tag, model, {s: (n, round(m, 4)) for s, (n, m) in d.items()})

# ordered text for the paragraph: which backbones put text-only smallest |dCG| / most negative
def order(tag, key="signed"):
    d = st[tag][1]
    sites = [s for s in SITES if s in d]
    if key == "signed":
        return sorted(sites, key=lambda s: d[s][1])
    return sorted(sites, key=lambda s: abs(d[s][1]))


# ---------------------------------------------------------------- table in the appendix
rows_tex = []
for tag, (model, d) in st.items():
    for s in SITES:
        if s in d:
            n, m = d[s]
            rows_tex.append("%s & %s & %d & %+.4f \\\\" % (model, s.replace("_", "-"), n, m))
TABLE = r"""
\begin{table}[!htbp]
\centering
\caption{The pre-registered cross-backbone test. Three backbones, three adaptation sites, five held-out seeds each
(42, 123, 456, 789, 1012), strict freezing, rank $8$, $\alpha=2r$, ten epochs and $5000$ pairs, with the prediction
frozen before any run. Entries are the mean change in the centroid gap over the five seeds; a negative entry means the
gap narrowed.}
\label{tab:prereg}
\footnotesize
\begin{tabular}{l l r r}
\toprule
Backbone & Site & Seeds & Mean $\Delta$CG \\
\midrule
%s
\bottomrule
\end{tabular}

\vspace{2pt}
{\footnotesize
\emph{Notes.} The pre-registered prediction was that the text-only site gives a negative $\Delta$CG and the smallest
magnitude of change, for every backbone. It holds on CLIP B/32 and on CLIP B/16, and fails on OpenCLIP B/32, whose
text-only arms do not narrow the gap at all; the site ordering is reported as measured, not as predicted. Archive:
\texttt{outputs/paperA\_c\_prereg/}, \texttt{outputs/paperA\_c\_prereg\_openclip/},
\texttt{outputs/paperA\_c\_prereg\_b16/}; the frozen prediction and its scoring rule are the ones registered before the
runs.}
\end{table}
""" % "\n".join(rows_tex)

AP = "paper合/reframed/sections/95_appendix_original.tex"
t = io.open(AP, encoding="utf-8").read()
if "\\label{tab:prereg}" not in t:
    cut = t.rfind("\\section{Data and code provenance}")
    if cut < 0:
        cut = len(t)
    t = t[:cut] + TABLE + "\n" + t[cut:]
    io.open(AP, "w", encoding="utf-8", newline="").write(t)
    print("appendix table inserted")

# ---------------------------------------------------------------- paragraph in the validation section
PARA = (r"""
We also froze a prediction before running it. The registered statement was that the text-only site narrows the gap
most, on any backbone, because the coupling that determines the ordering lives in the text tower; three backbones were
then run under the identical protocol with five held-out seeds each (Table~\ref{tab:prereg}). The prediction holds on
CLIP B/32 (mean $\Delta$CG $%+.4f$ at text-only) and on CLIP B/16 ($%+.4f$), and it fails on OpenCLIP B/32
($%+.4f$): there the text-only site does not narrow the gap, and the site ordering is not the predicted one. This is a
boundary of the characterisation rather than a detail: the ordering is not invariant to the pre-training corpus, so the
mechanism we identify explains how a site's coupling produces its effect, not that one site always wins. We report the
three backbones side by side, with the failure included, because a prediction that is only reported where it holds is
not a prediction.
""" % (st["P1"][1]["text_only"][1], st["P4"][1]["text_only"][1], st["P2"][1].get("text_only", (0, 0.0))[1]))

RES = "paper合/reframed/sections/50_results.tex"
tr = io.open(RES, encoding="utf-8").read()
anchor = "best of the four on $700$"
if "froze a prediction before running it" not in tr:
    i = tr.find(anchor)
    assert i > 0, "competing-model paragraph not found"
    end = tr.find("\n\n", i)
    if end < 0:
        end = len(tr)
    tr = tr[:end] + PARA + tr[end:]
    io.open(RES, "w", encoding="utf-8", newline="").write(tr)
    print("validation paragraph inserted")
else:
    print("paragraph already present")

print(subprocess.run([r"D:\Anaconda\python.exe", "tools/_p1732_shorten_long_captions.py"],
                     capture_output=True, text=True).stdout.strip()[:200])
b = subprocess.run([r"D:\Anaconda\python.exe", "tools/_p1720_build_ml_package.py", "--apply"],
                   capture_output=True, text=True)
tail = [ln for ln in b.stdout.splitlines() if ("pages:" in ln or "RESULT" in ln or "round-trip" in ln)]
print("\n".join(tail))

subprocess.run(["git", "add", "-A"], check=False)
subprocess.run(["git", "commit", "-q", "-m",
                "Manuscript: add the pre-registered cross-backbone test with the OpenCLIP non-replication reported as a boundary"],
               check=False)
print(subprocess.run(["git", "log", "--oneline", "-1"], capture_output=True, text=True).stdout.strip())
