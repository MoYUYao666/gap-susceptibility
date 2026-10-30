# P3 cloud runbook (VQA downstream + second-environment reproducibility)

> Purpose: finish the two items that need either more compute or a different machine:
> **(A) VQA-RAD downstream check** (R2.3 / R3.16 / R3.23) and **(B) a second-environment reproducibility run**
> (R3.18).
> Local smoke tests must pass before this runbook is used (see §0).
> Uploaded pack: `cloud_p3/` (code only; models and data are downloaded on the instance).

## 0. Local smoke tests (already required before upload)

```powershell
# 1) VQA pipeline: base eval on 4 held-out questions, and one tiny trained arm
python tools/_p1516_p3_vqa_downstream.py --rank base --eval-n 4
python tools/_p1516_p3_vqa_downstream.py --rank 5 --train-samples 12 --epochs 1 --eval-n 4
# 2) baseline-rule probe (already run): probe-smoke + arms
python tools/_p1514_p3_baseline_rules.py --probe-smoke
```

## 1. Instance layout

```bash
mkdir -p /root/autodl-tmp/p3/{models,data,paper3/scripts,tools,outputs/analysis,outputs/p3_vqa_adapters}
cd /root/autodl-tmp/p3
# from the local machine:
# scp -P <port> -r cloud_p3/* root@<host>:/root/autodl-tmp/p3/
```

## 2. Environment

```bash
pip install -q -i https://pypi.tuna.tsinghua.edu.cn/simple torch torchvision transformers peft bitsandbytes pandas pillow
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf
export HF_HUB_DISABLE_XET=1
```

## 3. Models and data (server-side download only)

```bash
python - <<'PY'
from huggingface_hub import snapshot_download
print(snapshot_download('llava-hf/llava-1.5-7b-hf', local_dir='/root/autodl-tmp/p3/models/llava-hf'))
print(snapshot_download('flaviagiammarino/vqa-rad', repo_type='dataset', local_dir='/root/autodl-tmp/p3/data/vqa_rad'))
PY
python tools/vqa_prepare.py
```

## 4. Run A: VQA-RAD downstream (R2.3/R3.16/R3.23)

```bash
python tools/vqa_downstream.py --rank base --eval-n 50
python tools/vqa_downstream.py --rank 5 --train-samples 200 --epochs 3 --eval-n 50
python tools/vqa_downstream.py --rank 6 --train-samples 200 --epochs 3 --eval-n 50
```

## 5. Run B: second-environment reproducibility (R3.18)

```bash
# same protocol as the local r=5/r=6 seed-42 runs
python paper3/scripts/run_training.py --rank 5 --seed 42 --epochs 3 --num-samples 20
python paper3/scripts/run_training.py --rank 6 --seed 42 --epochs 3 --num-samples 20
```

Compare the resulting `E` trajectories and `ΔE` with the local records
(`paper3/scripts/outputs/experiments/verify_r5_s42.json`, `..._r6_s42.json`). Record GPU model, CUDA and torch versions.

## 6. Retrieve results

```powershell
scp -P <port> -r root@<host>:/root/autodl-tmp/p3/outputs/analysis/p3_vqa_downstream_*.json outputs/analysis/
scp -P <port> -r root@<host>:/root/autodl-tmp/p3/paper3/scripts/outputs/experiments/*.json paper3/scripts/outputs/experiments/
```

## 7. Shutdown

`sync && shutdown -h now` after retrieval and verification (per the project's cloud shutdown rule).

## 8. Failure modes already handled

- `transformers` 5.x LLaVA + bitsandbytes: same versions as local (`transformers 5.16.1`, `torch 2.9.1+cu130` recommended
  but any 4-bit-capable stack works; record the actual versions).
- VQA parquet images are embedded bytes; `vqa_prepare.py` materialises PNGs.
- Do not upload model weights or datasets; download on the instance.
