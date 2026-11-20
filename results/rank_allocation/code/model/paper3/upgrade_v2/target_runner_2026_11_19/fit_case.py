"""Lock and fit the 21-arm public VizWiz case on train-only data; never scores."""
import argparse
import json
import math
from pathlib import Path

from csv_intake import CAL_COUNT, FIT_COUNT, HERE, RAW_SHA, ROOT, digest, emit, overlap, fingerprint
from fit import calibrate, fit_one, init_runtime, load_items, ordered
from score_release import ARMS, BUDGET, SEEDS, sha, validate_rank

MODEL = ROOT/"models/clip-vit-base-patch32"
SOURCE = HERE/"ProjectedSource.json"
STEPS = FIT_COUNT//16


def grid(projected, cal):
    if set(cal) != {str(s) for s in SEEDS}:
        raise ValueError("Calibration seed grid differs")
    if [r["seed"] for r in projected["seed_records"]] != list(SEEDS):
        raise ValueError("Projected source seed grid differs")
    result = {}
    for row in projected["seed_records"]:
        seed = row["seed"]
        cells = {f"gamma_n{x['size']}":x["rank"] for x in row["projected_source"]}
        cells.update(uniform=row["uniform"], random=row["random"], target_calibrated=cal[str(seed)])
        if set(cells) != set(ARMS):
            raise ValueError("Arm grid differs")
        for arm in ARMS:
            validate_rank(cells[arm])
            result[seed, arm] = cells[arm]
    return result


def check_clock(clock, order, expected=None):
    batches = [order[i:i+8] for i in range(0,len(order),8)]
    rates = clock["lr_used"]
    if (len(order) != FIT_COUNT or len(set(order)) != FIT_COUNT or clock["example_sequence"] != batches
            or clock["planned_updates"] != STEPS or clock["update_count"] != STEPS
            or clock["microbatches_per_update"] != [2]*STEPS or len(rates) != STEPS
            or any(len(v)!=1 or not math.isclose(v[0], 0.5e-4*(1+math.cos(math.pi*i/STEPS)), rel_tol=1e-12)
                   for i,v in enumerate(rates))):
        raise ValueError("Actual train order or paired cosine-update clock differs")
    signature = digest(json.dumps([batches, rates], separators=(",", ":")).encode())
    if expected is not None and expected != signature:
        raise ValueError("Actual clock differs from the paired arm")
    return signature


def validate_manifest_shape(doc):
    if (doc.get("mode") != "VIZWIZ_TRAIN_ONLY_MANIFEST" or doc.get("csv_sha256") != RAW_SHA
            or doc.get("scientific_result") is not None
            or doc.get("csv_routing",{}).get("evaluation_caption_fields_accessed") is not False):
        raise ValueError("Train-only admitted manifest required")
    if len(doc["train"]) != FIT_COUNT or len(doc["calibration"]) != CAL_COUNT:
        raise ValueError("Unexpected train or calibration population")
    rows = doc["train"] + doc["calibration"]
    if len({r["image"] for r in rows}) != len(rows) or len({r["annotation_id"] for r in rows}) != len(rows):
        raise ValueError("Overlapping fit and calibration IDs")


def load_train_manifest(staging, expected):
    import re
    manifest = staging/"TrainManifest.json"
    if sha(manifest) != expected:
        raise ValueError("Train manifest SHA-256 mismatch")
    doc = json.loads(manifest.read_bytes())
    validate_manifest_shape(doc)
    for name, h in doc["script_sha256"].items():
        if Path(name).name != name or sha(HERE/name) != h:
            raise ValueError("Frozen intake dependency drift")
    marks = []
    for n, h in sorted(doc["source_image_sha256"].items()):
        mark = fingerprint((ROOT/"data/marine_captions"/n).read_bytes())
        if mark["raw_sha256"] != h:
            raise ValueError("Source pool drift")
        marks.append(mark)
    for row in doc["calibration"] + doc["train"]:
        if not re.fullmatch(r"VizWiz_train_[0-9]+\.jpg", row["image"]):
            raise ValueError("Non-training image member")
        mark = fingerprint((staging/"train_images"/row["image"]).read_bytes())
        if (any(row[k] != v for k,v in mark.items()) or overlap(mark, marks) is not None
                or digest(row["caption"].encode()) != row["caption_sha256"]):
            raise ValueError("Input drift or image overlap")
        marks.append(mark)
    return doc


def train_case(staging, commitment, *, device, plan_only):
    doc = load_train_manifest(staging, commitment)
    model_pins = json.loads((HERE/"FitSmoke.json").read_bytes())["model_sha256"]
    if any(sha(MODEL/n) != h for n,h in model_pins.items()):
        raise ValueError("Local model or processor drift")
    fit_ids = [r["image"] for r in doc["train"]]
    cal_ids = [r["image"] for r in doc["calibration"]]
    order = {s:ordered(fit_ids,s) for s in SEEDS}
    cal_order = {s:ordered(cal_ids,s) for s in SEEDS}
    plan = {"scope":"VIZWIZ_PUBLIC_CASE_NOT_INDEPENDENT_OR_BLIND",
            "manifest_sha256":commitment, "model_sha256":model_pins,
            "script_sha256":{n:sha(HERE/n) for n in ("fit_case.py","fit.py","runner.py","ProjectedSource.json",
                                                     "CsvIntakePlan.md","FitPlan.md","VizWizImageIndex.json")},
            "legacy_sha256":{rel:sha(ROOT/rel) for rel in ("src/lora.py","tools/_p462_gamma_real_vs_blank.py")},
            "device":device, "order":order, "calibration_order":cal_order, "seeds":SEEDS, "arms":ARMS,
            "trainables_per_cell":BUDGET, "updates_per_cell":STEPS, "heldout_caption_access":False}
    plan = json.loads(json.dumps(plan))
    path = staging/"FitDesign.json"
    if plan_only:
        if path.exists():
            if json.loads(path.read_bytes()) != plan:
                raise ValueError("Existing plan differs from current plan")
        else:
            emit(path, plan)
        print("PASS: froze train/calibration rosters, backend/model pins and 21-cell design.")
        return
    if json.loads(path.read_bytes()) != plan:
        raise ValueError("Training design drift; verify plan first")

    torch = init_runtime(device)
    import numpy as np
    from transformers import CLIPModel, CLIPProcessor, __version__ as transformers_version
    proc = CLIPProcessor.from_pretrained(MODEL, local_files_only=True)
    load = lambda rows: load_items(proc, staging/"train_images", [(r["image"],r["image"],r["caption"]) for r in rows])
    fresh = lambda: CLIPModel.from_pretrained(MODEL, local_files_only=True)
    train, cal = load(doc["train"]), load(doc["calibration"])
    runtime = {"torch":torch.__version__, "transformers":transformers_version, "device":device}
    design_hash = sha(path)
    measured = {str(s):calibrate(fresh(),cal,cal_order[s],device) for s in SEEDS}
    measured = json.loads(json.dumps(measured, allow_nan=False))
    ranks = grid(json.loads(SOURCE.read_bytes()), {k:v["ranks"] for k,v in measured.items()})
    cal_receipt = {"fit_design_sha256":design_hash, "runtime":runtime, "per_seed":measured}
    cal_path = staging/"Calibration.json"
    if cal_path.exists():
        if json.loads(cal_path.read_bytes()) != cal_receipt:
            raise ValueError("Calibration differs from the already frozen receipt")
    else:
        emit(cal_path, cal_receipt)
    links, clocks = [], {}
    for (seed,arm), rank in ranks.items():
        cell_path = staging/f"S{seed}-{arm}.json"
        adapter_path = staging/f"S{seed}-{arm}.npz"
        expected = {"seed":seed, "arm":arm, "ranks":rank, "fit_design_sha256":design_hash,
                    "calibration_sha256":sha(cal_path), "runtime":runtime, "actual_trainables":BUDGET}
        if cell_path.exists():
            cell = json.loads(cell_path.read_bytes())
            if any(cell[k] != v for k,v in expected.items()) or sha(adapter_path) != cell["adapter_file_sha256"]:
                raise ValueError("Existing arm does not match frozen design")
        else:
            if adapter_path.exists():
                raise ValueError("Orphan checkpoint; do not overwrite or guess its receipt")
            model = fresh()
            receipt = fit_one(model, train, order[seed], rank, seed, device)
            check_clock(receipt["clock"], order[seed], clocks.get(seed))
            arrays = {n:p.detach().cpu().contiguous().numpy() for n,p in model.named_parameters() if p.requires_grad}
            if sum(a.size for a in arrays.values()) != BUDGET or not all(np.isfinite(a).all() for a in arrays.values()):
                raise ValueError("Adapter checkpoint budget or finiteness mismatch")
            with adapter_path.open("xb") as f:
                np.savez(f, **arrays)
            with np.load(adapter_path, allow_pickle=False) as reopened:
                if set(reopened.files) != set(arrays) or any(not np.array_equal(reopened[n],v) for n,v in arrays.items()):
                    raise ValueError("Persisted checkpoint differs from runtime adapter")
            cell = {**receipt, **expected, "adapter_file":adapter_path.name, "adapter_file_sha256":sha(adapter_path)}
            emit(cell_path, cell)
            del model, arrays
        clocks[seed] = check_clock(cell["clock"], order[seed], clocks.get(seed))
        links.append({"receipt":cell_path.name, "sha256":sha(cell_path), "adapter_sha256":cell["adapter_file_sha256"]})
        print(f"Verified {len(links)}/21 fitted cells: seed {seed}, {arm}.", flush=True)
    receipt = staging/"FitFreeze.json"
    obj = {"mode":"PUBLIC_DESCRIPTIVE_CASE_FIT_ONLY", "fit_design_sha256":design_hash,
           "calibration_sha256":sha(cal_path), "cells":links, "scientific_result":None}
    if receipt.exists():
        if json.loads(receipt.read_bytes()) != obj:
            raise ValueError("Fit freeze receipt drift")
    else:
        emit(receipt, obj)
    print("PASS: all 21 training checkpoints frozen; no held-out references have been scored.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    flags = parser.add_mutually_exclusive_group(required=True)
    flags.add_argument("--plan", action="store_true")
    flags.add_argument("--run", action="store_true")
    parser.add_argument("--device", choices=("cuda","cpu"), default="cuda")
    parser.add_argument("staging", type=Path)
    parser.add_argument("manifest_sha256")
    args = parser.parse_args()
    stage = args.staging.resolve(strict=True)
    if stage == ROOT or stage.is_relative_to(ROOT):
        parser.error("Private staging must be outside the project tree")
    train_case(stage, args.manifest_sha256, device=args.device, plan_only=args.plan)


if __name__ == "__main__":
    main()
