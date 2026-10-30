# -*- coding: utf-8 -*-
r"""Wait until a JSONL file has at least N lines, then exit 0 (used by the batch pipelines)."""
import io
import sys
import time

path, need = sys.argv[1], int(sys.argv[2])
while True:
    try:
        n = sum(1 for _ in io.open(path, encoding="utf-8"))
    except FileNotFoundError:
        n = 0
    if n >= need:
        print("ready: %d lines" % n)
        break
    time.sleep(60)
