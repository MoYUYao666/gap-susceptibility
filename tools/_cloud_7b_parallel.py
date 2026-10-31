# -*- coding: utf-8 -*-
r"""云端：**并行下载 7B 权重**（分片 × 分段，绕开单连接限速）（2026-10-09）。

## 实测问题

单连接 `curl` 下载 7B shard：**0.24 MB/s** → 15.5 GB 需 **18 h**。
但并行分段实测可达 **0.9–3 MB/s** → 用 **shard 并行 × shard 内分段**。

## 设计

- **5 个 shard 同时**下载（每个 shard 再分 8 段）→ 共 **40 个连接**；
- 每个 shard 写 `.tmp`，**校验字节数**后改名（防半截文件）；
- 断点续传：已完整的 shard 直接跳过；未完成的**重新下该 shard**（分段并行比重连续传简单可靠）。

    $env:CLOUD_PW='...'; python tools\_cloud_7b_parallel.py
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))
PY = "/root/miniconda3/bin/python"
WORK = "/root/autodl-tmp/work"

PY_SCRIPT = r'''
import os, subprocess, sys, time, json, math
from concurrent.futures import ThreadPoolExecutor
os.chdir("/root/autodl-tmp/work")

M = "https://hf-mirror.com/Qwen/Qwen2-VL-7B-Instruct/resolve/main"
DST = "models/qwen2vl7b"
os.makedirs(DST, exist_ok=True)

def log(m):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    with open("outputs_7b.log", "a") as f:
        f.write(line + "\n")

def head_len(url):
    """真实长度：GET 首字节 + size_download（跟随重定向）"""
    r = subprocess.run(["curl", "-sL", "-o", "/dev/null", "--max-time", "40",
                        "-w", "%{size_download}", "-r", "0-0", url],
                       capture_output=True, text=True)
    try:
        return int((r.stdout or "0").strip())
    except Exception:
        return 0

def seg(url, a, b, out):
    subprocess.run(["curl", "-sL", "--retry", "6", "--retry-delay", "2",
                    "--max-time", "5400", "-r", "%d-%d" % (a, b), "-o", out, url],
                   capture_output=True)

def dl_shard(shard, par=8):
    url = "%s/%s" % (M, shard)
    dst = os.path.join(DST, shard)
    if os.path.exists(dst) and os.path.getsize(dst) > 100e6:
        log("SKIP %s (%d B)" % (shard, os.path.getsize(dst)))
        return dst
    # 用 HEAD 拿长度不可靠（返回重定向页），故先取 index 里声明的 size
    try:
        idx = json.load(open(os.path.join(DST, "model.safetensors.index.json")))
        # index 不含 size，改用 curl -I 跟随重定向
    except Exception:
        pass
    r = subprocess.run(["curl", "-sL", "-o", "/dev/null", "--max-time", "40",
                        "-w", "%{size_download}", "-r", "0-0", url],
                       capture_output=True, text=True)
    total = 0
    # 用 --head 跟随重定向拿 Content-Length（此次 -L 会跟到 CDN，返回真实长度）
    r2 = subprocess.run(["curl", "-sL", "-I", "--max-time", "40", url],
                        capture_output=True, text=True)
    for ln in (r2.stdout or "").splitlines():
        if ln.lower().startswith("content-length:"):
            try:
                total = int(ln.split(":")[1].strip())
            except Exception:
                pass
    if total < 100e6:
        log("  %s: 拿不到长度(%d) → 单连接 retry" % (shard, total))
        subprocess.run(["curl", "-sL", "--retry", "8", "-C", "-", "-o", dst, url],
                       capture_output=True)
        log("  %s → %d B" % (shard, os.path.getsize(dst) if os.path.exists(dst) else 0))
        return dst

    tmp = dst + ".tmp"
    chunk = total // par + 1
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=par) as ex:
        futs = []
        for i in range(par):
            a = i * chunk
            b = min(a + chunk - 1, total - 1)
            if a >= total:
                break
            futs.append(ex.submit(seg, url, a, b, "%s.p%d" % (tmp, i)))
        for f in futs:
            f.result()
    # 按序合并
    with open(tmp, "wb") as out:
        for i in range(par):
            p = "%s.p%d" % (tmp, i)
            if os.path.exists(p):
                with open(p, "rb") as fp:
                    while True:
                        buf = fp.read(8 << 20)
                        if not buf:
                            break
                        out.write(buf)
                os.remove(p)
    got = os.path.getsize(tmp) if os.path.exists(tmp) else 0
    dt = time.time() - t0
    if got >= total * 0.999:
        os.replace(tmp, dst)
        log("  ✅ %s %d/%d in %.0fs (%.2f MB/s)" % (shard, got, total, dt, got/1e6/max(dt,1)))
    else:
        log("  ⚠️ %s %d/%d 不足，保留 .tmp" % (shard, got, total))
    return dst

log("=" * 60)
log("并行下载 7B（5 shard 同时，每 shard 8 段）")

# 小文件
for f in ("config.json", "preprocessor_config.json", "tokenizer.json",
          "tokenizer_config.json", "vocab.json", "merges.txt",
          "generation_config.json", "model.safetensors.index.json"):
    p = os.path.join(DST, f)
    if not os.path.exists(p) or os.path.getsize(p) < 50:
        subprocess.run(["curl", "-sL", "--max-time", "180", "-o", p, "%s/%s" % (M, f)],
                       capture_output=True)

try:
    idx = json.load(open(os.path.join(DST, "model.safetensors.index.json")))
    shards = sorted(set(idx["weight_map"].values()))
except Exception as e:
    log("❌ index 读取失败: %s" % str(e)[:120]); sys.exit(1)
log("shards: %s" % shards)

t_all = time.time()
with ThreadPoolExecutor(max_workers=len(shards)) as ex:
    list(ex.map(dl_shard, shards))
log("全部完成，用时 %.0f min" % ((time.time()-t_all)/60))

# 校验
big = [f for f in os.listdir(DST) if f.endswith(".safetensors")
       and os.path.getsize(os.path.join(DST, f)) > 100e6]
log("完整 shard: %d / %d ｜ 合计 %.1f GB"
    % (len(big), len(shards), sum(os.path.getsize(os.path.join(DST, f)) for f in big)/1e9))
log("SEVENBDONE")
'''


def main() -> int:
    from _cloud_ssh import bg, client, run

    c = client()
    try:
        # 停掉慢的串行下载（保留已下部分）
        run(c, "pkill -f _probe7b; sleep 2; echo stopped", timeout=60)
        # 关掉之前的禁用 xet 环境（不影响并行 curl）
        io.open(REPO / "outputs" / "_remote_7bp.py", "w", encoding="utf-8",
                newline="\n").write(PY_SCRIPT)
        sftp = c.open_sftp()
        sftp.put(str(REPO / "outputs" / "_remote_7bp.py"), f"{WORK}/_7bp.py")
        sftp.close()
        print("=== 启动并行 7B 下载（脱离运行）===")
        bg(c, f"{PY} _7bp.py", "outputs_7b.log")
        run(c, "sleep 30; cd /root/autodl-tmp/work && tail -5 outputs_7b.log", timeout=120)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
