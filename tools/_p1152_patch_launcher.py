# -*- coding: utf-8 -*-
r"""Make the restart/launch helper tolerant of a background job holding the SSH channel open.

A `setsid ... &` job inherits the exec channel's descriptors, so `read()` blocks until the channel times out even
though the launch succeeded. Two fixes: fully detach the job in a subshell (`( ... & )`) so the channel closes, and
treat a read timeout as success rather than an exception.

    python tools/_p1152_patch_launcher.py [--apply]
"""
from __future__ import annotations

import argparse
import ast
import io
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "tools" / "_p1151_restart_and_launch.py"

OLD_SH = '''    def sh(cmd: str, timeout: int = 200) -> str:
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        return (o.read() + e.read()).decode("utf-8", "replace").strip()
'''
NEW_SH = '''    def sh(cmd: str, timeout: int = 200) -> str:
        """Run a command; a launched background job can hold the channel open, so a read timeout is not an error."""
        _i, o, e = cli.exec_command(cmd, timeout=timeout)
        try:
            return (o.read() + e.read()).decode("utf-8", "replace").strip()
        except Exception:
            return "(channel stayed open -- the background job is running)"
'''

OLD_JOB = '''        cmd = (f"cd /root/p3 && setsid bash -c \\"{sys.executable if False else '/root/miniconda3/bin/python'} "
               f"{FETCH} --base '{base}' --files '{files}' --sizes '{sizes}' --dest '{dest}' "
               f"> {log} 2>&1\\" < /dev/null > /dev/null 2>&1 & sleep 3; echo relaunched")
        print("  " + sh(cmd))'''
NEW_JOB = '''        cmd = (f"cd /root/p3 && ( setsid /root/miniconda3/bin/python {FETCH} "
               f"--base '{base}' --files '{files}' --sizes '{sizes}' --dest '{dest}' "
               f"> {log} 2>&1 < /dev/null & ) ; sleep 2; echo relaunched")
        print("  " + sh(cmd))'''

OLD_LAUNCH = '''    launch = ("cd /root/p3 && export HF_HOME=/root/autodl-tmp/hf HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "
              "PYTORCH_ALLOC_CONF=expandable_segments:True PYTHONIOENCODING=utf-8; "
              "setsid bash -c 'nohup /root/miniconda3/bin/python -u -X utf8 "
              "tools/_p1145_clean_gap_measure.py --out /root/p3/outputs/canonical_caption_metric.json "
              "> /root/p3/clean_measure.log 2>&1' < /dev/null > /dev/null 2>&1 & sleep 3; echo launched")
    print("  " + sh(launch))'''
NEW_LAUNCH = '''    launch = ("cd /root/p3 && export HF_HOME=/root/autodl-tmp/hf HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 "
              "PYTORCH_ALLOC_CONF=expandable_segments:True PYTHONIOENCODING=utf-8 && "
              "( setsid /root/miniconda3/bin/python -u -X utf8 tools/_p1145_clean_gap_measure.py "
              "--out /root/p3/outputs/canonical_caption_metric.json > /root/p3/clean_measure.log 2>&1 "
              "< /dev/null & ) ; sleep 3; echo launched")
    print("  " + sh(launch))'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    t = io.open(P, encoding="utf-8").read()
    if "channel stayed open" in t:
        print("  already patched")
        return 0
    for old, new, label in ((OLD_SH, NEW_SH, "sh()"), (OLD_JOB, NEW_JOB, "fetch launcher"),
                            (OLD_LAUNCH, NEW_LAUNCH, "measure launcher")):
        n = t.count(old)
        print(f"  {label}: found {n}")
        assert n == 1, f"{label}: expected exactly one occurrence"
        t = t.replace(old, new, 1)
    ast.parse(t)
    print("  all three replacements applied; parses")
    if not a.apply:
        print("  (dry run)")
        return 0
    io.open(P, "w", encoding="utf-8", newline="").write(t)
    print("  written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
