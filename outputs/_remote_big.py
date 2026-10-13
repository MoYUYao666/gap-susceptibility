
import os, subprocess, sys, time
PY = "/root/miniconda3/bin/python"
os.chdir("/root/autodl-tmp/work")

def log(m):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with open("outputs_big.log", "a") as f:
        f.write(line + "\n")

def run(cmd, tag, timeout=6*3600):
    log("RUN %s" % tag)
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    dt = time.time() - t0
    if r.returncode == 0:
        log("  OK %.0fs" % dt)
    else:
        err = next((l for l in (r.stderr or "").splitlines()
                    if "Error" in l or "error" in l), "")
        log("  FAIL rc=%s %.0fs %s" % (r.returncode, dt, err[:150]))
    return r.returncode == 0

BASE = [PY, "experiments/strict_freeze_control.py", "--rank", "4",
        "--alpha-mult", "2", "--skip-frozen"]

log("=" * 60)
log("Starting high-cost queue Q1-Q4")

# ── Q1 large-scale: 20000 samples × 20 epochs × 3 seeds (B/32 text_only) ──
run(BASE + ["--model", "models/clip-vit-base-patch32",
            "--out-dir", "outputs/scale_b32_r4", "--name", "scale_",
            "--tags", "text_only", "--seeds", "42", "123", "456",
            "--epochs", "20", "--max-samples", "20000",
            "--batch-size", "128"],
    "Q1 large-scale B/32 r4 text_only (20000x20, 3 seeds)")

# ── Q2 batch axis (B/32 r4 text_only, batch 32/64/256) ──
for bs in ("32", "64", "256"):
    run(BASE + ["--model", "models/clip-vit-base-patch32",
                "--out-dir", "outputs/batchaxis_b32_r4", "--name", "bs%s_" % bs,
                "--tags", "text_only", "--seeds", "42",
                "--epochs", "10", "--max-samples", "5000",
                "--batch-size", bs],
        "Q2 batch=%s" % bs)

# ── Q3 OpenCLIP extra seeds 3/4/5 (text_only + both) ──
for arm in ("text_only", "both"):
    run(BASE + ["--model", "models/openclip",
                "--out-dir", "outputs/strict_freeze_oclip/r4", "--name", "oclip_r4_",
                "--tags", arm, "--seeds", "789", "1024",
                "--epochs", "10", "--max-samples", "5000",
                "--batch-size", "128"],
        "Q3 OpenCLIP %s seeds 789/1024" % arm)

log("Q1-Q4 complete")
log("ALLDONE_SMALL")
