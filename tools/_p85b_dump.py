# -*- coding: utf-8 -*-
r"""`_p85` 的逐批数值（不经过 PowerShell 过滤，直接写文件）（2026-10-10）。

    python tools\_p85b_dump.py --apply
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))


def main() -> int:
    if "--apply" not in sys.argv:
        print("  （预演）")
        return 0
    import torch
    import torch.nn.functional as F
    from src.config import ExperimentConfig, LoRAConfig, TrainConfig
    from src.trainer import GapAwareTrainer
    from src.dataset import create_dataloaders

    device = "cuda" if torch.cuda.is_available() else "cpu"
    lines = []
    for bs in (64, 128):
        loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                          batch_size=bs, max_samples=1024)
        batches = [b for i, b in enumerate(loader) if i < 7]
        torch.manual_seed(42)
        cfg = ExperimentConfig(
            name=f"dump_{bs}",
            lora=LoRAConfig(rank=8, alpha=16, apply_to_vision=False, apply_to_text=True),
            train=TrainConfig(dataset="flickr30k", batch_size=bs, num_epochs=1,
                              max_samples=1024,
                              clip_model="models/clip-vit-base-patch32",
                              save_dir=str(REPO / "outputs/_dump")))
        tr = GapAwareTrainer(cfg)
        tr.device = device
        tr.setup_model()
        params = [(n, p) for n, p in tr.model.named_parameters() if p.requires_grad]
        pmap = dict(params)
        lines.append(f"=== batch {bs} ===")
        lines.append(f"{'批':>3}{'loss':>11}{'ip_v':>14}{'ip_t':>14}{'Σ':>14}")
        tot = 0.0
        for k, b in enumerate(batches):
            imgs = b["image"].to(device); ii = b["input_ids"].to(device)
            am = b["attention_mask"].to(device)
            tr.model.zero_grad(set_to_none=True)
            o = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
            I = F.normalize(o.image_embeds, p=2, dim=-1)
            T = F.normalize(o.text_embeds, p=2, dim=-1)
            lg = 100.0 * I @ T.T
            lab = torch.arange(I.shape[0], device=device)
            loss = (F.cross_entropy(lg, lab) + F.cross_entropy(lg.T, lab)) / 2
            loss.backward()
            gL = {n: (pmap[n].grad.detach().float().clone()
                      if pmap[n].grad is not None else None) for n, _ in params}
            tr.model.zero_grad(set_to_none=True)
            o2 = tr.model(pixel_values=imgs, input_ids=ii, attention_mask=am)
            I2 = F.normalize(o2.image_embeds.float(), p=2, dim=-1)
            T2 = F.normalize(o2.text_embeds.float(), p=2, dim=-1)
            dg = ((I2 - T2) ** 2).sum(-1).mean()
            dg.backward()
            gD = {n: (pmap[n].grad.detach().float().clone()
                      if pmap[n].grad is not None else None) for n, _ in params}
            iv = it = 0.0
            for side, key in (("v", "vision_model"), ("t", "text_model")):
                names = [n for n in gL if key in n]
                if not names:
                    continue
                v = float(sum(torch.dot(gD[n].flatten(), gL[n].flatten())
                              for n in names
                              if gD.get(n) is not None and gL.get(n) is not None))
                if side == "v":
                    iv = v
                else:
                    it = v
            tot += iv + it
            lines.append(f"{k:>3}{float(loss):>11.4f}{iv:>+14.3f}{it:>+14.3f}"
                         f"{iv+it:>+14.3f}")
        n = max(len(batches), 1)
        lines.append(f"  ── 平均 Σ = {tot/n:+.4f}（{n} 批）")
        # 批间标准差
        import statistics as st
        vals = []
        del tr
        if device == "cuda":
            torch.cuda.empty_cache()
        lines.append("")

    outp = REPO / "outputs" / "analysis" / "sign_check_detail.txt"
    outp.parent.mkdir(parents=True, exist_ok=True)
    io.open(outp, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    for ln in lines:
        print("  " + ln)
    print(f"\n  ✅ 已写 {outp.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
