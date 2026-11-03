# -*- coding: utf-8 -*-
r"""Match adapters by arm prefix, and record the seed each one came from.

The seven files are named `<arm>_s<seed>_ckpt.pt` (text_only has only s456; vision_only has s42/s123/s456), while
the recomputation looked for `<arm>_ckpt.pt` and failed:

    FileNotFoundError: /root/p3/adapters/text_only_ckpt.pt

This makes the loader accept any file whose name starts with the arm, records the seed it used, and keeps results
per arm-and-seed so nothing is silently averaged.

    python tools/_p1112_adapter_by_prefix.py [--apply]
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "tools" / "_p1107_run_canonical.py"

OLD = """    if arm != "frozen":
        ck = ADAPTERS / f"{arm}_ckpt.pt"
        payload = torch.load(ck, map_location="cpu")
        sd = payload["model"] if isinstance(payload, dict) and "model" in payload else payload
        missing, unexpected = model.load_state_dict(sd, strict=False)
        print(f"  loaded {len(sd)} tensors; missing {len(missing)}, unexpected {len(unexpected)}", flush=True)
        if unexpected:
            print("  !! unexpected keys:", list(unexpected)[:3], flush=True)
    model.eval()
"""

NEW = """    seed_used = None
    if arm != "frozen":
        # files are named <arm>_s<seed>_ckpt.pt and not every arm has every seed (text_only has only s456)
        cands = sorted(ADAPTERS.glob(f"{arm}_s*_ckpt.pt")) or sorted(ADAPTERS.glob(f"{arm}*_ckpt.pt"))
        if not cands:
            print(f"  !! no adapter for {arm} in {ADAPTERS}; skipping", flush=True)
            results[arm] = {"arm": arm, "error": "no adapter"}
            continue
        ck = cands[0]
        seed_used = ck.stem.split("_s")[-1].replace("_ckpt", "") if "_s" in ck.stem else "?"
        payload = torch.load(ck, map_location="cpu")
        sd = payload["model"] if isinstance(payload, dict) and "model" in payload else payload
        missing, unexpected = model.load_state_dict(sd, strict=False)
        print(f"  adapter {ck.name} (seed {seed_used}): {len(sd)} tensors; "
              f"missing {len(missing)}, unexpected {len(unexpected)}", flush=True)
        if unexpected:
            print("  !! unexpected keys:", list(unexpected)[:3], flush=True)
    model.eval()
"""

OLD2 = """    rec = {"arm": arm, "n": len(held), "dg_star": sum(dgs) / len(dgs), "cg": sum(cgs) / len(cgs),"""
NEW2 = """    rec = {"arm": arm, "seed": seed_used, "n": len(held),
           "dg_star": sum(dgs) / len(dgs), "cg": sum(cgs) / len(cgs),"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = TARGET.read_text(encoding="utf-8")
    if "arm}_s*_ckpt.pt" in t:
        print("  already fixed")
        return 0
    assert t.count(OLD) == 1, f"load block: found {t.count(OLD)}"
    assert t.count(OLD2) == 1, f"record block: found {t.count(OLD2)}"
    t = t.replace(OLD, NEW, 1).replace(OLD2, NEW2, 1)
    print("  adapters now matched by arm prefix, with the seed recorded")
    if not a.apply:
        print("  (dry run)")
        return 0
    TARGET.write_text(t, encoding="utf-8", newline="")
    import ast
    ast.parse(t)
    print("  written and parses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
