#!/usr/bin/env bash
# A1 补种子：先重下 ImageNet 50k 分片，再串行跑剂量-响应的两个额外种子 + 早停第二种子。
# 用法（后台运行）：
#   bash tools/a1_supplement_seeds.sh > a1_supplement.log 2>&1 &
# GPU 严格串行：本脚本一次只跑一个 python 进程。
set -u
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1
PY="${PY:-/d/Anaconda/envs/pytorch/python.exe}"
LOG_PREFIX="[$(date '+%F %H:%M:%S')]"

say() { echo; echo "===== $LOG_PREFIX $* ====="; }

say "检查 ImageNet 50k 分片"
N=$(ls data/imagenet_hf/*.parquet 2>/dev/null | wc -l)
echo "  现有分片: $N / 14"
if [ "$N" -lt 14 ]; then
  say "尝试重下（先走 hf-mirror，失败再试直连；门控数据集，本机有 hf token）"
  for EP in "https://hf-mirror.com" "https://huggingface.co"; do
    echo "--- endpoint: $EP"
    HF_ENDPOINT="$EP" HF_HUB_DISABLE_XET=1 "$PY" - <<'PY'
import os, sys
try:
    from huggingface_hub import snapshot_download
    p = snapshot_download('imagenet-1k', repo_type='dataset',
                          allow_patterns=['data/*.parquet'],
                          local_dir='data/imagenet_hf')
    print('  下载完成 ->', p)
except Exception as e:
    print('  失败:', type(e).__name__, str(e)[:200])
    sys.exit(3)
PY
    [ $? -eq 0 ] && break
  done
  N=$(ls data/imagenet_hf/*.parquet 2>/dev/null | wc -l)
  [ "$N" -lt 14 ] && {
    say "分片仍未就绪（$N/14）→ 训练已跳过。"
    echo "  需要手动重下 14 个 parquet 分片（≈6.4 GB）到 data/imagenet_hf/："
    echo "  · 迅雷/浏览器（当初就是这么下的；gated 数据集直链可能 401/403）"
    echo "  · 或在能连 HF 的网络下：HF_ENDPOINT=https://hf-mirror.com python -c \"from huggingface_hub import snapshot_download; snapshot_download('imagenet-1k', repo_type='dataset', allow_patterns=['data/*.parquet'], local_dir='data/imagenet_hf')\""
    echo "  · 放好后重跑本脚本即可自动补种子"
    exit 3; }
fi
echo "  分片就绪: $(ls data/imagenet_hf/*.parquet | wc -l) 个"

say "开始补种子（4 个 λ × 2 个 seed = 8 次训练；GPU 串行）"
for lam in 0 0.1 0.5 1.0; do
  for seed in 123 456; do
    if [ -f "outputs/a1_class_aligned/lr$lam/seed$seed/eval_epoch10.json" ]; then
      echo "  跳过 λ=$lam seed=$seed（已有 eval_epoch10.json）"
      continue
    fi
    echo "--- $(date '+%H:%M:%S') 训练 λ=$lam seed=$seed"
    "$PY" tools/train_class_aligned.py --lambda-reg "$lam" --seed "$seed" || {
      echo "  λ=$lam seed=$seed 训练失败，继续下一个"; continue; }
    echo "--- $(date '+%H:%M:%S') 端点评测 λ=$lam seed=$seed (epoch 10)"
    "$PY" tools/train_class_aligned.py --eval-only --epoch 10 --lambda-reg "$lam" --seed "$seed" \
      || echo "  端点评测失败"
  done
done

say "早停表的第二/第三个种子（λ=0，逐 epoch 1/2/3/5/10）"
for seed in 123 456; do
  for ep in 1 2 3 5 10; do
    f="outputs/a1_class_aligned/lr0/seed$seed/eval_epoch$ep.json"
    [ -f "$f" ] && { echo "  跳过 λ=0 seed=$seed ep=$ep"; continue; }
    echo "--- $(date '+%H:%M:%S') 评测 λ=0 seed=$seed ep=$ep"
    "$PY" tools/train_class_aligned.py --eval-only --epoch "$ep" --lambda-reg 0 --seed "$seed" \
      || echo "  评测失败 ep=$ep"
  done
done

say "完成；汇总各配置的端点结果"
for lam in 0 0.1 0.5 1.0; do
  for seed in 123 456; do
    f="outputs/a1_class_aligned/lr$lam/seed$seed/eval_epoch10.json"
    [ -f "$f" ] && echo "  λ=$lam seed=$seed: $(cat "$f")"
  done
done
echo
echo "===== 结束 $(date '+%F %H:%M:%S') ====="
