
import os, subprocess, json
W = "/root/autodl-tmp/work"
print("=== 挂载与容量 ===")
for ln in subprocess.run(["df", "-h"], capture_output=True, text=True).stdout.splitlines():
    if any(k in ln for k in ("Filesystem", "/root", "overlay", "autodl", "/dev/")):
        print("  " + ln)
print("  work 目录所在设备:",
      subprocess.run(["df", "-h", W], capture_output=True, text=True).stdout.splitlines()[-1])

print("\n=== work 体积 ===")
r = subprocess.run(["du", "-sh", W + "/models", W + "/flickr30k", W + "/outputs"],
                   capture_output=True, text=True)
print("  " + (r.stdout or "").replace("\n", "\n  ").strip())

print("\n=== 7B shard 现状 ===")
D = W + "/models/qwen2vl7b"
tot = 0
for f in sorted(os.listdir(D)):
    p = os.path.join(D, f)
    if not os.path.isfile(p): continue
    s = os.path.getsize(p)
    tot += s
    if s > 1e6 or f.endswith(".tmp"):
        print("  %-46s %12d" % (f[:46], s))
print("  qwen2vl7b 合计 %.2f GB" % (tot/1e9))

print("\n=== 下载进程 ===")
n = subprocess.run(["pgrep", "-c", "curl"], capture_output=True, text=True).stdout.strip()
print("  curl 进程数:", n or "0")

print("\n=== 7B 日志 ===")
p = W + "/outputs_7b.log"
if os.path.exists(p):
    for ln in open(p).read().splitlines()[-8:]:
        print("  " + ln[:120])

print("\n=== seed 结果数 ===")
r = subprocess.run("find %s/outputs -name results.json 2>/dev/null | wc -l" % W,
                   shell=True, capture_output=True, text=True)
print("  results.json:", (r.stdout or "").strip())
r = subprocess.run("tail -5 %s/outputs_cloud_driver.log" % W, shell=True,
                   capture_output=True, text=True)
print("  " + (r.stdout or "").strip().replace("\n", "\n  ")[:400])
