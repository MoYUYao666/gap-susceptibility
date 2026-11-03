# -*- coding: utf-8 -*-
r"""PR R1.3 / R2.4 / R3.3 —— 与参数尺度匹配的相对扰动实验（纯评测，无训练）。

## 审稿人原话（Pattern Recognition，三位审稿人一致）

    "applying the same absolute noise to both encoders does not imply the same relative
     perturbation, because their weight scales, parameter distributions, layer
     architectures, and numbers of parameters may differ"

要求：① 层级归一化扰动（控制 ‖ΔW‖_F/‖W‖_F）② 多个噪声级 ③ 两塔匹配相对扰动预算 ④ 多种子。

## 本脚本做什么

对**冻结的** `openai/clip-vit-base-patch32` 分别给 vision / text 塔加权重噪声，
在**同一批固定图像与固定文本**上测 R@1（i→t、t→i）、R@5、CG、DG（`src.gap_metrics.GapTracker`）。
四种协议，全部在同一评测集上：

| key | 协议 | 每张量扰动 | 是否跨塔匹配相对预算 |
|---|---|---|---|
| `rel_layer`  | 层级归一化（本文新增，对应审稿人要求①③） | `‖ΔW_i‖_F = r·‖W_i‖_F`，方向各向同性 | **是**：逐张量与塔级都恰好 = r |
| `rel_uniform`| 塔预算均摊（对照：预算相同但层级分配不同） | `‖ΔW_i‖_F = r·‖W_inj‖_F/√n` | **是**：塔级恰好 = r |
| `abs_std`    | **现论文/归档协议**（`paper/scripts/noise_sensitivity.py:inject_noise_to_encoder`，按原路径 import 以保证一致） | `ΔW_i = σ·std(W_i)·randn` | 否（需实测） |
| `abs_raw`    | 字面意义的"同一绝对噪声" | `ΔW_i = σ·randn`，两塔共用同一 σ | 否（需实测） |

`abs_raw` 的 σ 由视觉塔注入集 RMS 标定：σ = r · rms(W_vision,injected)，
故其视觉塔塔级相对扰动 ≈ r，可与 `rel_layer` 的 r 对照。

## 为什么这样能回答审稿人

- 塔级相对扰动定义（分子恒为注入集 Frobenius 范数）：

      rel_injected = ‖ΔW_inj‖_F / ‖W_inj‖_F           （仅被注入张量）
      rel_encoder  = ‖ΔW_inj‖_F / ‖W_encoder‖_F       （含 embedding/layernorm）
      rel_all      = ‖ΔW_inj‖_F / ‖W_encoder+proj‖_F  （再含 visual/text_projection）

  `rel_layer`/`rel_uniform` 的 `rel_injected` **恒等于 r**（脚本内断言），
  而 `abs_std`/`abs_raw` 的两塔 `rel_injected` 实测不同 —— 第③条要求的数据就在这里。

- 每层实际相对扰动（`by_layer`、`by_kind`、逐张量 `expected_rel_at_unit_sigma = std/‖W‖_F`）
  给出"同一 σ ≠ 同一相对扰动"的定量证据。

- 脆弱性倍率 = 同 r 下 vision drop% / text drop%（逐 seed 配对），
  以及"达到同一下降所需的相对预算比 r_text/r_vision"（对数插值）。

## 纪律

- 单进程、串行；模型只加载一次；每个条件前后 `state_dict` 逐张量 bit-exact 还原并断言（无泄漏）。
- `level = 0` 为控制条件：必须**逐位复现** baseline（脚本内断言，失败即 abort）。
- 数据：`flickr30k/flickr30k.json` 第 400–1399 张图（capion#0），确定性预处理；
  图像张量一次性预处理好并算 sha1，所有条件共用同一份张量（无数据增强抖动）。
- 每个条件失败自动重试 2 次；失败的写进 JSON 的 `errors`，不得静默丢弃。
- 每 8 个条件把 partial 结果落盘（`meta.status = "partial"`）；跑完写 `"complete"`。
  报告只允许引用 `status == "complete"` 的输出。

    python tools\_p255_relative_perturbation.py --apply            # 全量
    python tools\_p255_relative_perturbation.py --apply --pilot    # 冒烟（256 图 1 seed）
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
from transformers import CLIPModel, CLIPProcessor  # noqa: E402

from src.gap_metrics import GapTracker  # noqa: E402

MODEL_ID = "openai/clip-vit-base-patch32"
ANNOT = REPO / "flickr30k" / "flickr30k.json"
IMAGE_DIR = REPO / "flickr30k" / "flickr30k-images"
ARCHIVE_NOISE_SCRIPT = REPO / "paper" / "scripts" / "noise_sensitivity.py"
OUT = REPO / "outputs" / "analysis" / "pr_relative_perturbation.json"

IMG_FROM, IMG_TO = 400, 1400          # 1000 unique images, deterministic slice
CAPTION_IDX = 0
BATCH_IMG, BATCH_TXT = 64, 256
# The first five seeds are the seed set of outputs/noise_fixed_aug.json (the archived
# equal-sigma probe); five more are added so the heavy-tailed text-tower response is sampled
# well enough to report a stable sd.
SEEDS_DEFAULT = "42,123,456,789,1024,2048,4096,8192,16384,32768"
REL_LEVELS = [0.0, 0.01, 0.03, 0.06, 0.1, 0.2, 0.3, 1.0]
ABS_STD_LEVELS = [0.0, 0.01, 0.03, 0.06, 0.1, 0.2, 0.3]
ABS_RAW_RS = [0.03, 0.06, 0.1, 0.3]   # sigma = r * rms(vision injected tensors)
REL_UNIFORM_LEVELS = [0.0, 0.01, 0.02, 0.03, 0.05]
MATCHED_DROP_TARGETS = [5.0, 10.0, 20.0]
SKIP_IF_IN_NAME = ("layernorm", "embedding")   # exact rule of the archived injector
REQUIRE_IN_NAME = "encoder.layers"             # exact rule of the archived injector
N_INJECTED_EXPECTED = 192                      # 12 layers x 16 tensors, both towers

T0 = time.time()


def log(msg: str) -> None:
    print("  [%7.1fs] %s" % (time.time() - T0, msg), flush=True)


def sha1_file(path: Path) -> str | None:
    if not Path(path).exists():
        return None
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def sha1_bytes(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def load_archive_injector():
    """Import the archived injector by path so the protocol is byte-for-byte the paper's."""
    spec = importlib.util.spec_from_file_location("arch_noise_mod", str(ARCHIVE_NOISE_SCRIPT))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def injected_names(encoder) -> list[str]:
    """The archived rule, applied to named_parameters() order (RNG order matters)."""
    out = []
    for name, _p in encoder.named_parameters():
        low = name.lower()
        if any(s in low for s in SKIP_IF_IN_NAME):
            continue
        if REQUIRE_IN_NAME not in name:
            continue
        out.append(name)
    return out


def layer_index(name: str) -> int | None:
    m = re.search(r"encoder\.layers\.(\d+)\.", name)
    return int(m.group(1)) if m else None


def tensor_kind(name: str) -> str:
    parts = name.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else name


def frob(p: torch.Tensor) -> float:
    return float(p.detach().float().norm())


def summarise(vals) -> dict:
    a = np.asarray([v for v in vals if v is not None], dtype=float)
    if a.size == 0:
        return {"n": 0}
    return {"n": int(a.size), "mean": float(a.mean()),
            "sd": (None if a.size < 2 else float(a.std(ddof=1))),
            "median": float(np.median(a)),
            "min": float(a.min()), "max": float(a.max())}


# --------------------------------------------------------------------------- model helpers

@torch.no_grad()
def encode_images(model, pixels: torch.Tensor) -> torch.Tensor:
    feats = []
    for i in range(0, pixels.shape[0], BATCH_IMG):
        v = model.vision_model(pixel_values=pixels[i:i + BATCH_IMG])
        vp = v[1] if isinstance(v, tuple) else v.pooler_output
        feats.append(F.normalize(model.visual_projection(vp), dim=-1))
    return torch.cat(feats)


@torch.no_grad()
def encode_text(model, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    feats = []
    for i in range(0, input_ids.shape[0], BATCH_TXT):
        t = model.text_model(input_ids=input_ids[i:i + BATCH_TXT],
                             attention_mask=attention_mask[i:i + BATCH_TXT])
        p = t[1] if isinstance(t, tuple) else t.pooler_output
        feats.append(F.normalize(model.text_projection(p), dim=-1))
    return torch.cat(feats)


def retrieval_metrics(img: torch.Tensor, txt: torch.Tensor, ks=(1, 5, 10)) -> dict:
    S = (img @ txt.T).float()
    n = S.shape[0]
    ar = torch.arange(n, device=S.device)
    out = {}
    for k in ks:
        i2t = S.topk(k, dim=1).indices
        t2i = S.T.topk(k, dim=1).indices
        out["R@%d_i2t" % k] = float((i2t == ar[:, None]).any(1).float().mean())
        out["R@%d_t2i" % k] = float((t2i == ar[:, None]).any(1).float().mean())
    return out


def gap_metrics(img: torch.Tensor, txt: torch.Tensor) -> dict:
    gt = GapTracker(sample_size=10 ** 9, device=str(img.device))
    m = gt.compute(img, txt, epoch=0, step=0)
    return {"CG": float(m.centroid_gap), "DG": float(m.distribution_gap),
            "mean_cosine_pos": float(m.mean_cosine_pos),
            "cosine_separation": float(m.cosine_separation)}


def restore_and_verify(model, orig: dict) -> None:
    sd = model.state_dict()
    with torch.no_grad():
        for k, v in orig.items():
            sd[k].copy_(v)
    bad = [k for k, v in orig.items() if not torch.equal(sd[k], v)]
    assert not bad, "state_dict restore is not bit-exact for %s" % bad[:5]


# --------------------------------------------------------------------------- protocols

def apply_rel_layer(params, names, r, tower_norm) -> tuple[dict, float]:
    """Per-tensor ||dW_i||_F = r * ||W_i||_F. Tower level rel_injected == r exactly."""
    realized, dsum = {}, 0.0
    with torch.no_grad():
        for n in names:
            p = params[n]
            wn = frob(p)
            g = torch.randn_like(p)
            gn = float(g.norm())
            d = (r * wn / gn) * g
            p.add_(d)
            realized[n] = float(d.norm()) / wn if wn > 0 else None
            dsum += float(d.norm()) ** 2
    return realized, float(np.sqrt(dsum))


def apply_rel_uniform(params, names, r, tower_norm) -> tuple[dict, float]:
    """Tower budget r spread uniformly over the n injected tensors: every ||dW_i||_F equal."""
    share = r * tower_norm / np.sqrt(len(names))
    realized, dsum = {}, 0.0
    with torch.no_grad():
        for n in names:
            p = params[n]
            wn = frob(p)
            g = torch.randn_like(p)
            gn = float(g.norm())
            d = (share / gn) * g
            p.add_(d)
            realized[n] = float(d.norm()) / wn if wn > 0 else None
            dsum += float(d.norm()) ** 2
    return realized, float(np.sqrt(dsum))


def apply_abs_raw(params, names, sigma) -> tuple[dict, float]:
    """Literal equal-absolute: the same sigma for every tensor of both towers."""
    realized, dsum = {}, 0.0
    with torch.no_grad():
        for n in names:
            p = params[n]
            wn = frob(p)
            g = torch.randn_like(p)
            d = sigma * g
            p.add_(d)
            realized[n] = float(d.norm()) / wn if wn > 0 else None
            dsum += float(d.norm()) ** 2
    return realized, float(np.sqrt(dsum))


def apply_abs_std(model, arch_mod, encoder_attr, names, params, sigma
                  ) -> tuple[dict, float, int]:
    """The archived protocol, executed by the archived function itself."""
    before = {n: params[n].detach().clone() for n in names}
    n_inj = arch_mod.inject_noise_to_encoder(model, encoder_attr, sigma)
    realized, dsum = {}, 0.0
    for n in names:
        d = params[n].detach() - before[n]
        wn = float(before[n].float().norm())
        realized[n] = float(d.float().norm()) / wn if wn > 0 else None
        dsum += float(d.float().norm()) ** 2
    return realized, float(np.sqrt(dsum)), int(n_inj)


def rel_by_layer(realized: dict) -> dict:
    """Mean realized relative perturbation per transformer layer index."""
    acc = {}
    for n, v in realized.items():
        li = layer_index(n)
        if li is None:
            continue
        acc.setdefault(li, []).append(v)
    return {str(k): {"mean": float(np.mean(v)), "n_tensors": len(v)}
            for k, v in sorted(acc.items())}


def rel_by_block(realized: dict, per_tensor_geom: dict) -> dict:
    """Realized ||dW_block||_F/||W_block||_F for each transformer block (all 16 tensors)."""
    num, den = {}, {}
    for n, v in realized.items():
        li = layer_index(n)
        if li is None:
            continue
        wn = per_tensor_geom[n]["frob"]
        num[li] = num.get(li, 0.0) + (v * wn) ** 2
        den[li] = den.get(li, 0.0) + wn ** 2
    return {str(k): float(np.sqrt(num[k] / den[k])) for k in sorted(den)}


# --------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="run (otherwise print the plan)")
    ap.add_argument("--pilot", action="store_true", help="smoke test: 256 images, 1 seed, 1 level")
    ap.add_argument("--seeds", default=SEEDS_DEFAULT)
    ap.add_argument("--protocols", default="rel_layer,rel_uniform,abs_std,abs_raw")
    ap.add_argument("--resume", action="store_true",
                    help="reuse every condition already recorded in --out (same config) and "
                         "run only the missing ones; use after a CUDA-context crash")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    protocols = [p.strip() for p in args.protocols.split(",") if p.strip()]
    img_to = IMG_FROM + 256 if args.pilot else IMG_TO
    levels = {
        "rel_layer": REL_LEVELS,
        "rel_uniform": REL_UNIFORM_LEVELS,
        "abs_std": ABS_STD_LEVELS,
        "abs_raw": ABS_RAW_RS,   # placeholder: replaced by the sigma grid after weight stats
    }

    # ------------------------------------------------------------------ data
    if not ANNOT.exists():
        print("missing %s" % ANNOT)
        return 1
    items = json.load(io.open(ANNOT, encoding="utf-8"))
    slice_items = items[IMG_FROM:img_to]
    captions = [it["captions"][CAPTION_IDX] for it in slice_items]
    files = [it["image"] for it in slice_items]
    missing = [f for f in files if not (IMAGE_DIR / f).exists()]
    assert not missing, "missing %d image files, e.g. %s" % (len(missing), missing[:3])

    from PIL import Image
    pil = [Image.open(IMAGE_DIR / f).convert("RGB") for f in files]
    processor = CLIPProcessor.from_pretrained(MODEL_ID, local_files_only=True)
    pix = processor(images=pil, return_tensors="pt")["pixel_values"]
    pix_sha1 = sha1_bytes(pix.numpy().tobytes())
    tok = processor(text=captions, return_tensors="pt", padding=True, truncation=True, max_length=77)
    log("data: %d images (flickr30k.json items %d..%d, caption #%d), pixel sha1=%s"
        % (len(pil), IMG_FROM, img_to - 1, CAPTION_IDX, pix_sha1[:16]))

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        log("WARNING: CUDA not available, running on CPU")
    pixels = pix.to(device)
    input_ids = tok["input_ids"].to(device)
    attention_mask = tok["attention_mask"].to(device)

    # ------------------------------------------------------------------ model (loaded exactly once)
    arch = load_archive_injector()
    model = CLIPModel.from_pretrained(MODEL_ID, local_files_only=True)
    model.eval().to(device)
    orig = {k: v.detach().clone() for k, v in model.state_dict().items()}
    params = {"vision": dict(model.vision_model.named_parameters()),
              "text": dict(model.text_model.named_parameters())}
    names = {"vision": injected_names(model.vision_model),
             "text": injected_names(model.text_model)}
    for tw in ("vision", "text"):
        assert len(names[tw]) == N_INJECTED_EXPECTED, \
            "%s: %d injected tensors, expected %d" % (tw, len(names[tw]), N_INJECTED_EXPECTED)
    log("model ready: %s on %s; injected tensors vision=%d text=%d"
        % (MODEL_ID, device, len(names["vision"]), len(names["text"])))

    # ------------------------------------------------------------------ weight geometry
    geometry = {}
    for tw in ("vision", "text"):
        enc = getattr(model, tw + "_model")
        per_tensor = {}
        for n, p in enc.named_parameters():
            w = p.detach().float()
            per_tensor[n] = {
                "shape": list(p.shape), "numel": int(p.numel()),
                "frob": float(w.norm()),
                "rms": float(w.pow(2).mean().sqrt()),
                "mean": float(w.mean()),
                "std_unbiased": float(w.std()),
                "injected": n in names[tw],
            }
        inj = [per_tensor[n] for n in names[tw]]
        other = [v for k, v in per_tensor.items() if not v["injected"]]
        proj = getattr(model, "visual_projection" if tw == "vision" else "text_projection").weight
        proj_frob = float(proj.detach().float().norm())
        frob_inj = float(np.sqrt(sum(v["frob"] ** 2 for v in inj)))
        frob_other = float(np.sqrt(sum(v["frob"] ** 2 for v in other)))
        frob_all = float(np.sqrt(frob_inj ** 2 + frob_other ** 2 + proj_frob ** 2))
        by_layer, by_kind = {}, {}
        for n in names[tw]:
            v = per_tensor[n]
            by_layer.setdefault(layer_index(n), []).append(v)
            by_kind.setdefault(tensor_kind(n), []).append(v)
        geometry[tw] = {
            "n_injected_tensors": len(names[tw]),
            "n_injected_params": int(sum(v["numel"] for v in inj)),
            "n_total_params": int(sum(v["numel"] for v in per_tensor.values())),
            "frob_injected": frob_inj, "frob_encoder_other": frob_other,
            "frob_projection": proj_frob, "frob_all_with_projection": frob_all,
            "rms_injected": float(np.sqrt(sum(v["rms"] ** 2 * v["numel"] for v in inj)
                                          / sum(v["numel"] for v in inj))),
            # expected tower-level relative perturbation of the ARCHIVED protocol at sigma = 1
            # (E||dW||_F^2 = sigma^2 * sum_i std_i^2 * numel_i; mean_tensor_std uses ddof=1 like
            # torch.std() inside the archived injector)
            "expected_rel_at_unit_sigma_injected": float(
                np.sqrt(sum(v["std_unbiased"] ** 2 * v["numel"] for v in inj)) / frob_inj),
            "injected_share_of_encoder_frob": frob_inj / float(
                np.sqrt(frob_inj ** 2 + frob_other ** 2)),
            "injected_share_of_all_frob": frob_inj / frob_all,
            "by_layer": {str(k): {
                "n_tensors": len(v), "n_params": int(sum(x["numel"] for x in v)),
                "frob": float(np.sqrt(sum(x["frob"] ** 2 for x in v))),
                "expected_rel_at_unit_sigma": float(
                    np.sqrt(sum(x["std_unbiased"] ** 2 * x["numel"] for x in v))
                    / np.sqrt(sum(x["frob"] ** 2 for x in v))),
                "mean_tensor_std": float(np.mean([x["std_unbiased"] for x in v])),
                "mean_tensor_frob": float(np.mean([x["frob"] for x in v])),
            } for k, v in sorted(by_layer.items())},
            "by_kind": {k: {
                "n_tensors": len(v), "n_params": int(sum(x["numel"] for x in v)),
                "frob": float(np.sqrt(sum(x["frob"] ** 2 for x in v))),
                "mean_rms": float(np.mean([x["rms"] for x in v])),
                "mean_abs_mean": float(np.mean([abs(x["mean"]) for x in v])),
                "mean_std": float(np.mean([x["std_unbiased"] for x in v])),
                "expected_rel_at_unit_sigma": float(
                    np.sqrt(sum(x["std_unbiased"] ** 2 * x["numel"] for x in v))
                    / np.sqrt(sum(x["frob"] ** 2 for x in v))),
            } for k, v in sorted(by_kind.items())},
            "per_tensor": per_tensor,
        }
        log("%s: injected params=%d (%.1f%% of tower), frob_inj=%.4f frob_all=%.4f rms=%.5f"
            % (tw, geometry[tw]["n_injected_params"],
               100.0 * geometry[tw]["n_injected_params"] / geometry[tw]["n_total_params"],
               frob_inj, frob_all, geometry[tw]["rms_injected"]))

    # abs_raw sigma grid: r * rms(vision injected tensors)
    rms_v = geometry["vision"]["rms_injected"]
    abs_raw_sigmas = [r * rms_v for r in ABS_RAW_RS]
    levels["abs_raw"] = abs_raw_sigmas
    if args.pilot:
        seeds = seeds[:1]
        levels = {k: [0.0, v[-1]] for k, v in levels.items()}
    log("levels: " + "; ".join("%s=%s" % (k, ["%.5g" % x for x in v])
                               for k, v in levels.items()))

    # ------------------------------------------------------------------ baseline
    with torch.no_grad():
        base_img = encode_images(model, pixels)
        base_txt = encode_text(model, input_ids, attention_mask)
    baseline = {"R1": retrieval_metrics(base_img, base_txt), **gap_metrics(base_img, base_txt)}
    log("baseline: R@1(i2t)=%.4f R@1(t2i)=%.4f CG=%.4f DG=%.4f"
        % (baseline["R1"]["R@1_i2t"], baseline["R1"]["R@1_t2i"], baseline["CG"], baseline["DG"]))

    # ------------------------------------------------------------------ conditions
    conditions = []
    for proto in protocols:
        for lv in levels[proto]:
            if lv == 0.0:
                conditions.append((proto, "vision", 0.0, seeds[0]))
                conditions.append((proto, "text", 0.0, seeds[0]))
            else:
                for tw in ("vision", "text"):
                    for sd in seeds:
                        conditions.append((proto, tw, lv, sd))
    log("plan: %d conditions (%d seeds, protocols=%s)"
        % (len(conditions), len(seeds), ",".join(protocols)))
    if not args.apply:
        print("  (dry run; add --apply)")
        return 0

    rows, errors = [], []
    injector_set_verified = None
    t_start = time.time()

    # ---- resume: reuse every condition already recorded in the output file ---------------
    done = {}
    if args.resume and Path(args.out).exists():
        try:
            prev = json.load(io.open(args.out, encoding="utf-8"))
            same_cfg = (prev["meta"]["seeds"] == seeds
                        and {k: prev["meta"]["levels"][k] for k in protocols}
                        == {k: levels[k] for k in protocols}
                        and prev["meta"]["data"]["pixel_tensor_sha1"] == pix_sha1
                        and prev["meta"]["status"] == "partial")
            if same_cfg:
                for r in prev["rows"]:
                    if "error" not in r:
                        done[(r["protocol"], r["tower"], r["level"], r["seed"])] = r
                errors.extend(prev.get("errors", []))
                injector_set_verified = prev["meta"]["archive_injector"][
                    "function_verified_to_touch_exactly_the_expected_set"]
                log("resume: %d conditions already done in %s" % (len(done), args.out))
            else:
                log("resume ignored: the existing output has a different configuration")
        except Exception as e:  # noqa: BLE001
            log("resume ignored (%s: %s)" % (type(e).__name__, str(e)[:120]))
    todo = [c for c in conditions if c not in done]
    rows.extend(done.values())
    log("to run: %d of %d conditions" % (len(todo), len(conditions)))

    for ci, (proto, tw, lv, sd) in enumerate(todo, 1):
        row = {"protocol": proto, "tower": tw, "level": lv, "seed": sd}
        last_err = None
        for attempt in (1, 2, 3):
            try:
                restore_and_verify(model, orig)
                torch.manual_seed(sd)
                np.random.seed(sd)
                enc_attr = tw + "_model"
                tn = geometry[tw]["frob_injected"]
                if proto == "rel_layer":
                    realized, dsum = apply_rel_layer(params[tw], names[tw], lv, tn)
                    n_inj = len(names[tw])
                elif proto == "rel_uniform":
                    realized, dsum = apply_rel_uniform(params[tw], names[tw], lv, tn)
                    n_inj = len(names[tw])
                elif proto == "abs_raw":
                    realized, dsum = apply_abs_raw(params[tw], names[tw], lv)
                    n_inj = len(names[tw])
                elif proto == "abs_std":
                    realized, dsum, n_inj = apply_abs_std(model, arch, enc_attr, names[tw],
                                                          params[tw], lv)
                    if injector_set_verified is None and lv > 0:
                        changed = {k for k in orig
                                   if not torch.equal(model.state_dict()[k], orig[k])}
                        expect = {enc_attr + "." + n for n in names[tw]}
                        injector_set_verified = bool(changed == expect) and n_inj == len(names[tw])
                        assert injector_set_verified, (
                            "archived injector touched an unexpected set: "
                            "%d changed vs %d expected" % (len(changed), len(expect)))
                else:
                    raise ValueError("unknown protocol %s" % proto)

                with torch.no_grad():
                    img = encode_images(model, pixels)
                    txt = encode_text(model, input_ids, attention_mask)
                r1 = retrieval_metrics(img, txt)
                gm = gap_metrics(img, txt)
                row.update({
                    "n_injected_tensors": n_inj,
                    "dW_frob_total": dsum,
                    "rel_injected": dsum / geometry[tw]["frob_injected"],
                    "rel_encoder": dsum / float(np.sqrt(geometry[tw]["frob_injected"] ** 2
                                                        + geometry[tw]["frob_encoder_other"] ** 2)),
                    "rel_all": dsum / geometry[tw]["frob_all_with_projection"],
                    "rel_realized_stats": summarise(list(realized.values())),
                    "rel_realized_max_abs_dev_from_target":
                        (None if proto not in ("rel_layer",) or lv == 0 else
                         max(abs(v - lv) for v in realized.values())),
                    "rel_realized_by_layer": rel_by_layer(realized),
                    "rel_realized_by_block": rel_by_block(realized,
                                                          geometry[tw]["per_tensor"]),
                    "R1": r1, "CG": gm["CG"], "DG": gm["DG"],
                    "mean_cosine_pos": gm["mean_cosine_pos"],
                    "drop_pct_i2t": 100.0 * (baseline["R1"]["R@1_i2t"] - r1["R@1_i2t"])
                                    / baseline["R1"]["R@1_i2t"],
                    "drop_pct_t2i": 100.0 * (baseline["R1"]["R@1_t2i"] - r1["R@1_t2i"])
                                    / baseline["R1"]["R@1_t2i"],
                    "dCG": gm["CG"] - baseline["CG"],
                    "dDG": gm["DG"] - baseline["DG"],
                })
                if proto == "rel_layer" and lv > 0:
                    assert row["rel_realized_max_abs_dev_from_target"] < 1e-4, \
                        "rel_layer realized != target: %s" % row["rel_realized_max_abs_dev_from_target"]
                if lv == 0.0:
                    assert abs(r1["R@1_i2t"] - baseline["R1"]["R@1_i2t"]) < 1e-12, \
                        "sigma=0 control does not reproduce the baseline"
                    assert abs(gm["CG"] - baseline["CG"]) < 1e-12
                rows.append(row)
                last_err = None
                break
            except Exception as e:  # noqa: BLE001
                last_err = "%s: %s" % (type(e).__name__, str(e)[:300])
                log("RETRY %d/3 %s/%s/level=%.5g/seed=%d -> %s"
                    % (attempt, proto, tw, lv, sd, last_err))
                cuda_broken = "CUDA" in last_err or "Accelerator" in last_err
                try:
                    torch.cuda.empty_cache()
                except Exception:  # noqa: BLE001
                    cuda_broken = True
                if cuda_broken:
                    # A lost CUDA context cannot be recovered inside this process. Dump what we
                    # have and let the caller re-run with --resume.
                    log("CUDA context lost -> dumping partial results and aborting")
                    rows.append({**row, "error": last_err})
                    errors.append({"protocol": proto, "tower": tw, "level": lv, "seed": sd,
                                   "error": last_err})
                    dump(args.out, "partial", rows, errors, geometry, baseline, seeds, levels,
                         protocols, pix_sha1, img_to, injector_set_verified)
                    return 3
        else:
            errors.append({"protocol": proto, "tower": tw, "level": lv, "seed": sd,
                           "error": last_err})
            rows.append({**row, "error": last_err})

        if ci % 8 == 0 or ci == len(todo):
            log("%d/%d done (%.1f min elapsed, %d errors)"
                % (ci, len(conditions), (time.time() - t_start) / 60, len(errors)))
            dump(args.out, "partial", rows, errors, geometry, baseline, seeds, levels,
                 protocols, pix_sha1, img_to, injector_set_verified)

    # ------------------------------------------------------------------ restore + final write
    try:
        restore_and_verify(model, orig)
        log("weights restored bit-exactly; total %.1f min" % ((time.time() - t_start) / 60))
    except Exception as e:  # noqa: BLE001
        log("WARNING: final restore check failed (%s: %s); the last condition is discarded"
            % (type(e).__name__, str(e)[:120]))
        errors.append({"protocol": "final", "tower": "-", "level": 0.0, "seed": 0,
                       "error": "final restore check failed: %s" % str(e)[:200]})

    payload = dump(args.out, "complete", rows, errors, geometry, baseline, seeds, levels,
                   protocols, pix_sha1, img_to, injector_set_verified)
    print("\n== summary ==")
    for proto in protocols:
        for lv in levels[proto]:
            if lv == 0.0:
                continue
            vv = [r for r in rows if r["protocol"] == proto and r["tower"] == "vision"
                  and r["level"] == lv and "error" not in r]
            tt = [r for r in rows if r["protocol"] == proto and r["tower"] == "text"
                  and r["level"] == lv and "error" not in r]
            if not vv or not tt:
                continue
            dv = np.mean([r["drop_pct_i2t"] for r in vv])
            dt = np.mean([r["drop_pct_i2t"] for r in tt])
            rv = np.mean([r["rel_injected"] for r in vv])
            rt = np.mean([r["rel_injected"] for r in tt])
            print("  %-12s level=%-8.5g dropV=%+6.2f%% dropT=%+6.2f%% ratio=%s  "
                  "relV=%.4f relT=%.4f (V/T=%.3f)"
                  % (proto, lv, dv, dt, ("%.2f" % (dv / dt)) if abs(dt) > 1e-9 else "n/a",
                     rv, rt, rv / rt if rt else float("nan")))
    print("\nwrote %s (%s, %d rows, %d errors)"
          % (args.out, payload["meta"]["status"], len(rows), len(errors)))
    return 0


def dump(out_path, status, rows, errors, geometry, baseline, seeds, levels, protocols,
         pix_sha1, img_to, injector_verified) -> dict:
    payload = {
        "meta": {
            "script": "tools/_p255_relative_perturbation.py",
            "script_sha1": sha1_file(Path(__file__)),
            "purpose": "PR R1.3/R2.4/R3.3 -- matched *relative* weight perturbation vs the "
                       "archived equal-sigma protocol, to test whether Vision is still more "
                       "fragile once ||dW||_F/||W||_F is matched across the two towers",
            "status": status,
            "model": MODEL_ID,
            "archive_injector": {
                "path": str(ARCHIVE_NOISE_SCRIPT.relative_to(REPO)),
                "sha1": sha1_file(ARCHIVE_NOISE_SCRIPT),
                "rule": "for encoder.layers tensors only; skip names containing 'layernorm' or "
                        "'embedding' (the archived skip test is case-insensitive substring, so "
                        "'layer_norm1' is NOT skipped); noise = randn_like(p) * sigma * p.std()",
                "function_verified_to_touch_exactly_the_expected_set": injector_verified,
            },
            "data": {
                "annotation": str(ANNOT.relative_to(REPO)), "annotation_sha1": sha1_file(ANNOT),
                "image_dir": str(IMAGE_DIR.relative_to(REPO)),
                "slice": "flickr30k.json items [%d, %d), caption index %d" % (IMG_FROM, img_to,
                                                                             CAPTION_IDX),
                "n_images": img_to - IMG_FROM,
                "pixel_tensor_sha1": pix_sha1,
                "preprocess": "CLIPProcessor (openai/clip-vit-base-patch32) image processor, "
                              "batch-precomputed once and reused byte-identically by every "
                              "condition; no random augmentation anywhere in this script",
                "text": "raw caption #0 of each image, CLIPProcessor padding=True truncation=True "
                        "max_length=77",
            },
            "metrics": {
                "retrieval": "R@k i2t/t2i over the full %d-sample evaluation set "
                             "(src.gap_metrics / this script)" % (img_to - IMG_FROM),
                "CG_DG": "src/gap_metrics.py::GapTracker.compute -- CG = ||mu_I-mu_T||_2, "
                         "DG = sqrt(CG^2 + ||sigma_I-sigma_T||^2), sigma = per-dimension std",
            },
            "protocols": {
                "rel_layer": "||dW_i||_F = r * ||W_i||_F per injected tensor (isotropic direction)",
                "rel_uniform": "||dW_i||_F = r * ||W_inj||_F / sqrt(n) for every injected tensor",
                "abs_std": "archived injector: dW_i = sigma * std(W_i) * randn",
                "abs_raw": "dW_i = sigma * randn, sigma = r * rms(vision injected tensors); "
                           "the same sigma for every tensor of both towers",
            },
            "levels": {k: [float(x) for x in v] for k, v in levels.items()},
            "seeds": seeds,
            "seed_design": "each condition is run with torch.manual_seed(seed) immediately before "
                           "the noise draw, and every protocol draws one randn_like per injected "
                           "tensor in the same order; therefore a given seed = one fixed tensor-"
                           "wise random DIRECTION, reused at every level and in every protocol "
                           "(only the per-tensor scaling differs). Level-to-level and protocol-to-"
                           "protocol comparisons for a given seed are therefore paired by "
                           "direction, and the seed-to-seed spread measures direction sensitivity.",
            "protocols_run": protocols,
            "relative_perturbation_definitions": {
                "rel_injected": "||dW_inj||_F / ||W_inj||_F (injected tensors only)",
                "rel_encoder": "||dW_inj||_F / ||W_encoder||_F (encoder incl. embedding/layernorm)",
                "rel_all": "||dW_inj||_F / ||W_encoder+projection||_F",
            },
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "torch": torch.__version__,
            "allow_tf32_matmul": bool(torch.backends.cuda.matmul.allow_tf32),
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_s": round(time.time() - T0, 1),
        },
        "weight_geometry": geometry,
        "baseline": {"R1": baseline["R1"], "CG": baseline["CG"], "DG": baseline["DG"],
                     "mean_cosine_pos": baseline["mean_cosine_pos"]},
        "rows": rows,
        "errors": errors,
    }
    payload["analysis"] = analyse(payload)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(out_path, "w", encoding="utf-8", newline="") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    return payload


# --------------------------------------------------------------------------- analysis

def _curve(rows, proto, tower, seed, key="drop_pct_i2t"):
    pts = sorted((r["level"], r[key]) for r in rows
                 if r["protocol"] == proto and r["tower"] == tower and r["seed"] == seed
                 and "error" not in r and r["level"] > 0)
    return pts


def _interp_level(pts, target):
    """log-x linear-y interpolation of drop(target); None if not bracketed."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= 0 or x1 <= 0:
            continue
        if (y0 - target) * (y1 - target) <= 0 and y1 != y0:
            f = (target - y0) / (y1 - y0)
            return float(np.exp(np.log(x0) + f * (np.log(x1) - np.log(x0))))
    return None


def analyse(payload) -> dict:
    rows = [r for r in payload["rows"] if "error" not in r]
    seeds = payload["meta"]["seeds"]
    protocols = payload["meta"]["protocols_run"]
    levels = payload["meta"]["levels"]
    out = {"per_level": {}, "headline": {}, "definition": {
        "drop_pct_i2t": "100 * (R@1_i2t_baseline - R@1_i2t_condition) / R@1_i2t_baseline",
        "ratio_of_drops": "mean drop of the vision tower / mean drop of the text tower at the "
                          "same perturbation level (positive = vision more degraded)",
        "paired_ratio": "per-seed vision drop / text drop at the same level; pooled mean/sd over "
                        "seeds and over levels with mean drop >= 1% in both towers",
        "matched_drop_budget_ratio": "relative budget r (or sigma for abs_*) needed to reach a "
                                     "given R@1 drop, per seed, by log-x linear-y interpolation "
                                     "over the level grid; ratio = text / vision",
        "pooled_ratio_levels": "pools over (seed, level) pairs: all_levels = everything; "
                               "levels_ge_1pct_both = both tower drops >= 1%; "
                               "levels_nonsaturated = both >= 1% and both <= 90% -- the headline "
                               "rule, which excludes the saturated R@1 floor where any ratio "
                               "collapses towards 1",
    }}
    for proto in protocols:
        out["per_level"][proto] = {}
        for lv in levels[proto]:
            if lv == 0.0:
                continue
            v = [r for r in rows if r["protocol"] == proto and r["tower"] == "vision"
                 and r["level"] == lv and r["seed"] in seeds]
            t = [r for r in rows if r["protocol"] == proto and r["tower"] == "text"
                 and r["level"] == lv and r["seed"] in seeds]
            if not v or not t:
                continue
            vm = {s: r for s, r in zip([r["seed"] for r in v], v)}
            tm = {s: r for s, r in zip([r["seed"] for r in t], t)}
            common = sorted(set(vm) & set(tm))
            dv = [vm[s]["drop_pct_i2t"] for s in common]
            dt = [tm[s]["drop_pct_i2t"] for s in common]
            paired = [a / b for a, b in zip(dv, dt) if abs(b) > 1e-9]
            out["per_level"][proto][repr(lv)] = {
                "level": lv,
                "vision_drop_i2t": summarise(dv),
                "text_drop_i2t": summarise(dt),
                "vision_drop_t2i": summarise([vm[s]["drop_pct_t2i"] for s in common]),
                "text_drop_t2i": summarise([tm[s]["drop_pct_t2i"] for s in common]),
                "ratio_of_means": (float(np.mean(dv) / np.mean(dt)) if abs(np.mean(dt)) > 1e-9
                                   else None),
                "paired_ratio_mean": (float(np.mean(paired)) if paired else None),
                "paired_ratio_sd": (float(np.std(paired, ddof=1)) if len(paired) > 1 else None),
                "paired_diff_mean": float(np.mean(np.subtract(dv, dt))),
                "paired_diff_sd": (float(np.std(np.subtract(dv, dt), ddof=1))
                                   if len(common) > 1 else None),
                "n_seeds_vision_gt_text": int(sum(1 for a, b in zip(dv, dt) if a > b)),
                "n_seeds": len(common),
                "n_seeds_vision_drop_gt_50pct": int(sum(1 for a in dv if a > 50)),
                "n_seeds_text_drop_gt_50pct": int(sum(1 for a in dt if a > 50)),
                "vision_rel_injected": summarise([vm[s]["rel_injected"] for s in common]),
                "text_rel_injected": summarise([tm[s]["rel_injected"] for s in common]),
                "rel_injected_ratio_vision_over_text": float(
                    np.mean([vm[s]["rel_injected"] for s in common])
                    / np.mean([tm[s]["rel_injected"] for s in common])),
                "vision_CG": summarise([vm[s]["CG"] for s in common]),
                "text_CG": summarise([tm[s]["CG"] for s in common]),
                "vision_DG": summarise([vm[s]["DG"] for s in common]),
                "text_DG": summarise([tm[s]["DG"] for s in common]),
            }

    # pooled matched-relative ratio (levels where both towers drop >= 1%)
    for proto in protocols:
        pools = {"all_levels": [], "levels_ge_1pct_both": [], "levels_nonsaturated": []}
        used = []
        for lv in levels[proto]:
            if lv == 0.0:
                continue
            pl = out["per_level"][proto].get(repr(lv))
            if not pl:
                continue
            v = [r for r in rows if r["protocol"] == proto and r["tower"] == "vision"
                 and r["level"] == lv]
            t = [r for r in rows if r["protocol"] == proto and r["tower"] == "text"
                 and r["level"] == lv]
            vm = {r["seed"]: r for r in v}
            tm = {r["seed"]: r for r in t}
            nonsat = (min(pl["vision_drop_i2t"]["mean"], pl["text_drop_i2t"]["mean"]) >= 1.0
                      and max(pl["vision_drop_i2t"]["mean"], pl["text_drop_i2t"]["mean"]) <= 90.0)
            for s in sorted(set(vm) & set(tm)):
                a, b = vm[s]["drop_pct_i2t"], tm[s]["drop_pct_i2t"]
                if abs(b) > 1e-9:
                    pools["all_levels"].append(a / b)
                    if min(a, b) >= 1.0:
                        pools["levels_ge_1pct_both"].append(a / b)
                    if nonsat:
                        pools["levels_nonsaturated"].append(a / b)
            if nonsat:
                used.append(lv)
        head = {}
        for k, pool in pools.items():
            if pool:
                logs = np.log(np.abs(pool)) if np.all(np.asarray(pool) > 0) else None
                head[k] = {
                    "n_pairs": len(pool),
                    "ratio_mean": float(np.mean(pool)),
                    "ratio_sd": (float(np.std(pool, ddof=1)) if len(pool) > 1 else None),
                    "ratio_median": float(np.median(pool)),
                    "geometric_mean": (float(np.exp(logs.mean())) if logs is not None else None),
                    "geometric_sd_factor": (float(np.exp(logs.std(ddof=1)))
                                            if logs is not None and len(pool) > 1 else None),
                    "n_ratio_gt_1": int(sum(1 for x in pool if x > 1)),
                }
        # matched-drop budget ratios
        budget = {}
        for target in MATCHED_DROP_TARGETS:
            facs, missing = [], 0
            for s in seeds:
                pv = _curve(payload["rows"], proto, "vision", s)
                pt = _curve(payload["rows"], proto, "text", s)
                rv = _interp_level(pv, target)
                rt = _interp_level(pt, target)
                if rv is None or rt is None or rv <= 0:
                    missing += 1
                    continue
                facs.append(rt / rv)
            budget["drop_%g_pct" % target] = {
                "n_seeds_bracketed": len(facs), "n_seeds_unbracketed": missing,
                "budget_ratio_text_over_vision": summarise(facs),
            }
        out["headline"][proto] = {
            "levels_used_for_pooled_ratio": used,
            "matched_relative_fragility": head,
            "matched_drop_budget_ratio": budget,
            "levels": {repr(lv): out["per_level"][proto][repr(lv)]["ratio_of_means"]
                       for lv in levels[proto] if lv != 0.0
                       and repr(lv) in out["per_level"][proto]},
        }
    return out


if __name__ == "__main__":
    raise SystemExit(main())
