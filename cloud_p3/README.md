# cloud_p3 pack — what to run on the AutoDL instance

Code only. Models and datasets are downloaded on the instance (never uploaded).

## Upload

```powershell
scp -P <port> -r cloud_p3/* root@<host>:/root/autodl-tmp/p3/
```

## Instance layout

```
/root/autodl-tmp/p3/
  run_training.py, run_training_qwen25.py, vqa_prepare.py, vqa_downstream.py,
  baseline_rules.py, hessian_probe.py, insert_baselines.py
  models/            # snapshot_download on the instance
  data/vqa_rad/      # snapshot_download on the instance
  paper3/scripts/    # put run_training.py here as paper3/scripts/run_training.py
  tools/             # vqa_prepare.py, vqa_downstream.py
  outputs/analysis, outputs/p3_vqa_adapters
```

## Run order

1. Environment: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple torch torchvision transformers peft
   bitsandbytes pandas pillow`; export `HF_ENDPOINT=https://hf-mirror.com`, `HF_HUB_DISABLE_XET=1`.
2. Download: `snapshot_download('llava-hf/llava-1.5-7b-hf', local_dir='models/llava-hf')`;
   `snapshot_download('flaviagiammarino/vqa-rad', repo_type='dataset', local_dir='data/vqa_rad')`.
3. `python tools/vqa_prepare.py` (materialises images and the two parquet files).
4. VQA downstream (200 training samples, 3 epochs, 50 held-out):
   `python tools/vqa_downstream.py --rank base --eval-n 50`
   `python tools/vqa_downstream.py --rank 5 --train-samples 200 --epochs 3 --eval-n 50`
   `python tools/vqa_downstream.py --rank 6 --train-samples 200 --epochs 3 --eval-n 50`
5. Second-environment reproducibility (R3.18):
   `python paper3/scripts/run_training.py --rank 5 --seed 42 --epochs 3 --num-samples 20`
   `python paper3/scripts/run_training.py --rank 6 --seed 42 --epochs 3 --num-samples 20`
6. Retrieve JSONs, verify, then `sync && shutdown -h now`.

Local smoke tests already passed: VQA base eval + tiny trained arm (`--train-samples 12 --epochs 1`), cloud pack compiles,
and the scripts are the same files used locally.
