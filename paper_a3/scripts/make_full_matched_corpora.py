# -*- coding: utf-8 -*-
r"""Build full-corpus matched corpora: one text per image, intersected across the arms that exist.

Used for the full-scale LLM-arm comparison (no 10k ceiling, no subset). Outputs
corpora/<dataset>/full_<arm>.jsonl for every arm found, restricted to images present in all arms.
"""
import argparse
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL_ARMS = ["human", "segmented", "templated", "metadata", "humanrich", "llmcaption", "llmcaption2"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--arms", default="")
    args = ap.parse_args()
    base = os.path.join(ROOT, "corpora", args.dataset)
    arms = [a.strip() for a in args.arms.split(",") if a.strip()] or ALL_ARMS
    available, first_seen = {}, {}
    for arm in arms:
        p = os.path.join(base, arm + ".jsonl")
        if not os.path.exists(p):
            continue
        rows, order = {}, []
        for line in io.open(p, encoding="utf-8"):
            r = json.loads(line)
            if r["image_id"] in rows:
                continue
            rows[r["image_id"]] = r
            order.append(r["image_id"])
        available[arm] = rows
        first_seen[arm] = order
    if not available:
        raise SystemExit("no arms found")
    common = set.intersection(*[set(v) for v in available.values()])
    ref_order = first_seen.get("human") or first_seen[sorted(first_seen)[0]]
    keep = [i for i in ref_order if i in common]
    print("arms %s | intersection %d images" % (sorted(available), len(keep)))
    for arm, rows in available.items():
        out = os.path.join(base, "full_%s.jsonl" % arm)
        with io.open(out, "w", encoding="utf-8", newline="") as f:
            for i in keep:
                f.write(json.dumps(rows[i], ensure_ascii=False) + "\n")
        print("  wrote %s | rows %d" % (os.path.basename(out), len(keep)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
