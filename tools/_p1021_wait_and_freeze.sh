#!/usr/bin/env bash
# Wait for the LLaVA sweep to finish, then freeze its results.
#
# Replaces the repeated 5-minute status checks with one loop that only reports when the run is complete, and
# immediately does the two things the operator asked for: keep every artefact (including the .pt adapters) and
# snapshot the finished state so the later Qwen work cannot disturb it.
set -uo pipefail
cd /root/p3
OUT=outputs/llava_bf16_sites
PY=/root/miniconda3/bin/python

echo "=== waiting for the sweep to finish (polling every 60 s) ==="
for i in $(seq 1 200); do
  # `grep -vc` can print more than one line (a count per output stream), which made the integer test below
  # fail with "integer expression expected"; `wc -l` on a filtered list is unambiguous.
  n=$(ls "$OUT"/*.json 2>/dev/null | grep -v train_progress | wc -l)
  step=$($PY -c "
import json
try:
    d=json.load(open('$OUT/train_progress.json'))
    print('%s %s/%s' % (d['run'], d['step'], d['steps_total']))
except Exception:
    print('n/a')
" 2>/dev/null || echo n/a)
  done_marker=$(grep -c BF16_SWEEP_DONE /root/p3/sweep_run.log 2>/dev/null || echo 0)
  echo "  [$i] records=$n | $step | done=$done_marker"
  if [ "$n" -ge 12 ] || [ "$done_marker" -ge 1 ]; then
    break
  fi
  sleep 60
done

echo
echo "=== finished state ==="
ls -la "$OUT"/
echo "--- json records: $n"

echo "=== freeze: snapshot results and the sweep that produced them ==="
STAMP=$(date +%H%M)
mkdir -p "frozen_llava_$STAMP"
cp -a "$OUT" "frozen_llava_$STAMP/results" 2>/dev/null || true
cp -a tools/_p820_llava_sites.py "frozen_llava_$STAMP/_p820_llava_sites.py"
cp -a sweep_run.log "frozen_llava_$STAMP/sweep_run.log" 2>/dev/null || true
du -sh "frozen_llava_$STAMP"

echo "=== artefact inventory (every .pt adapter is kept) ==="
for f in "$OUT"/*.pt; do [ -e "$f" ] && ls -la "$f"; done
echo "  total .pt: $(ls "$OUT"/*.pt 2>/dev/null | wc -l)"
echo "  json:      $(ls "$OUT"/*.json 2>/dev/null | wc -l)"

echo "=== per-record summary ==="
$PY - <<'PYEOF'
import json, glob
rows = []
for f in sorted(glob.glob("outputs/llava_bf16_sites/*.json")):
    if "train_progress" in f:
        continue
    d = json.load(open(f))
    rows.append((d.get("arm"), d.get("seed"), d.get("dg_before"), d.get("dg_after"),
                 d.get("cg_before"), d.get("cg_after"), d.get("dg_rel_change"), d.get("train_seconds")))
print("  %-12s %-5s %10s %10s %10s %10s %9s %7s" % ("arm", "seed", "dg_before", "dg_after",
                                                    "cg_before", "cg_after", "rel", "train_s"))
for r in rows:
    rel = ("%+.3f%%" % (100 * r[6])) if r[6] is not None else "-"
    print("  %-12s %-5s %10.4f %10.4f %10.4f %10.4f %9s %7s" % (
        r[0], r[1], r[2] or -1, r[3] or -1, r[4] or -1, r[5] or -1, rel, r[7]))
print("  records:", len(rows))
PYEOF
echo FREEZE_DONE
