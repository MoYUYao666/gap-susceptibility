
import os, subprocess
d = "models/qwen2vl7b"
size = sum(os.path.getsize(os.path.join(d,f)) for f in os.listdir(d)
           if os.path.isfile(os.path.join(d,f)))
print("  7B: %.2f GB ｜ 分段 %d ｜ curl %s"
      % (size/1e9, len([f for f in os.listdir(d) if ".tmp.p" in f]),
         subprocess.run(["pgrep","-c","curl"],capture_output=True,text=True).stdout.strip() or "0"))
r = subprocess.run("tail -3 outputs_cloud_driver.log", shell=True,
                   capture_output=True, text=True)
print("  seed: " + (r.stdout or "").strip().replace("\n", " | ")[:180])
n = subprocess.run("find outputs -name results.json | wc -l", shell=True,
                   capture_output=True, text=True).stdout.strip()
print("  results.json:", n)
