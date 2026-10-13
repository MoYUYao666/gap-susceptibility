# -*- coding: utf-8 -*-
r"""P3 R3.13：**逐块 Γ 在真实图文 vs blank images 下的差异**（CLIP ViT-B/32）。

## 定义（照抄论文 Appendix D 的协议）

    Γ_k = ⟨∇_{M_k} E, u_k⟩,   u_k = −∇_{M_k} L_task

两次反传：一次对 alignment energy $E$，一次对任务损失 $L_{\rm task}$（对比损失）。
论文用 **5 prompts 平均**、blank images、rank r=8 报的表（`tab:gamma_detail`）。
本脚本把**图像条件**变成自变量：`real` = Flickr30k 真实 jpg，`blank` = 全零张量。

块划分（K=4，与论文 Appendix D 同构；CLIP 文本塔 12 层）：

    vision        视觉编码器全部 LoRA 层
    text_shallow  文本层 0–2   （≈论文 7/32）
    text_mid      文本层 3–8   （≈论文 16/32）
    text_deep     文本层 9–11  （≈论文 8/32）

**LoRA 两侧都注入**（vision + text），否则没有 vision 块可测——故本实验用
`_p461` 的 `both` 臂设置。这与论文 LLaVA 主实验"vision encoder frozen"不同，
是**为了量 Γ 的块排序**而必须做的选择，已在报告中注明。

## 输出

`outputs/analysis/p3d_gamma_real_vs_blank.json`：
`conditions.{real,blank}.blocks.{name}` 里逐块 Γ_k / ‖∇E_k‖ / cos φ_k / %|Γ|，
外加 `ordering`（按 |Γ| 降序的块名列表）与 `per_batch`（逐 prompt 原始值，可复核）。

    python tools\_p462_gamma_real_vs_blank.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "outputs" / "analysis" / "p3d_gamma_real_vs_blank.json"
MANIFEST = REPO / "outputs" / "analysis" / "p3d_manifest.json"
MODEL_DIR = REPO / "models" / "clip-vit-base-patch32"
RANK = 8
N_PROMPTS = 5          # 每批 prompt 数（论文 Appendix D：5-prompt 平均）
N_BATCHES = 3          # 3 批 ×5，给出均值±标准差（单批无法估波动）
LAYER_SPLIT = {"text_shallow": (0, 2), "text_mid": (3, 8), "text_deep": (9, 11)}


def block_of(name: str) -> str:
    """LoRA 参数名 → 块名。

    注入后 `model.named_parameters()` 的真实名字带 **`vision_model.` / `text_model.`**
    前缀（不是 `vision.` / `text.`——那是 `apply_lora_to_model` 内部的 lora_layers key）。
    形如 `text_model.encoder.layers.3.self_attn.q_proj.lora_A`。
    """
    if name.startswith("vision_model."):
        return "vision"
    if name.startswith("text_model."):
        parts = name.split(".")
        try:
            li = int(parts[parts.index("layers") + 1])
        except (ValueError, IndexError):
            return "text_other"
        for blk, (lo, hi) in LAYER_SPLIT.items():
            if lo <= li <= hi:
                return blk
        return "text_other"
    return "other"


def measure(model, img, ids, am, device):
    """返回 {block: {'gamma','norm_gE','norm_gL','cos','E','L'}}（单批瞬时）。

    注意：任务损失必须在 **batch ≥ 2** 上算——batch=1 时对称对比 CE 只有单个
    正样本、无负样本，恒等于 0，∇L_task ≡ 0 ⇒ Γ ≡ 0（2026-10-12 实测踩过）。
    E 与 L 由**同一次前向**算出，用 retain_graph 分两次反传，保证两次反传
    作用在同一组激活上。
    """
    import torch
    import torch.nn.functional as F

    params = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    assert img.shape[0] >= 2, f"batch 必须 ≥2，实得 {img.shape[0]}"

    model.zero_grad(set_to_none=True)
    o = model(pixel_values=img, input_ids=ids, attention_mask=am)
    I = F.normalize(o.image_embeds.float(), p=2, dim=-1)
    T = F.normalize(o.text_embeds.float(), p=2, dim=-1)
    E = ((I - T) ** 2).sum(-1).mean()
    logits = model.logit_scale.exp() * I @ T.T
    lab = torch.arange(I.shape[0], device=I.device)
    L = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
    assert float(L) > 0, f"任务损失为 0（batch={img.shape[0]}）→ Γ 不可测"

    E.backward(retain_graph=True)
    gE = {n: p.grad.detach().float().clone() for n, p in params if p.grad is not None}
    model.zero_grad(set_to_none=True)
    L.backward()
    gL = {n: p.grad.detach().float().clone() for n, p in params if p.grad is not None}
    model.zero_grad(set_to_none=True)

    acc: dict[str, dict[str, float]] = {}
    for n, g in gE.items():
        if n not in gL:
            continue
        b = block_of(n)
        d = acc.setdefault(b, {"dot": 0.0, "nE": 0.0, "nL": 0.0})
        d["dot"] += float((g * gL[n]).sum())      # ⟨∇E, ∇L⟩
        d["nE"] += float((g * g).sum())
        d["nL"] += float((gL[n] * gL[n]).sum())
    out = {}
    for b, d in acc.items():
        nE, nL = d["nE"] ** 0.5, d["nL"] ** 0.5
        out[b] = {"gamma": -d["dot"], "norm_gE": nE, "norm_gL": nL,
                  "cos": (-d["dot"] / (nE * nL)) if nE > 0 and nL > 0 else 0.0,
                  "E": float(E), "L": float(L)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--device", default=None)
    a = ap.parse_args()

    import torch
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor
    from src.lora import apply_lora_to_model

    device = a.device or ("cuda" if torch.cuda.is_available() else "cpu")
    mf = json.loads(io.open(MANIFEST, encoding="utf-8").read())["datasets"]["flickr30k"]
    sel = mf["train_sel"]["16"][:N_PROMPTS * N_BATCHES]
    imgdir = REPO / "flickr30k" / "flickr30k-images"
    print(f"=== P3 R3.13: 逐块 Γ，真实图文 vs blank（CLIP B/32, rank={RANK}, "
          f"{N_PROMPTS} prompts, device={device}）===")

    torch.manual_seed(42)
    model = CLIPModel.from_pretrained(str(MODEL_DIR), local_files_only=True)
    for p in model.parameters():
        p.requires_grad = False
    model, layers, n_peft = apply_lora_to_model(
        model, rank=RANK, alpha=RANK * 2.0, dropout=0.0,
        target_modules=["q_proj", "v_proj"],
        apply_to_vision=True, apply_to_text=True)
    model = model.to(device).float().eval()
    proc = CLIPProcessor.from_pretrained(str(MODEL_DIR), local_files_only=True)

    blocks = {}
    for n, _ in model.named_parameters():
        if n.endswith(("lora_A", "lora_B")):
            blocks.setdefault(block_of(n), 0)
            blocks[block_of(n)] += 1
    print(f"  LoRA 参数张量数按块: {blocks}")

    px_real, ids, am = [], [], []
    for s in sel:
        with Image.open(imgdir / s["image"]) as im:
            px_real.append(proc(images=im.convert("RGB"),
                                return_tensors="pt")["pixel_values"][0])
        e = proc.tokenizer(text=s["caption"], return_tensors="pt", padding="max_length",
                           truncation=True, max_length=77)
        ids.append(e["input_ids"][0]); am.append(e["attention_mask"][0])
    px_real = torch.stack(px_real)
    ids = torch.stack(ids)
    am = torch.stack(am)
    assert px_real.shape[0] == ids.shape[0] == am.shape[0] == N_PROMPTS * N_BATCHES
    print(f"  prompts: {N_PROMPTS * N_BATCHES} (= {N_BATCHES} 批 × {N_PROMPTS}), "
          f"pixel {tuple(px_real.shape)}, tokens {tuple(ids.shape)}")

    result = {"experiment": "p3d_gamma_real_vs_blank",
              "script": "tools/_p462_gamma_real_vs_blank.py",
              "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "model": "models/clip-vit-base-patch32", "rank": RANK,
              "protocol": {"gamma": "Gamma_k = <grad_{M_k} E, -grad_{M_k} L_task>",
                           "E": "mean||normalize(z_I)-normalize(z_T)||^2 (retrieval)",
                           "L_task": "symmetric contrastive CE (same as _p461), batch=5",
                           "prompts_per_batch": N_PROMPTS, "n_batches": N_BATCHES,
                           "batch_offsets": [i * N_PROMPTS for i in range(N_BATCHES)],
                           "why_batch_ge_2": "batch=1 时对称对比 CE 恒为 0 → ∇L_task≡0 → Γ≡0",
                           "lora": "apply_to_vision=True, apply_to_text=True, dropout=0.0",
                           "blocks": {"vision": "all vision LoRA",
                                      **{k: f"text layers {v[0]}-{v[1]}"
                                         for k, v in LAYER_SPLIT.items()}},
                           "data": "outputs/analysis/p3d_manifest.json:"
                                   "datasets.flickr30k.train_sel['16'], 前 15 条分成 3 批 ×5"},
              "conditions": {}}

    for cond in ("real", "blank"):
        px = px_real if cond == "real" else torch.zeros_like(px_real)
        per_batch = []
        for bi in range(N_BATCHES):
            lo = bi * N_PROMPTS
            hi = lo + N_PROMPTS
            m = measure(model, px[lo:hi].to(device), ids[lo:hi].to(device),
                        am[lo:hi].to(device), device)
            per_batch.append(m)
            print(f"    [{cond} batch {bi+1}/{N_BATCHES}] L={m[list(m)[0]]['L']:.4f} "
                  f"Γ=" + " ".join(f"{k}:{m[k]['gamma']:+.1f}" for k in sorted(m)), flush=True)
        keys = sorted(per_batch[0].keys())
        agg = {}
        for blk in keys:
            g = [m[blk]["gamma"] for m in per_batch if blk in m]
            mu = sum(g) / len(g)
            agg[blk] = {
                "gamma": mu,
                "gamma_std": (sum((x - mu) ** 2 for x in g) / max(len(g) - 1, 1)) ** 0.5,
                "norm_gE": sum(m[blk]["norm_gE"] for m in per_batch if blk in m) / len(per_batch),
                "norm_gL": sum(m[blk]["norm_gL"] for m in per_batch if blk in m) / len(per_batch),
                "cos": sum(m[blk]["cos"] for m in per_batch if blk in m) / len(per_batch),
            }
        tot = sum(abs(v["gamma"]) for v in agg.values()) or 1.0
        for b, v in agg.items():
            v["pct_abs_gamma"] = 100.0 * abs(v["gamma"]) / tot
        order = sorted(agg, key=lambda b: -abs(agg[b]["gamma"]))
        result["conditions"][cond] = {
            "blocks": agg, "ordering_by_abs_gamma": order,
            "E_mean": sum(m[keys[0]]["E"] for m in per_batch) / N_BATCHES,
            "L_mean": sum(m[keys[0]]["L"] for m in per_batch) / N_BATCHES,
            "per_batch": per_batch,
        }
        print(f"\n  ── {cond} ──  E={result['conditions'][cond]['E_mean']:.4f} "
              f"L={result['conditions'][cond]['L_mean']:.4f}")
        for b in order:
            v = agg[b]
            print(f"     {b:<13} Γ={v['gamma']:+12.2f} ±{v['gamma_std']:9.2f}  "
                  f"‖∇E‖={v['norm_gE']:10.2f}  cos={v['cos']:+.4f}  "
                  f"|Γ|%={v['pct_abs_gamma']:5.1f}")

    r, b = result["conditions"]["real"], result["conditions"]["blank"]
    result["comparison"] = {
        "ordering_real": r["ordering_by_abs_gamma"],
        "ordering_blank": b["ordering_by_abs_gamma"],
        "ordering_identical": r["ordering_by_abs_gamma"] == b["ordering_by_abs_gamma"],
        "spearman_abs_gamma": None,   # 下面算
    }
    import statistics
    blocks = list(r["ordering_by_abs_gamma"])
    ra = [abs(r["blocks"][k]["gamma"]) for k in blocks]
    ba = [abs(b["blocks"][k]["gamma"]) for k in blocks]

    def _spearman(x, y):
        """秩相关（并列取平均秩）。"""
        def ranks(v):
            order = sorted(range(len(v)), key=lambda i: v[i])
            rk = [0.0] * len(v)
            i = 0
            while i < len(order):
                j = i
                while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                    j += 1
                avg = (i + j) / 2.0
                for t in range(i, j + 1):
                    rk[order[t]] = avg
                i = j + 1
            return rk
        rx, ry = ranks(x), ranks(y)
        mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
        num = sum((a - mx) * (bb - my) for a, bb in zip(rx, ry))
        dx = sum((a - mx) ** 2 for a in rx) ** 0.5
        dy = sum((bb - my) ** 2 for bb in ry) ** 0.5
        return num / (dx * dy) if dx > 0 and dy > 0 else float("nan")

    result["comparison"] = {
        "blocks": blocks,
        "abs_gamma_real": [round(v, 4) for v in ra],
        "abs_gamma_blank": [round(v, 4) for v in ba],
        "ordering_real": r["ordering_by_abs_gamma"],
        "ordering_blank": b["ordering_by_abs_gamma"],
        "ordering_identical": r["ordering_by_abs_gamma"] == b["ordering_by_abs_gamma"],
        "kendall_tau_abs_gamma": round(_spearman(ra, ba), 4),
        "ratio_abs_gamma_blank_over_real": [round(y / x, 4) if x else None
                                            for x, y in zip(ra, ba)],
    }
    print(f"\n  块（按 real 的 |Γ| 降序）: {blocks}")
    print(f"  排序 real : {' > '.join(r['ordering_by_abs_gamma'])}")
    print(f"  排序 blank: {' > '.join(b['ordering_by_abs_gamma'])}")
    print(f"  排序一致: {result['comparison']['ordering_identical']}  "
          f"秩相关(|Γ| real vs blank) = {result['comparison']['kendall_tau_abs_gamma']}")

    if not a.apply:
        print("\n（预演；加 --apply 写文件）")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="").write(
        json.dumps(result, ensure_ascii=False, indent=1))
    print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
