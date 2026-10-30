# -*- coding: utf-8 -*-
r"""云端本地对照：**tokenizer 与 caption 编码**是否一致（2026-10-09）。

## 为何查这里

云端 `cosine_separation(init) = 0`（正负样本对余弦**完全相等**）+ `loss 末 = 4.81`
（= `log(128) = 4.852`，即**随机水平**）→ 强烈指向**caption 与图未正确配对**
或 **tokenizer 编码异常**。

    python tools\_p72_tok_probe.py
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

PROBE = r'''
import os, sys, json
os.chdir(r"""%(work)s""")
sys.path.insert(0, r"""%(work)s""")
from transformers import CLIPTokenizerFast
tk = CLIPTokenizerFast.from_pretrained(r"""%(model)s""", local_files_only=True)
ids = tk("a photo of a dog", return_tensors="pt")["input_ids"]
res = {
    "vocab_size": int(tk.vocab_size),
    "model_max_length": int(tk.model_max_length),
    "token_ids": ids.tolist()[0][:14],
    "n_tokens": int(ids.shape[1]),
}
# 数据集给出的 caption
from src.dataset import create_dataloaders
loader, _, _ = create_dataloaders(dataset_name="flickr30k", data_dir=".",
                                  batch_size=8, max_samples=200)
b = next(iter(loader))
res["caption_0"] = str(b["caption"][0])[:80]
res["input_ids_0"] = b["input_ids"][0].tolist()[:16]
res["input_ids_shape"] = list(b["input_ids"].shape)
res["attention_sum_0"] = int(b["attention_mask"][0].sum())
res["n_unique_captions_in_batch"] = len(set(str(c) for c in b["caption"]))
print(json.dumps(res, indent=1))
'''


def main() -> int:
    print("=== 本地 ===")
    io.open(REPO / "outputs" / "_tok_local.py", "w", encoding="utf-8",
            newline="\n").write(PROBE % {"work": str(REPO),
                                         "model": str(REPO / "models/clip-vit-base-patch32")})
    r = subprocess.run([sys.executable, str(REPO / "outputs" / "_tok_local.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=str(REPO), timeout=1800)
    print((r.stdout or "")[-1100:])
    if r.stderr:
        print("  stderr:", (r.stderr or "").strip()[-400:])

    print("\n=== 云端 ===")
    from _cloud_ssh import client, run
    c = client()
    try:
        io.open(REPO / "outputs" / "_tok_cloud.py", "w", encoding="utf-8",
                newline="\n").write(PROBE % {
                    "work": "/root/autodl-tmp/work",
                    "model": "/root/autodl-tmp/work/models/clip-vit-base-patch32"})
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_tok_cloud.py"),
                 "/root/autodl-tmp/work/_tok.py")
        sftp.close()
        run(c, "/root/miniconda3/bin/python /root/autodl-tmp/work/_tok.py", timeout=1800)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
