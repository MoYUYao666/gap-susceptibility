# A3 cloud playbook (start machine -> run -> fetch -> shut down)

Purpose: run the two supplements that are too slow locally, then shut the machine down. Everything else is already
finished and frozen in the local repository.

## What runs

| phase | experiment | cells | expected wall time (RTX 4090, 2 workers) | expected cost |
|---|---|---|---|---|
| 1 | ViT-L/14 grid: 4 provenance arms x 2 corpora x 3 adaptation sites x 2 seeds | 48 | 60-90 min | about 2-4 RMB |
| 2 | full-corpus cells, 3 seeds: human + metadata x 2 corpora, joint site | 12 | 40-60 min | about 2-3 RMB |
| 3 | optional: GeoRSCLIP L/14 human vs metadata, 8 cells | 8 | 20-30 min | about 1 RMB |

All cells write one JSON record each and are resumable: a cell whose JSON exists is skipped.

## Machine requirements

- one GPU with >= 24 GB VRAM (4090 / A5000 / A100), CUDA 12 image with PyTorch 2.x;
- >= 60 GB free on the data disk (we keep datasets and outputs there);
- internet access to `hf-mirror.com` (measured 30-40 MB/s on AutoDL hosts).

## Sequence (Lead executes, not the operator)

```bash
# 0. environment
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple open_clip_torch peft pyarrow pandas
# torch/torchvision are expected in the image; if not: pip install torch torchvision (CUDA 12 wheel)

# 1. weights (three checkpoints, about 2.9 GB total)
python fetch_weights.py            # RemoteCLIP B/32 + L/14, GeoRSCLIP B/32
# 2. datasets (parquet from the mirror, about 1.3 GB) and conversion to images + annotation JSONL
python bootstrap_data.py           # downloads parquet, runs convert_rsicd.py and convert_nwpu.py
# 3. corpora (provenance arms + human-rich), deterministic from the annotation JSONL
python build_corpora.py
# 4. experiments (parallel, resumable)
python run_cloud_suite.py --run --workers 2 --phases l14,fullcorpus
# 5. fetch results to the local machine
tar czf runs_cloud_$(date +%m%d).tgz runs/
# 6. verify locally, merge into the manuscript, then shut the machine down
```

## Fetching results

From the local machine:

```bash
scp -P <port> root@<host>:/root/autodl-tmp/a3/runs_cloud_*.tgz .
tar xzf runs_cloud_*.tgz -C paper_a3/
python paper_a3/scripts/analyse_cloud_runs.py    # produces the tables/macros for the robustness section
```

## Shutdown rule (repository rule, mandatory)

Only after (a) every process exited, (b) the assertions in `run_cloud_suite.py --verify` pass, (c) the run JSONs are
copied back and their file sizes checked. Then:

```bash
sync; shutdown -h now
```

and record "shut down at <time>" in `HANDOFF.md`. If the container cannot shut down, report that the operator must stop
the instance in the AutoDL console - never claim it was shut down when it was not.

## Cost guard

The suite prints elapsed time and the number of finished cells; if phase 1 exceeds 2.5 hours, stop it, copy the finished
cells back and analyse those (the grid is resumable, so nothing is lost). Total spend target: below 10 RMB.
