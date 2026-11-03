#!/bin/bash
export PATH=/root/miniconda3/bin:$PATH
export PYTHONIOENCODING=utf-8
cd /root/autodl-tmp/a3
ls runs/logs | tail -6
echo "--- tails ---"
for f in $(ls -t runs/logs/*.log 2>/dev/null | head -3); do echo "== $f"; tail -2 "$f"; done
