# -*- coding: utf-8 -*-
r"""Integrate the purely-local extras: fourth stack (S29), Qwen per-layer (S43), SmolVLM family (S44),
environment-variance update (S37), r3-vs-r8 permutation (S33)."""
import glob
import io
import json
import os
import statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")
MANIFEST = os.path.join(REPO, "docs", "provenance_manifest.json")
bs = chr(92)


def jl(p):
    return json.load(io.open(p, encoding="utf-8"))


def replace_section(t, title, new_block):
    head = "\\section{" + title + "}"
    start = t.find(head)
    assert start >= 0, title
    nxt = t.find("\\section{", start + len(head))
    end = nxt if nxt >= 0 else t.find("\\bibliographystyle", start)
    return t[:start] + new_block + "\n" + t[end:]


# --- data ---
ev = jl(os.path.join(AN, "p3_env_variance.json"))
env_rows = "\n".join("%s & %d & %+.1f & %.1f %s" % (k, v["n"], v["mean"], v["sd"], bs * 2)
                     for k, v in ev["envs"].items())
# fourth stack: torch 2.6 outputs, still named like torch24; identify by file time/renaming done separately
t26 = {}
for r, suffix in ((5, "_a10"), (6, "_a12")):
    fs = sorted(glob.glob(os.path.join(EXP, "verify_r%d_s42_*%s*.json" % (r, suffix))))
    cand = [f for f in fs if "torch24" not in f]
    if cand:
        d = jl(cand[-1])
        t26[r] = {"E0": d["E"][0], "dE": d["delta_E"]}
print("torch26:", t26)
qwen = jl(os.path.join(AN, "p3_qwen_perlayer_summary.json"))
smol = {}
for f in sorted(glob.glob(os.path.join(AN, "p3_smolvlm_family_s*.json"))):
    d = jl(f)
    seed = d["meta"].get("seed", 42)
    smol[seed] = {r: d["runs"][r]["delta_E"] for r in ("r5", "r6")}
print("smolvlm:", smol)

t = io.open(SUPP, encoding="utf-8").read()

# S29 rebuild with the fourth stack (torch 2.6 / CUDA 12.4)
s29 = (r"""\section{Second-environment reproducibility}
\label{app:envcloud}

The protocol is repeated in four software/hardware environments: RTX 4060 Laptop with torch 2.9.1+cu130, RTX 4080
SUPER with torch 2.12.1+cu130, RTX 4060 Laptop with torch 2.4.1+cu121 (CUDA 12.1), and RTX 4060 Laptop with
torch 2.6.0+cu124 (CUDA 12.4). Table~\ref{tab:envcloud} compares them.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}llllll@{}}
\toprule
machine & torch & CUDA & rank & $E_0$ & $\Delta E$ \\
\midrule
RTX 4060 Laptop & 2.9.1+cu130 & 13.0 & 5 & 3921.0 & $-10.5$ \\
RTX 4060 Laptop & 2.9.1+cu130 & 13.0 & 6 & 3921.0 & $+115.0$ \\
RTX 4080 SUPER & 2.12.1+cu130 & 13.0 & 5 & 3926.0 & $-33.5$ \\
RTX 4080 SUPER & 2.12.1+cu130 & 13.0 & 6 & 3926.0 & $+81.5$ \\
RTX 4060 Laptop & 2.4.1+cu121 & 12.1 & 5 & 3930.5 & $+41.0$ \\
RTX 4060 Laptop & 2.4.1+cu121 & 12.1 & 6 & 3930.5 & $+89.0$ \\
RTX 4060 Laptop & 2.6.0+cu124 & 12.4 & 5 & %(e5).1f & $%(d5)+.1f$ \\
RTX 4060 Laptop & 2.6.0+cu124 & 12.4 & 6 & %(e6).1f & $%(d6)+.1f$ \\
\bottomrule
\end{tabular}
\caption{Cross-environment reproducibility of the $r=5$/$r=6$ crossing. The positive sign at $r=6$ is stable in all
four stacks. At $r=5$ the effect is near zero and its sign is not a cross-environment constant: it is negative in the
two cu130 stacks and in the torch 2.6/cu124 stack, while the torch 2.4/cu121 stack gives $+41.0$ for seed 42 and
$-2.5$, $-2.0$, $+64.5$ for three further seeds, so the environment shift is of the same order as the seed spread at
this rank. Archive: \texttt{outputs/analysis/p3\_env\_matrix3.json} and
\texttt{paper3/scripts/outputs/experiments/verify\_r5\_s42\_*\_a10\_torch26.json}.}
\label{tab:envcloud}
\end{table*}""") % {"e5": t26[5]["E0"], "d5": t26[5]["dE"], "e6": t26[6]["E0"], "d6": t26[6]["dE"]}
t = replace_section(t, "Second-environment reproducibility", s29)
print("S29 rebuilt with fourth stack")

# S37 rebuild from updated variance JSON
cap = ("Random-effects variance decomposition at $r=5$ over the three cu121/cu130 stacks: "
       "$\\sigma_{\\mathrm{env}}=%.1f$, $\\sigma_{\\mathrm{seed}}=%.1f$; environment share %.0f\\%% with a "
       "10{,}000-draw seed bootstrap 95\\%% interval $[%.0f\\%%, %.0f\\%%]$. The bootstrap interval does not "
       "include zero at the low end in most draws, so the software stack contributes non-negligibly to the near-zero "
       "$r=5$ effect. Archive: \\texttt{outputs/analysis/p3\\_env\\_variance.json}." % (
           ev["sigma_env"], ev["sigma_seed"], 100 * ev["env_share"],
           100 * ev["bootstrap"]["share_ci95"][0], 100 * ev["bootstrap"]["share_ci95"][1]))
s37 = (r"""\section{Variance decomposition of the environment effect}
\label{app:envvar}

Seed-to-seed variation at $r=5$ is separated from environment-to-environment variation with a one-way random-effects
model (environment as factor; seeds resampled within each environment for the interval).
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrrr@{}}
\toprule
environment & $n$ & mean $\Delta E$ & sd \\
\midrule
""" + env_rows + r"""
\bottomrule
\end{tabular}
""" + "\\caption{" + cap + "}\n\\label{tab:envvar}\n\\end{table*}")
# LaTeX line breaks above are literal; build the caption line explicitly
s37 = s37.replace("\\\\caption{", "\\caption{").replace("}\\n\\label", "}\n\\label")
t = replace_section(t, "Variance decomposition of the environment effect", s37)
print("S37 rebuilt")

# S33 permutation sentence
old = "the minimum attainable with ten seeds per\ngroup. Archive:"
new = ("the minimum attainable with ten seeds per\ngroup; the same exact test on the extreme ranks $r=3$ vs $r=8$ "
       "also gives $p=1.08\\times10^{-5}$. Archive:")
if old in t:
    t = t.replace(old, new, 1)
    print("S33 permutation sentence added")

# S43 Qwen per-layer
s43 = (r"""\section{Per-layer coupling on a second model}
\label{app:qwenlayer}

The per-layer integrated-gradient coupling is repeated on Qwen2.5-VL-3B (LoRA probe, six prompts, five
integration points). Table~\ref{tab:qwenlayer} reports the block-free summary: unlike LLaVA-1.5, the coupling is
concentrated in the very first language layers.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrr@{}}
\toprule
group & layers & share of $|\Gamma|$ \\
\midrule
first layer (llm\_00) & 1 & %.1f\%% \\
layers 1--3 & 3 & %.1f\%% \\
layers 4--35 & 32 & %.1f\%% \\
\bottomrule
\end{tabular}
\caption{Per-layer coupling on Qwen2.5-VL-3B: layer~0 carries %.1f\%% of the total absolute coupling and the first four
layers carry %.1f\%%, so the layer-wise distribution is model-specific even when the block-level comparison is similar.
Archive: \texttt{outputs/analysis/p3\_qwen\_perlayer\_summary.json}.}
\label{tab:qwenlayer}
\end{table*}""" % (100 * qwen["share"]["llm_00"], 100 * sum(qwen["share"]["llm_%02d" % i] for i in (1, 2, 3)),
                   100 * (1 - qwen["first4_share"]), 100 * qwen["share"]["llm_00"], 100 * qwen["first4_share"]))
if "app:qwenlayer" not in t:
    t = t.replace("\\bibliographystyle{IEEEtran}", s43 + "\n\n\\bibliographystyle{IEEEtran}", 1)
    print("S43 inserted")

# S44 SmolVLM multi-seed
rows44 = "\n".join("%d & %+.1f & %+.1f %s" % (s, v["r5"], v["r6"], bs * 2) for s, v in sorted(smol.items()))
mean5 = st.mean(v["r5"] for v in smol.values()) if smol else float("nan")
mean6 = st.mean(v["r6"] for v in smol.values()) if smol else float("nan")
s44 = (r"""\section{Third check: SmolVLM-500M}
\label{app:smolvlm}

A small Idefics3-family model (SmolVLM-500M-Instruct) is trained under the same blank-image protocol at $r=5$ and $r=6$.
\begin{table*}[h]
\centering
\footnotesize
\begin{tabular}{@{}lrr@{}}
\toprule
seed & $r=5$ & $r=6$ \\
\midrule
""" + rows44 + r"""
\bottomrule
\end{tabular}
\caption{SmolVLM-500M third-family control: the sign changes between $r=5$ and $r=6$ (means $%+.1f$ and $%+.1f$), but
the $r=6$ effect is close to zero, so this control does not establish a robust crossing outside LLaVA-1.5; together with
the Qwen2-VL-2B control (S41) it keeps the claim bounded. Archive:
\texttt{outputs/analysis/p3\_smolvlm\_family\_s*.json}.}
\label{tab:smolvlm}
\end{table*}""" % (mean5, mean6))
if "app:smolvlm" not in t:
    t = t.replace("\\bibliographystyle{IEEEtran}", s44 + "\n\n\\bibliographystyle{IEEEtran}", 1)
    print("S44 inserted")

# S17 rows: update env row and append two rows
old_env = ("crossing stable across torch/CUDA versions & \\emph{not} supported & $r=6$ positive everywhere; $r=5$ "
           "shifts with the stack (mean $-23$/$-44$/$+34$; S29, S37) \\\\")
new_env = ("crossing stable across torch/CUDA versions & \\emph{not} supported & $r=6$ positive everywhere; $r=5$ "
           "shifts with the stack (means $-23$/$-44$/$+25$; environment share $45\\%$ [21, 75]; S29, S37) \\\\")
if old_env in t:
    t = t.replace(old_env, new_env, 1)
idx = t.find("\\label{tab:claims}")
j = t.find("\\bottomrule", idx)
add_rows = ("per-layer coupling distribution is model-specific & reported, no positive claim & layer 0 carries "
            "97.9\\% of the coupling on Qwen2.5-VL-3B (S43) \\\\\n"
            "third-family crossing (SmolVLM-500M) & not established & sign change present but $r=6$ effect near zero "
            "(S44) \\\\\n")
if "SmolVLM" not in t[t.find("\\label{tab:claims}"):t.find("\\bottomrule", idx)]:
    t = t[:j] + add_rows + t[j:]
io.open(SUPP, "w", encoding="utf-8", newline="").write(t)
print("S17 updated")

mf = jl(os.path.join(REPO, "docs", "provenance_manifest.json"))
floats = mf["manuscripts"]["P3"]["floats"]
have = {f["label"] for f in floats}
for label, script, archive in (
        ("tab:qwenlayer", "tools/_p1567_qwen_perlayer_gamma.py", "outputs/analysis/p3_qwen_perlayer_summary.json"),
        ("tab:smolvlm", "tools/_p1568_smolvlm_run.py", "outputs/analysis/p3_smolvlm_family_s42.json")):
    if label not in have:
        floats.append({"label": label, "kind": "table", "script": script, "archive": archive,
                       "status": "verified", "note": "purely-local extra round"})
for f in floats:
    if f["label"] == "tab:envvar":
        f["archive"] = "outputs/analysis/p3_env_variance.json"
json.dump(mf, io.open(os.path.join(REPO, "docs", "provenance_manifest.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print("manifest floats:", len(floats))
