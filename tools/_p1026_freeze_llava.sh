#!/usr/bin/env bash
# Freeze the finished LLaVA run and inventory every artefact, including the .pt adapters.
#
# Operator instruction 2026-10-16: "跑完之后qwen新模型也试试看，注意先保存所有结果包括pt模型". So before anything
# touches the script for the Qwen work, the finished state is snapshotted: the records, every .pt adapter,
# the exact sweep that produced them, and its log.
set -uo pipefail
cd /root/p3
OUT=outputs/llava_bf16_sites
STAMP=$(date +%m%d_%H%M)
DEST=frozen_llava_$STAMP
PY=/root/miniconda3/bin/python

echo "=== records present ==="
ls "$OUT"/*.json | grep -v train_progress | wc -l

echo "=== snapshot into $DEST ==="
mkdir -p "$DEST"
cp -a "$OUT" "$DEST/results"
cp -a tools/_p820_llava_sites.py "$DEST/_p820_llava_sites.py"
cp -a sweep_run.log "$DEST/sweep_run.log"
cp -a outputs/analysis/llava_sites.json "$DEST/llava_sites.json" 2>/dev/null || true
du -sh "$DEST"
ls "$DEST"

echo "=== every artefact, with sizes ==="
for f in "$OUT"/*; do
  printf '  %12s  %s\n' "$(stat -c %s "$f")" "$(basename "$f")"
done

echo "=== .pt inventory (the trained adapters) ==="
ls -la "$OUT"/*.pt 2>/dev/null | awk '{printf "  %12s  %s\n", $5, $9}'
echo "  count: $(ls "$OUT"/*.pt 2>/dev/null | wc -l)"
echo "  total: $(du -sh "$OUT" | cut -f1)"

echo "=== per-record metrics ==="
$PY - <<'PYEOF'
import json, glob
rows = []
for f in sorted(glob.glob("outputs/llava_bf16_sites/*.json")):
    if "train_progress" in f:
        continue
    d = json.load(open(f))
    rows.append(d)
print("  %-12s %-5s %10s %10s %10s %10s %9s %8s" % ("arm", "seed", "dg_before", "dg_after",
                                                    "cg_before", "cg_after", "rel%", "train_s"))
for d in sorted(rows, key=lambda r: (r.get("arm", ""), r.get("seed", 0))):
    rel = d.get("dg_rel_change")
    print("  %-12s %-5s %10.4f %10.4f %10.4f %10.4f %9s %8s" % (
        d.get("arm"), d.get("seed"), d.get("dg_before") or -1, d.get("dg_after") or -1,
        d.get("cg_before") or -1, d.get("cg_after") or -1,
        ("%+.3f" % (100 * rel)) if rel is not None else "-", d.get("train_seconds")))
print("  records:", len(rows))
arms = {}
for d in rows:
    arms.setdefault(d.get("arm"), []).append(d)
print()
for arm, rs in sorted(arms.items()):
    rel = [r["dg_rel_change"] for r in rs if r.get("dg_rel_change") is not None]
    if rel:
        m = sum(rel) / len(rel)
        sd = (sum((x - m) ** 2 for x in rel) / len(rel)) ** 0.5
        print("  %-12s n=%d  mean %+.3f%%  sd %.3f%%" % (arm, len(rel), 100 * m, 100 * sd))
PYEOF
echo FREEZE_DONE
