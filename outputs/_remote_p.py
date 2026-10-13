
import subprocess, os
subprocess.run(["pkill", "-f", "_7bp.py"])
subprocess.run(["pkill", "curl"])
import time; time.sleep(3)
n = subprocess.run(["pgrep", "-c", "curl"], capture_output=True, text=True).stdout.strip()
d = "models/qwen2vl7b"
size = sum(os.path.getsize(os.path.join(d,f)) for f in os.listdir(d)
           if os.path.isfile(os.path.join(d,f)))
parts = len([f for f in os.listdir(d) if ".tmp.p" in f])
print("  paused | curl remaining %s | 7B downloaded %.2f GB | %d kept parts"
      % (n or "0", size/1e9, parts))
