# -*- coding: utf-8 -*-
r"""Make the trainer backbone-agnostic so SigLIP can run, upload it, and chain the SigLIP batch after P2/P4.

`src/trainer.py` hardcoded `CLIPModel` / `CLIPProcessor` and `self.model.logit_scale.exp()`. SigLIP has a
`model_type == "siglip"` config, exposes `image_embeds` / `text_embeds` identically, and carries a `logit_scale`
parameter, so the only change needed is (a) select the class from the config, (b) fall back to a fixed temperature when
a backbone has no `logit_scale`. The contrastive loss stays the same (softmax over the similarity matrix) for every
backbone, which keeps the protocol identical across P1-P4.

The SigLIP arms are chained to start only after the running P2/P4 batch writes logs/P24_DONE, so VRAM is never
oversubscribed (measured 9.2 GB per arm against 32.8 GB -> 3 concurrent is the ceiling).
"""
import io
import os

import paramiko

HOST = os.environ.get("CLOUD_HOST", "connect.westb.seetacloud.com")
PORT = int(os.environ.get("CLOUD_PORT", "39308"))
USER = os.environ.get("CLOUD_USER", "root")
PWD = os.environ["CLOUD_PASS"]
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE = "/root/autodl-tmp/work"

# ---------------------------------------------------------------- patch the local trainer
P = os.path.join(REPO, "src", "trainer.py")
t = io.open(P, encoding="utf-8").read()

OLD_IMPORT = "        from transformers import CLIPModel, CLIPProcessor\n"
NEW_IMPORT = (
    "        from transformers import AutoConfig\n"
    "        _cfg = AutoConfig.from_pretrained(self.train_cfg.clip_model)\n"
    "        _mtype = getattr(_cfg, \"model_type\", \"\")\n"
    "        if _mtype == \"siglip\":\n"
    "            from transformers import SiglipModel as _Model, SiglipProcessor as _Proc\n"
    "        else:\n"
    "            from transformers import CLIPModel as _Model, CLIPProcessor as _Proc\n"
    "        print(f\"\\U0001F9E9 model class: {_Model.__name__} (model_type={_mtype})\")\n"
)
assert OLD_IMPORT in t, "import anchor missing (already patched?)"
t = t.replace(OLD_IMPORT, NEW_IMPORT, 1)

OLD_LOAD = """        self.model = CLIPModel.from_pretrained(
            self.train_cfg.clip_model
        )
        self.processor = CLIPProcessor.from_pretrained(
            self.train_cfg.clip_model
        )"""
NEW_LOAD = """        self.model = _Model.from_pretrained(
            self.train_cfg.clip_model
        )
        self.processor = _Proc.from_pretrained(
            self.train_cfg.clip_model
        )"""
assert OLD_LOAD in t, "model load anchor missing"
t = t.replace(OLD_LOAD, NEW_LOAD, 1)

# a backbone without logit_scale gets a fixed temperature instead of crashing
OLD_SCALE = "        logit_scale = self.model.logit_scale.exp()"
NEW_SCALE = ("        logit_scale = (self.model.logit_scale.exp() if hasattr(self.model, \"logit_scale\")\n"
             "                       else torch.tensor(10.0, device=image_embeds.device))")
n_scale = t.count(OLD_SCALE)
t = t.replace(OLD_SCALE, NEW_SCALE)
io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("trainer patched: class selection + logit_scale fallback (%d scale sites)" % n_scale)

# ---------------------------------------------------------------- upload + chained driver
DRIVER = r"""#!/bin/bash
set -u
cd /root/autodl-tmp/work
export HF_HOME=/root/autodl-tmp/hf
PY=/root/miniconda3/bin/python
mkdir -p logs outputs/c_prereg_siglip
# wait for the running P2/P4 batch so VRAM is never oversubscribed
while [ ! -f logs/P24_DONE ]; do sleep 60; done
: > logs/queue_siglip.txt
for tag in text_only both vision_only; do
  for seed in 42 123 456 789 1012; do
    echo "$PY experiments/strict_freeze_control.py --model models/siglip-base-patch16-224 --out-dir outputs/c_prereg_siglip --name siglip_ --rank 8 --alpha-mult 2 --tags $tag --seeds $seed --epochs 10 --max-samples 5000 --batch-size 128 --skip-frozen --dg-star > logs/s_${tag}_${seed}.log 2>&1" >> logs/queue_siglip.txt
  done
done
start=$(date +%s)
cat logs/queue_siglip.txt | xargs -P 3 -I{} bash -c '{}'
end=$(date +%s)
echo "SIGLIP_DONE seconds=$((end-start)) results=$(find outputs/c_prereg_siglip -name results.json | wc -l)" > logs/SIGLIP_DONE
"""

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=PORT, username=USER, password=PWD, timeout=30, banner_timeout=30, auth_timeout=30)
sftp = c.open_sftp()
sftp.put(P, REMOTE + "/src/trainer.py")
tmp = os.path.join(REPO, "outputs", "_driver_siglip_chain.sh")
io.open(tmp, "w", encoding="utf-8", newline="\n").write(DRIVER)
sftp.put(tmp, REMOTE + "/c_driver_siglip_chain.sh")
sftp.close()
print("uploaded trainer.py and the chained SigLIP driver")

stdin, stdout, stderr = c.exec_command(
    "cd %s && sed -i 's/\\r$//' c_driver_siglip_chain.sh && chmod +x c_driver_siglip_chain.sh && "
    "(setsid nohup bash c_driver_siglip_chain.sh > logs/c_driver_siglip_chain.log 2>&1 < /dev/null &); sleep 3; "
    "echo chained; echo p24_queue=$(wc -l < logs/queue_p24.txt 2>/dev/null); "
    "echo p24_results=$(find outputs/c_prereg_b16 outputs/c_prereg_openclip -name results.json 2>/dev/null | wc -l); "
    "echo siglip_chain=$(ps aux | grep -c '[c]_driver_siglip_chain')" % REMOTE, timeout=180)
print(stdout.read().decode("utf-8", "replace").strip())
c.close()
