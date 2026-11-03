# -*- coding: utf-8 -*-
r"""PR R2.3 (part B2) -- is LLaVA-1.5-7B testable in bf16 on this machine?  Measured, not assumed.

WHY THIS EXISTS
    PR R2.3 asks for validation on larger / more modern VLMs.  The archive already has
    Qwen2-VL-2B under strict freezing (reused, not rerun -- see the report).  The only larger
    VLM available locally is `models/llava-hf` (LLaVA-1.5-7B, 3 safetensors shards totalling
    ~14.1 GB on disk).

PROJECT RULE THAT GOVERNS THIS SCRIPT
    Four-bit quantisation may NOT be used as evidence here: this project already measured that
    the same seed gives different results across two 4-bit runs (quantised matmuls are not
    deterministic), so a 4-bit LLaVA run would not be reproducible.  A bf16 run would be.  This
    script therefore asks only the bf16 question.  It does not produce a 4-bit number.

WHAT IT MEASURES
    1. device facts before load: total VRAM, free VRAM, what is already allocated;
    2. the model's on-disk weight footprint (from the shard files themselves);
    3. the exact failure of a bf16 load, if it fails: peak allocation reached, the exception
       text, and how far the weights got through the shard list;
    4. the corresponding number for 2-bit / 4-bit so the shortfall can be stated as a ratio.

OUTPUT
    outputs/analysis/llava_bf16_feasibility.json

USAGE
    python tools/_p294_llava_bf16_feasibility.py            # full: attempts the bf16 load
    python tools/_p294_llava_bf16_feasibility.py --disk-only
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

REPO = Path(__file__).resolve().parents[1]
MODEL_DIR = REPO / "models" / "llava-hf"
OUT = REPO / "outputs" / "analysis" / "llava_bf16_feasibility.json"


def shard_facts():
    """On-disk footprint, read from the shard files (not from the config's claims)."""
    shards = sorted(MODEL_DIR.glob("*.safetensors"))
    sizes = {p.name: p.stat().st_size for p in shards}
    total = sum(sizes.values())
    return {
        "model_dir": str(MODEL_DIR.relative_to(REPO)),
        "n_safetensors": len(shards),
        "shard_bytes": sizes,
        "total_bytes": total,
        "total_GiB": round(total / 2 ** 30, 3),
        "bf16_GiB": round(total / 2 ** 30, 3),        # weights stored in bf16
        "fp32_GiB": round(total / 2 ** 30 * 2, 3),
        "int8_GiB": round(total / 2 ** 30 * 0.5, 3),
        "int4_GiB": round(total / 2 ** 30 * 0.25, 3),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--disk-only", action="store_true",
                    help="skip the load attempt (no GPU needed)")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()

    report = {
        "experiment": "llava_bf16_feasibility",
        "asked": ("PR R2.3 -- can a larger/modern VLM (LLaVA-1.5-7B) be validated in bf16 on an "
                  "RTX 4060 Laptop 8 GB, i.e. reproducibly?"),
        "four_bit_excluded_because": (
            "project measurement: repeating one 4-bit configuration with an identical seed "
            "changed the measured gap span from 0.304 to 0.407 (quantised matmuls are not "
            "deterministic), so 4-bit output cannot serve as reproducible evidence"),
        "ran_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "disk": shard_facts(),
        "source": {"script": "tools/_p294_llava_bf16_feasibility.py"},
    }
    print("[disk] %s: %d shards, %.3f GiB on disk (bf16 weights)"
          % (report["disk"]["model_dir"], report["disk"]["n_safetensors"],
             report["disk"]["total_GiB"]), flush=True)

    if a.disk_only:
        report["verdict"] = "disk-only run; no load attempted"
    else:
        import torch
        import torch.nn.functional  # noqa: F401

        dev = torch.cuda.current_device() if torch.cuda.is_available() else None
        free_b, total_b = torch.cuda.mem_get_info(dev) if dev is not None else (0, 0)
        report["device"] = {
            "name": torch.cuda.get_device_name(dev) if dev is not None else "cpu",
            "total_VRAM_GiB": round(total_b / 2 ** 30, 3),
            "free_VRAM_at_start_GiB": round(free_b / 2 ** 30, 3),
            "already_allocated_by_torch_GiB": round(torch.cuda.memory_allocated() / 2 ** 30, 3),
        }
        print("[device] %s  total=%.2f GiB  free=%.2f GiB"
              % (report["device"]["name"], report["device"]["total_VRAM_GiB"],
                 report["device"]["free_VRAM_at_start_GiB"]), flush=True)

        from transformers import AutoProcessor, LlavaForConditionalGeneration

        dtype = torch.bfloat16 if a.dtype == "bfloat16" else torch.float16
        t0 = time.time()
        try:
            model = LlavaForConditionalGeneration.from_pretrained(
                str(MODEL_DIR), local_files_only=True, torch_dtype=dtype, low_cpu_mem_usage=True)
            model = model.to("cuda")
            report["load"] = {
                "status": "SUCCESS",
                "dtype": a.dtype,
                "params": sum(p.numel() for p in model.parameters()),
                "peak_allocated_GiB": round(torch.cuda.max_memory_allocated() / 2 ** 30, 3),
                "seconds": round(time.time() - t0, 1),
            }
            print("[load] SUCCESS", report["load"], flush=True)
            del model
            torch.cuda.empty_cache()
        except Exception as e:  # noqa: BLE001 -- the failure IS the measurement
            report["load"] = {
                "status": "FAILED",
                "dtype": a.dtype,
                "exception_type": type(e).__name__,
                "exception_text": str(e)[:4000],
                "peak_allocated_GiB": round(torch.cuda.max_memory_allocated() / 2 ** 30, 3),
                "peak_reserved_GiB": round(torch.cuda.max_memory_reserved() / 2 ** 30, 3),
                "seconds": round(time.time() - t0, 1),
                "traceback_tail": traceback.format_exc().strip().splitlines()[-6:],
            }
            print("[load] FAILED (%s): %s" % (type(e).__name__, str(e)[:300]), flush=True)

        d = report["disk"]
        need = d["bf16_GiB"]
        have = report["device"]["total_VRAM_GiB"]
        report["verdict"] = {
            "bf16_weights_GiB": need,
            "total_VRAM_GiB": have,
            "shortfall_GiB": round(need - have, 3),
            "ratio_needed_over_have": round(need / have, 2),
            "conclusion": ("bf16 weights alone exceed total VRAM" if need > have
                           else "weights fit; see load result for activation headroom"),
            "reproducible_local_route": None,
        }
        print("[verdict] %s" % json.dumps(report["verdict"], ensure_ascii=False), flush=True)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    print("[ok] wrote", a.out, flush=True)


if __name__ == "__main__":
    main()
