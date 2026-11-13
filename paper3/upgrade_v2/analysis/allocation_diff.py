# -*- coding: utf-8 -*-
"""Compute r5-r6 allocation contrasts across all P3 v2 public evaluations and plot them."""
import collections, io, json, os, re, string
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
AN = os.path.join(REPO, "outputs", "analysis")
OUT = os.path.join(REPO, "paper3", "upgrade_v2", "figures")


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
    n = norm(s)
    m = re.search(r"\b([abcde])\b", n)
    return m.group(1) if m else ""


def load(task, arm):
    p = os.path.join(AN, f"p3_v2_benchmark_{task}_{arm}.json")
    if not os.path.exists(p):
        return None
    return json.load(io.open(p, encoding="utf-8"))


def vqa_metrics():
    d5 = json.load(io.open(os.path.join(AN, "cloud_vqa_full451_5.json"), encoding="utf-8"))
    d6 = json.load(io.open(os.path.join(AN, "cloud_vqa_full451_6.json"), encoding="utf-8"))
    f5 = [f1(r, h) for r, h in zip(d5["refs"], d5["hypotheses"])]
    f6 = [f1(r, h) for r, h in zip(d6["refs"], d6["hypotheses"])]
    a5 = [1.0 if norm(r) == norm(h) else 0.0 for r, h in zip(d5["refs"], d5["hypotheses"])]
    a6 = [1.0 if norm(r) == norm(h) else 0.0 for r, h in zip(d6["refs"], d6["hypotheses"])]
    return (np.asarray(f5), np.asarray(f6), np.asarray(a5), np.asarray(a6))


def boot_delta(x, y, rng):
    d = np.asarray(x) - np.asarray(y)
    idx = rng.integers(0, len(d), (20000, len(d)))
    m = d[idx].mean(1)
    return float(100 * d.mean()), float(100 * np.quantile(m, .025)), float(100 * np.quantile(m, .975)), int(len(d))


def main():
    rng = np.random.default_rng(20261113)
    rows = []
    for task, label, metric in [
        ("flickr30k", "Flickr30k", "f1"), ("coco5k", "COCO5k", "f1"),
        ("pope", "POPE", "acc"), ("marinelife", "MarineLife", "acc"),
        ("inat", "iNaturalist", "acc"), ("dtd", "DTD", "acc"),
        ("scienceqa", "ScienceQA", "acc"), ("mmbench", "MMBench", "acc"),
    ]:
        a, b = load(task, "5"), load(task, "6")
        if not a or not b:
            continue
        if metric == "f1":
            x = [f1(r, h) for r, h in zip(a["refs"], a["hypotheses"])]
            y = [f1(r, h) for r, h in zip(b["refs"], b["hypotheses"])]
        else:
            x = [1.0 if letter(h) == str(r).lower() else 0.0 for h, r in zip(a["hypotheses"], a["refs"])]
            y = [1.0 if letter(h) == str(r).lower() else 0.0 for h, r in zip(b["hypotheses"], b["refs"])]
        d, lo, hi, n = boot_delta(x, y, rng)
        rows.append({"dataset": label, "metric": "F1" if metric == "f1" else "accuracy",
                     "delta_pp": d, "lo": lo, "hi": hi, "n": n})
    # VQA-RAD contrasts are taken from the archived canonical equivalence record so that
    # the figure, the table and the TOST analysis use one bootstrap seed.
    veq = json.load(io.open(os.path.join(AN, "p3_vqa_full_equivalence.json"), encoding="utf-8"))["rank5_equivalence"]
    for metric, key in [("token_f1", "F1"), ("accuracy", "accuracy")]:
        c = veq[metric]
        rows.append({"dataset": "VQA-RAD (%s)" % ("exact" if key == "accuracy" else "F1"),
                     "metric": key,
                     "delta_pp": float(100 * c["vs_r6_delta"]),
                     "lo": float(100 * c["vs_r6_ci95"][0]),
                     "hi": float(100 * c["vs_r6_ci95"][1]),
                     "n": int(veq["n"])})
    io.open(os.path.join(AN, "p3_v2_allocation_diff.json"), "w", encoding="utf-8", newline="").write(
        json.dumps(rows, indent=1) + "\n")

    import matplotlib as mpl
    mpl.use("Agg")
    mpl.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "Times", "STIXGeneral"],
        "mathtext.fontset": "stix", "pdf.fonttype": 42, "ps.fonttype": 42,
        "axes.unicode_minus": False, "font.size": 9,
    })
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    rows = sorted(rows, key=lambda r: (r["metric"], r["dataset"]))
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    y = np.arange(len(rows))[::-1]
    for i, r in enumerate(rows):
        col = "#4C72B0" if r["metric"] == "F1" else "#DD8452"
        ax.plot([r["lo"], r["hi"]], [y[i], y[i]], color=col, lw=1.2)
        ax.plot(r["delta_pp"], y[i], "o", color=col, ms=4)
    ax.axvline(0, color="black", lw=0.7, ls="--")
    ax.set_yticks(y)
    ax.set_yticklabels([r["dataset"] for r in rows])
    ax.set_xlabel("r5 $-$ r6 difference (percentage points)")
    ax.set_title("Allocation contrast across public evaluations", fontsize=9.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend([Line2D([0], [0], color="#4C72B0", marker="o", lw=1),
               Line2D([0], [0], color="#DD8452", marker="o", lw=1)],
              ["caption/VQA F1", "accuracy"], frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout(pad=0.2)
    fig.savefig(os.path.join(OUT, "fig3_allocation_diff.pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(os.path.join(OUT, "fig3_allocation_diff.png"), dpi=300, bbox_inches="tight", pad_inches=0.02)
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
