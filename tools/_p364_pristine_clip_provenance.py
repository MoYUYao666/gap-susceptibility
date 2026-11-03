# -*- coding: utf-8 -*-
r"""p364 -- is models/clip-vit-base-patch32 the upstream openai checkpoint, or a
project-modified copy?  (follow-up to p363's logit_scale=ln(100) finding)

Reads the HF cache snapshot for the same repo id (if present) and the local directory's
file metadata, and reports the logit_scale of each.  CPU, seconds.

    python tools/_p364_pristine_clip_provenance.py --apply
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import io
import json
import os
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "dinov2_hetero" / "pristine_clip_provenance.json"


def logit_scale_of(p: Path):
    import torch
    try:
        if p.suffix == ".safetensors":
            from safetensors.torch import load_file
            sd = load_file(str(p))
        else:
            sd = torch.load(str(p), map_location="cpu", weights_only=True)
    except Exception as e:  # noqa: BLE001
        return {"error": "%s: %s" % (type(e).__name__, e)}
    out = {}
    for k, v in sd.items():
        if "logit_scale" in k:
            out[k] = [float(x) for x in v.reshape(-1)]
    return out


def sha256_head(p: Path, n=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        h.update(fh.read(n))
    return h.hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    rep = {"script": "tools/_p364_pristine_clip_provenance.py", "sources": {}}

    local = REPO / "models" / "clip-vit-base-patch32"
    for name in ("pytorch_model.bin", "model.safetensors", "config.json"):
        f = local / name
        if f.exists():
            st = f.stat()
            rep["sources"][str(f.relative_to(REPO))] = {
                "size": st.st_size,
                "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                "sha256_first_1MiB": sha256_head(f),
                "logit_scale": logit_scale_of(f) if f.suffix != ".json" else None,
            }

    cache = Path.home() / ".cache" / "huggingface" / "hub" / "models--openai--clip-vit-base-patch32"
    snaps = sorted(glob.glob(str(cache / "snapshots" / "*")))
    rep["hf_cache_snapshots"] = snaps
    for s in snaps:
        for name in ("pytorch_model.bin", "model.safetensors"):
            f = Path(s) / name
            if f.exists():
                st = f.stat()
                rep["sources"][str(f)] = {
                    "size": st.st_size,
                    "resolved_target": str(f.resolve()),
                    "sha256_first_1MiB": sha256_head(f),
                    "logit_scale": logit_scale_of(f),
                }
    if not snaps:
        rep["hf_cache_note"] = ("no snapshot directory: the only local copy is "
                                "models/clip-vit-base-patch32")

    ls_local = None
    for k, v in rep["sources"].items():
        if k.endswith("pytorch_model.bin") and v.get("logit_scale"):
            ls_local = v["logit_scale"].get("logit_scale")
    rep["verdict_inputs"] = {
        "local_logit_scale": ls_local,
        "ln_1_over_0.07": 2.659260036932778,
        "ln_100": 4.605170185988092,
        "is_local_ln100": (ls_local is not None and abs(ls_local[0] - 4.605170185988092) < 1e-5),
    }

    print(json.dumps(rep, indent=1, ensure_ascii=False))
    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        io.open(OUT, "w", encoding="utf-8", newline="").write(
            json.dumps(rep, indent=2, ensure_ascii=False))
        print("\n[ok] wrote %s" % OUT.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
