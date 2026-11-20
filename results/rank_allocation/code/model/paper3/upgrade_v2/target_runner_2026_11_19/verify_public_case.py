"""Verify a completed public retrieval scoring receipt."""
import argparse
import json
from pathlib import Path
import re

from csv_intake import fingerprint, overlap, sorted_candidates
from score_case import (
    ARMS, CONTROLS, CSV_NAME, GAMMA, HERE, IMAGE_PATTERN, RAW_SHA, ROOT, SCOPE,
    SEEDS, TEST_COUNT, bound_json, caption_rows, check, score, sha, validate_frozen_fit,
)


def replay_scores(cells):
    result = []
    for seed, rows in zip(SEEDS,
                          (cells[i:i+len(ARMS)] for i in range(0, len(cells), len(ARMS))),
                          strict=True):
        counts = {}
        for arm, row in zip(ARMS, rows, strict=True):
            count = row["hits"]
            check(type(row["seed"]) is int and (row["seed"], row["arm"]) == (seed, arm),
                  "Missing, duplicate, or reordered cell")
            check(type(count) is int and 0 <= count <= TEST_COUNT and row["r1"] == count / TEST_COUNT,
                  "Invalid hit count or unmatched R@1")
            counts[arm] = count
        delta = {g: {c: (counts[g] - counts[c]) / TEST_COUNT for c in CONTROLS} for g in GAMMA}
        result.append({"seed": seed, "gamma_deltas": delta,
                       "worst_gamma_delta_vs_uniform": min(row["uniform"] for row in delta.values())})
    return result


def verify(staging, commitment, *, rescore=False):
    staging = staging.resolve(strict=True)
    check(not staging.is_relative_to(ROOT), "Private staging must stay outside the project tree")
    result = bound_json(staging / "PublicCaseResults.json", commitment, "public-case result")
    scorer = sha(HERE / "score_case.py")
    check(result["scope"] == SCOPE and result["query_count"] == TEST_COUNT and result["corpus_units"] == 1
          and result["predictor_threshold"] is None and result["cross_target_association"] is None
          and result["scorer_sha256"] == scorer, "Public case scope or scorer drift")
    paired = replay_scores(result["cells"])
    check(result["by_seed"] == paired, "Paired contrast archive drift")
    cells, train = validate_frozen_fit(staging, result["fit_freeze_sha256"])
    test = bound_json(staging / "PublicTestManifest.json", result["test_manifest_sha256"], "test manifest")
    index = json.loads((HERE / "VizWizImageIndex.json").read_bytes())["archives"]["test"]["index_sha256"]
    check(test["scope"] == SCOPE and test["scorer_sha256"] == scorer and test["test_zip_index_sha256"] == index
          and test["fit_freeze_sha256"] == result["fit_freeze_sha256"] and test["csv_sha256"] == RAW_SHA,
          "Test manifest drift or pre-freeze test roster")
    csv = staging / CSV_NAME
    check(sha(csv) == RAW_SHA, "Publisher CSV SHA-256 mismatch")
    references = caption_rows(csv)
    names = [r["image"] for r in test["queries"]]
    check(len(names) == TEST_COUNT and names == sorted_candidates(names, set(names), "test"), "Query order drift")
    source = ROOT / "data/marine_captions"
    marks = [fingerprint((source / n).read_bytes()) for n in sorted(train["source_image_sha256"])]
    marks += train["calibration"] + train["train"]
    gallery_size = 0
    for row in test["queries"]:
        name = row["image"]
        check(re.fullmatch(IMAGE_PATTERN.format(split="test"), name), "Non-test query")
        observed = fingerprint((staging / "test_images" / name).read_bytes())
        check(all(row[k] == v for k, v in observed.items()) and not overlap(observed, marks),
              "Overlapping or changed test image")
        marks.append(observed)
        expected = [list(ref) for ref in references[name]]
        check(expected and row["references"] == expected, "Test references differ from eligible source captions")
        gallery_size += len(expected)
    check(gallery_size == result["caption_count"], "Wrong gallery size")
    if rescore:
        fresh = score(staging, result["fit_freeze_sha256"], result["test_manifest_sha256"],
                      cells, train, result["runtime"]["device"])
        check(all(fresh[k] == result[k] for k in ("cells", "by_seed", "caption_count", "query_count")),
              "Independent rescore differs from the result receipt")
    return {"scope": SCOPE, "result_sha256": commitment, "query_count": TEST_COUNT,
            "caption_count": gallery_size, "cells": result["cells"], "by_seed": paired,
            "model_rescore_passed": rescore, "corpus_units": 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("staging", type=Path)
    parser.add_argument("result_sha256", help="Hash emitted in the successful pipeline log")
    parser.add_argument("--rescore", action="store_true", help="Replay the checkpoint scores on the recorded device")
    args = parser.parse_args()
    print(json.dumps(verify(args.staging, args.result_sha256, rescore=args.rescore), indent=2))


if __name__ == "__main__":
    main()
