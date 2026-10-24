# -*- coding: utf-8 -*-
r"""A23 (IEEE JOE 26-0663): does ANY encoder pair transfer a threshold on the margin-mass statistic?

Context. The fine-epsilon certificate (tools/_p1472_a23_fine_eps.py,
outputs/analysis/a23_fine_eps_certificate.json) shows that M(eps) = P(margin <= 2 eps) is informative
WITHIN a domain at the domain's own resolution, and that no threshold on it transfers across domains or
encoders. That negative claim currently rests on two adapted encoders (BioCLIP, OceanCLIP) plus the
generic-CLIP control. This script widens the test: it re-encodes the SAME corpora with a registry of
frozen encoders and asks, for every ordered pair of (encoder, corpus) units, whether a threshold fitted
on the source unit's surgery family is better than chance on the target unit.

Registry (each entry declares loader, image preprocessing, embedding dimension, probe requirement):

    clip-vit-base-patch32    openai/clip-vit-base-patch32      transformers CLIP      512   no probe
    siglip-base-patch16-224  google/siglip-base-patch16-224    transformers SigLIP    768   no probe
    clip-vit-large-patch14   openai/clip-vit-large-patch14     transformers CLIP      768   no probe
    dinov2-base              facebook/dinov2-base              vision tower + probe   768   linear probe
    remoteclip               chendelong/RemoteCLIP             open_clip ViT-B-32     512   no probe
    bioclip                  imageomics/bioclip                open_clip ViT-B-16     512   no probe  (adapted)
    oceanclip                zjunlp/OceanCLIP-0.15B            open_clip ViT-B-16     512   no probe  (adapted)

The two adapted encoders are the ones the published negative claim rests on; they are registered so the
claim can be reproduced and extended in one table, and they are excluded from the default selection
(`--include-adapted` adds them).

Corpora (the same three image sets for every encoder):

    marine_optical    data/fathomnet8           343 images,  7 classes, chance 14.29 %
    acoustic_sonar    data/NKSID/NKSID         1783 images,  7 classes, chance 14.29 %
    rare_species      outputs/ocean_subset.json 1608 images, 67 classes, chance  1.49 %

`acoustic_sonar` enumerates class subdirectories only: the corpus's eighth class (`tire`, 834 `img_*.jpg`
files) sits at the corpus root and is skipped by construction, exactly as in tools/_p1344 and tools/_p1472.
Its chance level is therefore 1/7 = 14.29 %, not 1/8. Prompt templates are the archived ones
("a photo of a <class>" with underscores turned into spaces; "a photo of a <sciName>" for the subset), so
the archived certificate rows are reproduced rather than approximated.

Passes:

    --encode    encode every selected (encoder, corpus) once and cache the normalized embeddings to
                outputs/analysis/_cache/a23_multiencoder/<encoder>__<corpus>.npz (idempotent: a cache whose
                metadata and image fingerprint still match the corpus is reused, and --force re-encodes).
    --analyze   statistics only, from the cache: top-1, margin distribution, median margin, M(eps) on the
                fine grid {0.001..0.10}, the median-margin-relative and sigma-relative resolutions, the
                within-unit and pooled correlation with top-1, and the full ordered-pair transfer table with
                a paired bootstrap over images.
    --dry-run   print the plan and assert every number printed against the JSON the run writes.

Statistics. For every unit a surgery family of nine configurations is built exactly as in _p1472: the image
features are translated along the modality-gap direction, x_lambda = normalize(i + lambda * ||d|| * d_hat)
for lambda in {-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0}, plus one text-side configuration
("text1.0"). margin_i = s_i(y_i) - max_{c != y_i} s_i(c) and M(eps) = mean(1[margin <= 2 eps]) as before.
The health label of a configuration is the archived one: `top1 <= median(top1 over the unit's family)`
(_p1352/_p1370 convention -- the archive calls this label "healthy"; the sign is irrelevant to balanced
accuracy, and the naming is kept so the numbers are comparable with the archived transfer blocks).

Transfer test, per ordered pair (source unit -> target unit) and per statistic: the threshold on M that is
optimal on the source's family (exact search over the observed source values, i.e. over every breakpoint of
the balanced-accuracy step function; the archived code searched a 401-point linspace and is therefore a
sub-grid of this search) is applied to the target's family; the reported balanced accuracy is the target's,
against chance 0.50. The bootstrap resamples IMAGES with replacement (2000 draws by default), recomputes the
family statistics of source and target on each draw, refits the threshold on the resampled source and scores
the resampled target -- so the interval is paired whenever source and target share a corpus (the same image
indices are reused) and independent otherwise (recorded per pair as `bootstrap.paired`).

Outputs (new files only; no existing archive is read for writing and none is modified):
    outputs/analysis/a23_multiencoder_transfer.json
    outputs/analysis/_cache/a23_multiencoder/<encoder>__<corpus>.npz

The script NEVER downloads anything. Every model is loaded with local_files_only=True from either
<models-root>/<dir> or the local Hugging Face cache (HF_HOME / HF_HUB_CACHE). A missing model is a hard
error that names the repository id to fetch on the server (mirror first, ModelScope as fallback); the same
message is printed by --dry-run.

    D:\Anaconda\envs\pytorch\python.exe tools/_p1614_a23_multi_encoder_transfer.py --dry-run
    D:\Anaconda\envs\pytorch\python.exe tools/_p1614_a23_multi_encoder_transfer.py --encode --analyze
    D:\Anaconda\envs\pytorch\python.exe tools/_p1614_a23_multi_encoder_transfer.py --encode --analyze \
        --encoders clip-vit-base-patch32 --include-adapted --boot 2000

Cloud (paths configurable, same code):
    python tools/_p1614_a23_multi_encoder_transfer.py --data-root /root/autodl-tmp/p3work/data \
        --models-root /root/autodl-tmp/p3work/models --cache-root outputs/analysis/_cache/a23_multiencoder \
        --encode --analyze
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import socket
import subprocess
import sys
import time

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_REL = "outputs/analysis/a23_multiencoder_transfer.json"
OUT = os.path.join(REPO, OUT_REL)
DEFAULT_CACHE_ROOT = os.path.join(REPO, "outputs", "analysis", "_cache", "a23_multiencoder")
DEFAULT_DATA_ROOT = os.path.join(REPO, "data")
DEFAULT_MODELS_ROOT = os.path.join(REPO, "models")
DEFAULT_SUBSET_JSON = os.path.join(REPO, "outputs", "ocean_subset.json")

REF_CONTROL = "outputs/analysis/a23_certificate_control.json"
REF_ADAPTED = "outputs/analysis/a23_certificate_adapted.json"

EPS_FINE = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.10]
EPS_ARCHIVED = [0.02, 0.05, 0.10]
C_MEDREL = [0.005, 0.01, 0.02]      # eps_row = c * median_i margin_i   (the resolution asked for)
C_SIGMAREL = [0.005, 0.01, 0.02]    # eps_row = c * sigma_D             (kept for continuity with _p1472)
LAMBDAS = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0, 2.0]
TEXT_ROW = "text1.0"
N_BOOT_DEFAULT = 2000
PROBE_SEED = 0
PROBE_PROTOCOL = ("no-bias multinomial logistic regression on L2-normalized frozen features (a cosine "
                  "classifier head), fitted on the CPU with full-batch Adam (lr 0.05, weight decay 1e-4, "
                  "400 epochs, torch.manual_seed(0)) on a stratified 70/30 split drawn with "
                  "numpy.random.default_rng(0); the 30 % held-out split is the only part used for the "
                  "reported top-1 and margins, so the probe is always out-of-sample")
PROBE_TEST_FRAC = 0.30
CACHE_VERSION = 1
REPRO_TOL = 1e-6

STAT_KEYS = ([("mass_%g" % e).replace(".", "p") for e in EPS_FINE]
             + [("mass_medrel_%g" % c).replace(".", "p") for c in C_MEDREL]
             + [("mass_sigmarel_%g" % c).replace(".", "p") for c in C_SIGMAREL])


def eps_key(e: float) -> str:
    return ("mass_%g" % e).replace(".", "p")


def medrel_key(c: float) -> str:
    return ("mass_medrel_%g" % c).replace(".", "p")


def sigmarel_key(c: float) -> str:
    return ("mass_sigmarel_%g" % c).replace(".", "p")


# --------------------------------------------------------------------------------------------------
# registry
# --------------------------------------------------------------------------------------------------
# Resolution model. Every asset of an encoder is declared by (local path relative to --models-root,
# repository id, required file names). On this workstation the assets live under models/; on the cloud
# they are normally inside the Hugging Face cache that HF_HOME points at, and are found with
# huggingface_hub.snapshot_download(<repo>, local_files_only=True) -- which never touches the network.
ENCODERS = {
    "clip-vit-base-patch32": {
        "group": "generic",
        "repo_id": "openai/clip-vit-base-patch32",
        "loader": "transformers AutoModel (CLIPModel): vision_model + visual_projection, text_model + text_projection",
        "preprocess": "auto processor from the snapshot: RGB, shortest side -> 224 (bicubic), centre crop 224, CLIP mean/std",
        "embed_dim": 512,
        "probe": False,
        "probe_protocol": None,
        "kind": "transformers_dual",
        "assets": {
            "snapshot": {"local": "clip-vit-base-patch32", "repo_id": "openai/clip-vit-base-patch32",
                         "files": ["config.json", "preprocessor_config.json"]},
            "weights": {"local": "clip-vit-base-patch32", "repo_id": "openai/clip-vit-base-patch32",
                        "files": ["pytorch_model.bin"]},
        },
        "notes": "the generic-CLIP control of the published negative claim (tools/_p1344)",
    },
    "siglip-base-patch16-224": {
        "group": "generic",
        "repo_id": "google/siglip-base-patch16-224",
        "loader": "transformers AutoModel (SiglipModel): vision_model + visual_projection, text_model + text_projection",
        "preprocess": "auto processor from the snapshot: RGB, resize to 224x224 (bicubic), rescale 1/255, mean/std 0.5",
        "embed_dim": 768,
        "probe": False,
        "probe_protocol": None,
        "kind": "transformers_dual",
        "assets": {
            "snapshot": {"local": "siglip-base-patch16-224", "repo_id": "google/siglip-base-patch16-224",
                         "files": ["config.json", "preprocessor_config.json"]},
            "weights": {"local": "siglip-base-patch16-224", "repo_id": "google/siglip-base-patch16-224",
                        "files": ["model.safetensors"]},
        },
        "notes": "sigmoid-loss dual encoder: a different training objective on the same corpora",
    },
    "clip-vit-large-patch14": {
        "group": "generic",
        "repo_id": "openai/clip-vit-large-patch14",
        "loader": "transformers AutoModel (CLIPModel): vision_model + visual_projection, text_model + text_projection",
        "preprocess": "auto processor from the snapshot: RGB, shortest side -> 224 (bicubic), centre crop 224, CLIP mean/std",
        "embed_dim": 768,
        "probe": False,
        "probe_protocol": None,
        "kind": "transformers_dual",
        "assets": {
            "snapshot": {"local": "clip-vit-large-patch14", "repo_id": "openai/clip-vit-large-patch14",
                         "files": ["config.json", "preprocessor_config.json", "tokenizer.json", "vocab.json", "merges.txt"]},
            "weights": {"local": "clip-vit-large-patch14", "repo_id": "openai/clip-vit-large-patch14",
                        "files": ["model.safetensors"]},
        },
        "notes": "same recipe as the control at 3x the width: is the failure a property of the scale?",
    },
    "dinov2-base": {
        "group": "generic",
        "repo_id": "facebook/dinov2-base",
        "loader": "transformers AutoModel (Dinov2Model, vision tower only) + a linear probe for top-1",
        "preprocess": "auto image processor from the snapshot: RGB, resize shortest side 256 (bicubic), centre crop 224, ImageNet mean/std",
        "embed_dim": 768,
        "probe": True,
        "probe_protocol": PROBE_PROTOCOL,
        "kind": "transformers_vision_probe",
        "assets": {
            "snapshot": {"local": "dinov2-base", "repo_id": "facebook/dinov2-base",
                         "files": ["config.json", "preprocessor_config.json"]},
            "weights": {"local": "dinov2-base", "repo_id": "facebook/dinov2-base",
                        "files": ["model.safetensors"]},
        },
        "notes": ("self-supervised vision backbone with no text tower: it has no prompt-based zero-shot "
                  "head, so top-1 comes from the frozen-feature probe declared in probe_protocol, and the "
                  "cached text-side matrix is the probe's L2-normalized weight matrix (a cosine head)"),
    },
    "remoteclip": {
        "group": "generic",
        "repo_id": "chendelong/RemoteCLIP",
        "loader": "open_clip ViT-B-32 + load_state_dict from RemoteCLIP-ViT-B-32.pt",
        "preprocess": "open_clip ViT-B-32 transforms: RGB, resize shortest side 224 (bicubic), centre crop 224, CLIP mean/std",
        "embed_dim": 512,
        "probe": False,
        "probe_protocol": None,
        "kind": "open_clip",
        "arch": "ViT-B-32",
        "assets": {
            "weights": {"local": "RemoteCLIP/RemoteCLIP-ViT-B-32.pt", "repo_id": "chendelong/RemoteCLIP",
                        "files": ["RemoteCLIP-ViT-B-32.pt"]},
        },
        "notes": ("remote-sensing CLIP, i.e. an encoder adapted to a different imagery domain; the repo "
                  "also ships RN50 and ViT-L/14 checkpoints -- fetch only the ViT-B/32 file"),
    },
    "bioclip": {
        "group": "adapted",
        "repo_id": "imageomics/bioclip",
        "loader": "open_clip ViT-B-16 + load_state_dict from open_clip_pytorch_model.bin",
        "preprocess": "open_clip ViT-B-16 transforms (from open_clip_config.json when present): RGB, resize shortest side 224, centre crop 224, CLIP mean/std",
        "embed_dim": 512,
        "probe": False,
        "probe_protocol": None,
        "kind": "open_clip",
        "arch": "ViT-B-16",
        "assets": {
            "weights": {"local": "oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin",
                        "repo_id": "imageomics/bioclip",
                        "files": ["open_clip_pytorch_model.bin", "open_clip_config.json"]},
        },
        "notes": "adapted encoder #1 of the published negative claim (tools/_p1352); primary corpus rare_species",
    },
    "oceanclip": {
        "group": "adapted",
        "repo_id": "zjunlp/OceanCLIP-0.15B",
        "loader": "open_clip ViT-B-16 initialised from BioCLIP, then load_state_dict from epoch_50.pt (inner state_dict)",
        "preprocess": "open_clip ViT-B-16 transforms of the BioCLIP base config: RGB, resize shortest side 224, centre crop 224, CLIP mean/std",
        "embed_dim": 512,
        "probe": False,
        "probe_protocol": None,
        "kind": "open_clip",
        "arch": "ViT-B-16",
        "assets": {
            "base_weights": {"local": "oceanclip-0.15b/bioclip/open_clip_pytorch_model.bin",
                             "repo_id": "imageomics/bioclip",
                             "files": ["open_clip_pytorch_model.bin"]},
            "weights": {"local": "oceanclip-0.15b/oceanclip-bio/epoch_50.pt",
                        "repo_id": "zjunlp/OceanCLIP-0.15B",
                        "files": ["epoch_50.pt"]},
        },
        "notes": ("adapted encoder #2 of the published negative claim (tools/_p1352); epoch_50.pt is a "
                  "trainer checkpoint whose weights live under the 'state_dict' key; primary corpus rare_species"),
    },
}

CORPORA = {
    "marine_optical": {
        "kind": "class_dirs",
        "rel": "fathomnet8",
        "prompt_template": "a photo of a {name}",
        "name_rule": "directory name with underscores replaced by spaces",
        "expected_images": 343,
        "expected_classes": 7,
        "note": ("FathomNet-derived optical tree: 7 class subdirectories (343 images) plus a root-level "
                 "meta.json that the loader ignores; chance level 1/7 = 14.29 %"),
    },
    "acoustic_sonar": {
        "kind": "class_dirs",
        "rel": "NKSID/NKSID",
        "prompt_template": "a photo of a {name}",
        "name_rule": "directory name with underscores replaced by spaces",
        "expected_images": 1783,
        "expected_classes": 7,
        "note": ("NKSID Bohai Bay sonar: 7 class subdirectories (1783 images). The eighth class `tire` "
                 "(834 img_*.jpg files) sits at the corpus root and is skipped by construction, as in "
                 "tools/_p1344 and tools/_p1472; chance level is therefore 1/7 = 14.29 %, not 1/8"),
    },
    "rare_species": {
        "kind": "subset_json",
        "rel": "rare-species/data",
        "prompt_template": "a photo of a {name}",
        "name_rule": "scientific name from outputs/ocean_subset.json:classes",
        "expected_images": 1608,
        "expected_classes": 67,
        "note": ("the 67-class marine subset (24 images per class, 1608 total) selected by "
                 "outputs/ocean_subset.json:subset_idx from data/rare-species/data/*.parquet; the prompt "
                 "template is the archived adapted one (tools/_p1352), i.e. 'a photo of a <sciName>', so "
                 "the archived adapted rows are reproduced exactly"),
    },
}


def log(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print("  " + msg, flush=True)


# --------------------------------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------------------------------
def pearson(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if len(a) < 3 or np.std(a) == 0 or np.std(b) == 0:
        return None
    r = float(np.corrcoef(a, b)[0, 1])
    return r if np.isfinite(r) else None


def bal_acc(pred, truth):
    """Balanced accuracy; None when either class is empty (the archived helper coerced the empty
    denominator to 1 instead, which yields 0.5 -- degenerate rows are marked here rather than scored)."""
    pred = np.asarray(pred, dtype=bool)
    truth = np.asarray(truth, dtype=bool)
    pos, neg = bool(truth.any()), bool((~truth).any())
    if not pos or not neg:
        return None
    tpr = float(np.sum(pred & truth)) / float(np.sum(truth))
    tnr = float(np.sum(~pred & ~truth)) / float(np.sum(~truth))
    return float(0.5 * (tpr + tnr))


def bal_acc_vec(pred, truth):
    """Vectorised balanced accuracy over the last axis. pred/truth: (..., n) boolean arrays.

    Returns (...,) float arrays; entries whose truth row is single-class are NaN.
    """
    pred = np.asarray(pred, dtype=bool)
    truth = np.asarray(truth, dtype=bool)
    tp = np.sum(pred & truth, axis=-1).astype(np.float64)
    fn = np.sum(~pred & truth, axis=-1).astype(np.float64)
    tn = np.sum(~pred & ~truth, axis=-1).astype(np.float64)
    fp = np.sum(pred & ~truth, axis=-1).astype(np.float64)
    with np.errstate(invalid="ignore", divide="ignore"):
        tpr = np.where((tp + fn) > 0, tp / np.maximum(tp + fn, 1.0), np.nan)
        tnr = np.where((tn + fp) > 0, tn / np.maximum(tn + fp, 1.0), np.nan)
    out = 0.5 * (tpr + tnr)
    return out


def vec_median(x, axis):
    """np.median without the RuntimeWarning noise for degenerate columns."""
    with np.errstate(invalid="ignore"):
        return np.median(x, axis=axis)


def linear_hist(values, edges=21):
    values = np.asarray(values, dtype=np.float64)
    if values.size == 0:
        return {"edges": [], "counts": []}
    lo, hi = float(values.min()), float(values.max())
    if hi <= lo:
        hi = lo + 1e-9
    grid = np.linspace(lo, hi, edges)
    counts, edges_out = np.histogram(values, bins=grid)
    return {"edges": [float(x) for x in edges_out], "counts": [int(c) for c in counts]}


def quantiles(values) -> dict:
    v = np.asarray(values, dtype=np.float64)
    q = [0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 1.0]
    qs = np.quantile(v, q) if v.size else np.zeros(len(q))
    out = {("q%02d" % int(round(x * 100))): float(y) for x, y in zip(q, qs)}
    out["mean"] = float(np.mean(v)) if v.size else None
    out["std"] = float(np.std(v)) if v.size else None
    out["min"] = float(np.min(v)) if v.size else None
    out["max"] = float(np.max(v)) if v.size else None
    return out


def sha1_text(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def sha1_file(path: str) -> str:
    h = hashlib.sha1()
    with io.open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_size(path: str):
    if not os.path.exists(path):
        return None
    total, n = 0, 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
                n += 1
            except OSError:
                pass
    return total, n


def git_info():
    def run(args):
        try:
            p = subprocess.run(["git"] + args, cwd=REPO, capture_output=True, text=True, timeout=20)
            return p.stdout.strip() if p.returncode == 0 else None
        except Exception:
            return None
    commit = run(["rev-parse", "HEAD"])
    status = run(["status", "--porcelain"])
    lines = [l for l in (status or "").splitlines() if l.strip()]
    return {
        "commit": commit,
        "dirty": bool(lines),
        "status_porcelain": lines[:40],
        "status_porcelain_entries": len(lines),
    }


def host_info() -> dict:
    info = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
    }
    try:
        import torch
        info["torch"] = torch.__version__
        info["torch_cuda"] = torch.version.cuda
        info["cuda_available"] = bool(torch.cuda.is_available())
        info["cuda_device_count"] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
        info["cuda_device_name"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception as exc:  # pragma: no cover
        info["torch"] = "unavailable: %s" % exc
    for mod in ("transformers", "open_clip", "numpy"):
        try:
            m = __import__(mod)
            info[mod + "_version"] = getattr(m, "__version__", "?")
        except Exception:
            info[mod + "_version"] = None
    return info


# --------------------------------------------------------------------------------------------------
# model resolution -- never downloads
# --------------------------------------------------------------------------------------------------
def _find_file(root: str, name: str):
    """Locate `name` under `root` (flat or nested); exact basename match first, then a suffix match."""
    direct = os.path.join(root, name)
    if os.path.isfile(direct):
        return direct
    for cur, _dirs, files in os.walk(root):
        if name in files:
            return os.path.join(cur, name)
    for cur, _dirs, files in os.walk(root):
        for f in files:
            if f.endswith(name):
                return os.path.join(cur, f)
    return None


def fetch_hint(asset: dict) -> str:
    repo = asset["repo_id"]
    files = ", ".join(asset["files"])
    return ("fetch on the server (mirror first, ModelScope as fallback; never upload from the laptop):\n"
            "      export HF_ENDPOINT=https://hf-mirror.com; export HF_HOME=/root/autodl-tmp/hf\n"
            "      python -c \"from huggingface_hub import snapshot_download; "
            "print(snapshot_download('%s'))\"            # required file(s): %s\n"
            "      python -c \"from modelscope import snapshot_download; "
            "print(snapshot_download('%s'))\"            # fallback if the mirror is slow" % (repo, files, repo))


def resolve_assets(enc_id: str, models_root: str):
    """Resolve every asset of an encoder. Returns (resolved, problems, provenance)."""
    enc = ENCODERS[enc_id]
    resolved, problems, prov = {}, [], {}
    hf_cache_root = os.environ.get("HF_HUB_CACHE") or os.path.join(
        os.environ.get("HF_HOME", os.path.join(os.path.expanduser("~"), ".cache", "huggingface")), "hub")

    def try_local(asset):
        base = os.path.join(models_root, asset["local"])
        if os.path.isfile(base):
            return base if any(os.path.basename(base) == f for f in asset["files"]) else None
        if not os.path.isdir(base):
            return None
        for f in asset["files"]:
            if _find_file(base, f) is None:
                return None
        return base

    def try_hf_cache(asset):
        try:
            from huggingface_hub import snapshot_download
        except Exception:
            return None
        try:
            snap = snapshot_download(asset["repo_id"], local_files_only=True)
        except Exception:
            return None
        if not snap or not os.path.isdir(snap):
            return None
        for f in asset["files"]:
            if _find_file(snap, f) is None:
                return None
        return snap

    for key, asset in enc["assets"].items():
        path = try_local(asset)
        mode = "local_dir"
        if path is None:
            path = try_hf_cache(asset)
            mode = "hf_cache"
        if path is None:
            problems.append("encoder '%s' asset '%s' is missing: no %s under %s and no local Hugging Face "
                            "cache entry for %s (HF_HUB_CACHE=%s)\n      %s"
                            % (enc_id, key, " or ".join(asset["files"]),
                               os.path.join(models_root, asset["local"]), asset["repo_id"], hf_cache_root,
                               fetch_hint(asset)))
            continue
        resolved[key] = path
        size = dir_size(path) if os.path.isdir(path) else (os.path.getsize(path), 1)
        prov[key] = {"mode": mode, "path": path, "repo_id": asset["repo_id"],
                     "required_files": asset["files"], "size_mb": round(size[0] / 1048576.0, 1),
                     "files": size[1]}
    return resolved, problems, prov


# --------------------------------------------------------------------------------------------------
# corpora
# --------------------------------------------------------------------------------------------------
def load_corpus(corpus_id: str, data_root: str, subset_json: str, quiet: bool = False) -> dict:
    """Return {"items": [(PIL image, label)], "class_names": [...], "audit": {...}} for one corpus."""
    from PIL import Image
    spec = CORPORA[corpus_id]
    audit = {"corpus": corpus_id, "kind": spec["kind"], "expected_images": spec["expected_images"],
             "expected_classes": spec["expected_classes"], "prompt_template": spec["prompt_template"],
             "note": spec["note"]}
    items, class_names, fingerprint = [], [], None

    if spec["kind"] == "class_dirs":
        root = os.path.join(data_root, spec["rel"])
        audit["path"] = os.path.relpath(root, REPO).replace("\\", "/") if root.startswith(REPO) else root
        audit["root_exists"] = os.path.isdir(root)
        if not audit["root_exists"]:
            audit["error"] = "corpus root not found: %s" % root
            return {"items": [], "class_names": [], "audit": audit, "fingerprint": None}
        classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
        per_class, skipped = {}, 0
        h = hashlib.sha1()
        for ci, c in enumerate(classes):
            files = sorted(f for f in os.listdir(os.path.join(root, c))
                           if f.lower().endswith((".jpg", ".jpeg", ".png")))
            per_class[c] = len(files)
            for f in files:
                h.update((c + "/" + f + "\n").encode("utf-8"))
                try:
                    items.append((Image.open(os.path.join(root, c, f)).convert("RGB"), ci))
                except Exception as exc:
                    skipped += 1
                    log("skipped unreadable %s/%s: %s" % (c, f, exc), quiet)
        fingerprint = h.hexdigest()
        class_names = [c.replace("_", " ") if spec["name_rule"].startswith("directory") else c for c in classes]
        root_files = [f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))]
        audit.update({"n_classes": len(classes), "classes": classes, "images_per_class": per_class,
                      "n_images": len(items), "n_unreadable": skipped,
                      "root_level_files_ignored": len(root_files),
                      "root_level_files_note": ("files at the corpus root are not enumerated (this is how the "
                                                "eighth sonar class `tire` is excluded, as in _p1344/_p1472)")})
    else:  # subset_json
        from datasets import load_dataset
        data_dir = os.path.join(data_root, spec["rel"])
        audit["path"] = os.path.relpath(data_dir, REPO).replace("\\", "/") if data_dir.startswith(REPO) else data_dir
        audit["subset_json"] = os.path.relpath(subset_json, REPO).replace("\\", "/") \
            if subset_json.startswith(REPO) else subset_json
        if not os.path.isdir(data_dir) or not os.path.exists(subset_json):
            audit["error"] = "missing %s or %s" % (data_dir, subset_json)
            return {"items": [], "class_names": [], "audit": audit, "fingerprint": None}
        sub = json.load(io.open(subset_json, encoding="utf-8"))
        idx = list(sub["subset_idx"])
        files = sorted(os.path.join(data_dir, f) for f in os.listdir(data_dir))
        ds = load_dataset("parquet", data_files=files, split="train")
        for j in idx:
            b = ds[j]["file_name"]
            if isinstance(b, dict):
                im = Image.open(io.BytesIO(b["bytes"])) if b.get("bytes") else Image.open(b["path"])
            else:
                im = b
            items.append((im.convert("RGB"), int(sub["classes"].index(ds[j]["sciName"]))))
        class_names = list(sub["classes"])
        fingerprint = sha1_text("|".join(os.path.basename(f) for f in files)
                                + "|" + sha1_file(subset_json)
                                + "|" + ",".join(str(i) for i in idx))
        audit.update({"n_classes": len(class_names), "classes": class_names,
                      "n_images": len(items), "parquet_files": [os.path.basename(f) for f in files],
                      "subset_json_sha1": sha1_file(subset_json),
                      "subset_class_counts": sub.get("class_counts")})
    return {"items": items, "class_names": class_names, "audit": audit, "fingerprint": fingerprint}


def corpus_plan(data_root: str, subset_json: str) -> dict:
    """Cheap corpus census for the plan/dry-run (no images decoded, no parquet read)."""
    out = {}
    for cid, spec in CORPORA.items():
        entry = {"kind": spec["kind"], "expected_images": spec["expected_images"],
                 "expected_classes": spec["expected_classes"], "chance_percent": round(100.0 / spec["expected_classes"], 4)}
        if spec["kind"] == "class_dirs":
            root = os.path.join(data_root, spec["rel"])
            entry["path"] = os.path.relpath(root, REPO).replace("\\", "/") if root.startswith(REPO) else root
            if os.path.isdir(root):
                classes = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
                counts = {c: len([f for f in os.listdir(os.path.join(root, c))
                                  if f.lower().endswith((".jpg", ".jpeg", ".png"))]) for c in classes}
                entry.update({"n_classes": len(classes), "n_images": int(sum(counts.values())),
                              "images_per_class": counts,
                              "root_level_files": len([f for f in os.listdir(root)
                                                       if os.path.isfile(os.path.join(root, f))]),
                              "chance_percent_from_disk": round(100.0 / max(len(classes), 1), 4)})
            else:
                entry["missing"] = True
        else:
            data_dir = os.path.join(data_root, spec["rel"])
            entry["path"] = os.path.relpath(data_dir, REPO).replace("\\", "/") if data_dir.startswith(REPO) else data_dir
            if os.path.isdir(data_dir) and os.path.exists(subset_json):
                sub = json.load(io.open(subset_json, encoding="utf-8"))
                entry.update({"n_classes": len(sub["classes"]), "n_images": int(sub.get("n_images", len(sub["subset_idx"]))),
                              "parquet_files": len([f for f in os.listdir(data_dir) if f.endswith(".parquet")]),
                              "chance_percent_from_disk": round(100.0 / max(len(sub["classes"]), 1), 4)})
            else:
                entry["missing"] = True
        out[cid] = entry
    return out


# --------------------------------------------------------------------------------------------------
# encoders
# --------------------------------------------------------------------------------------------------
class ImageTextEncoder:
    """Thin adapter over the three loader kinds; image() and text() return L2-normalized float32 rows."""

    def __init__(self, enc_id: str, resolved: dict, device: str, batch: int = 32):
        self.enc_id, self.device, self.batch = enc_id, device, batch
        self.enc = ENCODERS[enc_id]
        self.kind = self.enc["kind"]
        self.load_report = {}
        self._build(resolved)
        self.probe_weights = None
        self.probe_stats = None

    # ---- construction --------------------------------------------------------------------------
    def _build(self, resolved):
        import torch
        self.torch = torch
        if self.kind in ("transformers_dual", "transformers_vision_probe"):
            from transformers import AutoModel, AutoProcessor, AutoImageProcessor
            snap = resolved["snapshot"]
            self.model = AutoModel.from_pretrained(snap, local_files_only=True).to(self.device).eval()
            if self.kind == "transformers_dual":
                self.processor = AutoProcessor.from_pretrained(snap, local_files_only=True)
            else:
                self.processor = AutoImageProcessor.from_pretrained(snap, local_files_only=True)
        else:
            import open_clip
            self.open_clip = open_clip
            arch = self.enc["arch"]
            model, _, preprocess = open_clip.create_model_and_transforms(arch, pretrained=None,
                                                                        device=self.device)
            self.model, self.preprocess = model.eval(), preprocess
            self.tokenizer = open_clip.get_tokenizer(arch)
            for key in ("base_weights", "weights"):
                if key not in resolved:
                    continue
                path = resolved[key]
                try:
                    ckpt = torch.load(path, map_location="cpu", weights_only=False)
                except TypeError:  # older torch
                    ckpt = torch.load(path, map_location="cpu")
                sd = ckpt
                if isinstance(ckpt, dict):
                    for inner in ("state_dict", "model", "model_state_dict"):
                        if inner in ckpt and isinstance(ckpt[inner], dict):
                            sd = ckpt[inner]
                            break
                if not isinstance(sd, dict):
                    raise RuntimeError("checkpoint %s does not contain a state dict" % path)
                sd = {k[len("module."):] if k.startswith("module.") else k: v for k, v in sd.items()}
                missing, unexpected = self.model.load_state_dict(sd, strict=False)
                self.load_report[key] = {
                    "path": path, "state_dict_keys": len(sd),
                    "missing_keys": len(missing), "unexpected_keys": len(unexpected),
                    "missing_examples": sorted(missing)[:8], "unexpected_examples": sorted(unexpected)[:8],
                }
                if missing:
                    raise RuntimeError(
                        "loading %s left %d parameters uninitialised (first: %s); refusing to encode with a "
                        "partially random model" % (path, len(missing), sorted(missing)[:5]))
        self.dim = int(self.enc["embed_dim"])

    # ---- inference -----------------------------------------------------------------------------
    def image(self, images):
        t = self.torch
        feats = []
        with t.no_grad():
            for i in range(0, len(images), self.batch):
                chunk = images[i:i + self.batch]
                if self.kind == "transformers_dual":
                    inp = self.processor(images=chunk, return_tensors="pt").to(self.device)
                    out = self.model.vision_model(pixel_values=inp["pixel_values"])
                    pooled = out.pooler_output if hasattr(out, "pooler_output") else out[1]
                    f = self.model.visual_projection(pooled)
                elif self.kind == "transformers_vision_probe":
                    inp = self.processor(images=chunk, return_tensors="pt").to(self.device)
                    out = self.model(pixel_values=inp["pixel_values"])
                    f = out.last_hidden_state[:, 0]           # DINOv2 CLS token
                else:
                    xs = t.stack([self.preprocess(im) for im in chunk]).to(self.device)
                    f = self.model.encode_image(xs)
                feats.append(t.nn.functional.normalize(f.float(), dim=-1).cpu().numpy())
        return np.concatenate(feats, 0).astype(np.float32)

    def text(self, prompts):
        t = self.torch
        with t.no_grad():
            if self.kind == "transformers_dual":
                inp = self.processor(text=list(prompts), return_tensors="pt", padding=True,
                                     truncation=True).to(self.device)
                out = self.model.text_model(input_ids=inp["input_ids"],
                                            attention_mask=inp.get("attention_mask"))
                pooled = out.pooler_output if hasattr(out, "pooler_output") else out[1]
                f = self.model.text_projection(pooled)
            elif self.kind == "transformers_vision_probe":
                raise RuntimeError("encoder %s has no text tower; top-1 goes through the linear probe"
                                   % self.enc_id)
            else:
                f = self.model.encode_text(self.tokenizer(list(prompts)).to(self.device))
            f = t.nn.functional.normalize(f.float(), dim=-1).cpu().numpy()
        return f.astype(np.float32)

    # ---- linear probe (frozen features) --------------------------------------------------------
    def fit_probe(self, ifeat: np.ndarray, labels: np.ndarray, seed: int = PROBE_SEED):
        """No-bias multinomial logistic probe on L2-normalized features; returns (weights, test_mask, stats)."""
        t = self.torch
        n, d = ifeat.shape
        n_classes = int(labels.max()) + 1
        rng = np.random.default_rng(seed)
        test_mask = np.zeros(n, dtype=bool)
        for c in range(n_classes):
            idx = np.where(labels == c)[0]
            rng.shuffle(idx)
            k = int(np.ceil(PROBE_TEST_FRAC * len(idx)))
            k = min(max(k, 1), max(len(idx) - 1, 1))
            test_mask[idx[:k]] = True
        tr = np.where(~test_mask)[0]
        X = t.from_numpy(ifeat[tr].astype(np.float32))
        y = t.from_numpy(labels[tr].astype(np.int64))
        t.manual_seed(seed)
        W = t.zeros(d, n_classes, requires_grad=True)
        opt = t.optim.Adam([W], lr=0.05, weight_decay=1e-4)
        loss_fn = t.nn.CrossEntropyLoss()
        for _ in range(400):
            opt.zero_grad()
            loss = loss_fn(X @ W, y)
            loss.backward()
            opt.step()
        with t.no_grad():
            Wn = W.detach()
            logits_all = t.from_numpy(ifeat.astype(np.float32)) @ Wn
            pred = logits_all.argmax(1).numpy()
            train_acc = float((pred[tr] == labels[tr]).mean() * 100.0)
            test_acc = float((pred[test_mask] == labels[test_mask]).mean() * 100.0)
            Wn = t.nn.functional.normalize(Wn, dim=0).numpy().T          # (n_classes, d)
            logits_cos = ifeat @ Wn.T
            pred_cos = logits_cos.argmax(1)
            test_acc_cos = float((pred_cos[test_mask] == labels[test_mask]).mean() * 100.0)
            final_loss = float(loss_fn(t.from_numpy(ifeat[tr].astype(np.float32)) @ Wn.T,
                                       t.from_numpy(labels[tr].astype(np.int64))).item())
        stats = {"probe": "no-bias cosine logistic head", "seed": int(seed), "epochs": 400, "lr": 0.05,
                 "weight_decay": 1e-4, "test_fraction": PROBE_TEST_FRAC,
                 "n_train": int(len(tr)), "n_test": int(test_mask.sum()),
                 "train_top1_percent_bias_free_head": train_acc,
                 "heldout_top1_percent_bias_free_head": test_acc,
                 "heldout_top1_percent_cosine_head": test_acc_cos,
                 "train_loss_cosine_head": final_loss,
                 "reported_top1_rule": "held-out top-1 of the cosine head (the same matrix the margins use)"}
        self.probe_weights, self.probe_stats = Wn.astype(np.float32), stats
        return self.probe_weights, test_mask, stats


# --------------------------------------------------------------------------------------------------
# cache io
# --------------------------------------------------------------------------------------------------
def cache_path(cache_root: str, enc_id: str, corpus_id: str) -> str:
    return os.path.join(cache_root, "%s__%s.npz" % (enc_id, corpus_id))


def load_cache(cache_root: str, enc_id: str, corpus_id: str, dim: int, n_classes: int,
               fingerprint: str | None):
    """Return (payload, reason). payload is None when the cache is absent or fails a validity check."""
    p = cache_path(cache_root, enc_id, corpus_id)
    if not os.path.exists(p):
        return None, "absent"
    try:
        z = np.load(p, allow_pickle=False)
        meta = json.loads(str(z["meta"]))
    except Exception as exc:
        return None, "unreadable (%s)" % exc
    try:
        ifeat = z["ifeat"]
        tfeat = z["tfeat"]
        labels = z["labels"]
        used = z["used_mask"]
    except KeyError as exc:
        return None, "missing array %s" % exc
    if meta.get("cache_version") != CACHE_VERSION:
        return None, "cache_version %s != %s" % (meta.get("cache_version"), CACHE_VERSION)
    if meta.get("encoder") != enc_id or meta.get("corpus") != corpus_id:
        return None, "encoder/corpus mismatch in cache metadata"
    if ifeat.shape[1] != dim:
        return None, "embedding dim %d != registry %d" % (ifeat.shape[1], dim)
    if labels.shape[0] != ifeat.shape[0] or used.shape[0] != ifeat.shape[0]:
        return None, "ragged arrays"
    if tfeat.shape[0] != n_classes:
        return None, "cached class count %d != corpus %d" % (tfeat.shape[0], n_classes)
    if fingerprint is not None and meta.get("image_fingerprint") != fingerprint:
        return None, "image fingerprint changed (corpus or subset differs from the cache)"
    payload = {"ifeat": ifeat, "tfeat": tfeat, "labels": labels, "used_mask": used.astype(bool),
               "meta": meta, "path": p}
    return payload, "valid"


def save_cache(cache_root: str, enc_id: str, corpus_id: str, ifeat, tfeat, labels, used_mask,
               class_names, meta: dict) -> str:
    os.makedirs(cache_root, exist_ok=True)
    p = cache_path(cache_root, enc_id, corpus_id)
    np.savez_compressed(p,
                        ifeat=np.asarray(ifeat, dtype=np.float32),
                        tfeat=np.asarray(tfeat, dtype=np.float32),
                        labels=np.asarray(labels, dtype=np.int64),
                        used_mask=np.asarray(used_mask, dtype=bool),
                        class_names=np.asarray(class_names, dtype=object).astype("U128"),
                        meta=np.asarray(json.dumps(meta, ensure_ascii=True)))
    return p


# --------------------------------------------------------------------------------------------------
# statistics: family rows, correlations
# --------------------------------------------------------------------------------------------------
def margin_stats(x: np.ndarray, tfeat: np.ndarray, labels: np.ndarray) -> dict:
    """All per-configuration quantities for one frozen configuration (x, tfeat, labels already sliced)."""
    sn = (x @ tfeat.T).astype(np.float64)
    r = np.arange(len(labels))
    pred = sn.argmax(1)
    top1 = float((pred == labels).mean() * 100.0)
    true_s = sn[r, labels]
    comp = sn.copy()
    comp[r, labels] = -np.inf
    max_comp = comp.max(1)
    margin = true_s - max_comp
    sigma_d = float(1.0 - np.mean(max_comp))
    med = float(np.median(margin))
    out = {"top1": top1, "sigma_D": sigma_d, "margin_median": med,
           "margin_mean": float(np.mean(margin)), "margin_std": float(np.std(margin)),
           "margin_min": float(np.min(margin)), "margin_max": float(np.max(margin)),
           "margin_q01": float(np.quantile(margin, 0.01)), "margin_q05": float(np.quantile(margin, 0.05)),
           "top1_hits": (pred == labels), "margin": margin}
    for e in EPS_FINE:
        out[eps_key(e)] = float((margin <= 2.0 * e).mean())
    for c in C_MEDREL:
        out[medrel_key(c)] = float((margin <= 2.0 * c * med).mean())
    for c in C_SIGMAREL:
        out[sigmarel_key(c)] = float((margin <= 2.0 * c * sigma_d).mean())
    out["eps_medrel_per_c"] = {str(c): float(c * med) for c in C_MEDREL}
    out["eps_sigmarel_per_c"] = {str(c): float(c * sigma_d) for c in C_SIGMAREL}
    return out


def family_rows(ifeat: np.ndarray, tfeat: np.ndarray, labels: np.ndarray, lambdas=LAMBDAS) -> dict:
    """The nine-configuration surgery family of one unit plus the arrays the bootstrap needs."""
    ifeat = np.asarray(ifeat, dtype=np.float64)
    tfeat = np.asarray(tfeat, dtype=np.float64)
    labels = np.asarray(labels)
    mu_i, mu_t = ifeat.mean(0), tfeat.mean(0)
    d = mu_t - mu_i
    gn = float(np.linalg.norm(d))
    d_hat = d / gn if gn > 0 else np.zeros_like(d)
    rows, boot_top1, boot_mass = [], [], []

    def add(lam, x, t):
        st = margin_stats(x, t, labels)
        row = {"lambda": lam, "top1": st["top1"], "sigma_D": st["sigma_D"],
               "margin_median": st["margin_median"], "margin_mean": st["margin_mean"],
               "margin_std": st["margin_std"], "margin_min": st["margin_min"],
               "margin_max": st["margin_max"], "margin_q01": st["margin_q01"], "margin_q05": st["margin_q05"],
               "eps_medrel_per_c": st["eps_medrel_per_c"], "eps_sigmarel_per_c": st["eps_sigmarel_per_c"]}
        for k in STAT_KEYS:
            row[k] = st[k]
        # per-image indicator of "margin <= 2 eps" at THIS configuration's own eps for each statistic:
        # absolute eps for the fine grid, and the row's own c * median(margin) / c * sigma_D otherwise.
        eps_of = {eps_key(e): float(e) for e in EPS_FINE}
        eps_of.update({medrel_key(c): float(c) * st["margin_median"] for c in C_MEDREL})
        eps_of.update({sigmarel_key(c): float(c) * st["sigma_D"] for c in C_SIGMAREL})
        indicators = np.stack([(st["margin"] <= 2.0 * eps_of[k]) for k in STAT_KEYS], axis=1)
        rows.append(row)
        boot_top1.append(st["top1_hits"].astype(np.float32))
        boot_mass.append(indicators.astype(np.float32))

    for lam in lambdas:
        x = ifeat + float(lam) * gn * d_hat
        nrm = np.linalg.norm(x, axis=1, keepdims=True)
        x = x / np.where(nrm == 0, 1.0, nrm)
        add(float(lam), x, tfeat)
    tx = tfeat - 1.0 * gn * d_hat
    nrm = np.linalg.norm(tx, axis=1, keepdims=True)
    tx = tx / np.where(nrm == 0, 1.0, nrm)
    add(TEXT_ROW, ifeat, tx)
    return {"rows": rows, "boot_top1": np.stack(boot_top1, 0), "boot_mass": np.stack(boot_mass, 0),
            "gap_norm": gn, "n_rows": len(rows), "n_images": int(ifeat.shape[0])}


def health_labels(top1: np.ndarray) -> np.ndarray:
    """The archived health label: a configuration is labelled when its top-1 is at or below the median."""
    return np.asarray(top1, dtype=np.float64) <= float(np.median(top1))


def unit_correlations(fam: dict) -> dict:
    top = np.array([r["top1"] for r in fam["rows"]], dtype=np.float64)
    out = {"n_rows": len(fam["rows"]), "with_top1": {}}
    for k in STAT_KEYS:
        vals = np.array([r[k] for r in fam["rows"]], dtype=np.float64)
        out["with_top1"][k] = {"r": pearson(vals, top),
                               "n_distinct_values": int(len(np.unique(np.round(vals, 12)))),
                               "saturated": bool(np.all(vals >= 1.0)),
                               "min": float(vals.min()), "max": float(vals.max())}
    return out


def pooled_correlations(unit_fams: dict) -> dict:
    rows = [r for fam in unit_fams.values() for r in fam["rows"]]
    top = np.array([r["top1"] for r in rows], dtype=np.float64)
    out = {"n_rows": len(rows), "n_units": len(unit_fams), "with_top1": {}}
    for k in STAT_KEYS:
        vals = np.array([r[k] for r in rows], dtype=np.float64)
        out["with_top1"][k] = {"r": pearson(vals, top),
                               "n_distinct_values": int(len(np.unique(np.round(vals, 12)))),
                               "saturated": bool(np.all(vals >= 1.0)),
                               "min": float(vals.min()), "max": float(vals.max())}
    return out


# --------------------------------------------------------------------------------------------------
# transfer + paired bootstrap over images
# --------------------------------------------------------------------------------------------------
def fit_threshold_exact(values: np.ndarray, labels: np.ndarray):
    """Exact maximiser of BA(values <= t, labels) over all thresholds (every breakpoint is a value)."""
    order = np.argsort(values, kind="stable")
    v = np.asarray(values, dtype=np.float64)[order]
    y = np.asarray(labels, dtype=bool)[order]
    n, n_pos = len(v), int(np.sum(y))
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0 or n == 0:
        return None, None
    tp = np.cumsum(y).astype(np.float64)
    fp = np.cumsum(~y).astype(np.float64)
    tpr = tp / n_pos
    tnr = (n_neg - fp) / n_neg
    ba = 0.5 * (tpr + tnr)
    j = int(np.argmax(ba))
    return float(v[j]), float(ba[j])


def fit_threshold_exact_vec(values: np.ndarray, labels: np.ndarray):
    """Vectorised exact threshold search. values/labels: (B, R) -> (B,) thresholds and (B,) fit BA."""
    B, R = values.shape
    order = np.argsort(values, axis=1, kind="stable")
    v = np.take_along_axis(values, order, axis=1)
    y = np.take_along_axis(np.asarray(labels, dtype=bool), order, axis=1)
    n_pos = np.sum(y, axis=1).astype(np.float64)
    n_neg = (R - n_pos).astype(np.float64)
    tp = np.cumsum(y, axis=1).astype(np.float64)
    fp = np.cumsum(~y, axis=1).astype(np.float64)
    pos_ok = (n_pos > 0)[:, None]
    neg_ok = (n_neg > 0)[:, None]
    with np.errstate(invalid="ignore", divide="ignore"):
        tpr = np.where(pos_ok, tp / np.maximum(n_pos[:, None], 1.0), np.nan)
        tnr = np.where(neg_ok, (n_neg[:, None] - fp) / np.maximum(n_neg[:, None], 1.0), np.nan)
    ba = 0.5 * (tpr + tnr)
    j = np.argmax(np.where(np.isnan(ba), -np.inf, ba), axis=1)
    thr = v[np.arange(B), j]
    fit = ba[np.arange(B), j]
    degenerate = (n_pos == 0) | (n_neg == 0)
    fit = np.where(degenerate, np.nan, fit)
    return thr, fit, degenerate


def bootstrap_indices(n: int, draws: int, rng) -> np.ndarray:
    """(draws, n) integer index draw with replacement (kept for reuse by callers of resample_unit)."""
    return rng.integers(0, n, size=(draws, n))


def resample_unit(fam: dict, idx: np.ndarray, chunk: int = 256) -> dict:
    """Family statistics on resampled images. idx: (B, n). Returns per-row top1 (B,R) and mass (B,R,K).

    Chunked over draws so the temporary gather stays small on the 1,783-image sonar corpus.
    """
    B, n = idx.shape
    rows, n_stats = fam["n_rows"], fam["boot_mass"].shape[2]
    top1 = np.empty((B, rows), dtype=np.float64)
    mass = np.empty((B, rows, n_stats), dtype=np.float64)
    for s in range(0, B, chunk):
        sl = slice(s, min(s + chunk, B))
        for r in range(rows):
            top1[sl, r] = fam["boot_top1"][r][idx[sl]].mean(1)
            mass[sl, r, :] = fam["boot_mass"][r][idx[sl]].mean(1)
    return {"top1": top1, "mass": mass}


def transfer_point(stat_key: str, src: dict, tgt: dict) -> dict:
    vs = np.array([r[stat_key] for r in src["rows"]], dtype=np.float64)
    vt = np.array([r[stat_key] for r in tgt["rows"]], dtype=np.float64)
    hs = health_labels([r["top1"] for r in src["rows"]])
    ht = health_labels([r["top1"] for r in tgt["rows"]])
    thr, fit = fit_threshold_exact(vs, hs)
    out = {"source_threshold": thr, "source_fit_BA": fit,
           "chance": 0.5, "n_source": int(len(vs)), "n_target": int(len(vt)),
           "n_source_images": int(src.get("n_images_used", src["n_images"])),
           "n_target_images": int(tgt.get("n_images_used", tgt["n_images"])),
           "n_source_labelled": int(hs.sum()), "n_target_labelled": int(ht.sum()),
           "source_value_min": float(vs.min()), "source_value_max": float(vs.max()),
           "target_value_min": float(vt.min()), "target_value_max": float(vt.max()),
           "target_BA": None, "degenerate": True}
    if thr is None or bool(hs.all()) or bool((~hs).all()) or bool(ht.all()) or bool((~ht).all()):
        out["degenerate_reason"] = ("source or target family is single-class at the median split" if
                                    (hs.all() or (~hs).all() or ht.all() or (~ht).all()) else
                                    "no threshold separating the source labels")
        return out
    ba = bal_acc(vt <= thr, ht)
    out["target_BA"] = ba
    out["degenerate"] = ba is None
    if ba is None:
        out["degenerate_reason"] = "target family single-class at the transferred threshold"
    out["target_predicts_labelled"] = int(np.sum(vt <= thr))
    return out


def transfer_bootstrap(stat_keys, src_res: dict, tgt_res: dict, n_boot: int) -> dict:
    """Refit the source threshold and score the target on every image-bootstrap draw."""
    rs, rt = src_res, tgt_res
    ks = {k: i for i, k in enumerate(STAT_KEYS)}
    out = {}
    B, R = rs["top1"].shape
    src_lab = rs["top1"] <= vec_median(rs["top1"], axis=1)[:, None]
    tgt_lab = rt["top1"] <= vec_median(rt["top1"], axis=1)[:, None]
    for k in stat_keys:
        j = ks[k]
        vs, vt = rs["mass"][:, :, j], rt["mass"][:, :, j]
        thr, fit, deg_s = fit_threshold_exact_vec(vs, src_lab)
        pred = vt <= thr[:, None]
        ba = bal_acc_vec(pred, tgt_lab)
        usable = ~(deg_s | np.isnan(ba))
        n_usable = int(usable.sum())
        delta = ba[usable] - 0.5
        ci = ([float(np.percentile(ba[usable], 2.5)), float(np.percentile(ba[usable], 97.5))]
              if n_usable else [None, None])
        dci = ([float(np.percentile(delta, 2.5)), float(np.percentile(delta, 97.5))]
               if n_usable else [None, None])
        out[k] = {
            "n_boot": int(n_boot), "n_usable_draws": n_usable,
            "target_BA_mean": float(np.mean(ba[usable])) if n_usable else None,
            "target_BA_sd": float(np.std(ba[usable])) if n_usable else None,
            "target_BA_ci95": ci,
            "delta_vs_chance_mean": float(np.mean(delta)) if n_usable else None,
            "delta_vs_chance_ci95": dci,
            "p_target_BA_gt_chance": float(np.mean(ba[usable] > 0.5)) if n_usable else None,
            "p_delta_gt_zero": float(np.mean(delta > 0)) if n_usable else None,
            "survives": bool(n_usable > 0 and dci[0] is not None and dci[0] > 0.0),
            "mean_fit_BA_source": float(np.nanmean(fit)) if np.any(~np.isnan(fit)) else None,
        }
    return out


# --------------------------------------------------------------------------------------------------
# encode
# --------------------------------------------------------------------------------------------------
def encode_unit(enc_id: str, corpus_id: str, args, corpus_cache: dict, quiet: bool) -> dict:
    enc = ENCODERS[enc_id]
    corpus = corpus_cache[corpus_id]
    if corpus.get("error"):
        return {"ok": False, "reason": corpus["error"]}
    if not corpus["items"]:
        return {"ok": False, "reason": "corpus %s is empty" % corpus_id}
    t0 = time.time()
    resolved, problems, prov = resolve_assets(enc_id, args.models_root)
    if problems:
        return {"ok": False, "reason": "\n      ".join(problems), "provenance": prov}
    device = args.device if args.device != "auto" else ("cuda" if _cuda_ok() else "cpu")
    log("[%s / %s] loading %s (%s)" % (enc_id, corpus_id, enc["loader"], device), quiet)
    enc_obj = ImageTextEncoder(enc_id, resolved, device, batch=args.batch)
    images = [im for im, _lab in corpus["items"]]
    labels = np.array([lab for _im, lab in corpus["items"]], dtype=np.int64)
    prompts = [CORPORA[corpus_id]["prompt_template"].format(name=n) for n in corpus["class_names"]]
    t_enc = time.time()
    ifeat = enc_obj.image(images)
    used_mask = np.ones(len(labels), dtype=bool)
    probe_stats = None
    if enc["probe"]:
        weights, used_mask, probe_stats = enc_obj.fit_probe(ifeat, labels, seed=args.probe_seed)
        tfeat = weights
    else:
        tfeat = enc_obj.text(prompts)
    encode_seconds = time.time() - t_enc
    meta = {
        "cache_version": CACHE_VERSION, "encoder": enc_id, "corpus": corpus_id,
        "n_images": int(len(labels)), "n_classes": int(len(corpus["class_names"])),
        "embed_dim": int(ifeat.shape[1]), "probe": bool(enc["probe"]),
        "probe_protocol": enc["probe_protocol"], "probe_stats": probe_stats,
        "used_mask_rule": ("held-out 30 % split of the probe" if enc["probe"]
                           else "all images (prompt-based zero-shot head)"),
        "prompt_template": CORPORA[corpus_id]["prompt_template"],
        "prompts_first3": prompts[:3], "n_prompts": len(prompts),
        "image_fingerprint": corpus["fingerprint"],
        "model": {"repo_id": enc["repo_id"], "loader": enc["loader"], "preprocess": enc["preprocess"],
                  "assets": prov, "load_report": enc_obj.load_report, "device": device,
                  "batch": int(args.batch)},
        "image_order": ("sorted class directories, files sorted within a class" if CORPORA[corpus_id]["kind"] == "class_dirs"
                        else "outputs/ocean_subset.json:subset_idx order"),
        "normalisation": "L2-normalised image features and text/probe-head rows",
        "timings": {"encode_seconds": round(encode_seconds, 2)},
        "generator": "tools/_p1614_a23_multi_encoder_transfer.py",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    p = save_cache(args.cache_root, enc_id, corpus_id, ifeat, tfeat, labels, used_mask,
                   corpus["class_names"], meta)
    log("[%s / %s] encoded %d images in %.1f s -> %s"
        % (enc_id, corpus_id, len(labels), encode_seconds, os.path.relpath(p, REPO)), quiet)
    return {"ok": True, "path": p, "seconds": round(time.time() - t0, 2),
            "n_images": int(len(labels)), "probe_stats": probe_stats,
            "load_report": enc_obj.load_report, "provenance": prov}


def _cuda_ok() -> bool:
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


# --------------------------------------------------------------------------------------------------
# analyze
# --------------------------------------------------------------------------------------------------
def reproduction_block(enc_id, corpus_id, rows) -> dict:
    """Compare the rows present in the archived certificates with the rows computed here."""
    ref_rel = None
    if enc_id == "clip-vit-base-patch32" and corpus_id in ("marine_optical", "acoustic_sonar"):
        ref_rel = REF_CONTROL
    elif enc_id in ("bioclip", "oceanclip") and corpus_id == "rare_species":
        ref_rel = REF_ADAPTED
    if ref_rel is None:
        return {"reference": None,
                "note": "no archived certificate row set matches this unit"}
    ref_path = os.path.join(REPO, ref_rel)
    if not os.path.exists(ref_path):
        return {"reference": ref_rel, "note": "reference archive not present"}
    ref = json.load(io.open(ref_path, encoding="utf-8"))
    if ref_rel == REF_CONTROL:
        ref_rows = {r["lambda"]: r for r in ref.get("domains", {}).get(corpus_id, [])}
    else:
        ref_rows = {r["lambda"]: r for r in ref.get("models", {}).get(enc_id, {}).get("rows", [])}
    mine = {r["lambda"]: r for r in rows}
    pairs, worst = 0, 0.0
    for lam, rr in ref_rows.items():
        if lam not in mine:
            continue
        mr = mine[lam]
        pairs += 1
        worst = max(worst, abs(float(rr["top1"]) - float(mr["top1"])))
        for e in EPS_ARCHIVED:
            ref_key = next((c for c in ("mass_%g" % e, "mass_%.1f" % e, "mass_%.2f" % e, eps_key(e))
                            if c in rr), None)
            if ref_key is None:
                continue
            pairs += 1
            worst = max(worst, abs(float(rr[ref_key]) - float(mr[eps_key(e)])))
    return {"reference": ref_rel, "pairs_checked": pairs, "max_abs_diff": worst, "tolerance": REPRO_TOL,
            "reproduced": bool(worst < REPRO_TOL),
            "fields_compared": ["top1", "mass_0.02", "mass_0.05", "mass_0.1"],
            "note": ("prompt template and class enumeration follow the archived script, so these rows are "
                     "directly comparable with the archive; rows absent from the archive (lambda = 2.0 on "
                     "the control, the text-side row) are not compared")}


def selected_units(args):
    """(encoders, corpora, units) for this command: the cross product unless --units is given."""
    encs = all_encoder_ids(args)
    if args.encoders:
        want = [e.strip() for e in args.encoders.split(",") if e.strip()]
        unknown = [e for e in want if e not in ENCODERS]
        if unknown:
            raise SystemExit("unknown encoder(s): %s\nregistered: %s"
                             % (", ".join(unknown), ", ".join(ENCODERS)))
        encs = want
    corpora = [c.strip() for c in args.corpora.split(",") if c.strip()] if args.corpora else list(CORPORA)
    for c in corpora:
        if c not in CORPORA:
            raise SystemExit("unknown corpus '%s'\nregistered: %s" % (c, ", ".join(CORPORA)))
    if args.units:
        units = [u.strip() for u in args.units.split(",") if u.strip()]
        for u in units:
            if "__" not in u:
                raise SystemExit("--units entries must look like <encoder>__<corpus>, got '%s'" % u)
            e, c = u.split("__", 1)
            if e not in ENCODERS:
                raise SystemExit("unknown encoder '%s' in --units (registered: %s)" % (e, ", ".join(ENCODERS)))
            if c not in CORPORA:
                raise SystemExit("unknown corpus '%s' in --units (registered: %s)" % (c, ", ".join(CORPORA)))
            if e not in encs or c not in corpora:
                raise SystemExit("--units entry '%s' is outside the --encoders/--corpora selection "
                                 "(add --include-adapted for the two adapted encoders)" % u)
        return sorted({u.split("__")[0] for u in units}), sorted({u.split("__", 1)[1] for u in units}), sorted(units)
    return encs, corpora, ["%s__%s" % (e, c) for e in encs for c in corpora]


def all_encoder_ids(args) -> list:
    return [e for e, spec in ENCODERS.items() if args.include_adapted or spec["group"] == "generic"]


def run_analyze(args, quiet: bool) -> dict:
    encs, corpora, units_sel = selected_units(args)
    plan = corpus_plan(args.data_root, args.subset_json)
    unit_fams, unit_blocks, skipped = {}, {}, []
    for unit in units_sel:
        enc_id, corpus_id = unit.split("__", 1)
        enc = ENCODERS[enc_id]
        spec = plan[corpus_id]
        if spec.get("missing"):
            skipped.append({"unit": unit, "reason": "corpus not present"})
            continue
        cache, reason = load_cache(args.cache_root, enc_id, corpus_id, enc["embed_dim"],
                                   spec["n_classes"], None)
        if cache is None:
            skipped.append({"unit": unit, "reason": "cache %s" % reason})
            continue
        used = cache["used_mask"]
        ifeat = cache["ifeat"][used].astype(np.float64)
        labels = cache["labels"][used]
        tfeat = cache["tfeat"].astype(np.float64)
        fam = family_rows(ifeat, tfeat, labels)
        fam["n_images_used"] = int(used.sum())
        fam["n_images"] = int(cache["ifeat"].shape[0])
        key = unit
        unit_fams[key] = fam
        rows = fam["rows"]
        frozen = next(r for r in rows if r["lambda"] == 0.0)
        frozen_st = margin_stats(ifeat, tfeat, labels)
        unit_blocks[key] = {
            "encoder": enc_id, "corpus": corpus_id, "registry_group": enc["group"],
            "loader": enc["loader"], "preprocess": enc["preprocess"],
            "embed_dim": enc["embed_dim"], "probe": enc["probe"],
            "probe_protocol": enc["probe_protocol"],
            "n_images_corpus": int(cache["ifeat"].shape[0]),
            "n_images_used": int(used.sum()),
            "n_classes": int(tfeat.shape[0]),
            "chance_percent": round(100.0 / float(tfeat.shape[0]), 4),
            "chance_rule": "1 / n_classes (uniform random guessing)",
            "n_family_rows": len(rows), "family_rows": [str(r["lambda"]) for r in rows],
            "cache": os.path.relpath(cache["path"], REPO).replace("\\", "/"),
            "cache_bytes": int(os.path.getsize(cache["path"])),
            "gap_norm": fam["gap_norm"],
            "prompt_template": cache["meta"]["prompt_template"],
            "used_mask_rule": cache["meta"]["used_mask_rule"],
            "probe_stats": cache["meta"].get("probe_stats"),
            "model_source": cache["meta"]["model"],
            "cache_creation": {"created_at": cache["meta"].get("created_at"),
                               "encode_seconds": (cache["meta"].get("timings") or {}).get("encode_seconds"),
                               "device": (cache["meta"].get("model") or {}).get("device"),
                               "batch": (cache["meta"].get("model") or {}).get("batch"),
                               "n_images_encoded": cache["meta"].get("n_images")},
            "frozen_row": {k: v for k, v in frozen.items()},
            "margin_distribution_frozen": quantiles(frozen_st["margin"]),
            "margin_histogram_frozen": linear_hist(frozen_st["margin"]),
            "rows": rows,
            "correlations": unit_correlations(fam),
            "reproduction": reproduction_block(enc_id, corpus_id, rows),
        }
        if fam["n_rows"] != len(LAMBDAS) + 1:
            raise SystemExit("internal error: family has %d rows" % fam["n_rows"])
    if not unit_fams:
        raise SystemExit("no unit has a usable cache under %s; run --encode first" % args.cache_root)

    units = sorted(unit_fams)
    # One bootstrap draw per (corpus, number of scored images), reused by every unit of that corpus: the
    # resampling is therefore genuinely PAIRED for pairs that share a corpus (identical image indices on both
    # sides) and independent across corpora, and each unit is resampled once instead of once per pair.
    rng = np.random.default_rng(20261024)
    draws, resampled = {}, {}
    for u in units:
        cid = u.split("__")[1]
        n_used = unit_fams[u]["n_images_used"]
        key = (cid, n_used)
        if key not in draws:
            draws[key] = bootstrap_indices(n_used, int(args.boot), rng)
        resampled[u] = resample_unit(unit_fams[u], draws[key])
    log("bootstrap: %d draw(s) per (corpus, n) pair, %d unit resample(s)"
        % (int(args.boot), len(resampled)), quiet)
    pairs = []
    for src in units:
        for tgt in units:
            paired = (src.split("__")[1] == tgt.split("__")[1]
                      and unit_fams[src]["n_images_used"] == unit_fams[tgt]["n_images_used"])
            boot = transfer_bootstrap(STAT_KEYS, resampled[src], resampled[tgt], args.boot)
            by_stat = {}
            for k in STAT_KEYS:
                row = transfer_point(k, unit_fams[src], unit_fams[tgt])
                row["bootstrap"] = dict(boot[k], paired=bool(paired))
                by_stat[k] = row
            pairs.append({"source": src, "target": tgt,
                          "source_encoder": src.split("__")[0], "source_corpus": src.split("__")[1],
                          "target_encoder": tgt.split("__")[0], "target_corpus": tgt.split("__")[1],
                          "self_pair": bool(src == tgt), "same_corpus": bool(src.split("__")[1] == tgt.split("__")[1]),
                          "bootstrap_paired": bool(paired),
                          "n_source_images": unit_fams[src]["n_images_used"],
                          "n_target_images": unit_fams[tgt]["n_images_used"],
                          "by_statistic": by_stat})
    return build_document(args, plan, unit_blocks, unit_fams, pairs, skipped, encs, corpora, units_sel)


def build_document(args, plan, unit_blocks, unit_fams, pairs, skipped, encs, corpora, units_sel) -> dict:
    registry_block = {"encoders": {e: {k: v for k, v in ENCODERS[e].items()} for e in ENCODERS},
                      "corpora": {c: {k: v for k, v in CORPORA[c].items()} for c in CORPORA}}
    models_status = {}
    for enc_id in ENCODERS:
        resolved, problems, prov = resolve_assets(enc_id, args.models_root)
        models_status[enc_id] = {"available": not problems, "assets": prov,
                                 "problems": problems, "selected": enc_id in encs}
    doc = {
        "archive": OUT_REL,
        "generator": "tools/_p1614_a23_multi_encoder_transfer.py",
        "note": ("Widened transfer test of the A23 margin-mass certificate: the same corpora encoded with a "
                 "registry of frozen encoders, then every ordered pair of (encoder, corpus) units is asked "
                 "whether a threshold on M fitted on the source survives on the target. New file; no existing "
                 "archive is modified."),
        "meta": {
            "script": "tools/_p1614_a23_multi_encoder_transfer.py",
            "script_sha1": sha1_file(os.path.abspath(__file__)),
            "git": git_info(),
            "host": host_info(),
            "argv": sys.argv[1:],
            "started_at": args._started_at, "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "duration_seconds": round(time.time() - args._t0, 2),
            "paths": {"data_root": args.data_root, "cache_root": args.cache_root,
                      "models_root": args.models_root, "subset_json": args.subset_json,
                      "out": OUT_REL},
            "selection": {"encoders": encs, "corpora": corpora, "units": units_sel,
                          "include_adapted": bool(args.include_adapted),
                          "bootstrap_draws": int(args.boot), "probe_seed": int(args.probe_seed),
                          "device": args.device},
            "eps_fine_grid": EPS_FINE, "eps_archived_grid": EPS_ARCHIVED,
            "c_medrel_grid": C_MEDREL, "c_sigmarel_grid": C_SIGMAREL, "lambdas": LAMBDAS,
            "text_side_row": TEXT_ROW, "n_boot": int(args.boot), "cache_version": CACHE_VERSION,
            "statistic_keys": STAT_KEYS,
            "margin_definition": "margin_i = s_i(y_i) - max_{c != y_i} s_i(c); M(eps) = mean(1[margin <= 2 eps])",
            "family_definition": ("image-side gap surgery x_lambda = normalize(i + lambda * ||d|| * d_hat) with "
                                  "d = mean(text/probe rows) - mean(image features), lambda in %s, plus one "
                                  "text-side configuration text1.0 (t - 1.0 * ||d|| * d_hat)" % LAMBDAS),
            "relative_eps_definitions": {
                "median_margin": "eps_row = c * median_i(margin_i) of that configuration",
                "sigma_relative": "eps_row = c * sigma_D with sigma_D = 1 - mean_i max_{c != y_i} s_i(c)"},
            "family_note": ("tools/_p1472 used seven lambdas on the control (no text-side row) and eight plus "
                            "the text-side row on the adapted encoders; this script applies the union (eight "
                            "lambdas plus text1.0 = nine configurations) to every unit uniformly, which is why "
                            "the reproduction check compares only the rows the archives actually carry"),
            "prompt_note": ("prompts follow the archived scripts ('a photo of a <class>' and 'a photo of a "
                            "<sciName>'); tools/_p1472's adapted arm used 'a photo of <sciName>' instead, so "
                            "its adapted rows differ from these by up to 0.01 in M while the archived adapted "
                            "rows are reproduced instead"),
            "corpus_size_checks": {},
            "models": models_status,
            "units_analyzed": sorted(unit_blocks), "units_skipped": skipped,
            "n_units_expected_for_selection": len(units_sel),
            "n_units_analyzed": len(unit_blocks),
            "complete_for_selection": len(unit_blocks) == len(units_sel),
            "caches_root": args.cache_root,
        },
        "registry": registry_block,
        "encoders": {},
        "correlations": {"pooled": pooled_correlations({k: v for k, v in unit_fams.items()}),
                         "within_unit": {k: v["correlations"]["with_top1"] for k, v in unit_blocks.items()},
                         "note": ("within_unit: Pearson r between each statistic and top-1 over the nine "
                                  "family configurations of one (encoder, corpus) unit; pooled: the same over "
                                  "all units' rows together")},
        "transfer": {},
        "conclusion": {},
        "limits": {},
    }
    for cid, spec in plan.items():
        doc["meta"]["corpus_size_checks"][cid] = {
            "n_images": spec.get("n_images"), "n_classes": spec.get("n_classes"),
            "expected_images": spec["expected_images"], "expected_classes": spec["expected_classes"],
            "chance_percent": spec.get("chance_percent_from_disk", spec["chance_percent"]),
            "ok": bool(spec.get("n_images") == spec["expected_images"]
                       and spec.get("n_classes") == spec["expected_classes"]),
            "path": spec.get("path"), "images_per_class": spec.get("images_per_class"),
            "root_level_files_ignored": spec.get("root_level_files"),
        }
    for enc_id in encs:
        block = {"encoder": enc_id, "registry_group": ENCODERS[enc_id]["group"],
                 "repo_id": ENCODERS[enc_id]["repo_id"], "loader": ENCODERS[enc_id]["loader"],
                 "preprocess": ENCODERS[enc_id]["preprocess"], "embed_dim": ENCODERS[enc_id]["embed_dim"],
                 "probe": ENCODERS[enc_id]["probe"], "probe_protocol": ENCODERS[enc_id]["probe_protocol"],
                 "notes": ENCODERS[enc_id]["notes"], "corpora": {}}
        for corpus_id in corpora:
            key = "%s__%s" % (enc_id, corpus_id)
            if key in unit_blocks:
                block["corpora"][corpus_id] = unit_blocks[key]
        doc["encoders"][enc_id] = block

    # ---- transfer summary + conclusion ---------------------------------------------------------
    flat, flat_self = [], []
    for p in pairs:
        for k, v in p["by_statistic"].items():
            if v.get("target_BA") is None:
                continue
            src_vals = np.array([r[k] for r in unit_fams[p["source"]]["rows"]], dtype=np.float64)
            tgt_vals = np.array([r[k] for r in unit_fams[p["target"]]["rows"]], dtype=np.float64)
            entry = {"source": p["source"], "target": p["target"], "statistic": k,
                     "target_BA": v["target_BA"], "source_fit_BA": v["source_fit_BA"],
                     "source_threshold": v["source_threshold"], "chance": v["chance"],
                     "paired": bool(p["bootstrap_paired"]),
                     "survives": bool(v["bootstrap"]["survives"]),
                     "delta_ci95": v["bootstrap"]["delta_vs_chance_ci95"],
                     "p_delta_gt_zero": v["bootstrap"]["p_delta_gt_zero"],
                     "source_value_n_distinct": int(len(np.unique(np.round(src_vals, 12)))),
                     "target_value_n_distinct": int(len(np.unique(np.round(tgt_vals, 12)))),
                     "n_source": v["n_source"], "n_target": v["n_target"]}
            (flat_self if p["self_pair"] else flat).append(entry)
    degenerate = sum(1 for p in pairs for v in p["by_statistic"].values() if v.get("target_BA") is None)
    above = [e for e in flat if e["target_BA"] > e["chance"]]
    survivors = [e for e in above if e["survives"]]
    above.sort(key=lambda e: -e["target_BA"])
    survivors.sort(key=lambda e: -e["target_BA"])
    best = above[0] if above else None
    best_surv = survivors[0] if survivors else None
    cross_only = [e for e in flat if not e["paired"]]
    best_cross = max(cross_only, key=lambda e: e["target_BA"]) if cross_only else None
    doc["transfer"] = {
        "protocol": {
            "unit": "(encoder, corpus); a unit's configurations are its nine surgery-family rows",
            "statistic": "the 13 keys in meta.statistic_keys (7 absolute eps, 3 median-margin-relative, 3 sigma-relative)",
            "source_fit": ("threshold t on the statistic that maximises BA(stat <= t, top1 <= median(top1 over "
                           "the unit's family)) on the source family; exact search over the observed source "
                           "values (the archived code searched a 401-point linspace over the same range, a "
                           "sub-grid of this search)"),
            "target_score": "BA(stat <= t_source, top1 <= median(top1 over the target's family))",
            "chance": 0.5,
            "health_label_note": ("the archived label convention (_p1352/_p1370): a configuration whose top-1 "
                                  "is at or below its unit's median is 'unhealthy'; balanced accuracy is "
                                  "invariant to the naming and the archived transfer numbers are computed the "
                                  "same way"),
            "degenerate_rule": ("when either class is empty the fit is undefined and the entry carries "
                                "target_BA = null with degenerate = true (the archived helper coerced the "
                                "empty denominator to 1 and would report 0.5); the point estimates agree with "
                                "the archive on every non-degenerate row"),
            "bootstrap": ("paired bootstrap over images: %d draws with replacement per unit; the source "
                          "threshold is refitted on the resampled source family and the target BA recomputed "
                          "on the resampled target family. When source and target share a corpus the same "
                          "image indices are used on both sides (paired = true); across corpora the draws are "
                          "independent (paired = false)." % int(args.boot)),
            "survives_rule": "the 2.5th percentile of (target BA - chance) over the usable draws is > 0",
            "n_draws": int(args.boot),
        },
        "units": sorted(unit_blocks),
        "n_units": len(unit_blocks), "n_pairs": len(pairs),
        "self_pairs": sum(1 for p in pairs if p["self_pair"]),
        "cross_unit_pairs": sum(1 for p in pairs if not p["self_pair"]),
        "cross_corpus_pairs": sum(1 for p in pairs if not p["same_corpus"]),
        "pairs": pairs,
        "summary": {
            "n_pair_statistic_entries": len(flat) + len(flat_self) + degenerate,
            "n_scored_entries_cross_unit": len(flat), "n_scored_entries_self_pairs": len(flat_self),
            "n_degenerate_entries": degenerate,
            "n_entries_above_chance": len(above),
            "n_entries_surviving_bootstrap": len(survivors),
            "self_pairs_excluded_from_the_claim": (
                "a self-pair (same unit on both sides) fits and scores on the same nine configurations "
                "in-sample, so it is reported but never counted as a transfer; the claim is evaluated on "
                "the %d cross-unit entries" % len(flat)),
            "best_entry_overall": best, "best_cross_corpus_entry": best_cross,
            "best_entry_surviving_bootstrap": best_surv,
            "point_estimate_above_chance_examples": above[:5],
            "survivors": survivors[:10],
            "survivor_caveat": ("a survivor with few distinct values of the statistic across the nine target "
                                "configurations (target_value_n_distinct) is a structural split of a small "
                                "surgery family rather than a calibrated operating point; the family size is "
                                "nine configurations per unit"),
        },
    }
    n_enc = len({u.split("__")[0] for u in unit_blocks})
    n_corp = len({u.split("__")[1] for u in unit_blocks})
    if survivors:
        headline = ("%d of %d scored cross-unit (pair, statistic) entries beat chance at the point estimate and "
                    "%d of them keep a 95 %% bootstrap interval above chance over images; the strongest "
                    "surviving entry is %s -> %s on %s with target BA %.3f (chance 0.50, delta CI95 "
                    "[%.3f, %.3f]). The negative claim therefore cannot be extended as it stands: the text has "
                    "to name the transferring pair."
                    % (len(above), len(flat), len(survivors),
                       best_surv["source"], best_surv["target"], best_surv["statistic"],
                       best_surv["target_BA"], best_surv["delta_ci95"][0], best_surv["delta_ci95"][1]))
    else:
        headline = ("no entry beats chance by a margin that survives the paired bootstrap over images: of %d "
                    "scored cross-unit (pair, statistic) entries %d are nominally above chance 0.50 and none "
                    "of those keeps its 95 %% bootstrap interval above chance%s. The negative claim is "
                    "therefore supported for all %d ordered pairs over %d encoder x corpus units (%d "
                    "encoders, %d corpora), i.e. it can be widened rather than weakened."
                    % (len(flat), len(above),
                       ("" if best is None else
                        " (best nominal entry %s -> %s on %s: target BA %.3f, delta CI95 [%.3f, %.3f])"
                        % (best["source"], best["target"], best["statistic"], best["target_BA"],
                           best["delta_ci95"][0], best["delta_ci95"][1])),
                       len(pairs), len(unit_blocks), n_enc, n_corp))
    doc["conclusion"] = {
        "question": ("does a threshold on the margin-mass statistic M transfer from one (encoder, corpus) "
                     "unit to another?"),
        "answer": ("yes for at least one pair" if survivors else "no"),
        "n_encoders": n_enc, "n_corpora": n_corp, "n_units": len(unit_blocks),
        "n_ordered_pairs": len(pairs), "n_statistics_per_pair": len(STAT_KEYS),
        "n_scored_entries_cross_unit": len(flat), "n_scored_entries_self_pairs": len(flat_self),
        "n_degenerate_entries": degenerate,
        "n_entries_above_chance": len(above), "n_entries_surviving_bootstrap": len(survivors),
        "best_pair_point_estimate": best, "best_surviving_pair": best_surv,
        "headline": headline,
        "claim": ("the no-transfer claim must be weakened: name the surviving pair(s)" if survivors
                  else "the no-transfer claim can be widened to every registered encoder x corpus pair"),
        "effect_on_a23_text": {
            "current_sentence_scope": ("the A23 text asserts, on the strength of the generic-CLIP control plus "
                                       "the two adapted encoders, that no threshold on M transfers across "
                                       "domains or encoders (best cross-domain balanced accuracy 0.50-0.55 "
                                       "against chance 0.50)"),
            "n_encoders_before": 3, "n_encoders_after": n_enc,
            "n_units_after": len(unit_blocks), "n_pairs_after": len(pairs),
            "action": (("widen the sentence's evidential base from the three encoders cited today (generic CLIP, "
                        "BioCLIP, OceanCLIP) to the %d encoders over %d corpora analysed here (%d units, %d "
                        "ordered pairs) and quote the bootstrap interval instead of the 0.50-0.55 range"
                        % (n_enc, n_corp, len(unit_blocks), len(pairs)))
                       if not survivors and n_enc > 3 else
                       (("this run covers only %d encoder(s) -- a partial selection recorded in meta.selection "
                         "-- so the sentence can be widened only after the full grid is analysed; the "
                         "no-transfer result does repeat on every pair analysed here (%d units, %d ordered "
                         "pairs, no bootstrap survivor)" % (n_enc, len(unit_blocks), len(pairs)))
                        if not survivors else
                        "weaken the sentence: %d entry/entries survive the bootstrap, so the text must state "
                        "which pair transfers and drop the unconditional 'no threshold transfers'"
                        % len(survivors))),
        },
    }
    probe_units = [k for k, v in unit_blocks.items() if v["probe"]]
    missing_models = [e for e, v in doc["meta"]["models"].items() if v["selected"] and not v["available"]]
    doc["limits"] = {
        "probes": {"n_probe_units": len(probe_units), "units": probe_units,
                   "single_seed": ("the linear probe is fitted with one split seed (%d) and one training seed; "
                                   "a different split can move a probe unit's top-1 and its family" % args.probe_seed),
                   "protocol": PROBE_PROTOCOL},
        "class_imbalance": {
            "note": ("top-1 is computed on the natural corpora with no class-balanced reweighting, so a unit's "
                     "top-1 is dominated by its largest class"),
            "corpus_class_counts": {cid: plan[cid].get("images_per_class") for cid in plan},
            "chance_levels_percent": {cid: plan[cid].get("chance_percent_from_disk", plan[cid]["chance_percent"])
                                      for cid in plan}},
        "encoder_count": {"n_registered": len(ENCODERS), "n_selected": len(encs), "n_analyzed": n_enc,
                          "missing_models_in_selection": missing_models,
                          "note": ("encoders are frozen and used exactly as published; none was fine-tuned here, "
                                   "so the comparison is between checkpoints, not between training recipes")},
        "family_size": {"n_configurations_per_unit": len(LAMBDAS) + 1,
                        "note": ("the health label is a median split of nine top-1 values and a transferred BA "
                                 "over nine target values has a granularity of 1/4 to 1/5; a source fit near 1.0 "
                                 "on nine points is not evidence of a usable operating point (inherited from "
                                 "_p1472)")},
        "statistic": ("M(eps) is the margin CDF evaluated at 2 eps, so it saturates as soon as 2 eps exceeds the "
                      "bulk of the margin distribution; the median margin of these deep operating points is "
                      "negative, which is why the fine grid starts at 0.001"),
        "bootstrap_scope": ("the bootstrap resamples images within a corpus; it quantifies image-sampling "
                            "uncertainty only, not encoder choice, prompt choice or the construction of the "
                            "surgery family"),
        "corpora": ("the marine and sonar trees are the raw data trees used by the archived control (7 classes, "
                    "343 and 1783 images, the eighth sonar class `tire` excluded by construction), not the "
                    "manuscript's canonical protocols (6 concepts / 144 frames optical, 8 classes / 650 "
                    "balanced sonar); the 67-class subset is the manuscript's marine reference domain"),
        "artifact_scope": ("the local run of this script can cover fewer units than the cloud run; meta.selection "
                           "and meta.complete_for_selection record exactly which units are inside this archive"),
        "list": [],
    }
    lim = doc["limits"]
    lim["list"] = [
        "single seed for the linear probe (split seed %d, training seed %d) and one architecture per encoder" % (args.probe_seed, args.probe_seed),
        "class-imbalanced corpora: sonar floats 951/1783 images, marine 7-61 images per class; the 67-class subset is balanced at 24",
        "encoder count: %d registered, %d selected, %d analyzed; probe-free results are zero-shot and probe results are out-of-sample on 30 %% of the corpus" % (len(ENCODERS), len(encs), n_enc),
        "nine configurations per unit make the health label a median split and the transfer BA coarse",
        "the bootstrap covers image sampling only; encoder, prompt and surgery-family choices are not resampled",
        "cross-corpus pairs cannot use the paired bootstrap (the image sets differ), so their intervals are unpaired",
        "the marine and sonar corpora are raw data trees rather than the manuscript's canonical protocols",
        "ascending/descending label convention: 'unhealthy' means top-1 at or below the median, as archived",
    ]
    return doc


# --------------------------------------------------------------------------------------------------
# plan / dry-run
# --------------------------------------------------------------------------------------------------
def build_plan(args, doc=None) -> dict:
    encs, corpora, units = selected_units(args)
    cp = corpus_plan(args.data_root, args.subset_json)
    selection = doc["meta"]["selection"] if doc else {"encoders": encs, "corpora": corpora, "units": units}
    json_units = selection.get("units") or ["%s__%s" % (e, c) for e in selection["encoders"] for c in selection["corpora"]]
    json_units = [u for u in json_units if u in units] or list(json_units)
    sel_encs = sorted({u.split("__")[0] for u in json_units})
    sel_corpora = sorted({u.split("__", 1)[1] for u in json_units})
    models = {}
    for enc_id in all_encoder_ids(args):
        resolved, problems, prov = resolve_assets(enc_id, args.models_root)
        models[enc_id] = {"available": not problems, "assets": prov, "problems": problems,
                          "selected": enc_id in encs}
    plan = {
        "out": OUT_REL, "cache_root": args.cache_root,
        "encoders_selected": encs, "corpora_selected": corpora, "units_selected": units,
        "json_selection": {"encoders": sel_encs, "corpora": sel_corpora, "units": json_units},
        "n_registered_encoders": len(ENCODERS), "n_encoders_selected": len(encs),
        "n_corpora_selected": len(corpora),
        "n_units_full_selection": len(units),
        "n_units_in_json": len(json_units), "n_pairs_in_json": len(json_units) ** 2,
        "eps_fine_grid": EPS_FINE, "eps_archived_grid": EPS_ARCHIVED,
        "c_medrel_grid": C_MEDREL, "c_sigmarel_grid": C_SIGMAREL,
        "lambdas": LAMBDAS, "text_side_row": TEXT_ROW,
        "n_configurations_per_unit": len(LAMBDAS) + 1,
        "n_statistic_keys": len(STAT_KEYS), "statistic_keys": STAT_KEYS,
        "n_boot": int(args.boot), "probe_seed": int(args.probe_seed), "cache_version": CACHE_VERSION,
        "device": args.device, "batch": int(args.batch),
        "models": models, "corpora": cp, "units": json_units,
        "cache_files": [os.path.relpath(cache_path(args.cache_root, u.split("__")[0], u.split("__", 1)[1]), REPO)
                        .replace("\\", "/") for u in json_units],
        "expected_rows_per_unit": len(LAMBDAS) + 1,
    }
    return plan


def _get(doc, path):
    cur = doc
    for key in path:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return None
    return cur


def assert_plan(args, plan, doc, quiet: bool = False) -> tuple[int, int]:
    """Assert every number printed by the plan against the JSON. Returns (n_ok, n_fail)."""
    checks = []

    def add(label, expected, path, transform=None):
        actual = None if doc is None else _get(doc, path)
        if transform is not None and actual is not None:
            try:
                actual = transform(actual)
            except Exception:
                actual = None
        if doc is None:
            status = "UNASSERTED (no JSON yet)"
        elif isinstance(expected, float) and isinstance(actual, (int, float)):
            status = "OK" if abs(float(expected) - float(actual)) < 1e-9 else "FAIL"
        else:
            status = "OK" if expected == actual else "FAIL"
        checks.append({"label": label, "expected": expected, "json_path": ".".join(str(p) for p in path),
                       "actual": actual, "status": status})

    add("output file", plan["out"], ("archive",))
    add("eps fine grid", plan["eps_fine_grid"], ("meta", "eps_fine_grid"))
    add("eps archived grid", plan["eps_archived_grid"], ("meta", "eps_archived_grid"))
    add("c grid (median-margin-relative)", plan["c_medrel_grid"], ("meta", "c_medrel_grid"))
    add("c grid (sigma-relative)", plan["c_sigmarel_grid"], ("meta", "c_sigmarel_grid"))
    add("lambda grid", plan["lambdas"], ("meta", "lambdas"))
    add("text-side row", plan["text_side_row"], ("meta", "text_side_row"))
    add("configurations per unit", plan["n_configurations_per_unit"], ("limits", "family_size", "n_configurations_per_unit"))
    add("bootstrap draws", plan["n_boot"], ("transfer", "protocol", "n_draws"))
    add("bootstrap draws (meta)", plan["n_boot"], ("meta", "n_boot"))
    add("probe seed", plan["probe_seed"], ("meta", "selection", "probe_seed"))
    add("cache version", plan["cache_version"], ("meta", "cache_version"))
    add("units in JSON", plan["n_units_in_json"], ("transfer", "n_units"))
    add("ordered pairs in JSON", plan["n_pairs_in_json"], ("transfer", "n_pairs"))
    add("unit list", sorted(plan["units"]), ("transfer", "units"))
    add("registry: statistic keys", plan["statistic_keys"], ("meta", "statistic_keys"))
    add("registered encoders", plan["n_registered_encoders"], ("meta", "models"), transform=len)
    for cid, spec in plan["corpora"].items():
        if cid not in plan["json_selection"]["corpora"]:
            continue
        add("corpus %s: images on disk" % cid, spec.get("n_images"),
            ("meta", "corpus_size_checks", cid, "n_images"))
        add("corpus %s: classes on disk" % cid, spec.get("n_classes"),
            ("meta", "corpus_size_checks", cid, "n_classes"))
        add("corpus %s: chance percent" % cid, round(100.0 / max(spec.get("n_classes") or 1, 1), 4),
            ("meta", "corpus_size_checks", cid, "chance_percent"))
        if spec.get("images_per_class") is not None:
            add("corpus %s: images per class" % cid, spec["images_per_class"],
                ("meta", "corpus_size_checks", cid, "images_per_class"))
        if spec.get("root_level_files") is not None:
            add("corpus %s: root-level files ignored" % cid, spec["root_level_files"],
                ("meta", "corpus_size_checks", cid, "root_level_files_ignored"))
    for unit in plan["json_selection"]["units"]:
        enc_id, cid = unit.split("__", 1)
        block = ["encoders", enc_id, "corpora", cid]
        if _get(doc, tuple(block)) is None and doc is not None:
            checks.append({"label": "unit %s present" % unit, "expected": True,
                           "json_path": ".".join(block), "actual": None, "status": "FAIL"})
            continue
        add("unit %s: n_family_rows" % unit, plan["expected_rows_per_unit"], tuple(block + ["n_family_rows"]))
        add("unit %s: cache path" % unit,
            os.path.relpath(cache_path(plan["cache_root"], enc_id, cid), REPO).replace("\\", "/"),
            tuple(block + ["cache"]))
        add("unit %s: encoder embed dim" % unit, ENCODERS[enc_id]["embed_dim"], tuple(block + ["embed_dim"]))
        add("unit %s: probe flag" % unit, bool(ENCODERS[enc_id]["probe"]), tuple(block + ["probe"]))
        add("unit %s: chance percent" % unit,
            plan["corpora"][cid].get("chance_percent_from_disk", plan["corpora"][cid]["chance_percent"]),
            tuple(block + ["chance_percent"]))
    for enc_id, m in plan["models"].items():
        if enc_id in plan["json_selection"]["encoders"]:
            add("model %s available on this host" % enc_id, m["available"],
                ("meta", "models", enc_id, "available"))
            for key, asset in m["assets"].items():
                add("model %s asset %s path" % (enc_id, key), asset["path"],
                    ("meta", "models", enc_id, "assets", key, "path"))
                add("model %s asset %s size_mb" % (enc_id, key), asset["size_mb"],
                    ("meta", "models", enc_id, "assets", key, "size_mb"))
    n_ok = sum(1 for c in checks if c["status"] == "OK")
    n_un = sum(1 for c in checks if c["status"].startswith("UNASSERTED"))
    n_fail = sum(1 for c in checks if c["status"] == "FAIL")
    if not quiet:
        print("\n== plan assertions (every number printed above is checked against the JSON) ==", flush=True)
        for c in checks:
            shown = str(c["expected"])
            if len(shown) > 46:
                shown = shown[:43] + "..."
            print("   [%-24s] %-58s %s" % (c["status"], c["label"] + " = " + shown, c["json_path"]), flush=True)
        print("   -> %d asserted OK, %d unasserted, %d FAILED" % (n_ok, n_un, n_fail), flush=True)
    return n_ok, n_fail


def print_plan(args, plan, quiet: bool = False) -> None:
    print("== A23 multi-encoder transfer: plan ==", flush=True)
    print("   output                        : %s" % plan["out"], flush=True)
    print("   embedding cache root          : %s" % os.path.relpath(plan["cache_root"], REPO).replace("\\", "/"),
          flush=True)
    print("   device / batch                : %s / %d" % (plan["device"], plan["batch"]), flush=True)
    print("   data root / models root       : %s / %s"
          % (args.data_root, args.models_root), flush=True)
    print("   registered encoders           : %d (%s)"
          % (plan["n_registered_encoders"], ", ".join(ENCODERS)), flush=True)
    print("   selection                     : %d encoder(s) x %d corpus(es); %d unit(s), %d ordered pairs"
          % (plan["n_encoders_selected"], plan["n_corpora_selected"], plan["n_units_full_selection"],
             plan["n_units_full_selection"] ** 2), flush=True)
    print("   selected units                : %s" % ", ".join(plan["units_selected"]), flush=True)
    print("   JSON selection                : %s x %s -> %d units, %d pairs"
          % (plan["json_selection"]["encoders"], plan["json_selection"]["corpora"],
             plan["n_units_in_json"], plan["n_pairs_in_json"]), flush=True)
    print("   eps fine grid                 : %s" % plan["eps_fine_grid"], flush=True)
    print("   eps archived grid             : %s" % plan["eps_archived_grid"], flush=True)
    print("   c grid (median-margin)        : %s" % plan["c_medrel_grid"], flush=True)
    print("   c grid (sigma-relative)       : %s" % plan["c_sigmarel_grid"], flush=True)
    print("   lambda grid / text row        : %s / %s" % (plan["lambdas"], plan["text_side_row"]), flush=True)
    print("   configurations per unit       : %d" % plan["n_configurations_per_unit"], flush=True)
    print("   statistic keys per pair       : %d" % plan["n_statistic_keys"], flush=True)
    print("   bootstrap draws               : %d (probe seed %d, cache version %d)"
          % (plan["n_boot"], plan["probe_seed"], plan["cache_version"]), flush=True)
    print("   expected rows per unit        : %d" % plan["expected_rows_per_unit"], flush=True)
    print("\n   corpora:", flush=True)
    for cid, spec in plan["corpora"].items():
        flag = "MISSING" if spec.get("missing") else "ok"
        print("     [%-7s] %-16s %5s images %3s classes  chance %6s %%  %s"
              % (flag, cid, spec.get("n_images"), spec.get("n_classes"),
                 spec.get("chance_percent_from_disk", spec["chance_percent"]), spec.get("path")), flush=True)
        if spec.get("images_per_class"):
            print("               images per class: %s" % spec["images_per_class"], flush=True)
        if spec.get("root_level_files"):
            extra = " (the eighth sonar class `tire`)" if cid == "acoustic_sonar" else " (not class directories; ignored)"
            print("               root-level files ignored: %d%s" % (spec["root_level_files"], extra), flush=True)
    print("\n   encoders:", flush=True)
    for enc_id, m in plan["models"].items():
        spec = ENCODERS[enc_id]
        asset = m["assets"].get("snapshot") or m["assets"].get("weights") or {}
        state = "ok" if m["available"] else "MISSING"
        print("     [%-7s] %-24s %-8s dim %3d  probe %-5s  %s"
              % (state, enc_id, spec["group"], spec["embed_dim"], str(spec["probe"]),
                 asset.get("path", "-")), flush=True)
        if m["problems"]:
            for prob in m["problems"]:
                print("               %s" % prob.replace("\n", "\n               "), flush=True)
    print("\n   units and cache files:", flush=True)
    for u in plan["json_selection"]["units"]:
        e, c = u.split("__", 1)
        rel = os.path.relpath(cache_path(plan["cache_root"], e, c), REPO).replace("\\", "/")
        payload, reason = load_cache(plan["cache_root"], e, c, ENCODERS[e]["embed_dim"],
                                     plan["corpora"][c].get("n_classes") or CORPORA[c]["expected_classes"],
                                     None)
        mark = "cached" if payload else ("%s" % reason)
        print("     %-46s %s" % (rel, mark), flush=True)


# --------------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description="A23 multi-encoder threshold-transfer test (encode / analyze / dry-run)")
    ap.add_argument("--encode", action="store_true", help="encode every selected unit and cache the embeddings")
    ap.add_argument("--analyze", action="store_true", help="compute statistics and write the JSON from the cache")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and assert it against the JSON")
    ap.add_argument("--data-root", default=DEFAULT_DATA_ROOT, help="root holding fathomnet8/, NKSID/, rare-species/")
    ap.add_argument("--cache-root", default=DEFAULT_CACHE_ROOT, help="embedding cache directory")
    ap.add_argument("--models-root", default=DEFAULT_MODELS_ROOT, help="root holding the local model directories")
    ap.add_argument("--subset-json", default=DEFAULT_SUBSET_JSON, help="the 67-class subset index (outputs/ocean_subset.json)")
    ap.add_argument("--encoders", default=None, help="comma-separated encoder ids (default: every generic encoder; see --include-adapted)")
    ap.add_argument("--corpora", default=None, help="comma-separated corpus ids (default: all three)")
    ap.add_argument("--units", default=None,
                    help="comma-separated <encoder>__<corpus> units; overrides the --encoders x --corpora product")
    ap.add_argument("--include-adapted", action="store_true", help="also select BioCLIP and OceanCLIP")
    ap.add_argument("--allow-missing-models", action="store_true",
                    help="skip encoders whose weights are not resolvable instead of failing (recorded in meta)")
    ap.add_argument("--force", action="store_true", help="re-encode even when a valid cache exists")
    ap.add_argument("--boot", type=int, default=N_BOOT_DEFAULT, help="bootstrap draws over images (default 2000)")
    ap.add_argument("--probe-seed", type=int, default=PROBE_SEED, help="seed for the linear-probe split and fit")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--out", default=OUT, help="output JSON path")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    a._started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    a._t0 = time.time()
    quiet = a.quiet

    if not (a.encode or a.analyze or a.dry_run):
        ap.error("nothing to do: pass --encode, --analyze and/or --dry-run")

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    a.data_root = os.path.abspath(a.data_root)
    a.cache_root = os.path.abspath(a.cache_root)
    a.models_root = os.path.abspath(a.models_root)

    doc = None
    if os.path.exists(a.out):
        try:
            doc = json.load(io.open(a.out, encoding="utf-8"))
        except Exception as exc:
            print("  existing JSON is unreadable (%s); treating it as absent" % exc, flush=True)
            doc = None

    # ---- dry-run -------------------------------------------------------------------------------
    if a.dry_run:
        plan = build_plan(a, doc)
        print_plan(a, plan, quiet)
        missing_selected = [e for e, m in plan["models"].items() if m["selected"] and not m["available"]]
        n_ok, n_fail = assert_plan(a, plan, doc, quiet)
        if missing_selected and not a.allow_missing_models:
            print("\n   !! selected encoder(s) without resolvable weights: %s" % ", ".join(missing_selected),
                  flush=True)
            print("      fetch them on the server (mirror first, ModelScope fallback) or pass "
                  "--allow-missing-models to skip them", flush=True)
            return 1
        if n_fail:
            print("\n   !! %d plan assertion(s) failed against %s" % (n_fail, OUT_REL), flush=True)
            return 1
        if doc is None:
            print("\n   plan printed; no JSON yet, so the numbers above are marked unasserted. Run "
                  "--encode --analyze, then re-run --dry-run to assert them.", flush=True)
        return 0

    # ---- encode --------------------------------------------------------------------------------
    encoded, skipped_units = [], []
    if a.encode:
        encs, corpora, units = selected_units(a)
        # corpus-major: one corpus is held in memory at a time (all three at once cost >11 GB RSS locally:
        # the parquet subset plus two image trees), and a failure on a later corpus still leaves the earlier
        # caches on disk, so an interrupted run resumes at the first missing unit.
        for cid in sorted({u.split("__", 1)[1] for u in units}):
            spec = CORPORA[cid]
            if spec["kind"] == "class_dirs" and not os.path.isdir(os.path.join(a.data_root, spec["rel"])):
                skipped_units.append({"unit": "corpus:%s" % cid, "reason": "corpus root missing"})
                continue
            if spec["kind"] == "subset_json" and (not os.path.isdir(os.path.join(a.data_root, spec["rel"]))
                                                 or not os.path.exists(a.subset_json)):
                skipped_units.append({"unit": "corpus:%s" % cid, "reason": "corpus or subset index missing"})
                continue
            log("[%s] loading images" % cid, quiet)
            cdata = load_corpus(cid, a.data_root, a.subset_json, quiet)
            au = cdata["audit"]
            log("[%s] %s images, %s classes%s"
                % (cid, au.get("n_images"), au.get("n_classes"),
                   "" if not au.get("root_level_files_ignored") else
                   ", %d root-level file(s) ignored" % au["root_level_files_ignored"]), quiet)
            if cdata.get("error") or not cdata["items"]:
                skipped_units.append({"unit": "corpus:%s" % cid,
                                      "reason": cdata.get("error") or "no images decoded"})
                continue
            n_classes = len(cdata["class_names"])
            for unit in [u for u in units if u.endswith("__" + cid)]:
                enc_id = unit.split("__", 1)[0]
                if not a.force:
                    payload, reason = load_cache(a.cache_root, enc_id, cid, ENCODERS[enc_id]["embed_dim"],
                                                 n_classes, cdata["fingerprint"])
                    if payload is not None:
                        log("[%s / %s] cache valid (%s), reusing" % (enc_id, cid, reason), quiet)
                        encoded.append({"unit": unit, "reused": True, "path": payload["path"]})
                        continue
                    log("[%s / %s] cache not reusable: %s" % (enc_id, cid, reason), quiet)
                res = encode_unit(enc_id, cid, a, {cid: cdata}, quiet)
                if not res["ok"]:
                    if a.allow_missing_models and "is missing" in res["reason"]:
                        skipped_units.append({"unit": unit, "reason": res["reason"]})
                        log("[%s / %s] skipped: %s" % (enc_id, cid, res["reason"].splitlines()[0]), quiet)
                        continue
                    print("\n   !! cannot encode %s on %s:\n      %s" % (enc_id, cid, res["reason"]), flush=True)
                    return 2
                encoded.append({"unit": unit, "reused": False, "path": res["path"],
                                "seconds": res["seconds"], "probe_stats": res["probe_stats"]})
            del cdata

    # ---- analyze -------------------------------------------------------------------------------
    if a.analyze or a.encode:
        doc = run_analyze(a, quiet)
        doc["meta"]["units_skipped"] = doc["meta"].get("units_skipped", []) + skipped_units
        if a.encode:
            doc["meta"]["encode_log"] = encoded
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        io.open(a.out, "w", encoding="utf-8", newline="").write(json.dumps(doc, indent=1, ensure_ascii=True))
        log("wrote %s (%d units, %d ordered pairs, %d scored cross-unit entries, %d bootstrap survivors)"
            % (os.path.relpath(a.out, REPO), doc["transfer"]["n_units"], doc["transfer"]["n_pairs"],
               doc["conclusion"]["n_scored_entries_cross_unit"],
               doc["conclusion"]["n_entries_surviving_bootstrap"]), quiet)
        print("   conclusion: %s" % doc["conclusion"]["answer"], flush=True)
        print("   %s" % doc["conclusion"]["headline"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())