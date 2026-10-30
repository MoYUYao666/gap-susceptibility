# -*- coding: utf-8 -*-
r"""Never let one arm take the whole sweep down silently.

Three arms have now ended with the process gone and nothing in the log, so the sweep's structure is the real
problem: any exception in one arm ends the run, and with `grep` in the pipeline the message can be swallowed.

This wraps the body of each arm in a try/except that

* writes the traceback to `outputs/llava_bf16_sites/ARM_FAILURES.txt` (a file, so buffering cannot hide it),
* prints a short one-line summary to stdout and **continues with the next arm**,
* records the failing arm in the run list so the summary accounts for it.

The per-arm body is moved into a helper call so the wrap is a real `try:` around it rather than a
re-indentation of the whole block, which would be fragile to apply by script.

    python tools/_p1010_arm_exception_guard.py [--apply]
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

# the arm body starts at the release step and runs to the end of the seed loop
START = "            # Release the previous arm before building this one."
END_RE = re.compile(r"\n( *)    # ---- write the aggregate -+\n|\n( *)print\(\)\n( *)print\(\"=\" \* 100\)\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "_arm_guard" in t:
        print("  already guarded")
        return 0
    i = t.find(START)
    assert i > 0, "the release step was not found"
    # The arm body ends after `del mm` / `torch.cuda.empty_cache()` at its own indentation; locating it by
    # line rather than by a regex on loop headers, which did not match (the regex reported no boundary).
    end_marker = "            del mm\n            torch.cuda.empty_cache()\n"
    k = t.find(end_marker, i)
    assert k > i, "the end of the arm body was not found"
    j = k + len(end_marker)
    body = t[i:j]
    assert body.startswith("            # Release"), "the arm body does not start where expected"
    print(f"  arm body: {len(body.splitlines())} lines, from the release step to the record write")
    guard = (
        "            try:  # _arm_guard: one arm must not take the sweep down\n"
        + "".join(("    " + ln if ln.strip() else ln) + "\n" for ln in body.splitlines())
        + "            except BaseException as _arm_exc:  # noqa: BLE001 - the point is to survive anything\n"
        + "                import traceback as _tb\n"
        + "                _msg = f\"{name}: {type(_arm_exc).__name__}: {_arm_exc}\"\n"
        + "                print(f\"  ARM FAILED {_msg}\", flush=True)\n"
        + "                with open(OUT_DIR / \"ARM_FAILURES.txt\", \"a\", encoding=\"utf-8\") as _fh:\n"
        + "                    _fh.write(_msg + chr(10) + _tb.format_exc() + chr(10))\n"
        + "                results.setdefault(\"failures\", []).append(_msg)\n"
        + "                torch.cuda.empty_cache()\n"
        + "                continue\n")
    out = t[:i] + guard + t[j:]
    ast.parse(out)
    print(f"  wrapped {len(body.splitlines())} lines of the arm body in a guard")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")
    r = subprocess.run([PY, "-c", "import ast,io;ast.parse(io.open(r'" + str(SCRIPT)
                        + "',encoding='utf-8').read());print('local parse ok')"], capture_output=True)
    print("  " + r.stdout.decode("utf-8", "replace").strip())
    assert r.returncode == 0, r.stderr.decode("utf-8", "replace")
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
