import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_DISABLE_XET'] = '1'
from huggingface_hub import snapshot_download
p = snapshot_download('Qwen/Qwen2-VL-2B-Instruct', local_dir='models/Qwen2-VL-2B-Instruct')
print('DONE ->', p)
