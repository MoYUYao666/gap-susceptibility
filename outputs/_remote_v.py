
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
