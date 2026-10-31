# -*- coding: utf-8 -*-
r"""P3 F+G 组主实验：CLIP ViT-B/32 上的 **rank sweep × 真实图文 vs blank**。

## 回答哪几条审稿意见

- **R3.14**：把论文里用 blank images 做的 rank transition 用**真实图文对**重跑。
- **R3.13**：blank images 是否"substantially simplify"了跨模态对齐问题？→ 同设置下
  blank 与真实图文的 ΔE、下游 R@1 直接对照。
- **R1.3 / R2.3 / R3.15 / R3.16**：alignment energy 是否与**真实下游任务表现**相关？
  → 每个配置同时报 E（=DG*）与 **Flickr30k 检索 R@1/R@5**。

## 为什么用 CLIP 而不是 LLaVA

`outputs/analysis/llava_bf16_feasibility.json`：LLaVA-1.5-7B 权重 **13.157 GiB**
（bf16），本机 RTX 4060 Laptop 仅 8 GiB → **bf16 不可行**；项目铁律又禁用 4-bit
（同一 4-bit 配置同 seed 重跑，gap span 从 0.304 变到 0.407，不可复现）。
故 LLaVA 规模的复跑在本机**做不到**，见报告 `docs/P3_DOWNSTREAM.md` 的降级建议。

本脚本跑的是 CLIP ViT-B/32——**论文 Γ 结构律的来源模型**（`wan2026gap`）——
在同一个 `E = mean‖z_I − z_T‖²` 定义下做 rank sweep。

## 协议（对齐论文 Setup）

- LoRA 只注入**文本编码器**（`apply_to_vision=False`），视觉编码器**冻结**
  ——与论文 LLaVA 主实验 "vision encoder frozen" 一致；
  `--arms both` 时两侧都注入（项目 Γ 实验常用臂），作为次要对照片。
- `α = 2r`，dropout 0.1，target `q_proj`/`v_proj`，LR 5e-5，AdamW，3 epochs
  （论文 Appendix "Model and Training"）。
- 图像条件 `real` = 真实 jpg；`blank` = 与真实图**同形状的全零张量**
  （对应论文的 336×336 zero arrays，此处为 CLIP 的 224×224）。
- `E` 用 `src` 惯例（`compute_alignment_energy_retrieval`）：归一化嵌入的均方距离。
- 下游指标：Flickr30k 自建 test 1K（`_p430` 清单）上的 **R@1/R@5 i2t 与 t2i**。
  `E_test` 在固定 500 张真实 test 图上测（与训练条件无关，故跨条件可比）。

## 记账

每个 run 的 raw 数值都写进 `outputs/analysis/p3d_clip_ranksweep.json`，
字段见 `runs[]`；`summary` 只由 `runs` 聚合而来，不引入任何手填数字。

## 用法

    python tools\_p461_clip_ranksweep.py --baseline
    python tools\_p461_clip_ranksweep.py --ranks 4,5,6 --conditions real,blank \
        --sizes 16,128,1024 --seeds 42,123,999

编号说明：本脚本原为 `_p431`，因 `task-9` 已占用 `_p430`/`_p431`/`_p432`，
2026-10-12 整体改为 `_p460+`（见 `docs/P3_DOWNSTREAM.md`）。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import torch
import torch.nn.functional as F

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "outputs" / "analysis" / "p3d_clip_ranksweep.json"
MANIFEST = REPO / "outputs" / "analysis" / "p3d_manifest.json"
MODEL_DIR = REPO / "models" / "clip-vit-base-patch32"
DATASET = "flickr30k"

E_EVAL_N = 200       # E_test 固定用前 200 张真实 test 图（与训练条件无关，跨条件可比）
E_TRAIN_N = 256      # E_train 固定用训练子集前 min(n,256) 张（n<256 时取全部）
LR = 5e-5
EPOCHS = 3
BATCH = 32
ALPHA_MULT = 2.0
DROPOUT = 0.1
# 训练相关超参的**规范化快照**：用于"续跑不许改口径"的硬门禁，并逐 run 落盘（自描述）。
TRAIN_SPEC = {"model": "models/clip-vit-base-patch32", "dataset": DATASET,
              "lr": LR, "epochs": EPOCHS, "batch": BATCH, "alpha_mult": ALPHA_MULT,
              "dropout": DROPOUT, "target_modules": ["q_proj", "v_proj"],
              "E_eval_n": E_EVAL_N, "E_train_n_cap": E_TRAIN_N}


def load_manifest():
    return json.loads(io.open(MANIFEST, encoding="utf-8").read())["datasets"][DATASET]


def preprocess_images(paths, proc):
    """一次性把 jpg 解码成张量（fp32 CPU），全部 run 共享。"""
    from PIL import Image
    out = []
    for p in paths:
        with Image.open(p) as im:
            t = proc(images=im.convert("RGB"), return_tensors="pt")["pixel_values"][0]
        out.append(t)
    return torch.stack(out)


def preprocess_texts(texts, tok, max_len=77):
    enc = tok(text=list(texts), return_tensors="pt", padding="max_length",
              truncation=True, max_length=max_len)
    return enc["input_ids"], enc["attention_mask"]


def batch_energy(model, img, ids, am):
    """E = mean‖z_I − z_T‖²（归一化嵌入）。"""
    o = model(pixel_values=img, input_ids=ids, attention_mask=am)
    I = F.normalize(o.image_embeds.float(), p=2, dim=-1)
    T = F.normalize(o.text_embeds.float(), p=2, dim=-1)
    return ((I - T) ** 2).sum(-1).mean()


@torch.no_grad()
def eval_energy(model, img, ids, am, device, bs=64):
    was_training = model.training
    model.eval()
    tot, n = 0.0, 0
    for i in range(0, img.shape[0], bs):
        b = img[i:i + bs].shape[0]
        e = batch_energy(model, img[i:i + bs].to(device), ids[i:i + bs].to(device),
                         am[i:i + bs].to(device))
        tot += float(e) * b
        n += b
    if was_training:
        model.train()
    return tot / max(n, 1)


@torch.no_grad()
def _img_features(model, px):
    """CLIPModel.get_image_features 返回 BaseModelOutputWithPooling，
    pooler_output = visual_projection(vision pooled)（未归一化）。
    注意 CLIPOutput.image_embeds 已被 L2 归一化（见 modeling_clip.forward），
    故此处显式取 pooler_output 再自行归一化，与 E 的定义一致。"""
    out = model.get_image_features(pixel_values=px)
    return out.pooler_output if not torch.is_tensor(out) else out


@torch.no_grad()
def _txt_features(model, ids, am):
    out = model.get_text_features(input_ids=ids, attention_mask=am)
    return out.pooler_output if not torch.is_tensor(out) else out


@torch.no_grad()
def eval_retrieval(model, img, cap_ids, cap_am, device, bs=64):
    """i2t / t2i R@1/R@5。

    img:     (N, 3, H, W)
    cap_ids: (N, C, L)  —— **必须是三维**。若误传 (N*C, L)，C 会被读成 L(=77)，
             整个排序会变成对"词片段"排序，得到一个看似合理但完全错误的 R@1。
             2026-10-12 实测踩过（i2t R@1 0.145 vs 正确值 ~0.85），故此处硬断言。
    """
    assert cap_ids.dim() == 3, f"cap_ids 必须是 (N,C,L)，实得 {tuple(cap_ids.shape)}"
    assert cap_am.dim() == 3 and cap_am.shape == cap_ids.shape, \
        f"cap_am 形状不符 {tuple(cap_am.shape)} vs {tuple(cap_ids.shape)}"
    assert img.shape[0] == cap_ids.shape[0], \
        f"图数 {img.shape[0]} != 描述组数 {cap_ids.shape[0]}"
    was_training = model.training
    model.eval()
    N, C = img.shape[0], cap_ids.shape[1]
    assert C <= 16, f"C={C} 不合常理（应为每图描述条数，如 5）"
    IE = []
    for i in range(0, N, bs):
        o = _img_features(model, img[i:i + bs].to(device))
        IE.append(F.normalize(o.float(), p=2, dim=-1).cpu())
    IE = torch.cat(IE)                                   # (N, D)
    cap_ids_f = cap_ids.reshape(N * C, -1)
    cap_am_f = cap_am.reshape(N * C, -1)
    TE = []
    for i in range(0, cap_ids_f.shape[0], 256):
        o = _txt_features(model, cap_ids_f[i:i + 256].to(device),
                          cap_am_f[i:i + 256].to(device))
        TE.append(F.normalize(o.float(), p=2, dim=-1).cpu())
    TE = torch.cat(TE)                                   # (N*C, D)
    if was_training:
        model.train()

    sim = IE @ TE.T                                      # (N, N*C)
    metrics = {}
    for k in (1, 5):
        topk = sim.topk(k, dim=1).indices
        owner = topk // C
        hit = (owner == torch.arange(N).unsqueeze(1)).any(dim=1).float().mean().item()
        metrics[f"R@{k}_i2t"] = hit
        topkT = sim.T.topk(k, dim=1).indices
        hitT = (topkT == (torch.arange(N * C) // C).unsqueeze(1)).any(dim=1).float().mean().item()
        metrics[f"R@{k}_t2i"] = hitT
        metrics[f"R@{k}"] = (hit + hitT) / 2.0
    return metrics


def build_model(rank, apply_to_vision, seed, device):
    from transformers import CLIPModel, CLIPProcessor
    from src.lora import apply_lora_to_model

    torch.manual_seed(seed)
    model = CLIPModel.from_pretrained(str(MODEL_DIR), local_files_only=True)
    for p in model.parameters():
        p.requires_grad = False
    n_peft = 0
    if rank > 0:
        model, _layers, n_peft = apply_lora_to_model(
            model, rank=rank, alpha=rank * ALPHA_MULT, dropout=DROPOUT,
            target_modules=["q_proj", "v_proj"],
            apply_to_vision=apply_to_vision, apply_to_text=True)
    model = model.to(device).float()
    return model, n_peft


def run_one(rank, condition, n_train, seed, arm, data, device, verbose=True):
    apply_to_vision = (arm == "both")
    t0 = time.time()
    model, n_peft = build_model(rank, apply_to_vision, seed, device)
    model.train()

    if rank > 0:
        tr_img_real = data["train_img"][str(n_train)]
        tr_img = tr_img_real if condition == "real" else torch.zeros_like(tr_img_real)
        tr_ids, tr_am = data["train_txt"][str(n_train)]
        # 能量轨迹用固定子样本（n 大时全量太贵）；训练本身仍用全部 n 条
        k = min(tr_img.shape[0], E_TRAIN_N)
        tr_img, tr_ids, tr_am = tr_img[:k], tr_ids[:k], tr_am[:k]
    te_img, (te_ids, te_am) = data["test_img_e"], data["test_txt_e"]
    ev_img, ev_ids, ev_am = data["test_img"], data["test_cap_ids"], data["test_cap_am"]

    opt = None
    if rank > 0:
        opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)

    E_tr, E_te, losses = [], [], []
    if rank > 0:
        E_tr.append(eval_energy(model, tr_img, tr_ids, tr_am, device))
    E_te.append(eval_energy(model, te_img, te_ids, te_am, device))

    for ep in range(EPOCHS):
        if rank > 0:
            g = torch.Generator().manual_seed(seed * 1000 + ep)
            perm = torch.randperm(tr_img.shape[0], generator=g)
            ep_loss, nb = 0.0, 0
            model.train()
            for i in range(0, tr_img.shape[0], BATCH):
                idx = perm[i:i + BATCH]
                if idx.numel() < 2:
                    continue
                o = model(pixel_values=tr_img[idx].to(device),
                          input_ids=tr_ids[idx].to(device),
                          attention_mask=tr_am[idx].to(device))
                I = F.normalize(o.image_embeds.float(), p=2, dim=-1)
                T = F.normalize(o.text_embeds.float(), p=2, dim=-1)
                logits = model.logit_scale.exp() * I @ T.T
                lab = torch.arange(I.shape[0], device=device)
                loss = (F.cross_entropy(logits, lab) + F.cross_entropy(logits.T, lab)) / 2
                opt.zero_grad(set_to_none=True)
                loss.backward()
                opt.step()
                ep_loss += float(loss); nb += 1
            losses.append(ep_loss / max(nb, 1))
            E_tr.append(eval_energy(model, tr_img, tr_ids, tr_am, device))
        E_te.append(eval_energy(model, te_img, te_ids, te_am, device))

    ret = eval_retrieval(model, ev_img, ev_ids, ev_am, device)
    rec = {
        "rank": rank, "arm": arm, "condition": condition, "n_train": n_train, "seed": seed,
        "n_peft_params": n_peft, "device": str(device),
        # 逐 run 自带超参：这样即使顶层 protocol 将来被重写，旧 run 也不会被误标
        "lr": LR, "epochs": EPOCHS, "batch": BATCH, "alpha_mult": ALPHA_MULT,
        "dropout": DROPOUT, "E_eval_n": E_EVAL_N, "E_train_n_cap": E_TRAIN_N,
        "E_train_epochs": [None if v != v else round(v, 6) for v in E_tr],
        "E_test_epochs": [round(v, 6) for v in E_te],
        "loss_epochs": [round(v, 6) for v in losses],
        "dE_train": (round(E_tr[-1] - E_tr[0], 6) if rank > 0 else None),
        "dE_test": round(E_te[-1] - E_te[0], 6),
        "E_test_0": round(E_te[0], 6), "E_test_final": round(E_te[-1], 6),
        "seconds": round(time.time() - t0, 1),
    }
    rec.update({k: round(v, 6) for k, v in ret.items()})
    if verbose:
        print(f"    r={rank:<3} {arm:<6} {condition:<5} n={n_train:<5} s={seed}: "
              f"dE_test={rec['dE_test']:+.4f} R@1={rec['R@1']:.4f} "
              f"(i2t {rec['R@1_i2t']:.4f} / t2i {rec['R@1_t2i']:.4f}) "
              f"[{rec['seconds']}s]", flush=True)
    del model
    if device == "cuda":
        torch.cuda.empty_cache()
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ranks", default="4,5,6")
    ap.add_argument("--conditions", default="real,blank")
    ap.add_argument("--sizes", default="16,128,1024")
    ap.add_argument("--seeds", default="42,123,999")
    ap.add_argument("--arms", default="text")
    ap.add_argument("--baseline", action="store_true", help="只跑 rank=0 冻结基线")
    ap.add_argument("--device", default=None,
                    help="强制设备（cpu/cuda）。注意 CUDA_VISIBLE_DEVICES='' 在新版 "
                         "CUDA 下等于'未设置'，不保证走 CPU——要 CPU 就显式传 --device cpu")
    ap.add_argument("--fresh", action="store_true", help="丢弃已有 runs 重跑")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    ranks = [int(x) for x in a.ranks.split(",") if x]
    conds = [x for x in a.conditions.split(",") if x]
    sizes = [int(x) for x in a.sizes.split(",") if x]
    seeds = [int(x) for x in a.seeds.split(",") if x]
    arms = [x for x in a.arms.split(",") if x]

    mf = load_manifest()
    imgdir = REPO / DATASET / "flickr30k-images"
    test = mf["test"]
    print(f"=== P3 F+G: CLIP rank sweep ({DATASET}) ===")
    print(f"  test={len(test)} 图 × 5 描述;  ranks={ranks} conds={conds} "
          f"sizes={sizes} seeds={seeds} arms={arms}")
    if a.dry_run:
        print("  (dry-run)")
        return 0

    device = a.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  device={device}", flush=True)

    from transformers import CLIPProcessor
    proc = CLIPProcessor.from_pretrained(str(MODEL_DIR), local_files_only=True)
    tok = proc.tokenizer
    t0 = time.time()
    data = {"train_img": {}, "train_txt": {}}
    for n in sorted(set(sizes)):
        sel = mf["train_sel"][str(n)]
        data["train_img"][str(n)] = preprocess_images(
            [imgdir / s["image"] for s in sel], proc)
        data["train_txt"][str(n)] = preprocess_texts(
            [s["caption"] for s in sel], tok)
    data["test_img"] = preprocess_images([imgdir / s["image"] for s in test], proc)
    n_cap = min(len(test[0]["captions"]), 5)
    ids_c, am_c = preprocess_texts([c for s in test for c in s["captions"][:n_cap]], tok)
    # 关键：(N*C, L) -> (N, C, L)，否则 eval_retrieval 会把 C 读成 L
    data["test_cap_ids"] = ids_c.reshape(len(test), n_cap, -1)
    data["test_cap_am"] = am_c.reshape(len(test), n_cap, -1)
    assert data["test_cap_ids"].shape[:2] == (len(test), n_cap)
    data["test_img_e"] = data["test_img"][:E_EVAL_N]
    data["test_txt_e"] = preprocess_texts([s["captions"][0] for s in test[:E_EVAL_N]], tok)
    print(f"  预处理完成 {time.time()-t0:.1f}s  (test {tuple(data['test_img'].shape)})",
          flush=True)

    runs = []
    stored_spec = None
    if OUT.exists() and not a.fresh:
        try:
            _d = json.loads(io.open(OUT, encoding="utf-8").read())
            runs = _d.get("runs", [])
            stored_spec = _d.get("train_spec")
            print(f"  续跑：已有 {len(runs)} 条 run")
        except Exception:
            runs = []
    # ---- 来源保护（2026-10-13 新增，流程规则：不要把聚合产物当来源）----
    # 归档里的 `protocol` 会被每次调用**重写**；若续跑时训练超参变了，旧 run 会被静默误标。
    # 因此：(a) 每条 run 自带超参；(b) 共有核心键不一致时**硬失败**，不许静默重写。
    # 注意只比对**共有核心键**，不做整体相等——否则旧格式 spec 会把合法续跑也拒掉（实测踩到）。
    _CORE = ("lr", "epochs", "batch", "dropout", "alpha_mult", "target_modules",
             "E_eval_n", "E_train_n_cap")
    if stored_spec is not None:
        _common = [k for k in _CORE if k in stored_spec]
        _mismatch = {k: {"archive": stored_spec[k], "now": TRAIN_SPEC[k]}
                     for k in _common if stored_spec[k] != TRAIN_SPEC[k]}
        if _mismatch:
            raise SystemExit(
                f"!! {OUT.name} 里已有不同的超参 {_mismatch}。\n"
                "   续跑会重写 protocol 使旧 run 被误标 → 拒绝。请用 --fresh 或换输出文件。")
        print(f"  来源校验通过（比对 {len(_common)} 个共有超参键）")
    seen = {(r["rank"], r["arm"], r["condition"], r["n_train"], r["seed"]) for r in runs}

    def save():
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "experiment": "p3d_clip_ranksweep_real_vs_blank",
            "script": "tools/_p461_clip_ranksweep.py",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "dataset": DATASET,
            "manifest": "outputs/analysis/p3d_manifest.json",
            "model": "models/clip-vit-base-patch32",
            "source_of_truth": ("runs[*] —— 只增不改的逐 run 明细；顶层 protocol 只是"
                                "本次调用的说明，派生聚合见 p3d_summary.json"),
            "train_spec": TRAIN_SPEC,
            "protocol": {"lr": LR, "epochs": EPOCHS, "batch": BATCH,
                         "alpha": "2*rank", "dropout": DROPOUT,
                         "target_modules": ["q_proj", "v_proj"],
                         "E_def": "mean||normalize(z_I)-normalize(z_T)||^2 "
                                  "(src/compute_alignment_energy.py:compute_alignment_energy_retrieval)",
                         "E_eval_n": E_EVAL_N, "E_train_n_cap": E_TRAIN_N,
                         "E_train_note": ("energy trajectory measured on a fixed subsample "
                                          "min(n_train,%d) of the training condition's own "
                                          "data; training itself uses all n_train samples"
                                          % E_TRAIN_N),
                         "retrieval": "Flickr30k self-split test 1000 imgs x 5 caps "
                                      "(see p3d_manifest.json)",
                         "blank": "torch.zeros_like(real pixel_values, 224x224)"},
            "runs": runs,
        }, ensure_ascii=False, indent=1))

    todo = []
    if a.baseline:
        todo.append((0, "none", 0, seeds[0], "text"))
    else:
        # 循环次序 arm -> n -> rank -> condition -> seed：
        # 这样被时间截断时，已完成的部分仍是"每个 rank 的 real/blank 配对 × 全部 seed"，
        # 而不是"只有 real 没有 blank"的残表（2026-10-12 因 GPU 吞吐只有 1 run/min 而调整）。
        for arm in arms:
            for n in sizes:
                for r in ranks:
                    for cond in conds:
                        for s in seeds:
                            todo.append((r, cond, n, s, arm))

    t1 = time.time()
    done = 0
    for i, (r, cond, n, s, arm) in enumerate(todo):
        key = (r, arm, cond, n, s)
        if key in seen:
            continue
        print(f"  [{i+1}/{len(todo)}] r={r} arm={arm} cond={cond} n={n} seed={s}", flush=True)
        runs.append(run_one(r, cond, n, s, arm, data, device))
        seen.add(key)
        done += 1
        save()
    print(f"\n  本次新增 {done} 条, 共 {len(runs)} 条 run, 耗时 {time.time()-t1:.0f}s "
          f"→ {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
