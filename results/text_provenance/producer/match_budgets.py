# -*- coding: utf-8 -*-
r"""Freeze the budget-matched subsets used by A3.

Two matching schemes, both seeded so the run JSON can reproduce them:

  pairs  - sample N image-text pairs per corpus, N in {10k, 50k, 200k}, without replacement across images where possible;
  tokens - re-sample so that the total whitespace-token count equals that of the reference corpus at the same pair budget.

Inputs: corpora produced by build_text_provenance.py (`<arm>.jsonl`, one JSON object per line with image_id and text).
Outputs per (dataset, budget, scheme): a frozen subset JSONL, its sha256, and a manifest line.

Usage
  python match_budgets.py --plan
  python match_budgets.py --self-test
  python match_budgets.py --corpora paper_a3/corpora/rsicd --out paper_a3/corpora/rsicd/budgets
"""
import argparse
import hashlib
import io
import json
import os
import random
import sys

BUDGETS = [10_000, 50_000, 200_000]
ARMS = ["human", "segmented", "templated", "metadata"]


def _sha256_file(path):
    h = hashlib.sha256()
    with io.open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_arm(path):
    rows = []
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sample_pairs(rows, n, seed):
    """Sample n pairs, taking at most one pair per image before repeating an image."""
    rng = random.Random(seed)
    by_image = {}
    for r in rows:
        by_image.setdefault(r["image_id"], []).append(r)
    images = sorted(by_image)
    rng.shuffle(images)
    chosen = []
    for img in images:
        chosen.append(rng.choice(by_image[img]))
        if len(chosen) >= n:
            break
    if len(chosen) < n:
        rest = [r for r in rows if r not in chosen]
        rng.shuffle(rest)
        chosen.extend(rest[: n - len(chosen)])
    return chosen[:n]


def token_count(rows):
    return sum(len(r["text"].split()) for r in rows)


def sample_tokens(rows, target_tokens, seed):
    """Grow a subset until its token total reaches target_tokens (as close as possible without overshoot)."""
    rng = random.Random(seed)
    order = list(range(len(rows)))
    rng.shuffle(order)
    chosen, total = [], 0
    for i in order:
        t = len(rows[i]["text"].split())
        if total + t > target_tokens:
            continue
        chosen.append(rows[i])
        total += t
        if total >= target_tokens - 8:
            break
    return chosen


def run(corpora_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    manifest = {"corpora": os.path.abspath(corpora_dir), "schemes": {}}
    arms = {arm: load_arm(os.path.join(corpora_dir, arm + ".jsonl")) for arm in ARMS
            if os.path.exists(os.path.join(corpora_dir, arm + ".jsonl"))}
    for scheme in ("pairs", "tokens"):
        manifest["schemes"][scheme] = {}
        for budget in BUDGETS:
            ref_tokens = None
            for arm, rows in arms.items():
                if scheme == "pairs":
                    subset = sample_pairs(rows, min(budget, len(rows)), seed=budget + hash(arm) % 1000)
                    tokens = token_count(subset)
                else:
                    if ref_tokens is None:
                        ref_subset = sample_pairs(rows, min(budget, len(rows)), seed=budget)
                        ref_tokens = token_count(ref_subset)
                    subset = sample_tokens(rows, ref_tokens, seed=budget)
                    tokens = token_count(subset)
                path = os.path.join(out_dir, "%s_%d_%s.jsonl" % (arm, budget, scheme))
                with io.open(path, "w", encoding="utf-8", newline="") as f:
                    for r in subset:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                manifest["schemes"][scheme].setdefault(str(budget), {})[arm] = {
                    "pairs": len(subset), "tokens": tokens, "sha256": _sha256_file(path)}
    io.open(os.path.join(out_dir, "budget_manifest.json"), "w", encoding="utf-8", newline="").write(
        json.dumps(manifest, indent=1, ensure_ascii=False))
    print(json.dumps({s: {b: {a: v["pairs"] for a, v in arms_.items()} for b, arms_ in d.items()}
                      for s, d in manifest["schemes"].items()}, indent=1))
    return manifest


def self_test():
    rows = [{"image_id": "i%03d" % i, "text": "word " * (i % 4 + 1)} for i in range(200)]
    a = sample_pairs(rows, 50, seed=7)
    b = sample_pairs(rows, 50, seed=7)
    c = sample_pairs(rows, 50, seed=8)
    tok = sample_tokens(rows, 300, seed=7)
    checks = {
        "pairs sample size": len(a) == 50,
        "same seed reproducible": [r["image_id"] for r in a] == [r["image_id"] for r in b],
        "different seed differs": [r["image_id"] for r in a] != [r["image_id"] for r in c],
        "token sample respects ceiling": token_count(tok) <= 300,
        "token sample non-empty": len(tok) > 0,
    }
    ok = all(checks.values())
    for k, v in checks.items():
        print("  [%s] %s" % ("PASS" if v else "FAIL", k))
    return 0 if ok else 1


PLAN = """A3 budget matching plan

For every dataset with frozen corpora:
  for scheme in {pairs, tokens}:
    for budget in {10k, 50k, 200k}:
      for arm in {human, segmented, templated, metadata}:
        write <arm>_<budget>_<scheme>.jsonl and record pairs/tokens/sha256 in budget_manifest.json
The seeds are the budget value; identical inputs reproduce identical files.
Token-matched arms use the human arm's token total at that pair budget as the reference.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpora")
    ap.add_argument("--out")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.plan:
        print(PLAN)
        return 0
    if args.self_test:
        return self_test()
    if not args.corpora or not args.out:
        print("provide --corpora and --out, or use --plan / --self-test", file=sys.stderr)
        return 2
    run(args.corpora, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
