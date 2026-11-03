# -*- coding: utf-8 -*-
r"""**优先级 3**：BioCLIP 严格冻结对照——位置效应是"架构"还是"数据/目标"驱动？（2026-10-05）

## 为什么做

已测三个骨干：CLIP ViT-B/32（WIT）、OpenCLIP ViT-B/32（LAION-2B）、SigLIP ViT-B/16。
**位置效应按骨干分组**（CLIP/OpenCLIP → text-only 更降；SigLIP → both 更降）。

**但"骨干"这个变量混了几件事**：架构、预训练数据、训练目标（softmax vs sigmoid）。
本实验加一个**第四个点**：**BioCLIP**（OpenCLIP ViT-B/16，**生物域**数据），
它同时是**新的架构（B/16）+ 新的预训练域**。

## 加载（已实测）

`models/oceanclip-0.15b/bioclip/`：`open_clip_config.json` + `open_clip_pytorch_model.bin`。
**`open_clip_torch` 3.3.0 已装**，`create_model_and_transforms('ViT-B-16', pretrained=None, **model_cfg)`
后 `load_state_dict` **缺失 0 / 多余 0**（302 键全匹配）——**无需格式转换**。

## 协议（与三骨干对照一致）

严格冻结（仅 LoRA A/B 可训）｜ rank 4 与 8，$\alpha = 2r$ ｜ 5000 样本 ｜ 10 epochs ｜
batch 128 ｜ 3 seeds ｜ InfoNCE（双向 CE 平均）

## 臂

`text_only` / `both` / `vision_only`

## 通过判据（先写明）

- **位置排序**：与哪一组的骨干一致？（CLIP/OpenCLIP → `text_only` 的 ΔCG 更小；SigLIP → `both` 更小）
- **rank 方向**：r4 → r8 的 ΔCG 是降还是升？

    python tools\_exp3_bioclip_strict.py [--apply]
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.chdir(REPO)
sys.path.insert(0, str(REPO))

BIO = REPO / "models" / "oceanclip-0.15b" / "bioclip"
OUT = REPO / "outputs" / "strict_freeze_bioclip"
RANKS = [4, 8]
SEEDS = [42, 123, 456]
MAX_SAMPLES, EPOCHS, BATCH = 5000, 10, 128
ARMS = ("text_only", "both", "vision_only")


def inject_lora_bioclip(model, rank: int, alpha: int, apply_vision: bool, apply_text: bool,
                        target=("qkv", "c_fc", "c_proj", "q_proj", "k_proj", "v_proj", "out_proj")):
    """把 OpenCLIP 的 Linear 换成 LoRA 版；返回 (lora_layers, n_trainable)。

    先全冻，再把指定侧的 LoRA 矩阵设为可训。
    """
    # torch / nn 必须在**模块层可用**：它们是模块级函数与嵌套类的依赖，
    # 只在 main() 里 import 会 NameError（首次实跑即因此失败）。
    import torch as _torch
    import torch.nn as nn

    class LoRALinear(nn.Module):
        def __init__(self, base: nn.Linear, r: int, a: int):
            super().__init__()
            self.base = base
            for p in self.base.parameters():
                p.requires_grad = False
            self.lora_A = nn.Parameter(_torch.zeros(base.in_features, r))
            self.lora_B = nn.Parameter(_torch.zeros(r, base.out_features))
            nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
            self.scaling = a / r

        # OpenCLIP 内部会直接访问 .weight（如 fused attention），故代理到 base，
        # 否则报 AttributeError: 'LoRA' object has no attribute 'weight'（冒烟测试抓到）。
        @property
        def weight(self):
            return self.base.weight

        @property
        def bias(self):
            return getattr(self.base, "bias", None)

        def forward(self, x):
            return self.base(x) + (x @ self.lora_A @ self.lora_B) * self.scaling

    for p in model.parameters():
        p.requires_grad = False

    layers = {}
    for name, mod in list(model.named_modules()):
        # 实测：OpenCLIP 的文本塔名为 	ransformer（不是 	ext），视觉塔为 isual。
        # 先前按 	ext 判断 -> 文本层 0 命中，冒烟测试抓到。
        is_vis = name.startswith("visual")
        is_txt = name.startswith("transformer") or "text_" in name
        if not ((is_vis and apply_vision) or (is_txt and apply_text)):
            continue
        if not isinstance(mod, nn.Linear):
            continue
        if not any(t in name for t in target):
            continue
        parent = model
        parts = name.split(".")
        for pp in parts[:-1]:
            parent = getattr(parent, pp)
        setattr(parent, parts[-1], LoRALinear(mod, rank, alpha))
        layers[name] = getattr(parent, parts[-1])

    n = 0
    for w in layers.values():
        w.lora_A.requires_grad = True
        w.lora_B.requires_grad = True
        n += w.lora_A.numel() + w.lora_B.numel()
    return layers, n


def main() -> int:
    apply = "--apply" in sys.argv
    print("=== 优先级 3：BioCLIP 严格冻结对照 ===")
    print(f"  模型  : BioCLIP ViT-B/16（生物域预训练）")
    print(f"  协议  : 严格冻结 ｜ rank {RANKS} ｜ alpha=2r ｜ {MAX_SAMPLES} 样本 ｜ {EPOCHS} epochs")
    print(f"  臂    : {ARMS} ｜ seeds {SEEDS} ｜ batch {BATCH}")
    if not apply:
        print("\n  （预演；加 --apply 实跑，需 GPU 约 1–2 小时）")
        return 0

    import statistics as st

    import open_clip
    import torch
    import torch.nn.functional as F

    sys.path.insert(0, str(REPO / "src"))
    from dataset import create_dataloaders  # type: ignore

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    cfg = json.loads((BIO / "open_clip_config.json").read_text(encoding="utf-8"))
    tokenizer = open_clip.get_tokenizer("ViT-B-16")
    sd_path = BIO / "open_clip_pytorch_model.bin"

    loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                      batch_size=BATCH, max_samples=MAX_SAMPLES)

    records = []
    for rank in RANKS:
        for arm in ARMS:
            for seed in SEEDS:
                torch.manual_seed(seed)
                model, _, _ = open_clip.create_model_and_transforms(
                    "ViT-B-16", pretrained=None, **cfg["model_cfg"])
                state = torch.load(sd_path, map_location="cpu", weights_only=False)
                if hasattr(state, "state_dict"):
                    state = state.state_dict()
                miss, unexp = model.load_state_dict(state, strict=False)
                assert not miss and not unexp, f"权重不匹配：缺 {len(miss)} 多 {len(unexp)}"

                # 顺序很重要：**先注入 LoRA、再 .to(dev)**。
                # 反过来（先前写法）会让 lora_A/B 建在 CPU 上，
                # 首步即报 `RuntimeError: Expected all tensors to be on the same device`
                # ——首次实跑因此失败。
                layers, n_tr = inject_lora_bioclip(
                    model, rank, rank * 2,
                    apply_vision=arm in ("both", "vision_only"),
                    apply_text=arm in ("text_only", "both"))
                assert n_tr > 0, f"{arm}: 无可训参数（LoRA 未命中任何层）"
                model = model.to(dev).train()
                # 二次确认：所有可训参数确实在目标设备上
                for p in model.parameters():
                    if p.requires_grad:
                        assert p.device.type == dev.split(":")[0], \
                            f"{arm}: 可训参数不在 {dev}（{p.device}）"
                print(f"  r{rank} {arm:<12} seed={seed:<5} LoRA 层 {len(layers)} ｜ 可训 {n_tr}", flush=True)

                opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                                        lr=1e-4)
                first = last = None
                for ep in range(EPOCHS):
                    for b in loader:
                        imgs = b["image"].to(dev)
                        toks = tokenizer(b["caption"]).to(dev)
                        ie = F.normalize(model.encode_image(imgs), dim=-1)
                        te = F.normalize(model.encode_text(toks), dim=-1)
                        ls = model.logit_scale.exp()
                        lg = ls * ie @ te.t()
                        lb = torch.arange(lg.shape[0], device=dev)
                        loss = (F.cross_entropy(lg, lb) + F.cross_entropy(lg.t(), lb)) / 2.0
                        opt.zero_grad(set_to_none=True)
                        loss.backward()
                        opt.step()
                        with torch.no_grad():
                            cgi = float(((ie - te) ** 2).sum(-1).mean())
                            if first is None:
                                first = cgi
                            last = cgi
                dcg = last - first
                records.append(dict(rank=rank, arm=arm, seed=seed, n_lora_layers=len(layers),
                                    n_trainable=n_tr, initial_cg=first, final_cg=last, delta_cg=dcg))
                print(f"      → ΔCG={dcg:+.4f}（{first:.4f} → {last:.4f}）", flush=True)

    print("\n=== 结果 ===")
    summary = {}
    for rank in RANKS:
        for arm in ARMS:
            vs = [r["delta_cg"] for r in records if r["rank"] == rank and r["arm"] == arm]
            if vs:
                summary[f"r{rank}_{arm}"] = dict(mean=round(st.mean(vs), 4),
                                                 sd=round(st.stdev(vs), 4) if len(vs) > 1 else 0.0,
                                                 n=len(vs))
                print(f"  r{rank} {arm:<12} ΔCG={st.mean(vs):+.4f} ± "
                      f"{(st.stdev(vs) if len(vs) > 1 else 0):.4f}  (n={len(vs)})")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(
        {"model": "BioCLIP ViT-B/16 (models/oceanclip-0.15b/bioclip)",
         "protocol": {"max_samples": MAX_SAMPLES, "epochs": EPOCHS, "batch": BATCH,
                      "ranks": RANKS, "alpha_mult": 2, "seeds": SEEDS},
         "summary": summary, "records": records}, indent=2), encoding="utf-8")
    print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}/results.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
