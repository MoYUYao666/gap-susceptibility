# -*- coding: utf-8 -*-
r"""Cloud execution helper for the current instance (host/port passed in; password read from CLOUD_PW).

The password is never written to a file. Typical use from PowerShell:

    $env:CLOUD_PW='...'
    python tools/_p1615_cloud_exec.py --host connect.westc.seetacloud.com --port 48647 --probe
    python tools/_p1615_cloud_exec.py --host ... --port ... --cmd "nvidia-smi"
    python tools/_p1615_cloud_exec.py --host ... --port ... --upload cloud_next /root/autodl-tmp/p3work/cloud_next
    python tools/_p1615_cloud_exec.py --host ... --port ... --download /root/autodl-tmp/p3work/outputs/analysis outputs/analysis
"""
from __future__ import annotations

import argparse
import os
import posixpath
import stat
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_HOST = os.environ.get("CLOUD_HOST", "connect.westc.seetacloud.com")
DEFAULT_PORT = int(os.environ.get("CLOUD_PORT", "0") or 0)


def client(host: str, port: int):
    import paramiko
    pw = os.environ.get("CLOUD_PW")
    if not pw:
        print("ERROR: set the CLOUD_PW environment variable (the password is never stored in a file)")
        sys.exit(2)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(host, port=port, username="root", password=pw, timeout=40,
              banner_timeout=40, auth_timeout=40)
    return c


def run(c, cmd: str, timeout: int = 900, quiet: bool = False):
    """Run one remote command. A backgrounded process can keep the channel open past the timeout, which is
    not a failure (the job was started) -- report it as 'still running' instead of raising."""
    import paramiko
    _in, out, err = c.exec_command(cmd, timeout=timeout)
    try:
        o = out.read().decode("utf-8", "replace")
        e = err.read().decode("utf-8", "replace")
    except Exception as exc:  # paramiko.buffered_pipe.PipeTimeout and friends
        print("  (channel still busy after %ss: %s -- assuming a background job was launched)" % (timeout, type(exc).__name__))
        return "", ""
    if not quiet:
        for ln in o.splitlines():
            print("  " + ln[:200])
        for ln in e.splitlines():
            if ln.strip():
                print("  ! " + ln[:200])
    return o, e


def upload(c, local: str, remote: str):
    sftp = c.open_sftp()

    def mkdirs(path):
        parts, cur = [p for p in path.split("/") if p], ""
        for p in parts:
            cur += "/" + p
            try:
                sftp.stat(cur)
            except IOError:
                sftp.mkdir(cur)

    src = Path(local)
    if src.is_file():
        mkdirs(posixpath.dirname(remote))
        sftp.put(str(src), remote)
        print("  uploaded %s -> %s" % (local, remote))
    else:
        for p in sorted(src.rglob("*")):
            rel = p.relative_to(src).as_posix()
            dst = posixpath.join(remote, rel)
            if p.is_dir():
                mkdirs(dst)
            else:
                mkdirs(posixpath.dirname(dst))
                sftp.put(str(p), dst)
        print("  uploaded tree %s -> %s" % (local, remote))
    sftp.close()


def download(c, remote: str, local: str):
    sftp = c.open_sftp()
    dst_root = Path(local)
    count = 0

    def walk(rpath, lpath):
        nonlocal count
        lpath.mkdir(parents=True, exist_ok=True)
        for entry in sftp.listdir_attr(rpath):
            r = posixpath.join(rpath, entry.filename)
            l = lpath / entry.filename
            if stat.S_ISDIR(entry.st_mode):
                walk(r, l)
            else:
                sftp.get(r, str(l))
                count += 1

    walk(remote, dst_root)
    sftp.close()
    print("  downloaded %d file(s): %s -> %s" % (count, remote, local))


def probe(c):
    print("== identity / hardware ==")
    run(c, "hostname; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader; "
           "python -V; df -h /root/autodl-tmp | tail -1")
    print("== workspace ==")
    run(c, "ls -d /root/autodl-tmp/p3work 2>/dev/null && du -sh /root/autodl-tmp/p3work 2>/dev/null; "
           "ls /root/autodl-tmp | head -20")
    print("== caches ==")
    run(c, "du -sh /root/autodl-tmp/hf /root/autodl-tmp/ms_cache 2>/dev/null; "
           "ls /root/autodl-tmp/hf/hub 2>/dev/null | head -20")
    print("== mirror probe (12 s) ==")
    run(c, "curl -sL -m 12 -o /dev/null -w 'hf-mirror %{speed_download} B/s\\n' "
           "https://hf-mirror.com/Qwen/Qwen2-VL-2B-Instruct/resolve/main/config.json; "
           "curl -sL -m 12 -o /dev/null -w 'modelscope %{speed_download} B/s\\n' "
           "'https://modelscope.cn/api/v1/models/Qwen/Qwen2-VL-2B-Instruct/repo?Revision=master&FilePath=config.json'")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--cmd", default=None)
    ap.add_argument("--cmd-file", default=None, help="run the contents of a local script on the instance")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--upload", nargs=2, metavar=("LOCAL", "REMOTE"))
    ap.add_argument("--download", nargs=2, metavar=("REMOTE", "LOCAL"))
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()
    if not a.port:
        print("ERROR: pass --port (AutoDL changes it on every start)")
        return 2
    c = client(a.host, a.port)
    try:
        if a.probe:
            probe(c)
        if a.upload:
            upload(c, a.upload[0], a.upload[1])
        if a.download:
            download(c, a.download[0], a.download[1])
        if a.cmd_file:
            cmd = Path(a.cmd_file).read_text(encoding="utf-8")
            run(c, cmd, timeout=a.timeout)
        elif a.cmd:
            run(c, a.cmd, timeout=a.timeout)
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())