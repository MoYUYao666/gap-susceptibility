# -*- coding: utf-8 -*-
r"""Local run (1): cross-modal susceptibility for an audio-text backbone, on the laptop GPU.

Measures the same quantities the manuscript uses for image-text backbones, on LAION-CLAP:
  DG        mean squared distance between the paired, L2-normalised audio and text embeddings
  grad_k    ||d DG / d theta_k|| for the audio and text towers (one backward pass, no optimiser step)
  gamma_k   grad_k / sum(grad)  - the relative susceptibility the paper's ordering is about
Inputs are four deterministic synthetic tones paired with matching captions, so the measurement needs no corpus
download: it is the geometry of the encoder pair, which is exactly what the cross-modal claim is about.

Writes outputs/analysis/paperA_crossmodal_gamma_clap_local.json (English keys).
"""
import io
import json
import os
import sys

import numpy as np
import torch

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO_ID = "laion/clap-htsat-unfused"
OUT = "outputs/analysis/paperA_crossmodal_gamma_clap_local.json"
CACHE = os.path.join("local_runs", "ms")


def load_model():
    from transformers import AutoProcessor, ClapModel
    # only ModelScope is reachable from this machine, so the checkpoint is fetched there and loaded from disk
    import glob as _glob, shutil as _shutil
    dest = os.path.join("local_runs", "models", "clap-htsat-unfused")
    have = _glob.glob(os.path.join(dest, "*.bin")) + _glob.glob(os.path.join(dest, "*.safetensors"))
    if not have:
        os.environ.setdefault("MODELSCOPE_CACHE", CACHE)
        from modelscope.hub.snapshot_download import snapshot_download
        local = snapshot_download("laion/clap-htsat-unfused", cache_dir=CACHE)
        os.makedirs(dest, exist_ok=True)
        for f in _glob.glob(os.path.join(local, "*")):
            if os.path.isfile(f):
                _shutil.copy2(f, dest)
    model = ClapModel.from_pretrained(dest, local_files_only=True)
    proc = AutoProcessor.from_pretrained(dest, local_files_only=True)
    return model, proc


def main() -> int:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("device:", device, flush=True)
    model, proc = load_model()
    model.to(device).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    # the graph has to exist before the forward pass, so both towers are made differentiable up front
    for _tower in (model.audio_model, model.text_model):
        for _p in _tower.parameters():
            _p.requires_grad_(True)

    sr = 48000
    freqs = [220.0, 330.0, 440.0, 550.0]
    texts = ["a low tone", "a low mid tone", "a mid tone", "a high tone"]
    dur = 1.5
    t = np.arange(int(sr * dur)) / sr
    audios = [0.1 * np.sin(2 * np.pi * f * t).astype("float32") for f in freqs]

    audio_in = proc(audio=audios, sampling_rate=sr, return_tensors="pt", padding=True)
    text_in = proc(text=texts, return_tensors="pt", padding=True)
    audio_in = {k: v.to(device) for k, v in audio_in.items() if k in ("input_features", "is_longer")}
    text_in = {k: v.to(device) for k, v in text_in.items() if k == "input_ids"}

    with torch.enable_grad():
        def _emb(x):
            if hasattr(x, "pooler_output") and x.pooler_output is not None:
                return x.pooler_output
            if hasattr(x, "last_hidden_state"):
                return x.last_hidden_state.mean(dim=1)
            return x
        a = _emb(model.get_audio_features(**audio_in))
        b = _emb(model.get_text_features(**text_in))
        a = a / a.norm(dim=-1, keepdim=True)
        b = b / b.norm(dim=-1, keepdim=True)
        dg = ((a - b) ** 2).mean()
        grads = {}
        for name, tower in (("audio", model.audio_model), ("text", model.text_model)):
            for p in tower.parameters():
                p.requires_grad_(True)
            g = torch.autograd.grad(dg, [p for p in tower.parameters() if p.requires_grad],
                                    retain_graph=True, allow_unused=True)
            grads[name] = float(torch.sqrt(sum((x ** 2).sum() for x in g if x is not None)).item())
            for p in tower.parameters():
                p.requires_grad_(False)

    total = float(np.sqrt(sum(v ** 2 for v in grads.values()))) or 1.0
    gamma = {k: v / total for k, v in grads.items()}
    res = {"script": "tools/_p1773_local_crossmodal.py", "backbone": REPO_ID, "modality_pair": "audio-text",
           "device": device, "n_pairs": len(texts), "dg": float(dg.detach().cpu()),
           "grad_norm": grads, "gamma_relative": gamma,
           "ordering_by_gamma": sorted(gamma, key=lambda k: -gamma[k]),
           "note": "deterministic synthetic tones paired with matching captions; measures the geometry of the encoder pair"}
    os.makedirs("outputs/analysis", exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
