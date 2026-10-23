# -*- coding: utf-8 -*-
"""Download Dolly-15k and convert it to the instruction parquet schema used by run_training.py (D4)."""
import io
import json
import os

import pandas as pd

OUT = "paper3/train-dolly-00000.parquet"
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HOME", "/root/autodl-tmp/hf")


def main() -> int:
    from huggingface_hub import snapshot_download
    p = snapshot_download("databricks/databricks-dolly-15k",
                          allow_patterns=["*.jsonl", "*.json"],
                          local_dir="/root/autodl-tmp/p3work/dolly")
    f = None
    for name in os.listdir(p):
        if name.endswith(".jsonl"):
            f = os.path.join(p, name)
            break
    assert f, "no jsonl"
    rows = []
    for line in io.open(f, encoding="utf-8"):
        d = json.loads(line)
        instr = d.get("instruction", "")
        ctx = d.get("context", "")
        if ctx:
            instr = instr + "\n\n" + ctx
        rows.append({"instruction": instr, "output": d.get("response", "")})
    df = pd.DataFrame(rows)
    df.to_parquet(OUT)
    print("wrote", OUT, len(df))


if __name__ == "__main__":
    raise SystemExit(main())
