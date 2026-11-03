# -*- coding: utf-8 -*-
r"""Survey what is available locally for a larger-dataset or modern-VLM extension.

Reviewer R2-3 asks for broader validation on larger datasets and modern VLMs. Before choosing, this
establishes what can actually be run here: the HuggingFace cache (which VLMs are already downloaded),
the local dataset inventory and its size ranking, and whether the experiment server is reachable
(the project rule is to download weights on the server rather than locally).

    python tools/_p814_resources.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs" / "analysis" / "resources_survey.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    report = {}

    print("=" * 104)
    print("1. HuggingFace cache: which models are already on disk")
    print("=" * 104)
    hf = Path(os.path.expanduser("~")) / ".cache" / "huggingface" / "hub"
    models = []
    if hf.exists():
        for d in sorted(hf.iterdir()):
            if not d.is_dir() or not d.name.startswith("models--"):
                continue
            size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            models.append((d.name.replace("models--", "").replace("--", "/"), size))
    for name, size in sorted(models, key=lambda kv: -kv[1]):
        print(f"  {size / 1e9:>8.2f} GB  {name}")
    if not models:
        print("  (no cache found)")
    report["hf_models"] = [{"name": n, "gb": round(s / 1e9, 2)} for n, s in models]

    print()
    print("=" * 104)
    print("2. local datasets, ranked by image count")
    print("=" * 104)
    dss = []
    for base in ("data", "coco", "flickr30k"):
        d = REPO / base
        if not d.exists():
            continue
        for sub in sorted(d.iterdir()):
            if not sub.is_dir():
                continue
            imgs = sum(1 for f in sub.rglob("*")
                       if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
            if imgs:
                dss.append((f"{base}/{sub.name}", imgs))
    for name, n in sorted(dss, key=lambda kv: -kv[1])[:16]:
        print(f"  {n:>8,} images  {name}")
    report["datasets"] = [{"name": n, "images": c} for n, c in dss]

    print()
    print("=" * 104)
    print("3. experiment server")
    print("=" * 104)
    try:
        r = subprocess.run(["ping", "-n", "1", "-w", "2000", "192.168.1.103"],
                           capture_output=True, timeout=15)
        reachable = r.returncode == 0
    except Exception:
        reachable = False
    print(f"  192.168.1.103 reachable: {reachable}")
    report["server_reachable"] = reachable

    print()
    print("=" * 104)
    print("4. what each option costs, given the hardware")
    print("=" * 104)
    print("  local GPU: RTX 4060 Laptop, 8.6 GB")
    modern = [n for n, _ in models if any(k in n.lower() for k in
                                          ("qwen", "llava", "internvl", "blip", "siglip", "clip"))]
    print(f"  VLM-ish entries in the cache: {modern if modern else 'none'}")
    print()
    print("  options for R2-3:")
    print("    (a) a modern VLM already cached -> runnable here if it fits in 8.6 GB")
    print("    (b) a modern VLM only available on the server -> server must be reachable")
    print("    (c) a larger retrieval dataset -> COCO val is already the largest local corpus")

    if a.apply:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        print()
        print(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
