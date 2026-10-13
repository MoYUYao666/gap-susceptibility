
import os, subprocess, json
os.chdir("/root/autodl-tmp/work")

print("=== ① Disk ===")
for line in subprocess.run(["df","-h","/"],capture_output=True,text=True).stdout.splitlines():
    print("  " + line)

print("\n=== ② GPU ===")
print("  " + subprocess.run(["nvidia-smi","--query-gpu=name,memory.total,memory.used",
                            "--format=csv,noheader"],capture_output=True,text=True).stdout.strip())

print("\n=== ③ 7B model reachability (HEAD request only, no full download) ===")
CANDS = [
    ("Qwen/Qwen2-VL-7B-Instruct", "https://hf-mirror.com/Qwen/Qwen2-VL-7B-Instruct/resolve/main/config.json"),
    ("llava-hf/llava-1.5-7b-hf", "https://hf-mirror.com/llava-hf/llava-1.5-7b-hf/resolve/main/config.json"),
    ("Qwen/Qwen2.5-VL-7B-Instruct", "https://hf-mirror.com/Qwen/Qwen2.5-VL-7B-Instruct/resolve/main/config.json"),
]
for name, url in CANDS:
    r = subprocess.run(["curl","-sL","-o","/dev/null","--max-time","20",
                        "-w","%{http_code} %{size_download}","-r","0-2000",url],
                       capture_output=True, text=True)
    print("  %-32s %s" % (name, r.stdout.strip()))

print("\n=== ④ Existing model sizes ===")
tot = 0
for d in sorted(os.listdir("models")):
    p = os.path.join("models", d)
    if not os.path.isdir(p): continue
    s = sum(os.path.getsize(os.path.join(p,f)) for f in os.listdir(p)
            if os.path.isfile(os.path.join(p,f)))
    tot += s
    print("  %-32s %8.0f MB" % (d, s/1e6))
print("  Total %.1f GB" % (tot/1e9))
