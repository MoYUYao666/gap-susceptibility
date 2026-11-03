# -*- coding: utf-8 -*-
r"""云端：7B 下载的**进度监控 + 补段重试**（2026-10-09）。

## 观察到的问题

40 个分段（5 shard × 8 段）**进度不均**：有的段已满、有的很慢 →
整体 3.0 GB / 15.5 GB（约 0.5 MB/s）。

## 本脚本

1. **报告每个分段的字节数**（找出慢段）；
2. 对**明显落后**的段**重新发起**（不重复下载已满的）；
3. 全部满后**按序合并**并校验总长。

    $env:CLOUD_PW='...'; python tools\_cloud_7b_monitor.py [--fix]
"""
from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

REMOTE = r'''
import os, json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
os.chdir("/root/autodl-tmp/work")
M = "https://hf-mirror.com/Qwen/Qwen2-VL-7B-Instruct/resolve/main"
DST = "models/qwen2vl7b"
PAR = 8

idx = json.load(open(os.path.join(DST, "model.safetensors.index.json")))
shards = sorted(set(idx["weight_map"].values()))

def total_len(url):
    r = subprocess.run(["curl", "-sL", "-I", "--max-time", "40", url],
                       capture_output=True, text=True)
    for ln in (r.stdout or "").splitlines():
        if ln.lower().startswith("content-length:"):
            try: return int(ln.split(":")[1].strip())
            except Exception: pass
    return 0

print("=== 各 shard 分段进度 ===")
todo = []
for sh in shards:
    dst = os.path.join(DST, sh)
    if os.path.exists(dst) and os.path.getsize(dst) > 100e6:
        print("  ✅ %s 已完成 %d B" % (sh, os.path.getsize(dst)))
        continue
    url = "%s/%s" % (M, sh)
    tot = total_len(url)
    parts = []
    for i in range(PAR):
        p = "%s.tmp.p%d" % (dst, i)
        parts.append(os.path.getsize(p) if os.path.exists(p) else 0)
    chunk = tot // PAR + 1 if tot else 0
    have = sum(parts)
    print("  %s 总=%d 已有=%d (%.1f%%) 分段=%s"
          % (sh, tot, have, 100.0*have/max(tot,1), parts))
    if tot and have < tot * 0.999:
        todo.append((sh, url, tot, chunk, parts))

print("\n=== 需补: %d shard ===" % len(todo))
if "--fix" in sys.argv and todo:
    def fetch(sh, url, tot, chunk, i):
        a = i * chunk
        b = min(a + chunk - 1, tot - 1)
        if a >= tot: return
        p = "%s.tmp.p%d" % (os.path.join(DST, sh), i)
        cur = os.path.getsize(p) if os.path.exists(p) else 0
        need = b - a + 1 - cur
        if need <= 0: return
        # 续传该段（-C - 需从偏移开始 → 用 -r 精确区间重下更简单）
        subprocess.run(["curl", "-sL", "--retry", "8", "--retry-delay", "2",
                        "--max-time", "7200", "-r", "%d-%d" % (a, b), "-o", p, url],
                       capture_output=True)
    jobs = []
    for sh, url, tot, chunk, parts in todo:
        for i in range(PAR):
            a = i * chunk
            if a >= tot: break
            b = min(a + chunk - 1, tot - 1)
            got = parts[i] if i < len(parts) else 0
            if got < (b - a + 1) * 0.999:
                jobs.append((sh, url, tot, chunk, i))
    print("  重发 %d 个段" % len(jobs))
    with ThreadPoolExecutor(max_workers=min(40, len(jobs) or 1)) as ex:
        list(ex.map(lambda t: fetch(*t), jobs))
    print("  补段完成")

    # 合并
    for sh, url, tot, chunk, parts in todo:
        dst = os.path.join(DST, sh)
        tmp = dst + ".tmp"
        with open(tmp, "wb") as out:
            for i in range(PAR):
                p = "%s.p%d" % (tmp, i)
                if os.path.exists(p):
                    with open(p, "rb") as fp:
                        while True:
                            b = fp.read(8 << 20)
                            if not b: break
                            out.write(b)
                    os.remove(p)
        got = os.path.getsize(tmp)
        if got >= tot * 0.999:
            os.replace(tmp, dst)
            print("  ✅ 合并 %s %d/%d" % (sh, got, tot))
        else:
            print("  ⚠️ %s %d/%d 不足" % (sh, got, tot))
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    a = ap.parse_args()

    from _cloud_ssh import client, run

    c = client()
    try:
        io.open(REPO / "outputs" / "_remote_7bm.py", "w", encoding="utf-8",
                newline="\n").write(REMOTE)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_7bm.py"), f"{WORK}/_7bm.py")
        sftp.close()
        cmd = f"{PY} {WORK}/_7bm.py" + (" --fix" if a.fix else "")
        run(c, cmd, timeout=7200 if a.fix else 600)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
