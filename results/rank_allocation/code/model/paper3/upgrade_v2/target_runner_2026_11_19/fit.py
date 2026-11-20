"""Local CLIP fitting primitives; the CLI accepts only a pinned source smoke."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE.parent / "target_utility_readiness_2026_11_19"
POOL = ROOT / "data/marine_captions"
MODEL_FILES = ("pytorch_model.bin", "config.json", "merges.txt", "vocab.json",
               "tokenizer.json", "tokenizer_config.json", "preprocessor_config.json", "special_tokens_map.json")


def ordered(items, seed):
    ids = list(items)
    if any(type(x) is not str or not x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError("Unique nonempty string IDs required")
    return sorted(ids, key=lambda x: (hashlib.sha256(f"P3-VizWiz-Pilot-v1:order:{seed}:{x}".encode()).digest(), x))


def paired_split(train, calibration):
    if not train or not calibration:
        raise ValueError("Empty fit or calibration split")
    rows = [*train.items(), *calibration.items()]
    for column in ([x for x, _ in rows], *zip(*(pair for _, pair in rows), strict=True)):
        if len(set(column)) != len(rows):
            raise ValueError("Overlap within or between fit and calibration splits")


def load_helper(path):
    from importlib.util import module_from_spec, spec_from_file_location
    spec = spec_from_file_location(path.stem, path)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def init_runtime(device):
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
        os.environ[key] = "1"
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import torch
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_num_threads(min(6, os.cpu_count() or 1))
    if device == "cuda":
        torch.cuda.reset_peak_memory_stats()
    return torch


def load_items(processor, image_dir, rows):
    from PIL import Image
    data = {}
    for key, filename, text in rows:
        if key in data or Path(filename).name != filename or not text.strip():
            raise ValueError("Duplicate example, unsafe path, or empty caption")
        with Image.open(image_dir / filename) as image:
            pixels = processor(images=image.convert("RGB"), return_tensors="pt")["pixel_values"][0]
        tokens = processor.tokenizer(text, padding="max_length", truncation=True,
                                     max_length=77, return_tensors="pt")
        data[key] = (pixels, tokens["input_ids"][0], tokens["attention_mask"][0])
    return data


def stack(data, keys, device):
    import torch
    return tuple(torch.stack(columns).to(device) for columns in zip(*(data[k] for k in keys), strict=True))


def calibrate(model, calibration, keys, device):
    from runner import BLOCKS, project
    sys.path.insert(0, str(ROOT))
    from src.lora import apply_lora_to_model
    import torch
    if tuple(sorted(keys)) != tuple(sorted(calibration)) or len(keys) < 2:
        raise ValueError("Calibration order must cover a nontrivial calibration split exactly once")
    torch.manual_seed(42)
    model.requires_grad_(False)
    model, _, _ = apply_lora_to_model(model, rank=8, alpha=16., dropout=0.,
                                     target_modules=["q_proj", "v_proj"],
                                     apply_to_vision=True, apply_to_text=True)
    model.to(device).float().eval()
    helper = load_helper(ROOT / "tools/_p462_gamma_real_vs_blank.py")
    blocks = helper.measure(model, *stack(calibration, keys, device), device)
    if set(blocks) != set(BLOCKS) or any(not math.isfinite(x) for v in blocks.values() for x in v.values()):
        raise ValueError("Invalid signed Gamma measurements")
    return {"fit_order": keys, "signed_blocks": blocks, "ranks": project([blocks[b]["gamma"] for b in BLOCKS]),
            "optimizer_updates": 0, "backward_passes": 2}


def fit_one(model, train, order, ranks, seed, device):
    import torch
    from torch.nn import functional as F
    from qualify import hash_parameters
    from runner import BUDGET, inject, train_epochs
    if len(order) % 8 or len(order) == 0 or sorted(order) != sorted(train):
        raise ValueError("Fit order must cover complete 8-pair batches exactly once")
    batches = [order[i:i+8] for i in range(0, len(order), 8)]
    model = model.to(device).float()
    frozen = list(model.parameters())
    base_digest = hash_parameters(frozen)
    adapters, block_counts = inject(model, ranks, 20261119 + seed)
    params = [p for p in model.parameters() if p.requires_grad]
    before = hash_parameters(params)
    optimizer = torch.optim.AdamW(params, lr=1e-4, weight_decay=0.)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=math.ceil(len(batches)/2))

    def loss(ids):
        px, ids, mask = stack(train, ids, device)
        logits = model(pixel_values=px, input_ids=ids, attention_mask=mask).logits_per_image
        labels = torch.arange(logits.shape[0], device=device)
        return (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels))/2

    model.train()
    clock = train_epochs([batches], list, loss, optimizer, scheduler, 2)
    after = hash_parameters(params)
    if (clock["example_sequence"] != batches or sum(x.numel() for x in params) != BUDGET
            or len(optimizer.state) != len(params) or base_digest != hash_parameters(frozen)
            or before == after or any(not torch.isfinite(p).all().item() for p in params)
            or scheduler.last_epoch != clock["update_count"]
            or {v["step"].item() for v in optimizer.state.values()} != {clock["update_count"]}):
        raise ValueError("Trainable budget, update clock, numerical or frozen-weight contract failed")
    return {"ranks": ranks, "actual_trainables": BUDGET, "block_trainables": block_counts,
            "adapter_tensors": 2 * len(adapters), "adapter_after_sha256": after,
            "frozen_parameters_unchanged": True, "clock": clock}


def smoke(device, out):
    torch = init_runtime(device)
    from transformers import CLIPModel, CLIPProcessor, __version__ as transformers_version
    from qualify import MODEL, MODEL_SHA, SOURCE_SHA, SOURCE as GAMMA_SOURCE, sha, emit, source_projection
    if sha(MODEL/"pytorch_model.bin") != MODEL_SHA or sha(GAMMA_SOURCE) != SOURCE_SHA:
        raise ValueError("Unpinned weights or source projection")
    readiness = load_helper(SOURCE / "readiness.py")
    inventory = json.loads((SOURCE / "Readiness.json").read_bytes())
    if readiness.verify_pins(inventory):
        raise ValueError("Pinned source asset drift")
    captions = json.loads((POOL / "captions.json").read_bytes())["captions"]
    if type(captions) is not list or len(captions) < 32:
        raise ValueError("Missing pinned 32-image prefix of the source caption pool")
    image_names = [f"{i:04d}.jpg" for i in range(32)]
    fingerprints = {name: readiness.fingerprint_image(POOL/name) for name in image_names}
    train_names, cal_names = image_names[:16], image_names[16:]
    pair = lambda names: {name: tuple(fingerprints[name][k] for k in ("raw_sha256", "pixel_sha256")) for name in names}
    paired_split(pair(train_names), pair(cal_names))
    proc = CLIPProcessor.from_pretrained(MODEL, local_files_only=True)
    train, cal = [load_items(proc, POOL, [(n, n, captions[int(n[:4])]) for n in names])
                  for names in (train_names, cal_names)]
    fresh = lambda: CLIPModel.from_pretrained(MODEL, local_files_only=True)
    start = time.monotonic()
    measured = calibrate(fresh(), cal, ordered(cal, 0), device)
    order = ordered(train, 0)
    ranks = {"uniform": (4, 4, 4, 4), "source_n2": source_projection()["seed_records"][0]["projected_source"][0]["rank"],
             "source_fixture_calibrated": measured["ranks"]}
    fit = {name: fit_one(fresh(), train, order, rank, 0, device) for name, rank in ranks.items()}
    for cell in fit.values():
        for k in ("example_sequence", "planned_updates", "update_count", "lr_used", "microbatches_per_update"):
            if cell["clock"][k] != fit["uniform"]["clock"][k]:
                raise ValueError("Clock mismatch across smoke arms")
    emit(out, {"scope": "SOURCE_FIXTURE_FIT_SOFTWARE_SMOKE_ONLY", "target_result": None,
               "training_ids": train_names, "calibration_ids": cal_names, "calibration": measured, "arms": fit,
               "inputs_sha256": {n: fingerprints[n]["raw_sha256"] for n in image_names},
               "captions_sha256": sha(POOL/"captions.json"), "model_sha256": {n: sha(MODEL/n) for n in MODEL_FILES},
               "script_sha256": {str(p.relative_to(ROOT).as_posix()): sha(p) for p in
                                 (HERE/"fit.py", HERE/"FitPlan.md", HERE/"runner.py", HERE/"qualify.py",
                                  ROOT/"src/lora.py", ROOT/"tools/_p462_gamma_real_vs_blank.py")},
               "source_draws_sha256": SOURCE_SHA, "runtime": {"device": device, "torch": torch.__version__,
               "transformers": transformers_version, "compute_wall_seconds": time.monotonic()-start,
               "peak_cuda_allocated_bytes": torch.cuda.max_memory_allocated() if device == "cuda" else None}})
    print("PASS: disjoint source-fixture calibration and three equal-budget fit arms; no target result")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", required=True, type=Path)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    args = parser.parse_args()
    if args.smoke.exists():
        parser.error("Select a new receipt path")
    smoke(args.device, args.smoke)


if __name__ == "__main__":
    main()
