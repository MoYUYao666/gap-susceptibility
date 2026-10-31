#!/bin/bash
pkill -f run_cloud_suite.py || true
pkill -f train_lora_provenance.py || true
sleep 4
ps aux | grep -c "train_lora_provenance" || true
nvidia-smi --query-gpu=memory.used --format=csv,noheader
echo KILLED
