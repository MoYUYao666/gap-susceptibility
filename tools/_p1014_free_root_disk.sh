#!/usr/bin/env bash
# Free the root filesystem and keep future writes off it.
#
# Measured 2026-10-16 11:55: the root overlay was 100% full (30 G of 30 G, 200 K free) while the data disk
# had 35 G free. That is why the sweep died at 11:44 with nothing in the log: writing the epoch checkpoint
# hit ENOSPC, and the traceback never reached the log because the log lives on the same full filesystem.
# The truncated `text_only_s456_ckpt.pt` (64 bytes) is the leftover of that write.
#
# Actions:
#   1. delete the per-epoch checkpoints. They exist only to resume an interrupted run, and every finished
#      record is already in its own JSON, so removing them loses nothing that has been measured.
#   2. move `outputs/` to the data disk and symlink it back, so results and checkpoints no longer compete
#      with the system disk. A symlink keeps every existing path working unchanged.
#   3. drop the pip cache on the data disk as well; the environment is installed and the wheel cache is
#      only useful if packages are reinstalled.
set -uo pipefail
cd /root/p3

echo "=== before ==="
df -h / /root/autodl-tmp | tail -2
du -sh /root/p3 /root/p3/outputs /root/autodl-tmp/hf /root/autodl-tmp/pipcache 2>/dev/null

echo "=== remove per-epoch checkpoints (records are unaffected) ==="
rm -f outputs/llava_bf16_sites/*.pt outputs/*/*.pt outputs/*/*/*.pt 2>/dev/null || true
echo "  remaining .pt files: $(find /root/p3 -name '*.pt' 2>/dev/null | wc -l)"

echo "=== move outputs to the data disk ==="
if [ -L outputs ]; then
  echo "  already a symlink -> $(readlink outputs)"
else
  mkdir -p /root/autodl-tmp/p3_outputs
  cp -a outputs/. /root/autodl-tmp/p3_outputs/ 2>/dev/null || true
  rm -rf outputs
  ln -s /root/autodl-tmp/p3_outputs outputs
  echo "  outputs -> $(readlink outputs)"
fi
ls outputs/llava_bf16_sites/ | tr '\n' ' '; echo

echo "=== drop the pip cache ==="
rm -rf /root/autodl-tmp/pipcache

echo "=== after ==="
df -h / /root/autodl-tmp | tail -2
du -sh /root/p3 2>/dev/null

echo "=== the records that exist (these are the results so far) ==="
for f in outputs/llava_bf16_sites/*.json; do
  /root/miniconda3/bin/python -c "
import json,sys
d=json.load(open(sys.argv[1]))
print('  %-18s arm=%-11s seed=%s dg=%.6f cg=%.6f train_s=%s' % (
  sys.argv[1].split('/')[-1], d.get('arm'), d.get('seed'), d.get('dg_after', -1),
  d.get('cg_after', -1), d.get('train_seconds')))
" "$f" 2>/dev/null || echo "  $f unreadable"
done
echo FREE_DISK_DONE
