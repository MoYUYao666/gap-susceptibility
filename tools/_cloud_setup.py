# -*- coding: utf-8 -*-
r"""云端 setup：上传代码 → 装依赖 → 下载模型（2026-10-09）。

**分步可重入**（每步先查再动）：

    $env:CLOUD_PW='...'; python tools\_cloud_setup.py --step check
    $env:CLOUD_PW='...'; python tools\_cloud_setup.py --step upload
    $env:CLOUD_PW='...'; python tools\_cloud_setup.py --step deps
    $env:CLOUD_PW='...'; python tools\_cloud_setup.py --step models
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", required=True,
                    choices=["check", "upload", "deps", "models", "data"])
    a = ap.parse_args()

    from _cloud_ssh import client, run, sftp_put_dir

    c = client()
    try:
        run(c, f"mkdir -p {WORK}", quiet=True)

        if a.step == "check":
            print("=== 已装包 ===")
            run(c, f"{PY} -m pip list 2>/dev/null | grep -iE "
                   "'^(torch|transformers|peft|numpy|pillow|tqdm|accelerate|bitsandbytes|modelscope) ' "
                   "| sort")
            run(c, f"{PY} -c \"import torch;print('torch', torch.__version__, "
                   "'cuda', torch.cuda.is_available())\" 2>&1 | tail -2")

        elif a.step == "upload":
            print("=== 上传 cloud_pack（仅代码）===")
            n = sftp_put_dir(c, REPO / "cloud_pack", WORK)
            print(f"  ✅ {n} 个文件 → {WORK}")
            run(c, f"ls {WORK} | head -20")
            run(c, f"du -sh {WORK}")

        elif a.step == "deps":
            print("=== 安装依赖（后台，含日志）===")
            # 先装 torch（若缺），再装其余；用 hf-mirror 加速
            cmd = (f"cd {WORK} && export HF_ENDPOINT=https://hf-mirror.com && "
                   f"export HF_HUB_DISABLE_XET=1 && "
                   f"nohup {PY} -m pip install -q torch torchvision transformers peft "
                   f"accelerate bitsandbytes pillow numpy tqdm scipy modelscope "
                   f"> outputs_pip.log 2>&1 & echo started")
            run(c, cmd)
            print("  ✅ 已在后台安装；用 --step check 复查")

        elif a.step == "models":
            print("=== 下载模型（服务器端，ModelScope 优先）===")
            script = f'''
import os
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.makedirs("models", exist_ok=True)
targets = [
    ("openai/clip-vit-base-patch32", "models/clip-vit-base-patch32"),
    ("openai/clip-vit-base-patch16", "models/clip-vit-base-patch16"),
    ("laion/CLIP-ViT-B-32-laion2B-s34B-b79K", "models/openclip"),
]
try:
    from modelscope import snapshot_download as ms_dl
except Exception:
    ms_dl = None
from huggingface_hub import snapshot_download as hf_dl
for repo, dst in targets:
    if os.path.isdir(dst) and os.listdir(dst):
        print("SKIP exists", dst); continue
    ok = False
    if ms_dl:
        for mid in (repo, repo.replace("openai/", "AI-ModelScope/"),
                    "AI-ModelScope/" + repo.split("/")[-1]):
            try:
                ms_dl(mid, local_dir=dst, ignore_file_pattern=[r".*\\.msgpack$", r".*\\.h5$"])
                print("OK ms", mid, "->", dst); ok = True; break
            except Exception as e:
                print("ms fail", mid, str(e)[:90])
    if not ok:
        try:
            hf_dl(repo, local_dir=dst,
                  ignore_patterns=["*.msgpack", "*.h5", "flax_model.*", "tf_model.*"])
            print("OK hf", repo, "->", dst); ok = True
        except Exception as e:
            print("hf fail", repo, str(e)[:90])
    if not ok:
        print("FAILED", repo)
print("done")
'''
            Path(REPO / "tools" / "_cloud_models.py").write_text(script, encoding="utf-8")
            n = sftp_put_dir(c, REPO / "tools", f"{WORK}/tools")
            run(c, f"cd {WORK} && {PY} tools/_cloud_models.py 2>&1 | tail -14", timeout=1800)

        elif a.step == "data":
            print("=== 数据：Flickr30k（服务器端取）===")
            run(c, f"mkdir -p {WORK}/flickr30k && ls {WORK}/flickr30k | head -5")

    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
