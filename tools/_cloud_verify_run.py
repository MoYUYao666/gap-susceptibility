# -*- coding: utf-8 -*-
r"""云端：**版本对齐后验证单 run**（2026-10-09）。

## 判据

`both` / seed 42 / batch 128 / 10 epoch / max 5000：
- **通过**：`R@1 ≈ 0.68`（本地 0.685）且 `CGΔ ≈ −0.0186`；
- **仍失败**：说明不是版本问题，继续查。

    $env:CLOUD_PW='...'; python tools\_cloud_verify_run.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

SH = r'''
cd /root/autodl-tmp/work
rm -rf outputs/_verify
/root/miniconda3/bin/python experiments/strict_freeze_control.py \
  --model models/clip-vit-base-patch32 \
  --out-dir outputs/_verify/r4 --name verify_ \
  --rank 4 --alpha-mult 2 --tags both --seeds 42 \
  --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen \
  > outputs_verify.log 2>&1
echo "rc=$?"
/root/miniconda3/bin/python - <<'PY'
import json, os, glob
fs = glob.glob("outputs/_verify/**/results.json", recursive=True)
print("results:", fs)
for f in fs:
    d = json.load(open(f))
    cg0 = d["initial_gap"]["centroid_gap"]; cg1 = d["final_gap"]["centroid_gap"]
    print("  R@1=%.4f ｜ CGΔ=%+.4f ｜ loss 末=%.4f ｜ 用时=%.0fs ｜ sep(init)=%.6f"
          % (d["final_task_metrics"]["R@1"], cg1-cg0, d["final_train_loss"],
             d["elapsed_sec"], d["initial_gap"]["cosine_separation"]))
    print("  本地对照: R@1=0.685 ｜ CGΔ=-0.0186 ｜ loss 末=0.157 ｜ 用时=1563s ｜ sep=0.141407")
PY
'''


def main() -> int:
    from _cloud_ssh import client, run

    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_v.py", "w", encoding="utf-8",
                newline="\n").write(SH)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_v.py"), f"{WORK}/_verify.sh")
        sftp.close()
        run(c, f"cd {WORK} && sed -i 's/\\r$//' _verify.sh && bash _verify.sh", timeout=3600)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
