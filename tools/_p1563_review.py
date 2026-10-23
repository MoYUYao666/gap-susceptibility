# -*- coding: utf-8 -*-
r"""Review pass: cross-check supplement numbers against the archives, plus structural checks (robust windows)."""
import glob
import io
import json
import os
import re
import statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUPP = os.path.join(REPO, "paper3", "paper_ieee", "supplementary", "supplementary.tex")
AN = os.path.join(REPO, "outputs", "analysis")
EXP = os.path.join(REPO, "paper3", "scripts", "outputs", "experiments")

problems = []
t = io.open(SUPP, encoding="utf-8").read()


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        problems.append(msg)


def window(label, before=8000, after=2000):
    i = t.find("\\label{" + label + "}")
    return t[max(0, i - before): i + after]


def delta(f):
    return json.load(io.open(f, encoding="utf-8")).get("delta_E")


check(t.count("\\end{document}") == 1, "single \\end{document}")
check(t.count("\\begin{table*}") == t.count("\\end{table*}"), "table* balanced")
check(len(re.findall(r"\\section\{", t)) == 43, "43 sections")
check(not re.search(r"[\u4e00-\u9fff]", t), "no CJK")

# C1
r3 = sorted(delta(f) for f in glob.glob(os.path.join(EXP, "cloud_verify_r3_s*.json"))
            if all(x not in f for x in ("partial", "_e1_", "imgs")))
r8 = sorted(delta(f) for f in glob.glob(os.path.join(EXP, "cloud_verify_r8_s*.json"))
            if all(x not in f for x in ("partial", "_e1_", "imgs")))
check(len(r3) == 10 and len(r8) == 10, "C1 n=10 each (r3=%d r8=%d)" % (len(r3), len(r8)))
blk = window("app:crossing10")
check(("%.1f" % st.mean(r3)) in blk and ("%.1f" % st.mean(r8)) in blk, "S33 means match archives")
check(all(v < 0 for v in r3) and all(v > 0 for v in r8), "S33 complete separation")

# S35
blk = window("app:realimage")
real = {}
for f in glob.glob(os.path.join(EXP, "cloud_verify_r*_imgs_cap*.json")):
    d = json.load(io.open(f, encoding="utf-8"))
    real[(d["rank"], d.get("seed", 42))] = d["delta_E"]
for (r, s), v in real.items():
    check(("%+.1f" % v) in blk, "S35 value %s %s %+.1f present" % (r, s, v))

# S40
blk = window("app:dolly")
dolly = {}
for f in glob.glob(os.path.join(EXP, "cloud_dolly_verify_r*_s*.json")):
    d = json.load(io.open(f, encoding="utf-8"))
    dolly.setdefault(d["rank"], []).append(d["delta_E"])
for r, v in sorted(dolly.items()):
    check(("%+.1f" % st.mean(v)) in blk, "S40 mean r%d %+.1f present" % (r, st.mean(v)))
check(all(x < 0 for r in (4, 5) for x in dolly[r]) and all(x > 0 for r in (6, 7) for x in dolly[r]),
      "S40 crossing pattern repeats")

# S41
blk = window("app:thirdfamily")
for r in (5, 6):
    d = json.load(io.open(os.path.join(AN, "cloud_qwen_cf_uniform_rank%d_seed42_qwen2vl.json" % r), encoding="utf-8"))
    check(("%+.1f" % d["delta_E"]) in blk, "S41 r%d %+.1f present" % (r, d["delta_E"]))

# S28
blk = window("app:vqa")
for k in ("base", "5", "6"):
    d = json.load(io.open(os.path.join(AN, "cloud_vqa1793_%s.json" % k), encoding="utf-8"))
    check(("%.4f" % d["accuracy"]) in blk, "S28 acc %s %.4f present" % (k, d["accuracy"]))

# S29 fourth stack
blk = window("app:envcloud")
check(("-35.5" in blk) and ("+42.0" in blk), "S29 fourth-stack rows present")
# S43 Qwen per-layer
blk = window("app:qwenlayer")
q = json.load(io.open(os.path.join(AN, "p3_qwen_perlayer_summary.json"), encoding="utf-8"))
check(("%.1f" % (100 * q["share"]["llm_00"])) in blk, "S43 layer-0 share present")
check(("%.1f" % (100 * q["first4_share"])) in blk, "S43 first-four share present")
# S44 SmolVLM means
blk = window("app:smolvlm")
sm = [json.load(io.open(f, encoding="utf-8")) for f in glob.glob(os.path.join(AN, "p3_smolvlm_family_s*.json"))]
m5 = st.mean(d["runs"]["r5"]["delta_E"] for d in sm)
m6 = st.mean(d["runs"]["r6"]["delta_E"] for d in sm)
check(("%+.1f" % m5) in blk and ("%+.1f" % m6) in blk, "S44 SmolVLM means present")
check(all(d["runs"]["r5"]["delta_E"] < 0 < d["runs"]["r6"]["delta_E"] for d in sm), "S44 sign change across seeds")

# archive paths in captions: only explicit repo-relative paths
raw = re.findall(r"\\texttt\{([^}]*)\}", t)
archives = []
for a in raw:
    a2 = a.replace("\\_", "_").replace("\\allowbreak", "").replace("/ ", "/").strip()
    if not a2.endswith(".json"):
        continue
    if "*" in a2 or "..." in a2:
        continue
    if not a2.startswith(("outputs/", "paper3/", "tools/", "docs/", "cloud_p3/", "models/")):
        continue
    archives.append(a2)
missing = sorted({a for a in archives if not os.path.exists(os.path.join(REPO, a))})
check(not missing, "caption archive paths exist (missing=%s)" % missing)

print("\nPROBLEMS:", problems if problems else "none")
raise SystemExit(1 if problems else 0)
