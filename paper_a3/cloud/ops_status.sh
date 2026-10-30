#!/bin/bash
cd /root/autodl-tmp/a3
echo "l14_done: $(ls runs/cloud_l14/*.json 2>/dev/null | wc -l) / 48"
echo "full_done: $(ls runs/cloud_fullcorpus/*.json 2>/dev/null | wc -l) / 12"
echo "--- suite log tail ---"
tail -7 logs/suite.log
echo "--- gpu ---"
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
df -h /root/autodl-tmp | tail -1
