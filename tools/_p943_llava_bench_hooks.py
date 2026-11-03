# -*- coding: utf-8 -*-
r"""Add `--bench-steps` and a per-batch token report to the LLaVA sweep script.

Two small additions used by `tools/_p942_llava_step_bench.py`:

* `--bench-steps N` -- stop training after N optimisation steps, so a configuration can be timed in
  minutes instead of hours;
* a one-line report of the first batch's padded sequence length and token count, which decides whether
  the cost is padding (a long `max-len` with short captions) or genuine model work.

Insertion is by regex on the argument block and on the timing lines, and the result is parsed with the
sweep's own interpreter before it is accepted; an earlier attempt used fixed anchors and silently left
the file unchanged.

    python tools/_p943_llava_bench_hooks.py [--apply]
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

ARG_RE = re.compile(r'( *ap\.add_argument\("--resume", action="store_true",\n(?: .*\n)*?.*\)\n)')
ARG_NEW = ('    ap.add_argument("--bench-steps", type=int, default=0,\n'
           '                    help="stop training after this many steps (timing runs only)")\n')

REPORT_RE = re.compile(r"( *inp = \{k: \(v\.to\(0\) if hasattr\(v, \"to\"\) else v\) for k, v in inp\.items\(\)\}\n"
                       r" *tb1 = time\.time\(\)\n)")
REPORT_NEW = (
    '                        if step_i == 0:\n'
    '                            _seq = int(inp["input_ids"].shape[1])\n'
    '                            _tok = int(inp["input_ids"].numel())\n'
    '                            _mean = _tok / max(1, int(inp["input_ids"].shape[0]))\n'
    '                            print("    batch tokens: " + str(_tok) + " mean " + str(int(_mean))\n'
    '                                  + " | sequence length in this batch: " + str(_seq), flush=True)\n')

CAP_RE = re.compile(r"( *if a\.report_every and step_i % a\.report_every == 0:)")
CAP_NEW = ('                        if a.bench_steps and step_i >= a.bench_steps:\n'
           '                            print("    bench stop after " + str(step_i) + " steps", flush=True)\n'
           '                            break\n')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "--bench-steps" in t:
        print("  already patched")
        return 0

    m = ARG_RE.search(t)
    assert m, "the --resume argument block was not found"
    out = t[: m.end(1)] + ARG_NEW + t[m.end(1):]
    print("  --bench-steps argument inserted after --resume")

    m = REPORT_RE.search(out)
    assert m, "the batch-construction timing lines were not found"
    out = out[: m.end(1)] + REPORT_NEW + out[m.end(1):]
    print("  first-batch token report inserted")

    m = CAP_RE.search(out)
    assert m, "the heartbeat line was not found"
    out = out[: m.start(1)] + CAP_NEW + out[m.start(1):]
    print("  step cap inserted before the heartbeat")

    ast.parse(out)
    print(f"  parses; {len(t.splitlines())} -> {len(out.splitlines())} lines")

    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")

    check = SCRIPT.read_text(encoding="utf-8")
    assert "--bench-steps" in check and "batch tokens" in check, "the write did not take effect"
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'"
                        + str(SCRIPT) + "',encoding='utf-8').read());print('ok')"], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    print("  written; the sweep's own interpreter parses it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
