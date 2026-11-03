# -*- coding: utf-8 -*-
r"""实验 ④ 主体：Qwen2-VL-2B 的**严格冻结三臂对照 + 逐 epoch DG\\***（2026-10-08）。

## 要解决什么

`discussion.tex` Limitations 自认本文**只覆盖双塔对比模型**；
摘要称验证跨"five architectures"，而那五个**都是双塔编码器**。
**本实验补这个 scope 缺口。**

## 严格冻结（与 CLIP 侧同标准）

只放开 LoRA 的 A/B，其余全冻；`build()` 里的分塔已由 `tools/_p4_verify_tower_split.py`
**CPU 实测验证**（三臂互不污染）。

## 测量口径（**与论文同量**）

- **`DG*` = 配对均方距离** `(1/N)Σ‖ẑ_I − ẑ_T‖²`（L2 归一化后）——
  与 `src/dg_star_tracker.py:compute` 一致，**与 ODE 的状态变量同量**；
- **`CG` = ‖μ_I − μ_T‖**；
- 嵌入取**最后一层隐状态的均值池化**（两塔各自），再经**固定的随机投影**到 512 维
  （固定 seed、不训练）以便统一维度与可比性。

## 训练

- rank 8 / α=16；lr 1e-4；AdamW；cosine；
- 默认 **1000 样本 × 5 epoch**（8 GB 卡上 2B 模型的可行规模，先冒烟再定）；
- 对比损失：取投影后的**成对余弦对比损失**（InfoNCE，batch 内）。

## 用法

    python tools\_p47_qwen_train.py --smoke        # 极小规模，验证链路
    python tools\_p47_qwen_train.py --apply        # 三臂正式跑
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
MDIR = REPO / "models" / "Qwen2-VL-2B-Instruct"
OUT = REPO / "outputs" / "vlm_strictfreeze"

ARMS = {
    "text_only":   ["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    "vision_only": ["qkv", "proj", "fc1", "fc2"],
    "both":        ["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj",
                    "qkv", "proj", "fc1", "fc2"],
}
RANK, ALPHA = 8, 16
PROJ_DIM = 512


def build(arm: str, device: str, use_4bit: bool):
    """构造模型 + 严格冻结。返回 (model, proc, n_trainable, lora_names)。"""
    import torch
    from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
    from peft import LoraConfig, get_peft_model

    kw = {"device_map": device}
    if use_4bit:
        from transformers import BitsAndBytesConfig
        kw["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True, bnb_4bit_quant_type="nf4")
    else:
        kw["torch_dtype"] = torch.bfloat16
    m = Qwen2VLForConditionalGeneration.from_pretrained(str(MDIR), **kw)
    proc = AutoProcessor.from_pretrained(str(MDIR), trust_remote_code=True)
    m.config.use_cache = False
    m = get_peft_model(m, LoraConfig(r=RANK, lora_alpha=ALPHA, lora_dropout=0.05,
                                     bias="none", target_modules=list(ARMS[arm])))
    lora_names = []
    for n, p in m.named_parameters():
        is_lora = ("lora_A" in n) or ("lora_B" in n)
        p.requires_grad = bool(is_lora)
        if is_lora:
            lora_names.append(n)
    n_tr = sum(p.numel() for p in m.parameters() if p.requires_grad)
    return m, proc, n_tr, lora_names


def precompute_inputs(proc, batches):
    """**一次性**算好全部批次的输入张量 → 消除每批调处理器的瓶颈。

    实测（`tools/_p51_diag_qwen_bf16.py`）：bf16 下 forward+backward 只要 **0.47s（batch 2）**，
    但每批重跑处理器会让 `vision_only` **>27 min 跑不完 1 个 epoch**。
    **瓶颈在数据管线，不在模型。**
    """
    cache = []
    for b in batches:
        content = [[{"type": "image"}, {"type": "text", "text": str(c)}] for c in b["caption"]]
        texts = [proc.apply_chat_template([{"role": "user", "content": c}],
                                         tokenize=False, add_generation_prompt=True)
                 for c in content]
        inp = proc(text=texts, images=[im for im in b["image"]],
                   return_tensors="pt", padding=True)
        cache.append(dict(inp))
    return cache


def pooled_features(model, proc, images, captions, device, proj_i, proj_t, cached=None):
    """返回 (I, T)：两塔最后一层隐状态的均值池化 → 固定投影 → L2 归一化。

    `cached` 非空时**直接用预计算张量**（不再调处理器）——训练循环始终传它。
    """
    import torch
    import torch.nn.functional as F

    if cached is not None:
        inp = {k: (v.to(device) if hasattr(v, "to") else v) for k, v in cached.items()}
        out = model(**inp, output_hidden_states=True)
        hid = out.hidden_states[-1]
        mask = inp["attention_mask"].unsqueeze(-1).to(hid.dtype)
        T = (hid * mask).sum(1) / mask.sum(1).clamp(min=1)
        tok = inp["input_ids"]
        vis_mask = ((tok >= 151652) & (tok <= 151656)).unsqueeze(-1).to(hid.dtype)
        n_vis = vis_mask.sum(1)
        I = (hid * vis_mask).sum(1) / n_vis.clamp(min=1) if float(n_vis.min()) > 0 else T
        return (F.normalize(proj_i(I.float()), p=2, dim=-1),
                F.normalize(proj_t(T.float()), p=2, dim=-1))

    # caption 是**字符串**（数据集给出），故直接构造 Qwen2-VL 的多模态模板。
    content = [[{"type": "image"}, {"type": "text", "text": str(c)}] for c in captions]
    texts = [proc.apply_chat_template([{"role": "user", "content": c}],
                                     tokenize=False, add_generation_prompt=True)
             for c in content]
    inp = proc(text=texts, images=images, return_tensors="pt", padding=True).to(device)
    out = model(**inp, output_hidden_states=True)
    hid = out.hidden_states[-1]                      # (B, L, D_lang)
    grid = None
    if hasattr(out, "image_grid_thw") and out.image_grid_thw is not None:
        grid = out.image_grid_thw
    # 语言侧：对非 padding 位置做均值池化
    mask = inp["attention_mask"].unsqueeze(-1).to(hid.dtype)
    T = (hid * mask).sum(1) / mask.sum(1).clamp(min=1)
    # 视觉侧：取被图像 token 占据的位置（Qwen2-VL 用特殊 id 区间）
    tok = inp["input_ids"]
    vis_mask = ((tok >= 151652) & (tok <= 151656)).unsqueeze(-1).to(hid.dtype)
    n_vis = vis_mask.sum(1)
    if float(n_vis.min()) > 0:
        I = (hid * vis_mask).sum(1) / n_vis.clamp(min=1)
    else:
        I = T                                          # 兜底（不该发生）
    I = F.normalize(proj_i(I.float()), p=2, dim=-1)
    T = F.normalize(proj_t(T.float()), p=2, dim=-1)
    return I, T


def main() -> int:
    argv = sys.argv
    apply = "--apply" in argv
    smoke = "--smoke" in argv
    epochs = 1 if smoke else (int(argv[argv.index("--epochs") + 1]) if "--epochs" in argv else 5)
    maxs = 16 if smoke else (int(argv[argv.index("--maxsamples") + 1])
                             if "--maxsamples" in argv else 1000)
    batch = 2 if smoke else (int(argv[argv.index("--batch") + 1]) if "--batch" in argv else 4)
    use_4bit = "--4bit" in argv
    seed = (int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 42)
    # 独立输出目录（补 seed 时不与归档混写）
    if "--outdir" in argv:
        OUT = REPO / argv[argv.index("--outdir") + 1]
    # **每臂可在独立进程中跑**：同进程内切换臂时，上一个 2B 模型 + CUDA 上下文
    # 无法完全释放 → 累积碎片 → 实测 CUDA error: unknown error（vision_only 崩溃）。
    if smoke:
        arms = ["text_only"]
    elif "--arms" in argv:
        arms = argv[argv.index("--arms") + 1].split(",")
    else:
        arms = list(ARMS)

    if not apply:
        print("=== 实验 ④：Qwen2-VL 严格冻结三臂 + 逐 epoch DG* ===")
        print(f"  模型 {MDIR}（4.13 GB）｜4bit={use_4bit}")
        print(f"  arms={arms} ｜ epochs={epochs} ｜ max_samples={maxs} ｜ batch={batch}")
        print("  （预演；--smoke 极小规模验证链路，--apply 正式跑）")
        return 0

    import torch
    import torch.nn.functional as F
    from src.dataset import create_dataloaders

    OUT.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"=== 实验 ④ 启动（device={device} 4bit={use_4bit}）===", flush=True)

    # **可复现性**：批顺序由 shuffle=True 消费全局 RNG 决定，故 seed 必须在建 loader
    # **之前**设定；否则顺序取决于进程初始 RNG，跨 `python` 调用不可复现（实测：
    # 同 seed 42 同配置，cg_span 复跑 0.3417 vs 归档 0.3056）。见 `--repro-check`。
    torch.manual_seed(seed)
    loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                      batch_size=batch, max_samples=maxs)
    print(f"  数据: {len(loader)} 批 × batch {batch}", flush=True)
    batches = list(loader)

    summary = {}
    for arm in arms:
        print(f"\n  ── {arm} ──", flush=True)
        # 注意：seed 已在建 loader 之前设定（见上）；此处不再重置，
        # 否则会改变批顺序在各臂之间的推进方式。
        t0 = time.time()
        model, proc, n_tr, lora_names = build(arm, device, use_4bit)
        n_vis = sum(1 for n in lora_names if ".visual." in n)
        n_lang = sum(1 for n in lora_names if "language_model" in n)
        print(f"     n_trainable={n_tr:,} ｜ 视觉 {n_vis} ｜ 语言 {n_lang}", flush=True)
        bad = []
        if arm == "text_only" and n_vis:
            bad.append(f"text_only 碰到视觉塔 {n_vis}")
        if arm == "vision_only" and n_lang:
            bad.append(f"vision_only 碰到语言塔 {n_lang}")
        if bad:
            print(f"     ❌ 分塔污染：{'; '.join(bad)} → 中止", flush=True)
            return 1

        # 固定随机投影（不训练、跨臂同 seed → 可比）
        g = torch.Generator().manual_seed(0)
        hid_dim = model.config.text_config.hidden_size
        proj_i = torch.nn.Linear(hid_dim, PROJ_DIM, bias=False).to(device)
        proj_t = torch.nn.Linear(hid_dim, PROJ_DIM, bias=False).to(device)
        with torch.no_grad():
            for L in (proj_i, proj_t):
                L.weight.copy_(torch.randn(PROJ_DIM, hid_dim, generator=g) / hid_dim ** 0.5)
        for L in (proj_i, proj_t):
            L.requires_grad_(False)

        # **预计算输入**（处理器只调一次）→ 训练与评估都复用
        if "_cache" not in dir():
            pass
        _t0 = time.time()
        CACHE = precompute_inputs(proc, batches)
        print(f"     预计算 {len(CACHE)} 批（{time.time()-_t0:.1f}s）", flush=True)

        params = [p for p in model.parameters() if p.requires_grad]
        opt = torch.optim.AdamW(params, lr=1e-4, weight_decay=0.01)
        total = len(batches) * epochs
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(total, 1))

        dg_hist, cg_hist, loss_hist = [], [], []
        for ep in range(1, epochs + 1):
            model.train()
            ep_loss, nb = 0.0, 0
            for bi, b in enumerate(batches):
                imgs = [im for im in b["image"]]
                I, T = pooled_features(model, proc, imgs, b["caption"], device,
                                       proj_i, proj_t, cached=CACHE[bi])
                logits = I @ T.T
                labels = torch.arange(I.shape[0], device=device)
                loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2
                loss.backward()
                torch.nn.utils.clip_grad_norm_(params, 1.0)
                opt.step(); sched.step(); opt.zero_grad()
                ep_loss += float(loss); nb += 1
            # 逐 epoch 测 DG* 与 CG（全数据、no_grad）
            model.eval()
            with torch.no_grad():
                II, TT = [], []
                for _bi, b in enumerate(batches):
                    i_, t_ = pooled_features(model, proc, [im for im in b["image"]],
                                             b["caption"], device, proj_i, proj_t,
                                             cached=CACHE[_bi])
                    II.append(i_); TT.append(t_)
                I = torch.cat(II); T = torch.cat(TT)
                dg = float(((I - T) ** 2).sum(-1).mean())
                cg = float((I.mean(0) - T.mean(0)).norm())
            dg_hist.append(dg); cg_hist.append(cg); loss_hist.append(ep_loss / max(nb, 1))
            print(f"     ep {ep:>2}/{epochs} loss={ep_loss/max(nb,1):.4f} "
                  f"DG*={dg:.4f} CG={cg:.4f}", flush=True)
            if device == "cuda":
                torch.cuda.empty_cache()

        rec = {"arm": arm, "seed": seed, "n_trainable": n_tr, "n_vis": n_vis,
               "n_lang": n_lang,
               "epochs": epochs, "max_samples": maxs, "batch": batch, "4bit": use_4bit,
               "dg_star": dg_hist, "cg": cg_hist, "loss": loss_hist,
               "dg_span": max(dg_hist) - min(dg_hist),
               "cg_span": max(cg_hist) - min(cg_hist),
               "elapsed_sec": round(time.time() - t0, 1)}
        summary[arm] = rec
        p = OUT / f"{arm}_seed{seed}.json"
        io.open(p, "w", encoding="utf-8", newline="").write(
            json.dumps(rec, ensure_ascii=False, indent=1))
        print(f"     ✅ 已写 {p.relative_to(REPO)}（{rec['elapsed_sec']}s，DG* 跨度 {rec['dg_span']:.4f}）",
              flush=True)
        del model
        if device == "cuda":
            torch.cuda.empty_cache()

    io.open(OUT / "summary.json", "w", encoding="utf-8", newline="").write(
        json.dumps(summary, ensure_ascii=False, indent=1))
    print(f"\n  ✅ 三臂完成，汇总 → {(OUT / 'summary.json').relative_to(REPO)}")
    for a, r in summary.items():
        print(f"     {a:<12} DG* 跨度 {r['dg_span']:.4f} ｜ CG 跨度 {r['cg_span']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
