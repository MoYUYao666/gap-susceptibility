# -*- coding: utf-8 -*-
"""Print the cloud environment facts the run depends on."""
import os, shutil, subprocess, sys

def line(label, value):
    print("%-22s %s" % (label + ":", value))

line("python", sys.version.split()[0])
line("executable", sys.executable)
try:
    import torch
    line("torch", torch.__version__)
    line("cuda available", torch.cuda.is_available())
    if torch.cuda.is_available():
        line("gpu", torch.cuda.get_device_name(0))
        line("vram GB", round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1))
except Exception as e:
    line("torch", "MISSING: %s" % e)
for mod in ("open_clip", "peft", "pyarrow", "pandas", "PIL", "numpy", "huggingface_hub"):
    try:
        m = __import__(mod)
        line(mod, getattr(m, "__version__", "ok"))
    except Exception as e:
        line(mod, "MISSING")
line("disk free GB", round(shutil.disk_usage("/root/autodl-tmp").free / 1e9, 1))
line("cpu cores", os.cpu_count())
