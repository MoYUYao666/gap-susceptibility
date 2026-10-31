# -*- coding: utf-8 -*-
r"""Cross-modal susceptibility on REAL audio-caption data (local GPU, inference only, memory-safe chunking).

Dataset: `ashraq/esc50` (ESC-50: 2000 five-second recordings, 50 human-annotated categories), read straight from the
parquet shards so only the sampled rows are decoded. The category name serves as a real human-written description.

Why chunked: the 8 GB card cannot hold a graph for a few hundred clips, so the measurement runs in clips of `CHUNK`
and reports a size-weighted DG plus per-tower gradient norms accumulated as root-mean-square over chunks (an
approximation, stated as such). Bootstrap confidence intervals resample clips the same way.

Outputs outputs/analysis/paperA_crossmodal_esc50.json (English keys).
"""
import io
import json
import os

import numpy as np
import torch

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEST = os.path.join("local_runs", "models", "clap-htsat-unfused")
OUT = "outputs/analysis/paperA_crossmodal_esc50.json"
N_CLIPS = int(os.environ.get("ESC50_CLIPS", "160"))
N_BOOT = int(os.environ.get("ESC50_BOOT", "120"))
CHUNK = int(os.environ.get("ESC50_CHUNK", "24"))


def load_model():
    from transformers import AutoProcessor, ClapModel
    model = ClapModel.from_pretrained(DEST, local_files_only=True)
    proc = AutoProcessor.from_pretrained(DEST, local_files_only=True)
    return model, proc


def load_pairs(n_clips):
    import glob as globmod
    import io as iomod

    import librosa
    import pyarrow.parquet as pq
    import soundfile as sf

    root = os.path.join("local_runs", "hf", "hub", "datasets--ashraq--esc50", "snapshots")
    shards = sorted(globmod.glob(os.path.join(root, "*", "data", "*.parquet")))
    if not shards:
        raise SystemExit("ESC-50 parquet not found under %s" % root)
    pf = pq.ParquetFile(shards[0])
    total = pf.metadata.num_rows
    stride = max(1, total // n_clips)
    wanted = set(range(0, total, stride))
    audio, texts, labels = [], [], []
    seen = 0
    for batch in pf.iter_batches(batch_size=64):
        d = batch.to_pydict()
        count = len(d[list(d)[0]])
        for i in range(count):
            if len(audio) >= n_clips:
                break
            if seen not in wanted:
                seen += 1
                continue
            seen += 1
            a = d["audio"][i]
            raw = a.get("bytes") if isinstance(a, dict) else None
            if not raw:
                continue
            arr, sr = sf.read(iomod.BytesIO(raw), dtype="float32")
            if arr.ndim > 1:
                arr = arr.mean(axis=1)
            if int(sr) != 48000:
                arr = librosa.resample(np.asarray(arr, dtype=np.float32), orig_sr=int(sr), target_sr=48000)
            audio.append(np.asarray(arr, dtype=np.float32))
            label = str(d["category"][i]) if "category" in d else str(d["target"][i])
            labels.append(label)
            texts.append("the sound of %s" % label)
        if len(audio) >= n_clips:
            break
    return audio, 48000, texts, labels


def _pool(x):
    if hasattr(x, "pooler_output") and x.pooler_output is not None:
        return x.pooler_output
    if hasattr(x, "last_hidden_state"):
        return x.last_hidden_state.mean(dim=1)
    return x


def measure(model, proc, audio, sr, texts, device):
    """Size-weighted DG and root-mean-square tower gradient norms, computed chunk by chunk."""
    n = len(audio)
    dg_parts, audio_sq, text_sq, sizes = [], [], [], []
    for start in range(0, n, CHUNK):
        stop = min(start + CHUNK, n)
        a_chunk, t_chunk = audio[start:stop], texts[start:stop]
        for p in model.parameters():
            p.requires_grad_(False)
        for tower in (model.audio_model, model.text_model):
            for p in tower.parameters():
                p.requires_grad_(True)
        inputs = proc(audio=a_chunk, sampling_rate=sr, return_tensors="pt", padding=True)
        tokens = proc(text=t_chunk, return_tensors="pt", padding=True, truncation=True)
        a_in = {k: v.to(device) for k, v in inputs.items() if k in ("input_features", "is_longer")}
        t_in = {k: v.to(device) for k, v in tokens.items() if k == "input_ids"}
        emb_a = _pool(model.get_audio_features(**a_in))
        emb_t = _pool(model.get_text_features(**t_in))
        a = emb_a / emb_a.norm(dim=-1, keepdim=True)
        t = emb_t / emb_t.norm(dim=-1, keepdim=True)
        dg = ((a - t) ** 2).mean()
        dg_parts.append(float(dg.detach().cpu()))
        sizes.append(stop - start)
        for idx, (name, tower) in enumerate((("audio", model.audio_model), ("text", model.text_model))):
            g = torch.autograd.grad(dg, [p for p in tower.parameters() if p.requires_grad],
                                    retain_graph=(idx == 0), allow_unused=True)
            norm = float(torch.sqrt(sum((x ** 2).sum() for x in g if x is not None)).item())
            (audio_sq if name == "audio" else text_sq).append(norm ** 2)
        del emb_a, emb_t, a, t, dg
        torch.cuda.empty_cache()
    sizes = np.array(sizes, float)
    dg = float((np.array(dg_parts) * sizes).sum() / sizes.sum())
    grad = {"audio": float(np.sqrt(np.mean(audio_sq))), "text": float(np.sqrt(np.mean(text_sq)))}
    total = float(np.sqrt(sum(v ** 2 for v in grad.values()))) or 1.0
    return {"dg": dg, "grad_norm": grad, "gamma_relative": {k: v / total for k, v in grad.items()}}


def main() -> int:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("device:", device, flush=True)
    model, proc = load_model()
    model.to(device).eval()
    audio, sr, texts, labels = load_pairs(N_CLIPS)
    print("clips:", len(audio), "| classes:", len(set(labels)), "| chunk:", CHUNK, flush=True)

    matched = measure(model, proc, audio, sr, texts, device)
    rng = np.random.default_rng(7)
    shuffled = [texts[i] for i in rng.permutation(len(texts))]
    mismatch = measure(model, proc, audio, sr, shuffled, device)

    rng2 = np.random.default_rng(11)
    dg_boot, share_boot = [], []
    n = len(audio)
    for _ in range(N_BOOT):
        idx = rng2.integers(0, n, n)
        r = measure(model, proc, [audio[i] for i in idx], sr, [texts[i] for i in idx], device)
        dg_boot.append(r["dg"])
        share_boot.append(r["gamma_relative"]["text"])
    ci = lambda v: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))

    res = {"script": "tools/_p1782_crossmodal_real.py", "backbone": "laion/clap-htsat-unfused",
           "dataset": "ashraq/esc50 (ESC-50, human-annotated categories)",
           "modality_pair": "audio-text", "n_pairs": len(audio), "n_classes": len(set(labels)),
           "chunk": CHUNK, "device": device, "matched": matched, "mismatched_captions": mismatch,
           "bootstrap": {"n_resamples": N_BOOT, "dg_ci95": ci(dg_boot), "text_gamma_ci95": ci(share_boot)},
           "note": "inference only; DG is size-weighted mean squared distance of normalised paired embeddings; "
                   "tower gradients are root-mean-square over chunks (approximation, stated)"}
    io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    print("wrote", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
