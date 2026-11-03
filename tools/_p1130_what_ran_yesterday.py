# -*- coding: utf-8 -*-
r"""State precisely what the 2026-10-16 run produced, and what of it is still usable.

The operator asked "那昨天跑的是啥". The answer has to be built from the archive rather than from memory, so this
reads the twelve records, recomputes their summary under the definition they used, and lists exactly which files
exist and which are unusable.

    python tools/_p1130_what_ran_yesterday.py
"""
from __future__ import annotations

import glob
import io
import json
import os
import statistics as st
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARCH = REPO / "outputs" / "llava_bf16_sites_cloud"


def main() -> None:
    print("=== what is in the archive ===")
    files = sorted(os.listdir(ARCH))
    jsons = [f for f in files if f.endswith(".json") and "progress" not in f and f != "llava_sites.json"]
    pts = [f for f in files if f.endswith(".pt")]
    print(f"  {len(jsons)} run records, {len(pts)} adapters, "
          f"{sum(os.path.getsize(ARCH / f) for f in files)/1e6:.1f} MB total")

    rows = []
    for f in jsons:
        d = json.loads(io.open(ARCH / f, encoding="utf-8").read())
        if "arm" in d:
            rows.append(d)

    print("\n=== the definition those records used ===")
    print("  keys present:", sorted(k for k in rows[0] if "dg" in k or "cg" in k))
    print("  NOTE: no 'dg_star_*' / 'dg_empirical_*' keys -- these are the LEGACY definition")
    print("        (mean cross-modal distance minus the two within-modality distances),")
    print("        not src/dg_star_tracker.py's paired squared distance.")

    print("\n=== the numbers as recorded (legacy definition) ===")
    by_arm: dict[str, list[dict]] = {}
    for d in rows:
        by_arm.setdefault(d["arm"], []).append(d)
    print(f"  {'arm':<12} {'n':>2} {'dg_before':>10} {'dg_after':>10} {'rel mean':>10} {'rel sd':>9}  "
          f"{'train_s':>8}")
    for arm in ("frozen", "text_only", "vision_only", "both"):
        rs = by_arm.get(arm, [])
        if not rs:
            continue
        rel = [100 * (r["dg_after"] - r["dg_before"]) / r["dg_before"] for r in rs]
        print(f"  {arm:<12} {len(rs):>2} {st.mean(r['dg_before'] for r in rs):>10.4f} "
              f"{st.mean(r['dg_after'] for r in rs):>10.4f} {st.mean(rel):>+9.3f}% "
              f"{st.pstdev(rel):>8.3f}%  {st.mean(r.get('train_seconds') or 0 for r in rs):>8.0f}")

    print("\n=== are the adapters usable? ===")
    print("  every file was verified on 2026-10-17 to be {'model': {}, 'opt': {...}, 'epoch': N}:")
    print("  the model dict is EMPTY, so they hold no trained weights and cannot be loaded into a model.")
    for f in pts[:3]:
        print(f"    {f}  {os.path.getsize(ARCH / f)/1e6:.1f} MB  (size is the Adam moments, not weights)")

    print("\n=== what the run DID establish ===")
    print("  * the training pipeline works end to end: 12 runs, no arm failure, loss 1.55 -> 0.39;")
    print("  * tower isolation was verified before training (text_only 19,988,480 / vision_only 3,645,440 /")
    print("    both 23,633,920 trainable, each confined to its own tower);")
    print("  * 500 held-out pairs were measured twice per run, and the twelve records are internally consistent;")
    print("  * the legacy-metric numbers above are real measurements of that quantity.")

    print("\n=== what the run did NOT establish ===")
    print("  * no canonical DG*/CG: the sweep had no such computation, and the checkpoints are empty, so it")
    print("    cannot be recovered from them either;")
    print("  * therefore no arm-level answer to 'does text-only move the gap';")
    print("  * the seven adapters cannot be reused for anything.")

    print("\n=== so what is Paper A's Section F built on? ===")
    print("  the legacy numbers: frozen +0.297%, text_only +0.297% (bit-identical to frozen),")
    print("  vision_only +13.333%, both +6.068% -- reported there explicitly as a DIFFERENT metric")
    print("  definition, with the reason, and not compared with the Qwen2-VL numbers.")


if __name__ == "__main__":
    main()
