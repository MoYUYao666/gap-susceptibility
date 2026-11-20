"""Score the public VizWiz case only after the complete fit freeze; not a blind release."""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from csv_intake import (HERE, ROOT, RAW_SHA, REQUIRED, IMAGE_PATTERN, ZipMembers,
                        digest, emit, fingerprint, overlap, precanned, read_or_get_image, sorted_candidates)
from fit import init_runtime, ordered
from fit_case import MODEL, SOURCE, STEPS, check_clock, grid, load_train_manifest
from score_release import (ARMS, BUDGET, CONTROLS, GAMMA, SEEDS, bound_json, check,
                           hits_in_gallery, sha)

SCOPE = "VIZWIZ_PUBLIC_CASE_NOT_INDEPENDENT_OR_BLIND"
TEST_COUNT = 256
CSV_NAME = "VizWiz_captions_project_all_metadata.csv"


def caption_rows(path):
    refs, ids = defaultdict(list), set()
    with path.open(encoding="latin-1", newline="") as f:
        reader = csv.reader(f, strict=True)
        cols = next(reader)
        check(len(cols) == len(set(cols)) and set(REQUIRED).issubset(cols), "Unexpected CSV schema")
        aid, img, rejected, raw, corrected, split = map(cols.index, REQUIRED)
        for row in reader:
            check(len(row) == len(cols), "Nonrectangular metadata CSV")
            if row[split].strip().casefold() != "test" or not re.fullmatch(
                    IMAGE_PATTERN.format(split="test"), row[img]):
                continue
            check(re.fullmatch(r"[0-9]+", row[aid]), "Invalid test annotation ID")
            index = int(row[aid])
            check(index not in ids, "Duplicate test annotation ID")
            ids.add(index)
            check(row[rejected] in ("0", "1"), "Unknown test rejection flag")
            if row[rejected] == "1" or not row[corrected].strip() or any(
                    precanned(row[k]) for k in (raw, corrected)):
                continue
            caption = row[corrected].encode("latin-1").decode("cp1252").strip()
            check(caption and not any(ord(c) < 32 and c not in "\n\r\t" for c in caption),
                  "Invalid test caption encoding or control character")
            refs[row[img]].append((index, caption))
    return {name: sorted(rows) for name, rows in refs.items()}


def validate_frozen_fit(staging, commitment):
    freeze = bound_json(staging/"FitFreeze.json", commitment, "fit freeze")
    check(freeze["mode"] == "PUBLIC_DESCRIPTIVE_CASE_FIT_ONLY" and freeze["scientific_result"] is None,
          "Complete public case fit freeze required")
    design = bound_json(staging/"FitDesign.json", freeze["fit_design_sha256"], "fit design")
    doc = load_train_manifest(staging, design["manifest_sha256"])
    model_pins = json.loads((HERE/"FitSmoke.json").read_bytes())["model_sha256"]
    check(design["scope"] == SCOPE and design["heldout_caption_access"] is False
          and design["seeds"] == list(SEEDS) and design["arms"] == list(ARMS)
          and design["trainables_per_cell"] == BUDGET and design["updates_per_cell"] == STEPS
          and design["model_sha256"] == model_pins and all(sha(MODEL/n) == h for n,h in model_pins.items())
          and set(design["script_sha256"]) == {"fit_case.py", "fit.py", "runner.py", "ProjectedSource.json",
                                               "CsvIntakePlan.md", "FitPlan.md", "VizWizImageIndex.json"}
          and all(sha(HERE/n) == h for n,h in design["script_sha256"].items())
          and set(design["legacy_sha256"]) == {"src/lora.py", "tools/_p462_gamma_real_vs_blank.py"}
          and all(sha(ROOT/n) == h for n,h in design["legacy_sha256"].items()), "Fit design drift")
    cal = bound_json(staging/"Calibration.json", freeze["calibration_sha256"], "calibration")
    check(cal["fit_design_sha256"] == freeze["fit_design_sha256"], "Unbound calibration")
    ranks = grid(json.loads(SOURCE.read_bytes()), {k:v["ranks"] for k,v in cal["per_seed"].items()})
    cells, clocks = {}, {}
    fit_ids = [r["image"] for r in doc["train"]]
    cal_ids = [r["image"] for r in doc["calibration"]]
    for (seed, arm), link in zip(ranks, freeze["cells"], strict=True):
        key = str(seed)
        name = f"S{seed}-{arm}"
        m = cal["per_seed"][key]
        check(design["calibration_order"][key] == m["fit_order"] == ordered(cal_ids, seed)
              and m["optimizer_updates"] == 0 and m["backward_passes"] == 2
              and design["order"][key] == ordered(fit_ids, seed), "Unpaired order or calibration clock")
        check(link["receipt"] == name+".json", "Missing or misordered cell receipt")
        cell = bound_json(staging/link["receipt"], link["sha256"], name)
        path = staging/(name+".npz")
        check(cell["seed"] == seed and cell["arm"] == arm and cell["ranks"] == ranks[seed, arm]
              and cell["actual_trainables"] == BUDGET and cell["frozen_parameters_unchanged"] is True
              and cell["fit_design_sha256"] == freeze["fit_design_sha256"]
              and cell["calibration_sha256"] == freeze["calibration_sha256"]
              and cell["runtime"] == cal["runtime"] and cell["runtime"]["device"] == design["device"]
              and cell["adapter_file"] == path.name
              and sha(path) == cell["adapter_file_sha256"] == link["adapter_sha256"], "Unbound checkpoint")
        clocks[seed] = check_clock(cell["clock"], design["order"][key], clocks.get(seed))
        with np.load(path, allow_pickle=False) as data:
            values = [data[n] for n in data.files]
            actual = hashlib.sha256()
            for a in values:
                check(a.ndim == 2 and a.dtype == np.float32 and np.isfinite(a).all(), "Invalid adapter tensor")
                actual.update(a.tobytes(order="C"))
            check(len(set(data.files)) == len(values) == cell["adapter_tensors"]
                  and sum(a.size for a in values) == BUDGET
                  and actual.hexdigest() == cell["adapter_after_sha256"], "Adapter payload mismatch")
        cells[seed, arm] = cell
    return cells, doc


def prepare_test(staging, doc, commitment):
    path = staging/CSV_NAME
    check(sha(path) == RAW_SHA, "Publisher CSV SHA-256 mismatch")
    refs = caption_rows(path)
    index = json.loads((HERE/"VizWizImageIndex.json").read_bytes())["archives"]["test"]["index_sha256"]
    archive = ZipMembers("test", expected_digest=index)
    order = sorted_candidates(refs, set(archive.members), "test")
    directory = staging/"test_images"
    directory.mkdir(exist_ok=True)
    excluded, picked = [], []
    marks = doc["calibration"] + doc["train"] + [
        fingerprint((ROOT/"data/marine_captions"/n).read_bytes()) for n in sorted(doc["source_image_sha256"])]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for start in range(0, len(order), 4):
            window = order[start:start+4]
            for name, mark in zip(window, pool.map(
                    lambda name: read_or_get_image(archive, directory/name), window), strict=True):
                reason = overlap(mark, marks+picked)
                if reason:
                    excluded.append({"image": name, "reason": reason})
                    continue
                picked.append({"image": name, **mark, "references": [list(row) for row in refs[name]]})
                if len(picked) == TEST_COUNT:
                    break
            print(f"Verified ordered test staging: {len(picked)}/{TEST_COUNT} admitted.", flush=True)
            if len(picked) == TEST_COUNT:
                break
    check(len(picked) == TEST_COUNT, "Insufficient eligible held-out images")
    return {"scope": SCOPE, "fit_freeze_sha256": commitment, "csv_sha256": RAW_SHA,
            "test_zip_index_sha256": index, "candidate_order_sha256": digest("\n".join(order).encode()),
            "scorer_sha256": sha(__file__), "exclusions": excluded, "queries": picked}


def evaluate_grid(query, owners, encode):
    check(len(query) == len(set(query)) and set(query) == set(owners) and query, "Invalid query/gallery owners")
    rows, by_seed = [], []
    for seed in SEEDS:
        counts = {}
        for arm in ARMS:
            x, t = (np.array(z, dtype=np.float64, copy=True) for z in encode(seed, arm))
            check(x.ndim == t.ndim == 2 and len(x) == len(query) and len(t) == len(owners)
                  and x.shape[1] == t.shape[1], "Invalid embedding shape")
            for z in (x, t):
                norm = np.linalg.norm(z, axis=1)
                check(np.isfinite(norm).all() and (norm > 0).all(), "Invalid embedding norm")
                z /= norm[:,None]
            counts[arm] = hits_in_gallery(x, t, owners, query)
            rows.append({"seed": seed, "arm": arm, "hits": counts[arm], "r1": counts[arm]/len(query)})
        delta = {a:{c:(counts[a]-counts[c])/len(query) for c in CONTROLS} for a in GAMMA}
        by_seed.append({"seed": seed, "gamma_deltas": delta,
                        "worst_gamma_delta_vs_uniform": min(d["uniform"] for d in delta.values())})
    return rows, by_seed


def encode_checkpoint(staging, cell, seed, pixels, tokens, device):
    import torch
    from runner import inject
    from transformers import CLIPModel

    model = CLIPModel.from_pretrained(MODEL, local_files_only=True).to(device).float()
    inject(model, cell["ranks"], 20261119+seed)
    params = {n:p for n,p in model.named_parameters() if p.requires_grad}
    path = staging/cell["adapter_file"]
    check(sha(path) == cell["adapter_file_sha256"], "Checkpoint drift at reload")
    with torch.no_grad(), np.load(path, allow_pickle=False) as adapter:
        check(set(params) == set(adapter.files), "Adapter names mismatch")
        for name, p in params.items():
            check(tuple(p.shape) == adapter[name].shape, "Adapter shape mismatch")
            p.copy_(torch.from_numpy(adapter[name]))
        model.eval()
        images = [model.visual_projection(model.vision_model(pixel_values=x.to(device)).pooler_output).cpu()
                  for x in pixels.split(16)]
        texts = [model.text_projection(model.text_model(
            input_ids=tokens["input_ids"][i:i+64].to(device),
            attention_mask=tokens["attention_mask"][i:i+64].to(device)).pooler_output).cpu()
                 for i in range(0, len(tokens["input_ids"]), 64)]
        x, t = torch.cat(images).numpy(), torch.cat(texts).numpy()
        check(x.shape[1] == t.shape[1] == 512, "Unexpected CLIP projection dimension")
        return x, t


def score(staging, fit_hash, test_hash, cells, train, device):
    from PIL import Image
    torch = init_runtime(device)
    from transformers import CLIPProcessor, __version__ as transformers_version

    test = bound_json(staging/"PublicTestManifest.json", test_hash, "public test manifest")
    check(test["scope"] == SCOPE and test["fit_freeze_sha256"] == fit_hash
          and test["csv_sha256"] == RAW_SHA and test["scorer_sha256"] == sha(__file__)
          and len(test["queries"]) == TEST_COUNT, "Public test roster drift")
    proc = CLIPProcessor.from_pretrained(MODEL, local_files_only=True)
    query, pixels, owners, refs, ids = [], [], [], [], set()
    marks = train["calibration"] + train["train"] + [
        fingerprint((ROOT/"data/marine_captions"/n).read_bytes()) for n in sorted(train["source_image_sha256"])]
    for r in test["queries"]:
        name = r["image"]
        check(re.fullmatch(IMAGE_PATTERN.format(split="test"), name), "Non-test query")
        image = staging/"test_images"/name
        mark = fingerprint(image.read_bytes())
        check(all(r[k] == v for k,v in mark.items()) and not overlap(mark, marks), "Test image drift or overlap")
        marks.append(mark)
        with Image.open(image) as f:
            pixels.append(proc(images=f.convert("RGB"), return_tensors="pt")["pixel_values"])
        query.append(name)
        references = r["references"]
        check(references and references == sorted(references), "Invalid gallery reference order")
        for index, caption in references:
            check(type(index) is int and index not in ids and caption.strip(), "Duplicate/invalid gallery reference")
            ids.add(index)
            owners.append(name)
            refs.append(caption)
    pixels = torch.cat(pixels)
    tokens = proc.tokenizer(refs, padding="max_length", truncation=True, max_length=77, return_tensors="pt")

    rows, by_seed = evaluate_grid(query, owners, lambda seed, arm: encode_checkpoint(
        staging, cells[seed, arm], seed, pixels, tokens, device))
    return {"scope": SCOPE, "fit_freeze_sha256": fit_hash, "test_manifest_sha256": test_hash,
            "scorer_sha256": sha(__file__), "corpus_units": 1, "query_count": len(query),
            "caption_count": len(owners), "predictor_threshold": None, "cross_target_association": None,
            "runtime": {"device": device, "torch": torch.__version__, "transformers": transformers_version},
            "cells": rows, "by_seed": by_seed}


def run(staging, commitment, *, prepare=False, test_hash=None, device="cuda"):
    cells, train = validate_frozen_fit(staging, commitment)
    if prepare:
        path = staging/"PublicTestManifest.json"
        check(not path.exists(), "Refusing to overwrite frozen public test roster")
        emit(path, prepare_test(staging, train, commitment))
        print(f"Public test manifest SHA-256: {sha(path)}")
    elif test_hash:
        path = staging/"PublicCaseResults.json"
        check(not path.exists(), "Refusing to overwrite public-case results")
        emit(path, score(staging, commitment, test_hash, cells, train, device))
        print(f"Public case results SHA-256: {sha(path)}")
    else:
        print("PASS: 21 frozen fitted cells verified; no test caption fields read.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--verify-fit", action="store_true")
    mode.add_argument("--prepare-test", action="store_true")
    mode.add_argument("--score-test", metavar="TEST_MANIFEST_SHA256")
    p.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    p.add_argument("staging", type=Path)
    p.add_argument("fit_freeze_sha256")
    args = p.parse_args()
    stage = args.staging.resolve(strict=True)
    if stage == ROOT or stage.is_relative_to(ROOT):
        p.error("Private staging must be outside the project tree")
    run(stage, args.fit_freeze_sha256, prepare=args.prepare_test, test_hash=args.score_test, device=args.device)


if __name__ == "__main__":
    main()
