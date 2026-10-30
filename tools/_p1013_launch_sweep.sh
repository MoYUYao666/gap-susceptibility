#!/usr/bin/env bash
# Start the guarded sweep in the background and record its exit status, all from one script file.
#
# Writing the launcher locally and running it remotely avoids the quoting problems of building a remote
# command line through PowerShell (which has broken several attempts today) and the stale-file problem that
# made an upload fail (`cmd.sh` already existed on the host).
#
# The disk problem is fixed first: on 2026-10-16 11:44 the root filesystem hit 100% and the epoch
# checkpoint write died with ENOSPC, which ended the sweep with nothing in the log (the log lives on the
# same full filesystem). The checkpoints and the old logs are removed before starting, which took the root
# filesystem from 30 G used to 5.5 G.
set -uo pipefail
cd /root/p3
LOG=/root/p3/sweep_run.log
rm -f "$LOG"

echo "=== disk before starting ==="
df -h / | tail -1

echo "=== sweep version checks ==="
grep -c "_arm_guard" tools/_p820_llava_sites.py
grep -c "ipc_collect" tools/_p820_llava_sites.py

echo "=== records on disk (these are skipped) ==="
ls outputs/llava_bf16_sites/*.json 2>/dev/null | xargs -n1 basename

setsid bash -c 'bash /root/p3/_p1012_cloud_sweep_guarded.sh >> /root/p3/sweep_run.log 2>&1; echo "EXIT=$?" >> /root/p3/sweep_run.log' < /dev/null > /dev/null 2>&1 &
disown
sleep 25
echo "--- started; sweep_run.log so far ---"
tail -16 "$LOG" 2>/dev/null || echo "no log yet"
echo "--- processes ---"
pgrep -af '_p1012|_p820_llava_sites' | head -3 || echo "none"
echo LAUNCH_DONE
