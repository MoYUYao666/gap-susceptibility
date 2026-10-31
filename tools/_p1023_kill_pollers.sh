#!/usr/bin/env bash
# Stop the leftover wait-and-freeze pollers and report the sweep's state.
# `pkill -f wait_and_freeze` left copies running (three were counted afterwards), so this kills by PID with a
# pattern that cannot match the script doing the killing.
set -uo pipefail
echo "=== pollers before ==="
pgrep -af wait_and_freeze.sh | grep -v pgrep || echo none
for p in $(pgrep -f 'bash _p1021_wait_and_freeze.sh'); do
  [ "$p" = "$$" ] && continue
  kill -9 "$p" 2>/dev/null || true
done
sleep 2
echo "=== pollers after ==="
pgrep -af wait_and_freeze.sh | grep -v pgrep || echo none
echo "=== sweep progress ==="
cat /root/p3/outputs/llava_bf16_sites/train_progress.json | head -6
echo "=== records ==="
ls /root/p3/outputs/llava_bf16_sites/*.json | grep -v train_progress | wc -l
df -h / | tail -1
echo KILL_POLLERS_DONE
