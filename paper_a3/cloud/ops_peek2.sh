#!/bin/bash
export PATH=/root/miniconda3/bin:$PATH
export PYTHONIOENCODING=utf-8
cd /root/autodl-tmp/a3
python - <<PY
import glob, io, json
for p in sorted(glob.glob("runs/cloud_l14/*.json"))[:8]:
    r = json.loads(io.open(p, encoding="utf-8").read())
    print(p.split("/")[-1][:-5].ljust(38), "R@1 %.4f" % r["metrics"]["R@1_i2t"], "vram %.1f" % r.get("peak_vram_gb", 0), "min %.1f" % (r["wall_seconds"]/60))
PY
