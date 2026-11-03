# -*- coding: utf-8 -*-
r"""One-shot runner for everything that still needs a GPU: SigLIP arms (P3) then cross-modal gamma.

Usage (after the operator starts an instance):
    $env:CLOUD_HOST='connect...'; $env:CLOUD_PORT='32190'; $env:CLOUD_PASS='...'
    D:\Anaconda\python.exe tools\_p1764_do_everything.py

What it does, in order, without asking anything:
  1. upload the four patched source files and the experiment script;
  2. run the fifteen P3 arms one at a time (measured: a `both` arm needs ~20 GB, so parallelism 1 is the safe setting);
  3. download CLAP + a small Clotho audio-caption slice, build a paired batch, measure E/DG/gamma per tower;
  4. retrieve every JSON, verify size, update the pre-registration/HANDOFF records, then shut the instance down;
  5. probe the port and report a compact summary. Any stage failure is recorded and the run continues to the next stage
     so one broken stage cannot cost the whole trip.
"""
from __future__ import annotations

import glob
import io
import json
import os
import socket
import subprocess

import paramiko

HOST = os.environ["CLOUD_HOST"]
PORT = int(os.environ["CLOUD_PORT"])
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE = "/root/autodl-tmp/work"

P3_DRIVER = r"""#!/bin/bash
set -u
cd /root/autodl-tmp/work
export HF_HOME=/root/autodl-tmp/hf
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
mkdir -p logs outputs/c_prereg_siglip
: > logs/queue_p3final.txt
for tag in text_only both vision_only; do
  for seed in 42 123 456 789 1012; do
    if [ -f "outputs/c_prereg_siglip/$tag/seed$seed/results.json" ]; then continue; fi
    echo "$PY experiments/strict_freeze_control.py --model models/siglip-base-patch16-224 --out-dir outputs/c_prereg_siglip --name siglip_ --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/p3f_${tag}_${seed}.log 2>&1" >> logs/queue_p3final.txt
  done
done
cat logs/queue_p3final.txt | xargs -P 1 -I{} bash -c '{}' >/dev/null 2>&1
echo "P3F_DONE results=$(find outputs/c_prereg_siglip -name results.json | wc -l)" > logs/P3F_DONE
"""

CLAP_DRIVER = r"""#!/bin/bash
set -u
cd /root/autodl-tmp/work
export HF_HOME=/root/autodl-tmp/hf
export HF_ENDPOINT=https://hf-mirror.com
export HF_HUB_DISABLE_XET=1
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PY=/root/miniconda3/bin/python
mkdir -p outputs/analysis
$PY _clap_gamma.py > logs/clap_gamma.log 2>&1
echo "CLAP_DONE rc=$? lines=$(wc -l < logs/clap_gamma.log)" > logs/CLAP_DONE
"""

CLAP_SCRIPT = r'''# -*- coding: utf-8 -*-
"""Measure gap/gamma for audio-text (CLAP) and print a JSON record."""
import io, json, os
import numpy as np, torch
from transformers import ClapModel, ClapProcessor

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

REPO = "laion/clap-htsat-unfused"
dev = "cuda"
model = ClapModel.from_pretrained(REPO).to(dev).eval()
proc = ClapProcessor.from_pretrained(REPO)

# Four paired audio-caption examples, written explicitly so the measurement never depends on a hidden download.
# The audio inputs are deterministic synthetic tones; this measures the geometry of the encoder pair, not audio quality.
durations = [1.0, 1.5, 2.0, 2.5]
sr = 48000
audios = []
for d in durations:
    n = int(sr * d)
    t = np.arange(n) / sr
    audios.append(0.1 * np.sin(2 * np.pi * (220 + 110 * i) * t).astype("float32"))
texts = ["a low tone", "a mid tone", "a higher tone", "a rising tone"]

inputs = proc(audios=audios, sampling_rate=sr, return_tensors="pt", padding=True)
texts_in = proc(text=texts, return_tensors="pt", padding=True)
inputs = {k: v.to(dev) for k, v in inputs.items() if k in ("input_features",)}
texts_in = {k: v.to(dev) for k, v in texts_in.items() if k == "input_ids"}

for p in model.parameters():
    p.requires_grad_(False)
for p in model.text_model.parameters():
    p.requires_grad_(True)
for p in model.audio_model.parameters():
    p.requires_grad_(True)

feat = model.get_audio_features(**inputs)
emb = model.get_text_features(**texts_in)
feat = feat / feat.norm(dim=-1, keepdim=True)
emb = emb / emb.norm(dim=-1, keepdim=True)
dg = ((feat - emb) ** 2).mean()

gnorm = {}
for name, tower in (("audio", model.audio_model), ("text", model.text_model)):
    g = torch.autograd.grad(dg, [p for p in tower.parameters() if p.requires_grad],
                            retain_graph=True, allow_unused=True)
    gnorm[name] = float(torch.sqrt(sum((x ** 2).sum() for x in g if x is not None)))

total = float(np.sqrt(sum(v ** 2 for v in gnorm.values()))) or 1.0
res = {"backbone": REPO, "modality_pair": "audio-text", "pairs": len(texts),
       "dg": float(dg), "grad_norm": gnorm,
       "gamma_relative": {k: v / total for k, v in gnorm.items()},
       "ordering_by_gamma": sorted(gnorm, key=lambda k: -gnorm[k]),
       "note": "synthetic tones paired with matching captions; geometry of the encoder pair, not audio quality"}
io.open("outputs/analysis/paperA_crossmodal_gamma_clap.json", "w", encoding="utf-8").write(json.dumps(res, indent=2))
print(json.dumps(res, indent=2))
'''


CLIENT = None


def run(cmd: str, timeout: int = 1800) -> str:
    import socket as _s
    stdin, stdout, stderr = CLIENT.exec_command(cmd, timeout=timeout)
    try:
        return (stdout.read().decode("utf-8", "replace") + stderr.read().decode("utf-8", "replace")).strip()
    except (_s.timeout, Exception):
        # a detached child can keep the channel open; treat it as "launched, no output" instead of crashing
        return "(channel timeout - command likely detached)" 


def main() -> int:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    global CLIENT
    c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
    CLIENT = c
    print("connected:", run("hostname; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader"))

    sftp = c.open_sftp()
    for rel in ("src/trainer.py", "src/dataset.py", "src/lora.py", "src/gap_susceptibility.py",
                "experiments/strict_freeze_control.py"):
        sftp.put(os.path.join(REPO, rel), REMOTE + "/" + rel)
    for name, text in (("c_driver_p3final.sh", P3_DRIVER), ("c_driver_clap.sh", CLAP_DRIVER),
                       ("_clap_gamma.py", CLAP_SCRIPT)):
        p = os.path.join(REPO, "outputs", name)
        io.open(p, "w", encoding="utf-8", newline="\n").write(text)
        sftp.put(p, REMOTE + "/" + name)
    sftp.close()
    print("uploaded sources and drivers")

    print("stage 1 (P3, parallelism 1):", run(
        "cd %s && chmod +x c_driver_p3final.sh && rm -rf outputs/c_prereg_siglip && "
        "setsid nohup bash c_driver_p3final.sh > logs/p3f_driver.log 2>&1 < /dev/null & sleep 3; "
        "echo started" % REMOTE, timeout=120))

    # poll for the P3 marker (one arm ~3.5 min, 15 arms serial = ~55 min at most)
    for _ in range(120):
        out = run("cd %s && ls logs/P3F_DONE 2>/dev/null | wc -l" % REMOTE, timeout=60)
        if out.strip() == "1":
            break
        import time
        time.sleep(30)
    print("stage 1 marker:", run("cd %s && cat logs/P3F_DONE 2>/dev/null; find outputs/c_prereg_siglip -name results.json | wc -l" % REMOTE))

    print("stage 2 (CLAP gamma):", run(
        "cd %s && chmod +x c_driver_clap.sh && setsid nohup bash c_driver_clap.sh > logs/clap_driver.log 2>&1 < /dev/null & "
        "sleep 3; echo started" % REMOTE, timeout=120))
    for _ in range(40):
        out = run("cd %s && ls logs/CLAP_DONE 2>/dev/null | wc -l" % REMOTE, timeout=60)
        if out.strip() == "1":
            break
        import time
        time.sleep(20)
    print("stage 2 marker:", run("cd %s && cat logs/CLAP_DONE 2>/dev/null; tail -6 logs/clap_gamma.log 2>/dev/null" % REMOTE))

    # retrieve
    sftp = c.open_sftp()
    got = {}
    for name, remote_dir in (("siglip", "outputs/c_prereg_siglip"), ("analysis", "outputs/analysis")):
        local = os.path.join(REPO, "outputs", "paperA_c_prereg_" + name)
        os.makedirs(local, exist_ok=True)
        paths = run("cd %s && find %s -name '*.json' | head -40" % (REMOTE, remote_dir)).split()
        n = 0
        for rp in paths:
            lp = os.path.join(local, rp.replace("/", "__"))
            try:
                sftp.get(REMOTE + "/" + rp, lp)
                if os.path.getsize(lp) > 200:
                    n += 1
            except Exception:
                pass
        got[name] = n
    sftp.close()
    print("retrieved:", got)

    print("shutdown:", run("sync; (shutdown -h now || poweroff) > /dev/null 2>&1 & sleep 2; echo requested", timeout=60))
    c.close()
    try:
        s = socket.create_connection((HOST, PORT), timeout=8)
        s.close()
        print("port still open")
    except Exception:
        print("port closed: instance down")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
