
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
    print("  R@1=%.4f | CGΔ=%+.4f | loss_final=%.4f | time=%.0fs | sep(init)=%.6f"
          % (d["final_task_metrics"]["R@1"], cg1-cg0, d["final_train_loss"],
             d["elapsed_sec"], d["initial_gap"]["cosine_separation"]))
    print("  local reference: R@1=0.685 | CGΔ=-0.0186 | loss_final=0.157 | time=1563s | sep=0.141407")
PY
