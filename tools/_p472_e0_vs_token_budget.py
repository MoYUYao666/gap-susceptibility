# -*- coding: utf-8 -*-
r"""P3 R3.13：**初始化对齐能量 E0 随视觉 token 预算的变化**（真实图 vs 空白图）。

## 为什么需要这个实验（而不是补 54-token 的训练网格）

论文 `paper3/scripts/run_training.py:237` 硬编码 **576 个 image token**
（LLaVA 的 CLIP-ViT-L/14-336 → 24×24=576 patch），blank 图是 `:227` 的 336×336 全零数组。
而我的训练档只有 **15** 与 **54** token —— **两档都远低于论文的操作点**，
所以"在 54 token 下建立新规律"对答复 R3.13 **没有增量价值**（54 ≠ 576）。

**但有一条便宜得多、而且能直达 576 的路**：

    E0 = 初始化时刻的对齐能量，**只需要一次前向，不需要任何训练**

⇒ ① **没有 seed 噪声**（E0 对给定输入是确定性的），因此不受"随机分配 seed 极差上万"那种噪声限制；
   ② 可以在几十分钟内（甚至 CPU 上）把预算扫到**论文的 576**；
   ③ 它直接测量的是本文档 §3.3.2 那条主张的**自变量**：真实图与空白图在**初始化**时差多少。

**关键控制**：blank 图必须与真实图**同尺寸**（`Image.new("RGB", real.size)`），
否则两者经同一个 `max_pixels` 会被缩放到不同 token 数，比较不成立。脚本会打印实测 token 数自证。

    python tools\_p472_e0_vs_token_budget.py --device cpu --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "p3d_e0_vs_token_budget.json"   # main() 里按 split/n 改名
MANIFEST = REPO / "outputs" / "analysis" / "p3d_manifest.json"
MODEL_DIR = REPO / "models" / "Qwen2-VL-2B-Instruct"
ITEM = 151655          # model.config.image_token_id
PAD_ID = 151643

# max_pixels → 期望 token 数 ≈ max_pixels / 784（Qwen2-VL：14×14 patch，2×2 merge → 28×28/ token）
BUDGETS = [16384, 50176, 156800, 451584]     # ≈ 15 / 54 / 200 / 576 token
MIN_PIX_DEFAULT = 4096


def build(proc, img, caption, max_pixels, min_pixels=4096):
    msgs = [{"role": "user",
             "content": [{"type": "image"}, {"type": "text", "text": "Describe this image."}]},
            {"role": "assistant", "content": [{"type": "text", "text": caption}]}]
    prompt = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
    return proc(text=[prompt], images=[img], return_tensors="pt",
                min_pixels=min_pixels, max_pixels=max_pixels)


def energy(model, enc):
    import torch
    kw = {"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]}
    for k in ("pixel_values", "image_grid_thw", "mm_token_type_ids"):
        if enc.get(k) is not None:
            kw[k] = enc[k]
    out = model(**kw, output_hidden_states=True)
    h = out.hidden_states[-1].float()
    ids = enc["input_ids"]
    vis = ids == ITEM
    lang = (~vis) & (ids != PAD_ID) & enc["attention_mask"].bool()
    hv = h[vis].mean(dim=0)
    hl = h[lang].mean(dim=0)
    return float(((hv - hl) ** 2).sum()), int(vis.sum()), int(ids.numel())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--n-samples", type=int, default=4)
    ap.add_argument("--split", default="test", choices=["test", "train_sel"],
                    help="test = 清单 held-out test；train_sel = 与 _p464 训练档**同一批样本**"
                         "（验证 E0 能复现训练归档里的 E_train_epochs[0] 才说明口径一致）")
    ap.add_argument("--budgets", default=",".join(str(b) for b in BUDGETS))
    ap.add_argument("--min-pixels", default=str(MIN_PIX_DEFAULT),
                    help="下采样下限。可以给**逗号分隔的列表**（与 --budgets 一一对应）——"
                         "因为【放大到论文的 576 token】只对高档需要（COCO 图仅 640×427，"
                         "max_pixels 只封顶、不放大）。576 token 需 min_pixels≈451584（=576×28²）")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    import torch
    from PIL import Image
    from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

    budgets = [int(x) for x in a.budgets.split(",") if x]
    minpix = [int(x) for x in str(a.min_pixels).split(",") if x]
    if len(minpix) == 1:
        minpix = minpix * len(budgets)          # 单个值 → 对所有预算生效
    assert len(minpix) == len(budgets), \
        f"--min-pixels 必须与 --budgets 等长（{len(minpix)} vs {len(budgets)}）"
    for mp, npix in zip(budgets, minpix):
        assert npix <= mp, f"min_pixels({npix}) 不能大于 max_pixels({mp})"
    # 归档按 (split, n) 分开：不同样本集的 E0 水平不同（实测 15 token 下 train_sel +3.1%
    # vs test +18.5%），混进一个文件会被误当成同一个总体。
    global OUT
    OUT = OUT.with_name(f"p3d_e0_vs_token_budget_{a.split}_n{a.n_samples}.json")
    mf = json.loads(io.open(MANIFEST, encoding="utf-8").read())["datasets"]["coco"]
    idir = REPO / "coco" / "val2014"
    if a.split == "train_sel":
        recs = mf["train_sel"]["16"][:a.n_samples]
        # 与 _p464 完全同一批：每张取第 1 条描述（_p460 的 train_sel 就是 caption 字段）
        recs = [{"image": s["image"], "captions": [s["caption"]]} for s in recs]
    else:
        recs = mf["test"][:a.n_samples]
    print(f"=== E0 随视觉 token 预算的变化（device={a.device}, split={a.split}, "
          f"n={len(recs)}）===")
    print(f"  论文的操作点：576 image token（run_training.py:237，LLaVA CLIP-ViT-L/14-336）")

    # ---- 设备一致性守卫（2026-10-13）----
    # CPU 与 GPU 的 bf16 E0 差约 0.09%（实测 21771.7 vs 21751.8）。本脚本按 max_pixels
    # **覆盖式合并** rows ⇒ 换设备重跑会让旧行的值被静默替换。因此禁止同一文件混设备。
    _prev_dev = set()
    if OUT.exists():
        try:
            _prev_dev = {r.get("device") for r in
                         json.loads(io.open(OUT, encoding="utf-8").read()).get("rows", [])}
        except Exception:
            _prev_dev = set()
    if _prev_dev and _prev_dev != {a.device}:
        raise SystemExit(
            f"!! {OUT.name} 里已有 device={_prev_dev} 的行，本次为 '{a.device}'。"
            "CPU/GPU 的 E0 差 0.09%，混档会让旧行被静默替换 → 拒绝。请换输出文件。")

    proc = AutoProcessor.from_pretrained(str(MODEL_DIR), local_files_only=True)
    try:
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            str(MODEL_DIR), dtype=torch.bfloat16, local_files_only=True)
    except TypeError:
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            str(MODEL_DIR), torch_dtype=torch.bfloat16, local_files_only=True)
    model = model.to(a.device).eval()

    imgs = []
    for s in recs:
        with Image.open(idir / s["image"]) as im:
            imgs.append(im.convert("RGB").copy())     # copy：脱离 with 后仍可用

    rows = []
    for mp, npix in zip(budgets, minpix):
        t0 = time.time()
        e_real, e_blank, tok_r, tok_b = [], [], [], []
        for im, s in zip(imgs, recs):
            cap = s["captions"][0]
            blank = Image.new("RGB", im.size)          # 同尺寸纯黑 → 同一 max_pixels 下 token 数相同
            with torch.no_grad():
                er, tr, _ = energy(model, build(proc, im, cap, mp, npix).to(a.device))
                eb, tb, _ = energy(model, build(proc, blank, cap, mp, npix).to(a.device))
            e_real.append(er); e_blank.append(eb); tok_r.append(tr); tok_b.append(tb)
        mr = sum(e_real) / len(e_real); mb = sum(e_blank) / len(e_blank)
        row = {"max_pixels": mp, "min_pixels": npix, "device": a.device,
               "tokens_real": tok_r, "tokens_blank": tok_b,
               "mean_tokens": sum(tok_r) / len(tok_r),
               "tokens_match": tok_r == tok_b,
               "E0_real": mr, "E0_blank": mb,
               "gap_pct": 100.0 * (mb - mr) / mr,
               "E0_real_list": e_real, "E0_blank_list": e_blank,
               "seconds": round(time.time() - t0, 1)}
        rows.append(row)
        print(f"  max_pixels={mp:<8} tokens={row['mean_tokens']:>6.1f} "
              f"(real==blank tokens: {row['tokens_match']})  "
              f"E0_real={mr:>10.1f}  E0_blank={mb:>10.1f}  "
              f"gap={row['gap_pct']:>+6.1f}%  [{row['seconds']}s]", flush=True)

    res = {"experiment": "p3d_e0_vs_token_budget",
           "script": "tools/_p472_e0_vs_token_budget.py",
           "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "model": "models/Qwen2-VL-2B-Instruct", "dtype": "bfloat16",
           "device": a.device, "n_samples": len(recs), "split": a.split,
           "data": ("outputs/analysis/p3d_manifest.json datasets.coco."
                    + ("train_sel['16']（与 _p464 训练档同批）" if a.split == "train_sel"
                       else "test（held-out）")),
           "E_def": "mean||mean(h_vis)-mean(h_lang)||^2, last hidden state（与 _p464 同一口径）",
           "no_training": "E0 只需一次前向；对给定输入是确定性的 → 无 seed 噪声",
           "blank_control": "Image.new('RGB', real.size) 同尺寸纯黑，保证两条件 token 数相同",
           "paper_operating_point_tokens": 576,
           "paper_source": "paper3/scripts/run_training.py:237 (img_tokens=576); blank 图见 :227",
           "rows": rows}
    if a.apply:
        prev_rows = []
        if OUT.exists():
            try:
                prev_rows = json.loads(io.open(OUT, encoding="utf-8").read()).get("rows", [])
            except Exception:
                prev_rows = []
        merged = {r["max_pixels"]: r for r in prev_rows}
        for r in rows:                       # 同一 max_pixels 重跑则覆盖
            merged[r["max_pixels"]] = r
        res["rows"] = [merged[k] for k in sorted(merged)]
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(res, ensure_ascii=False, indent=1))
        print(f"\n  ✅ 已写 {OUT.relative_to(REPO)}（{len(res['rows'])} 个预算点）")
    else:
        print("\n（预演；加 --apply 写文件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
