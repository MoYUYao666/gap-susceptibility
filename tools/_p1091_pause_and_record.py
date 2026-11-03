# -*- coding: utf-8 -*-
r"""Stop everything running on the host and record exactly what is on disk, so tomorrow resumes cleanly.

Operator instruction 2026-10-16 evening: "明天再跑". The host is paused rather than left downloading, and this
writes the resume note: which path was being tried, how far it got, what is reusable, and what the next command
should be.

    python tools/_p1091_pause_and_record.py [--apply]
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import time
from pathlib import Path

import paramiko

HOST = os.environ.get("P3SSH_HOST", "")
PORT = int(os.environ.get("P3SSH_PORT", "22"))
PASS = os.environ.get("P3SSH_PASS", "")
REPO = Path(__file__).resolve().parents[1]
NOTE = REPO / "docs" / "resume_2026-10-17_llava_metric.md"

STOP = [
    ("multi-connection ModelScope fetcher", "pkill -9 -f _p1083_parallel_fetch || true"),
    ("HF mirror snapshot_download", "pkill -9 -f snapshot_download || true"),
    ("COCO fixture fetcher", "pkill -9 -f _p1088_coco_fixture || true"),
    ("stray curl downloads", "pkill -9 -f 'curl -sS' || true; pkill -9 -f 'curl -sSL' || true"),
]

REPORT = r"""
echo "=== processes still alive ==="
ps -eo pid,etimes,cmd | grep -E "snapshot_download|_p108[0-9]|curl" | grep -v grep || echo "  none"
echo "=== what survived on the data disk ==="
du -sh /root/autodl-tmp/hf /root/autodl-tmp/modelscope /root/autodl-tmp/pipcache 2>/dev/null
echo "--- HF mirror cache (host-3 method) ---"
find /root/autodl-tmp/hf/hub -maxdepth 1 -type d -name 'models--*' 2>/dev/null | head
du -sh /root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf 2>/dev/null
ls /root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf/blobs 2>/dev/null | head -8
echo "--- ModelScope partial (multi-connection, 9.9 GB fetched) ---"
ls -la /root/autodl-tmp/modelscope/hub/llava-hf/llava-1.5-7b-hf/ 2>/dev/null | head -8
echo "=== adapters uploaded? ==="
ls -la /root/p3/adapters/ 2>/dev/null | head
echo "=== environment ==="
/root/miniconda3/bin/python -c "import torch,transformers,peft; print('torch',torch.__version__,'transformers',transformers.__version__,'peft',peft.__version__)"
echo "=== disk ==="
df -h / /root/autodl-tmp | tail -2
echo PAUSE_REPORT_DONE
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if not a.apply:
        print("  (dry run)")
        return 0
    if not (HOST and PASS):
        print("  P3SSH_HOST / P3SSH_PASS are not set")
        return 2
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(HOST, port=PORT, username="root", password=PASS, timeout=30,
                allow_agent=False, look_for_keys=False)

    def sh(cmd: str, timeout: int = 240) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read().decode("utf-8", "replace") + e.read().decode("utf-8", "replace")).strip()

    for label, cmd in STOP:
        sh(cmd)
        print(f"  stopped: {label}")
    time.sleep(3)
    report = sh(REPORT)
    print(report)
    cli.close()

    NOTE.parent.mkdir(parents=True, exist_ok=True)
    with io.open(NOTE, "w", encoding="utf-8", newline="") as fh:
        fh.write("# Resume note: LLaVA canonical-metric recomputation (for 2026-10-17)\n\n")
        fh.write("## Why this is being done\n\n")
        fh.write("The archived LLaVA records were produced with a gap definition written inside "
                 "`tools/_p820_llava_sites.py` (mean cross-modal distance minus the two within-modality "
                 "distances). The paper and the ODE use `src/dg_star_tracker.py:compute`:\n\n")
        fh.write("```\nDG*  = mean_i || I_i - T_i ||^2      (paired, squared, after L2 normalisation)\n"
                 "CG   = || mean_i I_i - mean_i T_i ||\n"
                 "DG_e = sqrt(CG^2 + || sigma_I - sigma_T ||^2)\n```\n\n")
        fh.write("with embeddings taken as in `tools/_p47_qwen_train.py`: the last hidden state, mean-pooled over "
                 "the non-padding positions for the text side and over the image-token positions for the vision "
                 "side. The recomputation needs **no training** -- the seven LoRA adapters are saved -- so it is "
                 "forward passes only.\n\n")
        fh.write("**The first thing to establish** is whether the frozen arm is stable under the canonical "
                 "definition. If frozen moves as much as the trained arms, the quantity cannot resolve anything "
                 "on this model and the recomputation stops there. The archived frozen run moves "
                 "0.261161 -> 0.261937 under the old definition.\n\n")
        fh.write("## State at the pause (2026-10-16 21:00)\n\n")
        fh.write("Host: `connect.weste.seetacloud.com:43147` (RTX 4080 SUPER 32 GB, fresh instance).\n\n")
        fh.write("| Item | State |\n|---|---|\n")
        fh.write("| Pinned stack | installed: torch 2.9.1+cu130, torchvision 0.24.1+cu130, transformers 5.16.1, "
                 "peft 0.20.0, accelerate 1.14.0, modelscope 1.40.2 (all from the tuna mirror) |\n")
        fh.write("| LoRA adapters | **uploaded to `/root/p3/adapters/`** (7 files, 773 MB) |\n")
        fh.write("| LLaVA weights | **not complete.** Two routes tried, both left partial data on `/root/autodl-tmp` |\n")
        fh.write("| Recompute script | `tools/_p1060_recompute_canonical.py` (ready; calls the canonical formula) |\n")
        fh.write("| Fixture script | `tools/_p1088_coco_fixture.py` (multi-connection COCO fetch; the official "
                 "source throttled to ~0 B/s in the last attempt) |\n")
        fh.write("| Claim ledger | 96/96 passing; the LLaVA batch is already in it as a scoped negative result |\n")
        fh.write("| Paper A | supplement Section F written and compiled (NC 67 pp, Springer 49 pp, 0 errors) |\n\n")
        fh.write("## Measured transfer rates on this host (all 2026-10-16)\n\n")
        fh.write("| Source | Rate |\n|---|---|\n")
        fh.write("| ModelScope single connection | ~1 MB/s (throttled) |\n")
        fh.write("| ModelScope with 32 range connections | **13-18 MB/s** (reached 9.9 GB of 15 GB) |\n")
        fh.write("| hf-mirror.com single connection | ~0.5 MB/s (125 MB in 4 min); host 3 did 15 GB in 6-8 min |\n")
        fh.write("| pypi.tuna.tsinghua.edu.cn | 3.1-4.6 MB/s |\n")
        fh.write("| images.cocodataset.org (annotation archive) | ~400 B/s single; multi-connection did not start |\n\n")
        fh.write("## Next steps, in order\n\n")
        fh.write("1. Decide the weight source: ModelScope's multi-connection fetcher is already written and proven "
                 "(`tools/_p1083_parallel_fetch.py`, resume-safe). Restarting it should finish the last ~5 GB in "
                 "minutes; the hf-mirror route is the operator's stated preference but measured 0.5 MB/s here.\n")
        fh.write("2. Get the COCO val2014 annotations and the 500 held-out images onto the host "
                 "(`tools/_p1088_coco_fixture.py`; the archive is 472 MB and needs a working source).\n")
        fh.write("3. Run the frozen-only recomputation first: "
                 "`python tools/_p1060_recompute_canonical.py --arms frozen`.\n")
        fh.write("4. Only if frozen is stable, run the other three arms and put the numbers into the ledger.\n\n")
        fh.write("## Host at pause\n\n")
        fh.write("All downloads stopped. Whether the instance is stopped or released is the operator's call; "
                 "nothing depends on it except the reusable partial downloads listed above.\n\n")
        fh.write("## Raw report from the host\n\n```\n")
        fh.write(report + "\n```\n")
    print(f"  wrote {NOTE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
