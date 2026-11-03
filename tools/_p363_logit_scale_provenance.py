# -*- coding: utf-8 -*-
r"""p363 -- is the training temperature the same in the paper's runs and in the DINOv2 run?

`tools/_p293_dinov2_hetero_strict.py:107-108` hardcodes
    LOGIT_SCALE_INIT = 2.659260036932778   # ln(1/0.07), "fixed CLIP logit scale init"
and freezes it.  p361 read the local checkpoint's value as 4.605170249938965 = ln(100)
(temperature 0.01).  If that is right, the paper's arms (which load the same directory
through experiments/strict_freeze_control.py PRISTINE) trained at tau=0.01 while the
DINOv2 arm trained at tau=0.07.

This script reads the raw tensor out of the checkpoint files and reports, for every
candidate CLIP directory in the repo, the config's logit_scale_init_value and the stored
parameter -- no model instantiation needed.

    python tools/_p363_logit_scale_provenance.py --apply
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "logit_scale_provenance.json"


def read_tensor(path: Path):
    """Return {name: value} for scalar-ish keys of interest, without loading transformers."""
    import torch
    vals = {}
    if path.suffix == ".safetensors":
        from safetensors.torch import load_file
        sd = load_file(str(path))
    else:
        sd = torch.load(str(path), map_location="cpu", weights_only=True)
    for k, v in sd.items():
        if "logit_scale" in k or k in ("logit_scale", "visual.proj", "text_projection.weight"):
            if v.numel() <= 4:
                vals[k] = [float(x) for x in v.reshape(-1)]
            else:
                vals[k] = {"shape": list(v.shape)}
    return vals


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rep = {"script": "tools/_p363_logit_scale_provenance.py",
           "dinov2_script_constant": 2.659260036932778,
           "dinov2_script_line": "tools/_p293_dinov2_hetero_strict.py:107-108",
           "candidates": {}}

    dirs = sorted(set(
        [str(Path(p).parent) for p in
         glob.glob(str(REPO / "models" / "*" / "config.json"))] +
        [str(Path(p).parent) for p in
         glob.glob(str(REPO / "models" / "*" / "*" / "config.json"))]))
    for d in dirs:
        dd = Path(d)
        rec = {"dir": str(dd.relative_to(REPO))}
        cfg = dd / "config.json"
        if cfg.exists():
            c = json.loads(cfg.read_text(encoding="utf-8"))
            rec["config_logit_scale_init_value"] = c.get("logit_scale_init_value")
            rec["architectures"] = c.get("architectures")
        for name in ("model.safetensors", "pytorch_model.bin"):
            f = dd / name
            if f.exists():
                try:
                    rec["weights_file"] = name
                    rec["tensors"] = read_tensor(f)
                except Exception as e:  # noqa: BLE001
                    rec["weights_error"] = "%s: %s" % (type(e).__name__, e)
                break
        rep["candidates"][str(dd.relative_to(REPO))] = rec

    # which path does each experiment load?
    import re
    sc = (REPO / "src" / "config.py").read_text(encoding="utf-8")
    m = re.search(r"clip_model\s*:\s*str\s*=\s*[\"']([^\"']+)[\"']", sc)
    rep["src_config_default_clip_model"] = m.group(1) if m else None
    rep["paper_control_PRISTINE"] = "models/clip-vit-base-patch32 (experiments/" \
                                    "strict_freeze_control.py:63)"

    # hf cache copies of the same repo id, if any
    cache = Path.home() / ".cache" / "huggingface" / "hub"
    rep["hf_cache_dirs"] = [str(p) for p in glob.glob(str(cache / "models--openai--clip*"))]

    print(json.dumps(rep, indent=1, ensure_ascii=False))
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, indent=2, ensure_ascii=False))
        print("\n[ok] wrote %s" % OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
