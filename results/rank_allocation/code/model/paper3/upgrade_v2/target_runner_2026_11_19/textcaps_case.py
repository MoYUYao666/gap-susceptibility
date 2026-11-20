"""Re-run the matched-budget retrieval case on official TextCaps files."""

import argparse
from collections import defaultdict
from hashlib import file_digest
import json
from pathlib import Path
import re
from zipfile import ZipFile

from csv_intake import digest, emit, fingerprint, overlap
from fit import calibrate, fit_one, init_runtime, load_items, ordered
from fit_case import MODEL, SOURCE, check_clock, grid
from score_case import encode_checkpoint, evaluate_grid
from score_release import BUDGET, SEEDS, sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VIZ = ROOT.parent / "_research_data/VizWizCaptions20261119"
INPUTS = {
    "train": "e2b4ae504a230a80d2abc58bf57f7d4294b5340bbaa03252ebf1e26df69ca92d",
    "val": "1909abda82adefc7e998f5bd16b4bc03d0326507676b4de7c57499ad1b867f22",
}
ZIP_MD5 = "d12dd8098899044e4ae1af34db7ecfef"
SCOPE = "TEXTCAPS_SECOND_PUBLIC_RETRIEVAL_CASE_NOT_BLINDED"
SIZE = {"calibration": 16, "train": 512, "val": 256}


def read(path):
    return json.loads(path.read_bytes())


def roster(raw, split):
    result, ids = defaultdict(list), set()
    for row in raw["data"]:
        key, cid, caption = row["image_id"], row["caption_id"], row["caption_str"]
        path = row["image_path"]
        if (row["set_name"] != split or not re.fullmatch(r"[a-f0-9]{16}", key)
                or type(cid) is not int or cid in ids or not isinstance(caption, str)
                or path != f"train/{key}.jpg"):
            raise ValueError("Invalid annotation identifier, path, or split")
        ids.add(cid)
        if caption.strip():
            result[key].append([cid, caption.strip()])
    for refs in result.values():
        refs.sort()
    return result


def freeze(path, data):
    normalized = json.loads(json.dumps(data, allow_nan=False))
    if path.exists():
        if read(path) != normalized:
            raise ValueError(f"Immutable receipt differs: {path}")
    else:
        emit(path, normalized)
    return normalized


def prior_marks():
    for n, pin in (
        ("TrainManifest.json", None),
        ("PublicTestManifest.json", "9a9106069dd3107b38fa7b432dd0c4ec8cee04a1e101a98f6362c0fa2c4c3ae0"),
        ("FitDesign.json", None),
        ("FitFreeze.json", "0c89622954053bc32c65e4bd24c331226fa15c7418f863ba1f68432e6ee4d794"),
    ):
        if pin and sha(VIZ / n) != pin:
            raise ValueError("Prior VizWiz commitment drift")
    design = read(VIZ / "FitDesign.json")
    if (sha(VIZ / "FitDesign.json") != read(VIZ / "FitFreeze.json")["fit_design_sha256"]
            or sha(VIZ / "TrainManifest.json") != design["manifest_sha256"]):
        raise ValueError("Unbound prior training roster")
    train = read(VIZ / "TrainManifest.json")
    marks = train["train"] + train["calibration"] + read(VIZ / "PublicTestManifest.json")["queries"]
    for name, pin in train["source_image_sha256"].items():
        mark = fingerprint((ROOT / "data/marine_captions" / name).read_bytes())
        if mark["raw_sha256"] != pin:
            raise ValueError("Prior marine source image drift")
        marks.append(mark)
    return marks


def design():
    pins = read(HERE / "FitSmoke.json")["model_sha256"]
    if any(sha(MODEL / n) != h for n, h in pins.items()):
        raise ValueError("Model/processor drift")
    names = ("textcaps_case.py", "fit.py", "fit_case.py", "csv_intake.py", "runner.py",
             "qualify.py", "ProjectedSource.json", "score_case.py", "score_release.py")
    return {"scope": SCOPE, "input_sha256": INPUTS, "archive_md5": ZIP_MD5, "sizes": SIZE,
            "script_sha256": {n: sha(HERE / n) for n in names}, "model_sha256": pins,
            "helper_sha256": {n: sha(ROOT / n) for n in ("src/lora.py", "tools/_p462_gamma_real_vs_blank.py")},
            "metric": "owner-positive image-to-text R@1 over all retained references",
            "selection": "SHA-256 order on Open Images ID, first unique decoded images; lowest valid caption ID for fit",
            "practical_margin_pp": 1, "test_public": True, "no_threshold_fitted": True}


def admit(inputs, stage, split, count, marks, exclude):
    annotation = inputs / f"TextCaps_0.1_{split}.json"
    if sha(annotation) != INPUTS[split]:
        raise ValueError("TextCaps annotation fingerprint differs")
    rows = roster(read(annotation), split)
    if set(rows) & set(exclude):
        raise ValueError("Official fit and evaluation image IDs overlap")
    archive = inputs / "TextCapsImages.zip"
    with archive.open("rb") as f:
        if file_digest(f, "md5").hexdigest() != ZIP_MD5:
            raise ValueError("Image archive is incomplete or differs from publisher metadata")
    images = stage / "images"
    images.mkdir(exist_ok=True)
    selected, rejected = [], []
    with ZipFile(archive) as z:
        members = {}
        for member in z.namelist():
            if not member.endswith(".jpg"):
                continue
            key = Path(member).stem
            if key in members:
                raise ValueError("Duplicate image identifier in official ZIP")
            members[key] = member
        for key in sorted(rows, key=lambda k: digest(f"TextCaps-independent-roster-v1:{split}:{k}".encode())):
            payload = z.read(members[key])
            mark = fingerprint(payload)
            duplicate = overlap(mark, marks)
            if duplicate:
                rejected.append({"image_id": key, "reason": duplicate})
                continue
            name = key + ".jpg"
            p = images / name
            if p.exists() and p.read_bytes() != payload:
                raise ValueError("Cached image differs")
            if not p.exists():
                with p.open("xb") as f:
                    f.write(payload)
            record = {"image": name, "references": rows[key] if split == "val" else rows[key][:1], **mark}
            selected.append(record)
            marks.append(record)
            if len(selected) == count:
                break
    if len(selected) != count:
        raise ValueError("Rosters do not meet predeclared sample size")
    return freeze(stage / (split + "Roster.json"), {"scope": SCOPE, "rows": selected, "excluded": rejected,
                                                     "official_image_ids": sorted(rows)})


def fit(stage, train_roster, device):
    import numpy as np
    torch = init_runtime(device)
    from transformers import CLIPModel, CLIPProcessor, __version__ as transformers_version
    proc = CLIPProcessor.from_pretrained(MODEL, local_files_only=True)
    fresh = lambda: CLIPModel.from_pretrained(MODEL, local_files_only=True)
    rows = train_roster["rows"]
    data = lambda r: load_items(proc, stage / "images", [(v["image"], v["image"], v["references"][0][1]) for v in r])
    cal, train = data(rows[:16]), data(rows[16:])
    binding = {"design_sha256": sha(stage/"Design.json"), "train_roster_sha256": sha(stage/"trainRoster.json"),
               "device": device, "torch": torch.__version__, "transformers": transformers_version}
    calibration = stage / "Calibration.json"
    if not calibration.exists():
        freeze(calibration, {"binding": binding, "seeds": {
            str(s): calibrate(fresh(), cal, ordered(cal, s), device) for s in SEEDS}})
    measured = read(calibration)
    if measured["binding"] != binding:
        raise ValueError("Calibrated arm receipt is from a different run")
    ranks = grid(read(SOURCE), {s: r["ranks"] for s, r in measured["seeds"].items()})
    cells, clocks = [], {}
    for seed, arm in ranks:
        order = ordered(train, seed)
        name = f"S{seed}-{arm}"
        ref, adapter = stage / f"{name}.json", stage / f"{name}.npz"
        expected = {"seed": seed, "arm": arm, "ranks": ranks[seed, arm], "binding": binding,
                    "calibration_sha256": sha(calibration)}
        if not ref.exists():
            model = fresh()
            cell = fit_one(model, train, order, ranks[seed, arm], seed, device)
            check_clock(cell["clock"], order, clocks.get(seed))
            with adapter.open("xb") as f:
                np.savez(f, **{n: p.detach().cpu().numpy() for n,p in model.named_parameters() if p.requires_grad})
            del model
            freeze(ref, {**cell, **expected, "adapter_file": adapter.name, "adapter_file_sha256": sha(adapter)})
        cell = read(ref)
        if (any(cell[k] != v for k,v in expected.items()) or cell["actual_trainables"] != BUDGET
                or cell["frozen_parameters_unchanged"] is not True or cell["adapter_file"] != adapter.name
                or cell["adapter_file_sha256"] != sha(adapter)):
            raise ValueError("Invalid checkpoint or receipt")
        with np.load(adapter, allow_pickle=False) as bank:
            if sum(bank[n].size for n in bank.files) != BUDGET or not all(np.isfinite(bank[n]).all() for n in bank.files):
                raise ValueError("Invalid serialized checkpoint")
        clocks[seed] = check_clock(cell["clock"], order, clocks.get(seed))
        cells.append((ref.name, sha(ref)))
        print(f"Verified fitted TextCaps cell {len(cells)}/21: {name}", flush=True)
    return freeze(stage/"FitFreeze.json", {"binding": binding, "calibration_sha256": sha(calibration),
                                           "cells": cells, "val_reference_fields_read_during_fit": False})


def score(stage, heldout, fitted, device):
    from PIL import Image
    torch = init_runtime(device)
    from transformers import CLIPProcessor
    proc = CLIPProcessor.from_pretrained(MODEL, local_files_only=True)
    captions, owners, pixels, query = [], [], [], []
    for row in heldout["rows"]:
        name = row["image"]
        path = stage / "images" / name
        if fingerprint(path.read_bytes()) != {k: row[k] for k in ("raw_sha256","pixel_sha256","dhash64")}:
            raise ValueError("Evaluation image changed")
        with Image.open(path) as image:
            pixels.append(proc(images=image.convert("RGB"), return_tensors="pt")["pixel_values"])
        query.append(name)
        for _, caption in row["references"]:
            captions.append(caption)
            owners.append(name)
    cells = {}
    for name, pin in fitted["cells"]:
        if sha(stage/name) != pin:
            raise ValueError("Cell receipt drift before scoring")
        cell = read(stage/name)
        cells[cell["seed"], cell["arm"]] = cell
    x = torch.cat(pixels)
    t = proc.tokenizer(captions, padding="max_length", max_length=77, truncation=True, return_tensors="pt")
    rows, paired = evaluate_grid(query, owners, lambda s, a: encode_checkpoint(stage, cells[s,a], s, x, t, device))
    freeze(stage/"Results.json", {"scope": SCOPE, "fit_freeze_sha256": sha(stage/"FitFreeze.json"),
                                  "eval_roster_sha256": sha(stage/"valRoster.json"), "query_count": len(query),
                                  "reference_count": len(captions), "cells": rows, "by_seed": paired})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "run"))
    p.add_argument("inputs", type=Path)
    p.add_argument("stage", type=Path)
    p.add_argument("--device", choices=("cuda","cpu"), default="cuda")
    a = p.parse_args()
    a.stage.mkdir(parents=True, exist_ok=True)
    freeze(a.stage/"Design.json", design())
    marks = prior_marks()
    if a.mode == "plan":
        print(f"PASS: frozen design and {len(marks)} prior reference-image fingerprints.")
        return
    train = admit(a.inputs, a.stage, "train", SIZE["train"] + SIZE["calibration"], marks, ())
    print("Train/calibration roster fixed; starting local fit.", flush=True)
    fitted = fit(a.stage, train, a.device)
    heldout = admit(a.inputs, a.stage, "val", SIZE["val"], marks, train["official_image_ids"])
    score(a.stage, heldout, fitted, a.device)
    print("PASS: matched TextCaps public case scored; not independently blinded.", flush=True)


if __name__ == "__main__":
    main()
