# -*- coding: utf-8 -*-
r"""上传单个文件到云端并启动（2026-10-09）。

    $env:CLOUD_PW='...'; python tools\_cloud_push_file.py <本地相对路径> [远端目录]
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

WORK = "/root/autodl-tmp/work"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    local = REPO / sys.argv[1]
    remote_dir = sys.argv[2] if len(sys.argv) > 2 else f"{WORK}/tools"
    remote = f"{remote_dir.rstrip('/')}/{local.name}"

    from _cloud_ssh import client

    c = client()
    try:
        run_ = c.exec_command(f"mkdir -p {remote_dir}")[1].read()
        sftp = c.open_sftp()
        sftp.put(str(local), remote)
        st = sftp.stat(remote)
        sftp.close()
        print(f"  ✅ 已上传 {local.name} → {remote}（{st.st_size:,} B）")
        out = c.exec_command(f"ls -la {remote} && head -3 {remote}")[1].read()
        print("  远端核对:")
        for ln in out.decode("utf-8", "replace").splitlines()[:5]:
            print("    " + ln[:120])
        # 上传 tools/ 下依赖的公共模块（_cloud_ssh 不需要，但脚本可能要）
        for extra in ("tools/_p56_add_seeds.py", "tools/_p58_gamma_clip.py"):
            p = REPO / extra
            if p.exists() and p.name != local.name:
                sftp = c.open_sftp()
                try:
                    sftp.put(str(p), f"{WORK}/{extra}")
                except Exception:
                    pass
                sftp.close()
    finally:
        c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
