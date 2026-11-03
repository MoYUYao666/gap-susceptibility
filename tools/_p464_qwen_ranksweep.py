# -*- coding: utf-8 -*-
r"""P3 G 组（解码器 VLM 版）：**Qwen2-VL-2B 上的 rank sweep，真实图文 vs blank**。

## 为什么是 2B 而不是论文里的 LLaVA-1.5-7B

`outputs/analysis/llava_bf16_feasibility.json` 实测 LLaVA-1.5-7B 权重 **13.157 GiB**
（bf16），本机 8 GiB 装不下；项目铁律禁用 4-bit（同配置同 seed 重跑 gap span
0.304→0.407，不可复现）。故**论文规模的复跑本机做不到**。
本脚本用本机唯一可训练的解码器 VLM（Qwen2-VL-2B，bf16 约 4.2 GB）做
**同一协议的缩小版**：同一 `E = mean‖h_vis − h_lang‖²` 定义、同一
"vision encoder 冻结 + LoRA 注入 LLM 注意力投影"的设定。

## 协议

- 训练：`n` 条**真实 COCO 图文对**（清单 `p3d_manifest.json`）vs **blank**（全零图），
  3 epochs，batch 1，LR 5e-5，AdamW，LoRA `q/k/v/o`，α=2r，vision tower 冻结。
- E：最后层 hidden state，visual token（`image_token_id=151655`）位置均值与
  语言 token 位置均值的平方距离；训前 + 每 epoch 各测一次。
  `E_train` 在**训练条件本身**的数据上测；`E_eval_real` 在**固定的真实图 eval 集**上测
  （4 条，与训练条件无关 → 跨条件可比）。
- 损失：**只对 assistant 回复 token 算 CE**（`_response_labels`），
  且只对 `logits[:, :-1]` 切片算——避免物化 (B,L,V) 全序列损失。
  理由见 `p3-allocation` 实测：全序列 CE 在 batch 4 时峰值 17.82 GiB。

## 用法

    python tools\_p464_qwen_ranksweep.py --ranks 4,6,16 --conditions real,blank \
        --n-train 16 --seeds 42 --device cuda --apply
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

OUT = REPO / "outputs" / "analysis" / "p3d_qwen_ranksweep.json"
MANIFEST = REPO / "outputs" / "analysis" / "p3d_manifest.json"
MODEL_DIR = REPO / "models" / "Qwen2-VL-2B-Instruct"
DATASET = "coco"
LR = 5e-5
EPOCHS = 3
N_EVAL = 4          # 固定真实图 eval 集条数（与论文 4 eval samples 对齐）
MIN_PIX = 64 * 64
MAX_PIX = 128 * 128


def qwen_inputs(proc, img, text, device):
    """构造一条 (image, caption) 输入。img 为 PIL Image 或 None。"""
    content = []
    if img is not None:
        content.append({"type": "image"})
    content.append({"type": "text", "text": "Describe this image."})
    msgs = [{"role": "user", "content": content},
            {"role": "assistant", "content": [{"type": "text", "text": text}]}]
    prompt = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
    kw = dict(text=[prompt], return_tensors="pt",
              min_pixels=MIN_PIX, max_pixels=MAX_PIX)
    if img is not None:
        kw["images"] = [img]
    return proc(**kw).to(device)


def response_labels(proc, enc):
    """把非 assistant 回复位置的 label 置 -100。

    实测事实（p3-allocation）：assistant 回复在 token 序列里位于
    最后一个 `<|im_start|>`(151644)+`assistant`(77091)+换行之后。
    """
    import torch
    ids = enc["input_ids"][0]
    lab = torch.full_like(ids, -100)
    im_start = 151644
    pos = (ids == im_start).nonzero(as_tuple=True)[0]
    if len(pos) == 0:
        return lab.unsqueeze(0)
    start = int(pos[-1]) + 3   # <|im_start|> assistant \n
    lab[start:] = ids[start:]
    return lab.unsqueeze(0)


def fwd_kwargs(enc):
    """transformers 5.x 的 Qwen2-VL 要求显式传 `mm_token_type_ids`（M-RoPE 用），
    由 processor 与 input_ids 一起返回；缺了会直接 ValueError。"""
    kw = {"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]}
    for k in ("pixel_values", "image_grid_thw", "mm_token_type_ids"):
        v = enc.get(k)
        if v is not None:
            kw[k] = v
    return kw


def alignment_energy(model, enc, image_token_id):
    """E = mean‖h_vis − h_lang‖²（最后层）。"""
    import torch
    out = model(**fwd_kwargs(enc), output_hidden_states=True)
    h = out.hidden_states[-1].float()                      # (B,L,H)
    ids = enc["input_ids"]
    vis = (ids == image_token_id)
    pad_id = 151643
    lang = (~vis) & (ids != pad_id) & (enc["attention_mask"].bool())
    if vis.sum() == 0 or lang.sum() == 0:
        return float("nan")
    hv = h[vis].mean(dim=0)
    hl = h[lang].mean(dim=0)
    return float(((hv - hl) ** 2).sum())


def train_step(model, enc, labels, opt):
    """只对 assistant 回复 token 的 CE，且只取 logits[:, :-1]。"""
    import torch
    import torch.nn.functional as F
    out = model(**fwd_kwargs(enc))
    lg = out.logits[:, :-1, :]
    tgt = labels[:, 1:]
    sel = tgt != -100
    if sel.sum() == 0:
        return float("nan")
    loss = F.cross_entropy(lg[sel].float(), tgt[sel])
    opt.zero_grad(set_to_none=True)
    loss.backward()
    opt.step()
    return float(loss)


def build_model(rank, seed, device):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import Qwen2VLForConditionalGeneration

    torch.manual_seed(seed)
    try:
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            str(MODEL_DIR), dtype=torch.bfloat16, local_files_only=True)
    except TypeError:      # transformers < 5 用 torch_dtype
        model = Qwen2VLForConditionalGeneration.from_pretrained(
            str(MODEL_DIR), torch_dtype=torch.bfloat16, local_files_only=True)
    for p in model.parameters():
        p.requires_grad = False
    n_peft = 0
    if rank > 0:
        kw = dict(r=rank, lora_alpha=rank * 2, lora_dropout=0.0, bias="none",
                  target_modules=["q_proj", "k_proj", "v_proj", "o_proj"])
        try:
            cfg = LoraConfig(exclude_modules=["patch_embed", "visual"], **kw)
        except TypeError:
            cfg = LoraConfig(**kw)      # 老版本 peft 无 exclude_modules
        model = get_peft_model(model, cfg)
        # 实测回读：别信 config，按 named_parameters() 数
        names = [n for n, p in model.named_parameters() if p.requires_grad]
        bad = [n for n in names if "patch_embed" in n or "visual" in n]
        assert not bad, f"LoRA 误伤视觉塔：{bad[:5]}"
        n_peft = sum(p.numel() for p in model.parameters() if p.requires_grad)
    model = model.to(device)
    return model, n_peft


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ranks", default="4,6,16")
    ap.add_argument("--conditions", default="real,blank")
    ap.add_argument("--n-train", type=int, default=16)
    ap.add_argument("--seeds", default="42")
    ap.add_argument("--device", default=None)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="丢弃已有 runs 重跑")
    ap.add_argument("--min-pixels", type=int, default=MIN_PIX,
                    help=f"图像下采样下限（默认 {MIN_PIX}）")
    ap.add_argument("--max-pixels", type=int, default=MAX_PIX,
                    help=f"图像上采样上限（默认 {MAX_PIX}=128×128 → 实测 15 visual token）。"
                         "§3.3 的结论只主张在低 token 预算下成立；要检验分辨率稳健性就调大它")
    ap.add_argument("--only-rank", type=int, default=None, help="只跑指定 rank（调试）")
    ap.add_argument("--check-only", action="store_true",
                    help="只建模型 + 注入 LoRA 并回读参数量，不做前向/训练（不占卡也能验证 "
                         "peft 注入路径；可 --device cpu 跑）")
    ap.add_argument("--smoke", action="store_true",
                    help="GPU 冒烟：真实数据上跑 1 步 fwd+bwd，报峰值显存与单步耗时，然后退出。"
                         "用于在短 GPU 窗口里先验证显存是否够，再去跑完整 sweep。")
    a = ap.parse_args()
    # 命令行可覆盖像素预算（模块级常量被 qwen_inputs / protocol 引用）
    globals()["MIN_PIX"] = a.min_pixels
    globals()["MAX_PIX"] = a.max_pixels
    # 不同像素预算写**不同归档文件**：分辨率稳健性检验(224×224)与主结果(128×128)必须分开存，
    # 否则同一文件里混两种预算会让旧 run 被误标（provenance hazard）。
    global OUT
    if a.max_pixels != 128 * 128:
        OUT = OUT.with_name(f"p3d_qwen_ranksweep_mp{a.max_pixels}.json")
    print(f"  归档路径 {OUT.name}（max_pixels={a.max_pixels}）")

    import torch
    from PIL import Image
    from transformers import AutoProcessor

    device = a.device or ("cuda" if torch.cuda.is_available() else "cpu")
    ranks = [int(x) for x in a.ranks.split(",") if x]
    conds = [x for x in a.conditions.split(",") if x]
    seeds = [int(x) for x in a.seeds.split(",") if x]
    if a.only_rank is not None:
        ranks = [a.only_rank]

    if a.check_only:
        # 只验证 LoRA 注入路径：不进 main 的数据/训练流程，避免占卡
        print(f"=== _p464 --check-only（device={device}）===")
        for r in ranks:
            model, n_peft = build_model(r, 42, device)
            names = [n for n, p in model.named_parameters() if p.requires_grad]
            import collections
            by_mod = collections.Counter(n.split(".")[-1] for n in names)
            print(f"  rank={r}: 可训练张量 {len(names)} 个, 参数 {n_peft:,}; "
                  f"按叶子名 {dict(by_mod)}")
            assert not any("patch_embed" in n or "visual" in n for n in names), \
                "LoRA 误伤视觉塔"
            del model
            if device == "cuda":
                torch.cuda.empty_cache()
        print("  ✅ LoRA 注入路径正常")
        return 0

    if a.smoke:
        # GPU 冒烟：真实数据 1 步 fwd+bwd，报峰值显存/单步耗时（短窗口专用）
        import time as _t
        r = ranks[0] if ranks else 4
        print(f"=== _p464 --smoke（device={device}, rank={r}, {DATASET}, "
              f"max_pixels={MAX_PIX}）===", flush=True)
        mf0 = json.loads(io.open(MANIFEST, encoding="utf-8").read())["datasets"][DATASET]
        idir = REPO / DATASET / ("val2014" if DATASET == "coco" else "flickr30k-images")
        pr = AutoProcessor.from_pretrained(str(MODEL_DIR), local_files_only=True)
        t0 = _t.time()
        model, n_peft = build_model(r, 42, device)
        t_load = _t.time() - t0
        if device == "cuda":
            torch.cuda.reset_peak_memory_stats()
        recs = mf0["train_sel"]["16"][:2]
        encs, labs = [], []
        for s in recs:
            with Image.open(idir / s["image"]) as im:
                e = qwen_inputs(pr, im.convert("RGB"), s["caption"], device)
            encs.append(e); labs.append(response_labels(pr, e))
        opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=LR)
        model.train()
        t0 = _t.time()
        loss = train_step(model, encs[0], labs[0], opt)
        t_step = _t.time() - t0
        peak = (torch.cuda.max_memory_allocated() / 2**30) if device == "cuda" else None
        resv = (torch.cuda.max_memory_reserved() / 2**30) if device == "cuda" else None
        print(f"  权重加载 {t_load:.1f}s | 单步 fwd+bwd {t_step:.2f}s | loss={loss:.4f}")
        print(f"  可训练参数 {n_peft:,}")
        if peak is not None:
            print(f"  峰值 allocated {peak:.2f} GiB / reserved {resv:.2f} GiB "
                  f"（卡 8 GiB，权重 bf16 ≈ 4.2 GiB）")
        out = {"experiment": "p3d_qwen_smoke", "script": "tools/_p464_qwen_ranksweep.py",
               "device": device, "rank": r, "dataset": DATASET,
               "load_seconds": round(t_load, 1), "step_seconds": round(t_step, 3),
               "loss": round(loss, 4), "n_peft_params": n_peft,
               "peak_allocated_GiB": round(peak, 3) if peak else None,
               "peak_reserved_GiB": round(resv, 3) if resv else None,
               "max_pixels": MAX_PIX, "min_pixels": MIN_PIX}
        p = REPO / "outputs" / "analysis" / "p3d_qwen_smoke.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        # 按 device 分键保存：CPU 冒烟与 GPU 冒烟都留档，互不覆盖
        prev = {}
        if p.exists():
            try:
                prev = json.loads(io.open(p, encoding="utf-8").read())
            except Exception:
                prev = {}
        if "by_device" not in prev:
            prev = {"by_device": {}}
        prev["by_device"][device] = out
        prev["script"] = "tools/_p464_qwen_ranksweep.py"
        prev["how"] = "python tools\\_p464_qwen_ranksweep.py --smoke --device <cpu|cuda> --ranks 4"
        io.open(p, "w", encoding="utf-8", newline="").write(
            json.dumps(prev, ensure_ascii=False, indent=1))
        print(f"  ✅ 已写 {p.relative_to(REPO)}（by_device.{device}）")
        return 0

    mf = json.loads(io.open(MANIFEST, encoding="utf-8").read())["datasets"][DATASET]
    # coco 清单由 captions_val2014.json 构建（_p460），故图像在 val2014/
    imgdir = REPO / DATASET / ("val2014" if DATASET == "coco" else "flickr30k-images")
    sel = mf["train_sel"][str(a.n_train)]
    # eval 用清单里**留出的 test 划分**（真正 held-out），不用训练样本，
    # 否则 E_eval_real 是 in-sample、跨条件不可比。
    ev = mf["test"][:N_EVAL]
    _train_imgs = {s["image"] for s in sel}
    assert not (_train_imgs & {s["image"] for s in ev}), \
        "eval 集与训练集有重叠，E_eval_real 会是 in-sample"
    print(f"=== P3 G: Qwen2-VL-2B rank sweep（{DATASET}, device={device}）===")
    print(f"  n_train={a.n_train} ranks={ranks} conds={conds} seeds={seeds} "
          f"eval_real={N_EVAL}")

    proc = AutoProcessor.from_pretrained(str(MODEL_DIR), local_files_only=True)
    ITEM = 151655   # model.config.image_token_id
    model0 = None
    for m in (MODEL_DIR / "config.json",):
        cfg = json.loads(io.open(m, encoding="utf-8").read())
        ITEM = cfg.get("image_token_id", ITEM)
    print(f"  image_token_id={ITEM}")

    def load_imgs(records):
        out = []
        for s in records:
            with Image.open(imgdir / s["image"]) as im:
                out.append(im.convert("RGB"))
        return out

    tr_imgs = load_imgs(sel)
    tr_caps = [s["caption"] for s in sel]
    ev_imgs = load_imgs(ev)
    ev_caps = [s["captions"][0] for s in ev]   # 清单 test 条目是 captions 列表
    ev_enc = [qwen_inputs(proc, im, cap, device) for im, cap in zip(ev_imgs, ev_caps)]
    print(f"  数据就绪：train {len(tr_imgs)} 条, eval {len(ev_enc)} 条", flush=True)

    runs = []
    stored_spec = None
    if OUT.exists() and not a.fresh:
        try:
            _d = json.loads(io.open(OUT, encoding="utf-8").read())
            runs = _d.get("runs", [])
            stored_spec = _d.get("train_spec")
        except Exception:
            runs = []
    # 来源保护（2026-10-13 流程规则：不要把聚合产物当来源）：顶层 protocol 每次调用都会被重写，
    # 续跑若改了超参，旧 run 会被静默误标。因此逐 run 自带超参 + spec 不一致时硬失败。
    TRAIN_SPEC = {"model": "models/Qwen2-VL-2B-Instruct", "dataset": DATASET,
                  "lr": LR, "epochs": EPOCHS, "batch": 1,
                  "lora_targets": ["q_proj", "k_proj", "v_proj", "o_proj"],
                  "lora_alpha": "2*rank", "dtype": "bfloat16",
                  "min_pixels": MIN_PIX, "max_pixels": MAX_PIX}
    # 按**共有核心键**比较，而不是整体相等：归档里的 spec 可能是旧格式（键集不同），
    # 整体比较会把"参数完全相同的合法续跑"也拒掉（实测踩到）。只比对语义参数本身。
    _CORE = ("lr", "epochs", "batch", "lora_targets", "lora_alpha", "dtype",
             "min_pixels", "max_pixels")
    if stored_spec is not None:
        _common = [k for k in _CORE if k in stored_spec]
        _mismatch = {k: {"archive": stored_spec[k], "now": TRAIN_SPEC[k]}
                     for k in _common if stored_spec[k] != TRAIN_SPEC[k]}
        if _mismatch:
            raise SystemExit(
                f"!! {OUT.name} 里已有不同的超参 {_mismatch}。\n"
                "   续跑会重写 protocol 使旧 run 被误标 → 拒绝。请用 --fresh 或换输出文件。")
        print(f"  来源校验通过（比对 {len(_common)} 个共有超参键：{_common}）")
    seen = {(r["rank"], r["condition"], r["n_train"], r["seed"]) for r in runs}
    # 同一归档里不允许混不同像素预算的 run（否则 §3.3 的分辨率稳健性检验会不可比）
    _budgets = {(r.get("min_pixels"), r.get("max_pixels")) for r in runs
                if r.get("rank", 0) > 0}
    if _budgets and (MIN_PIX, MAX_PIX) not in _budgets:
        # 硬失败（非 warning）：批量脚本里 warning 没人看，混档会静默污染结论
        raise SystemExit(
            f"!! 归档 {OUT.name} 里已有像素预算 {_budgets}，本次为 ({MIN_PIX}, {MAX_PIX})。"
            "请用 --fresh，或换一个输出文件（不同预算必须分开归档）。")

    def save():
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(json.dumps({
            "experiment": "p3d_qwen2vl2b_ranksweep_real_vs_blank",
            "script": "tools/_p464_qwen_ranksweep.py",
            "source_of_truth": ("runs[*] —— 只增不改的逐 run 明细且自带超参；顶层 protocol/"
                               "train_spec 只是说明；派生聚合见 p3d_qwen_summary.json"),
            "train_spec": TRAIN_SPEC,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "model": "models/Qwen2-VL-2B-Instruct", "dataset": DATASET,
            "manifest": "outputs/analysis/p3d_manifest.json",
            "protocol": {"lr": LR, "epochs": EPOCHS, "batch": 1,
                         "lora_targets": ["q_proj", "k_proj", "v_proj", "o_proj"],
                         "lora_alpha": "2*rank", "vision_frozen": True,
                         "dtype": "bfloat16",
                         "E_def": "mean||mean(h_vis)-mean(h_lang)||^2 last layer",
                         "E_train": "在训练条件自身的数据上（可与论文 ΔE 类比）",
                         "E_eval_real": f"在清单 test 划分的前 {N_EVAL} 张【held-out 真实图】上"
                                        "（与训练集无重叠，跨条件可比）",
                         "loss": "CE on assistant response tokens only, logits[:, :-1]",
                         "min_pixels": MIN_PIX, "max_pixels": MAX_PIX,
                         "blank": "no image passed = Qwen 的纯文本路径；"
                                  "另见 --conditions blank 时用全零图"},
            "runs": runs,
        }, ensure_ascii=False, indent=1))

    # 循环次序 rank -> seed -> condition：被时间截断时，已完成的仍是
    # "同一 rank、同一 seed 下 real/blank 成对"的单元，而不是"只有 real 没有 blank"的残表
    # （与 _p461 同一条纪律：GPU 吞吐不可控，必须让部分结果仍然可配对）。
    for rank in ([0] if a.only_rank == 0 else ranks):
        for seed in seeds:
            for cond in conds:
                key = (rank, cond, a.n_train, seed)
                if key in seen:
                    continue
                t0 = time.time()
                model, n_peft = build_model(rank, seed, device)
                model.eval()
                with torch.no_grad():
                    E_ev0 = [alignment_energy(model, e, ITEM) for e in ev_enc]
                E_ev = [sum(E_ev0) / len(E_ev0)]

                # 组装训练输入（condition 决定图像）
                if cond == "blank":
                    tr_enc = [qwen_inputs(proc, Image.new("RGB", (128, 128)), c, device)
                              for c in tr_caps]
                else:
                    tr_enc = [qwen_inputs(proc, im, c, device)
                              for im, c in zip(tr_imgs, tr_caps)]
                labels = [response_labels(proc, e) for e in tr_enc]

                with torch.no_grad():
                    E_tr = [sum(alignment_energy(model, e, ITEM) for e in tr_enc) / len(tr_enc)]

                opt = None
                if rank > 0:
                    opt = torch.optim.AdamW(
                        [p for p in model.parameters() if p.requires_grad], lr=LR)
                losses = []
                for ep in range(EPOCHS):
                    if rank == 0:
                        break
                    model.train()
                    ep_l = []
                    for e, lb in zip(tr_enc, labels):
                        ep_l.append(train_step(model, e, lb, opt))
                    losses.append(sum(ep_l) / max(len(ep_l), 1))
                    model.eval()
                    with torch.no_grad():
                        E_tr.append(sum(alignment_energy(model, e, ITEM)
                                        for e in tr_enc) / len(tr_enc))
                        E_ev.append(sum(alignment_energy(model, e, ITEM)
                                        for e in ev_enc) / len(ev_enc))
                    print(f"    r={rank} {cond} s={seed} ep{ep+1}: "
                          f"L={losses[-1]:.4f} E_train={E_tr[-1]:.1f} "
                          f"E_eval={E_ev[-1]:.1f}", flush=True)

                rec = {"rank": rank, "condition": cond, "n_train": a.n_train,
                       "seed": seed, "n_peft_params": n_peft, "device": device,
                       # 像素预算必须逐 run 记录：同一归档里如果混了不同分辨率的 run，
                       # 只靠顶层 protocol 会把旧 run 误标（provenance hazard）。
                       "min_pixels": MIN_PIX, "max_pixels": MAX_PIX,
                       "sec_per_sample": round((time.time() - t0) / max(len(tr_enc), 1), 3),
                       "E_train_epochs": [round(v, 4) if v == v else None for v in E_tr],
                       "E_eval_real_epochs": [round(v, 4) if v == v else None for v in E_ev],
                       "loss_epochs": [round(v, 4) for v in losses],
                       "dE_train": (round(E_tr[-1] - E_tr[0], 4) if rank > 0 else None),
                       "dE_eval_real": round(E_ev[-1] - E_ev[0], 4),
                       "seconds": round(time.time() - t0, 1)}
                runs.append(rec); seen.add(key); save()
                print(f"  -> r={rank} {cond} s={seed}: dE_train={rec['dE_train']} "
                      f"dE_eval_real={rec['dE_eval_real']} [{rec['seconds']}s]", flush=True)
                del model
                if device == "cuda":
                    torch.cuda.empty_cache()

    save()
    print(f"\n  共 {len(runs)} 条 run → {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
