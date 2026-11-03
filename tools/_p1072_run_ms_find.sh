#!/usr/bin/env bash
# Run the ModelScope repository probe on the host.
set -uo pipefail
export PYTHONIOENCODING=utf-8
cd /root/p3
/root/miniconda3/bin/python /root/p3/tools/_p1071_modelscope_find.py 2>&1 | grep -vE "^\s*$|Downloading|%\|" | head -60
echo MS_FIND_DONE
