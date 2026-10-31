# -*- coding: utf-8 -*-
r"""云端 SSH 工具（2026-10-09）。

## 凭据处理（**安全**）

**密码不写入任何文件**——从**环境变量** `CLOUD_PW` 读取：
```powershell
$env:CLOUD_PW='...'; python tools\_cloud_ssh.py --cmd "nvidia-smi"
```
**且日志输出会过滤密码**（`channels.py` 里也确保不打屏）。

## 用法

```powershell
python tools\_cloud_ssh.py --probe                    # 探明实例环境
python tools\_cloud_ssh.py --cmd "nvidia-smi"         # 跑一条命令
python tools\_cloud_ssh.py --upload cloud_pack /root/autodl-tmp/work   # 上传目录
python tools\_cloud_ssh.py --script tools/_p56_add_seeds.py          # 上传并后台跑
```
"""
from __future__ import annotations

import argparse
import io
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOST = "connect.westb.seetacloud.com"
PORT = 45736
USER = "root"


def client():
    import paramiko
    pw = os.environ.get("CLOUD_PW")
    if not pw:
        print("  ❌ 未设置环境变量 CLOUD_PW（密码不写入文件）")
        sys.exit(2)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=pw, timeout=30,
              banner_timeout=30, auth_timeout=30)
    return c


def run(c, cmd: str, timeout: int = 600, quiet: bool = False):
    stdin, stdout, stderr = c.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    if not quiet:
        for ln in out.splitlines():
            print("  " + ln[:160])
        for ln in err.splitlines():
            if ln.strip():
                print("  ! " + ln[:160])
    return out, err


def sftp_put_dir(c, local: Path, remote: str):
    """递归上传目录（保留相对结构）。"""
    sftp = c.open_sftp()
    n = 0
    for f in local.rglob("*"):
        if f.is_file():
            rel = f.relative_to(local).as_posix()
            dst = f"{remote.rstrip('/')}/{rel}"
            d = os.path.dirname(dst)
            try:
                sftp.stat(d)
            except IOError:
                parts = d.split("/")
                for i in range(2, len(parts) + 1):
                    sub = "/".join(parts[:i])
                    try:
                        sftp.stat(sub)
                    except IOError:
                        try:
                            sftp.mkdir(sub)
                        except IOError:
                            pass
            sftp.put(str(f), dst)
            n += 1
    sftp.close()
    return n



def bg(c, cmd: str, log: str, cwd: str = "/root/autodl-tmp/work") -> None:
    """**正确脱离**地后台运行：`setsid` + 三流重定向 → paramiko 不再阻塞。

    实测教训：只用 `nohup ... &` 时后台进程仍持有 stdout 的 fd，
    `stdout.read()` 会**等到通道关闭**（`PipeTimeout`）。
    """
    full = (f"cd {cwd} && setsid nohup {cmd} < /dev/null > {log} 2>&1 & "
            f"disown; sleep 1; echo started")
    stdin, stdout, stderr = c.exec_command(full, timeout=60)
    try:
        out = stdout.read().decode("utf-8", "replace").strip()
    except Exception:
        out = "(detached)"
    print(f"  {out or '(detached)'}")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--cmd")
    ap.add_argument("--upload", nargs=2, metavar=("LOCAL", "REMOTE"))
    ap.add_argument("--script")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args()

    c = client()
    try:
        if a.probe:
            print("=== 实例探测 ===")
            run(c, "hostname; whoami; pwd")
            run(c, "nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader")
            run(c, "python -c 'import torch,transformers;print(torch.__version__, transformers.__version__)' 2>&1 | tail -2")
            run(c, "df -h /root | tail -1")
            run(c, "ls -la /root/autodl-tmp/ 2>&1 | head -12")
            run(c, "ls /root/autodl-tmp/work 2>&1 | head -12")
        elif a.cmd:
            run(c, a.cmd, timeout=a.timeout)
        elif a.upload:
            local, remote = a.upload
            n = sftp_put_dir(c, Path(local), remote)
            print(f"  ✅ 上传 {n} 个文件 → {remote}")
        elif a.script:
            p = Path(a.script)
            print(f"  上传并后台运行 {p.name}")
            n = sftp_put_dir(c, p.parent, "/root/autodl-tmp/work/tools_upload")
            run(c, f"cp -r /root/autodl-tmp/work/tools_upload/* /root/autodl-tmp/work/ && rm -rf /root/autodl-tmp/work/tools_upload")
            print(f"  （已传 {n} 个文件并合并到 work/）")
        else:
            print("  请指定 --probe / --cmd / --upload / --script")
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
