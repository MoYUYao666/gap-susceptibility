#!/bin/bash
BASE=/root/autodl-tmp/p3work
rm -rf /root/autodl-tmp/hf/hub/models--llava-hf--llava-1.5-7b-hf
rm -rf $BASE/models/llava-hf
rm -rf /root/p3/data /root/p3/outputs /root/p3/coco_eval /root/p3/flickr30k
rm -rf /root/autodl-tmp/hf/hub/models--Qwen--Qwen2-VL-2B-Instruct
rm -f $BASE/cloud_upload.zip
mkdir -p $BASE/models
ln -sfn /root/autodl-tmp/ms/models/llava-hf--llava-1.5-7b-hf/snapshots/master $BASE/models/llava-hf
df -h /root/autodl-tmp | tail -1
du -sh /root/autodl-tmp/ms $BASE/models/llava-hf /root/autodl-tmp/p3work 2>/dev/null
echo CLEAN_DONE
