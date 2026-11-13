# -*- coding: utf-8 -*-
"""Post-hoc multiplicity check for the r5/r6 versus base benchmark contrasts.

This is a descriptive check, not a pre-registered test. Bootstrap p-values are two-sided
paired bootstrap tail probabilities with the add-one correction; BH q-values are reported.
"""
import collections, io, json, os, re, string
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AN = os.path.join(REPO, "outputs", "analysis")


def norm(s):
    s = str(s).lower().strip()
    s = re.sub(r"[%s]" % re.escape(string.punctuation), " ", s)
    return " ".join(s.split())


def f1(r, h):
    rt = collections.Counter(norm(r).split())
    ht = collections.Counter(norm(h).split())
    c = sum((rt & ht).values())
    if c == 0:
        return 0.0
    p = c / max(sum(ht.values()), 1)
    rec = c / max(sum(rt.values()), 1)
    return 2 * p * rec / max(p + rec, 1e-12)


def letter(s):
    m = re.search(r"\b([abcde])\b", norm(s))
    return m.group(1) if m else ""


def load(task, arm):
    return json.load(io.open(os.path.join(AN, f"p3_v2_benchmark_{task}_{arm}.json"), encoding="utf-8"))


def pboot(d, rng, B=20000):
    d = np.asarray(d)
    if np.allclose(d, 0):
        return 1.0, float(d.mean())
    idx = rng.integers(0, len(d), (B, len(d)))
    m = d[idx].mean(1)
    p = 2 * min((1 + np.sum(m <= 0)) / (B + 1), (1 + np.sum(m >= 0)) / (B + 1))
    return float(min(1.0, p)), float(d.mean())


def main():
    rng = np.random.default_rng(20261113)
    tests = []
    for task, label, metric in [("flickr30k", "Flickr30k", "F1"), ("coco5k", "COCO5k", "F1"),
                                ("pope", "POPE", "accuracy"), ("marinelife", "MarineLife", "accuracy"),
                                ("inat", "iNaturalist", "accuracy"), ("dtd", "DTD", "accuracy"),
                                ("scienceqa", "ScienceQA", "accuracy"), ("mmbench", "MMBench", "accuracy")]:
        a, b = load(task, "base"), load(task, "5") if task else None
        # base vs r5 and r6; files loaded per arm below
        for arm in ("5", "6"):
            x = load(task, arm)
            if metric == "F1":
                rb = [f1(r, h) for r, h in zip(a["refs"], a["hypotheses"])]
                ra = [f1(r, h) for r, h in zip(x["refs"], x["hypotheses"])]
            else:
                rb = [1.0 if letter(h) == str(r).lower() else 0.0 for h, r in zip(a["hypotheses"], a["refs"])]
                ra = [1.0 if letter(h) == str(r).lower() else 0.0 for h, r in zip(x["hypotheses"], x["refs"])]
            p, delta = pboot(np.asarray(ra) - np.asarray(rb), rng)
            tests.append({"benchmark": label, "metric": metric, "contrast": "r%s-base" % arm,
                          "delta": delta, "p_boot": p, "n": len(ra)})
    # VQA-RAD canonical contrasts; paired bootstrap on per-question metrics
    veq = json.load(io.open(os.path.join(AN, "p3_vqa_full_equivalence.json"), encoding="utf-8"))
    d5 = json.load(io.open(os.path.join(AN, "cloud_vqa_full451_5.json"), encoding="utf-8"))
    d6 = json.load(io.open(os.path.join(AN, "cloud_vqa_full451_6.json"), encoding="utf-8"))
    db = json.load(io.open(os.path.join(AN, "cloud_vqa_full451_base.json"), encoding="utf-8"))
    for arm, d in (("5", d5), ("6", d6)):
        for met, fn in (("F1", lambda r, h: f1(r, h)),
                        ("exact", lambda r, h: 1.0 if norm(r) == norm(h) else 0.0)):
            rb = np.asarray([fn(r, h) for r, h in zip(db["refs"], db["hypotheses"])])
            ra = np.asarray([fn(r, h) for r, h in zip(d["refs"], d["hypotheses"])])
            p, delta = pboot(ra - rb, rng)
            tests.append({"benchmark": "VQA-RAD", "metric": met, "contrast": "r%s-base" % arm,
                          "delta": float(delta), "p_boot": p, "n": len(ra)})
    # allocation-arm family: r5-r6 for each benchmark/metric
    alloc = []
    for task, label, metric in [("flickr30k", "Flickr30k", "F1"), ("coco5k", "COCO5k", "F1"),
                                ("pope", "POPE", "accuracy"), ("marinelife", "MarineLife", "accuracy"),
                                ("inat", "iNaturalist", "accuracy"), ("dtd", "DTD", "accuracy"),
                                ("scienceqa", "ScienceQA", "accuracy"), ("mmbench", "MMBench", "accuracy")]:
        a, b = load(task, "5"), load(task, "6")
        if metric == "F1":
            x = np.asarray([f1(r, h) for r, h in zip(a["refs"], a["hypotheses"])])
            y = np.asarray([f1(r, h) for r, h in zip(b["refs"], b["hypotheses"])])
        else:
            x = np.asarray([1.0 if letter(h) == str(r).lower() else 0.0 for h, r in zip(a["hypotheses"], a["refs"])])
            y = np.asarray([1.0 if letter(h) == str(r).lower() else 0.0 for h, r in zip(b["hypotheses"], b["refs"])])
        p, delta = pboot(x - y, rng)
        alloc.append({"benchmark": label, "metric": metric, "contrast": "r5-r6",
                      "delta": float(delta), "p_boot": p, "n": len(x)})
    for met, fn in (("F1", lambda r, h: f1(r, h)),
                    ("exact", lambda r, h: 1.0 if norm(r) == norm(h) else 0.0)):
        x = np.asarray([fn(r, h) for r, h in zip(d5["refs"], d5["hypotheses"])])
        y = np.asarray([fn(r, h) for r, h in zip(d6["refs"], d6["hypotheses"])])
        p, delta = pboot(x - y, rng)
        alloc.append({"benchmark": "VQA-RAD", "metric": met, "contrast": "r5-r6",
                      "delta": float(delta), "p_boot": p, "n": len(x)})
    def bh(rows):
        order = sorted(range(len(rows)), key=lambda i: rows[i]["p_boot"])
        m = len(rows); q = [0.0] * m; prev = 1.0
        for rank, i in enumerate(reversed(order), start=1):
            val = min(prev, rows[i]["p_boot"] * m / (m - rank + 1)); q[i] = val; prev = val
        for i, r in enumerate(rows): r["q_bh"] = float(q[i])
        return min(q), m
    min_q, m = bh(tests); min_q_alloc, m_alloc = bh(alloc)
    tests_sorted = sorted(tests, key=lambda t: t["p_boot"])
    alloc_sorted = sorted(alloc, key=lambda t: t["p_boot"])
    out = {"meta": {"method": "paired two-sided bootstrap p-values with add-one correction; Benjamini-Hochberg q separately for base-vs-arm and r5-r6 families",
                    "n_boot": 20000, "seed": 20261113,
                    "note": "descriptive post-hoc check, not a pre-registered multiplicity analysis"},
           "base_vs_arm": tests_sorted, "base_vs_arm_min_q": min_q, "base_vs_arm_n": m,
           "r5_minus_r6": alloc_sorted, "r5_minus_r6_min_q": min_q_alloc, "r5_minus_r6_n": m_alloc}
    io.open(os.path.join(AN, "p3_v2_multiplicity.json"), "w", encoding="utf-8", newline="").write(
        json.dumps(out, indent=1) + "\n")
    for t in alloc_sorted[:6]:
        print(t)
    print("base min q", min_q, "n", m, "alloc min q", min_q_alloc, "n", m_alloc)


if __name__ == "__main__":
    main()
