#!/bin/bash
export PATH=/root/miniconda3/bin:$PATH
cd /root/autodl-tmp/a3
grep "^FAIL" logs/suite_extra3.log
echo "--- tails of failed cell logs ---"
for f in $(grep "^FAIL" logs/suite_extra3.log | awk '{print $2}'); do echo "== $f"; tail -5 "runs/logs/$f.log" 2>/dev/null; done
