"""OpenCLIP + BitFit ODE fit — recovers the Paper A generalization table

Usage:
  conda activate pytorch
  python exp/run_openclip_bitfit.py --method openclip
  python exp/run_openclip_bitfit.py --method bitfit

Dependencies: src/ (trainer, dataset, gap_susceptibility) — src/ must be included when packaging

Output: openclip_results.json / bitfit_results.json
  [{"name", "seed", "alpha", "beta", "r_squared", "dg_star_trajectory"}, ...]
"""
import os, sys, json, warnings
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch
from scipy.optimize import curve_fit

warnings.filterwarnings("ignore")

NUM_EPOCHS = 10
BATCH_SIZE = 128
LEARNING_RATE = 1e-4
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def fit_exponential(epochs, dg_star_vals):
    """Fit DG*(t) = A + B*exp(-beta*t). Returns (A, B, beta, r_squared)."""
    epochs = np.array(epochs, dtype=float)
    dg_star_vals = np.array(dg_star_vals, dtype=float)
    if len(epochs) < 3:
        return None, None, None, None

    def model(t, A, B, beta):
        return A + B * np.exp(-beta * t)

    A0 = float(dg_star_vals[-1])
    B0 = float(dg_star_vals[0] - A0)
    try:
        popt, _ = curve_fit(model, epochs, dg_star_vals,
                            p0=[A0, B0, 0.5], maxfev=5000)
        A, B, beta = popt
        predicted = model(epochs, A, B, beta)
        ss_res = np.sum((dg_star_vals - predicted) ** 2)
        ss_tot = np.sum((dg_star_vals - np.mean(dg_star_vals)) ** 2)
        r2 = 1.0 - ss_res / max(ss_tot, 1e-8)
        return float(A), float(B), float(abs(beta)), float(r2)
    except Exception:
        return None, None, None, None


_TOKENIZER_CACHE = {}


def get_tokenizer(method):
    if method not in _TOKENIZER_CACHE:
        if method == 'openclip':
            import open_clip
            _TOKENIZER_CACHE[method] = open_clip.get_tokenizer("ViT-B-32")
        else:
            from transformers import CLIPProcessor
            _TOKENIZER_CACHE[method] = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32").tokenizer
    return _TOKENIZER_CACHE[method]


def load_model(method):
    """OpenCLIP or CLIP (BitFit: bias-only)."""
    if method == 'openclip':
        import open_clip
        m, _, _ = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="laion2b_s34b_b79k")
    else:  # bitfit
        from transformers import CLIPModel
        m = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    m = m.to(DEVICE)
    m.train()
    # BitFit: unfreeze only the bias
    for n, p in m.named_parameters():
        p.requires_grad = "bias" in n
    return m


_TOKENIZER_METHOD = 'openclip'


def get_embeds(model, batch):
    if isinstance(batch, dict):
        # raw batch (image/caption strings)
        img = batch["image"].to(DEVICE)
        txt = batch["caption"]
        tok = get_tokenizer(_TOKENIZER_METHOD)
        return get_embeds_tok(model, img, tok)
    # already-tokenized (img_tensor, tokens)
    img, tokens = batch
    return get_embeds_tok(model, img, tokens)


def compute_dg_star(model, batch):
    zi, zt = get_embeds(model, batch)
    return torch.mean(torch.sum((zi - zt) ** 2, dim=-1)).item()


def get_embeds_tok(model, img, tokens):
    if hasattr(model, 'get_image_features'):
        zi = model.get_image_features(img)
        zt = model.get_text_features(tokens)
        # handle the case that returns BaseModelOutputWithPooling
        if not torch.is_tensor(zi):
            zi = zi.pooler_output if zi.pooler_output is not None else zi.last_hidden_state.mean(dim=1)
        if not torch.is_tensor(zt):
            zt = zt.pooler_output if zt.pooler_output is not None else zt.last_hidden_state.mean(dim=1)
    else:  # open_clip
        zi = model.encode_image(img)
        zt = model.encode_text(tokens)
    zi = torch.nn.functional.normalize(zi, dim=-1)
    zt = torch.nn.functional.normalize(zt, dim=-1)
    return zi, zt


def contrastive_loss(model, batch):
    zi, zt = get_embeds(model, batch)
    logits = zi @ zt.T * 100.0
    labels = torch.arange(len(zi), device=DEVICE)
    return (torch.nn.functional.cross_entropy(logits, labels)
            + torch.nn.functional.cross_entropy(logits.T, labels)) / 2


def run_seed(method, seed, train_loader):
    torch.manual_seed(seed)
    np.random.seed(seed)
    model = load_model(method)
    tokenizer = get_tokenizer(method)
    opt = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=LEARNING_RATE)

    def tokenize_batch(batch):
        texts = batch["caption"]
        if method == 'openclip':
            tokens = tokenizer(texts).to(DEVICE)
            return batch["image"].to(DEVICE), tokens
        else:
            tokens = tokenizer(texts, return_tensors="pt", padding=True).input_ids.to(DEVICE)
            return batch["image"].to(DEVICE), tokens

    first_batch = next(iter(train_loader))
    dg_star_history = [compute_dg_star(model, tokenize_batch(first_batch))]
    for epoch in range(NUM_EPOCHS):
        model.train()
        for batch in train_loader:
            loss = contrastive_loss(model, tokenize_batch(batch))
            opt.zero_grad()
            loss.backward()
            opt.step()
        dg_star_history.append(compute_dg_star(model, tokenize_batch(first_batch)))

    epochs = list(range(len(dg_star_history)))
    A, B, beta, r2 = fit_exponential(epochs, dg_star_history)
    alpha = None
    if beta is not None:
        alpha = beta * (A - dg_star_history[0])
    return {
        "name": f"{method}_s{seed}",
        "seed": seed,
        "alpha": alpha,
        "beta": beta,
        "r_squared": r2,
        "dg_star_trajectory": dg_star_history,
    }


def main():
    import argparse, os
    parser = argparse.ArgumentParser()
    parser.add_argument('--method', choices=['openclip', 'bitfit'], required=True)
    parser.add_argument('--seeds', type=int, default=3)
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()

    out_path = args.output or f"{args.method}_results.json"

    # ===== Resume: read existing results, skip seeds already done =====
    results = []
    done_seeds = set()
    if os.path.exists(out_path):
        try:
            with open(out_path, encoding='utf-8') as f:
                results = json.load(f)
            done_seeds = {r['seed'] for r in results}
            print(f"[resume] {len(results)} already done: seeds {sorted(done_seeds)}", flush=True)
        except Exception as e:
            print(f"[resume] read failed (starting from scratch): {e}", flush=True)
            results = []

    from src.dataset import create_dataloaders
    try:
        _, train_loader, _ = create_dataloaders(
            dataset_name="flickr30k", data_dir=str(PROJECT_ROOT),
            batch_size=BATCH_SIZE, max_samples=500, num_workers=0)
    except Exception as e:
        print(f"WARNING: dataset loading failed (flickr30k data may be required): {e}")
        print("Experiment 5 must be run locally (the data is local), or upload the flickr30k data")
        return

    for seed in [42, 123, 456][:args.seeds]:
        if seed in done_seeds:
            print(f"  seed={seed}: already done, skipping", flush=True)
            continue
        print(f"  seed={seed}: training {args.method}...", flush=True)
        r = run_seed(args.method, seed, train_loader)
        results.append(r)

        # save immediately after each one completes (core of resuming)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        print(f"  [saved] {r['name']}: α={r['alpha']} β={r['beta']} R²={r['r_squared']}", flush=True)

    print(f"Saved: {out_path}")
    for r in results:
        print(f"  {r['name']}: α={r['alpha']} β={r['beta']} R²={r['r_squared']}")


if __name__ == '__main__':
    main()
