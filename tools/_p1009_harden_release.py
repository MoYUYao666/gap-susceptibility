# -*- coding: utf-8 -*-
r"""Make the between-arm release actually return the memory, and stop hiding the log tail.

Three arms have now died at a reload, so the release added earlier is not sufficient. Two separate faults:

1. **The release is not aggressive enough.** It drops the references and empties the cache, but between the
   arms there are still live objects holding device memory: the previous arm's optimizer state (AdamW keeps
   two tensors per trainable parameter, and the `both` arm has 23.6 M of them), plus the CUDA context's own
   cached blocks. `torch.cuda.ipc_collect()` and `torch.cuda.synchronize()` are added, and the freed amount
   is reported so the effect is visible rather than assumed.

2. **`grep` in the pipeline buffers the tail.** `sweep 2>&1 | grep -Ev "..."` keeps the last block in
   grep's buffer, so when the process exits the final lines -- including a `raise SystemExit` message -- are
   lost, and the log ends mid-heartbeat. The pipeline drops `grep` and the noise is filtered afterwards.

    python tools/_p1009_harden_release.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
PY = r"D:\Anaconda\envs\pytorch\python.exe"

OLD_RE = re.compile(r"( *)            _gc\.collect\(\)\n"
                    r" *torch\.cuda\.empty_cache\(\)\n"
                    r" *torch\.cuda\.reset_peak_memory_stats\(\)\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "ipc_collect" in t:
        print("  already hardened")
        return 0
    m = OLD_RE.search(t)
    assert m, "the release lines were not found"
    indent = "            "
    new = (
        f"{indent}_gc.collect()\n"
        f"{indent}torch.cuda.synchronize()\n"
        f"{indent}torch.cuda.empty_cache()\n"
        f"{indent}torch.cuda.ipc_collect()\n"
        f"{indent}torch.cuda.empty_cache()\n"
        f"{indent}torch.cuda.reset_peak_memory_stats()\n"
        f"{indent}_allocated = torch.cuda.memory_allocated() / 1e9\n"
        f"{indent}_reserved = torch.cuda.memory_reserved() / 1e9\n"
        f"{indent}print(f\"  after release: allocated {{_allocated:.2f}} GB, reserved {{_reserved:.2f}} GB\",\n"
        f"{indent}      flush=True)\n")
    out = t[: m.start()] + new + t[m.end():]
    ast.parse(out)
    print("  release hardened: synchronize, empty_cache, ipc_collect, empty_cache, and a size report")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
