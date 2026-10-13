
import os, sys, time, json, subprocess
os.chdir("/root/autodl-tmp/work")
log = lambda m: print("[%s] %s" % (time.strftime("%H:%M:%S"), m), flush=True)

# ① 下载 config 与权重（hf-mirror，后台可断）
os.makedirs("models/qwen2vl7b", exist_ok=True)
M = "https://hf-mirror.com/Qwen/Qwen2-VL-7B-Instruct/resolve/main"
log("下载 7B config/small files")
for f in ("config.json", "preprocessor_config.json", "tokenizer.json",
          "tokenizer_config.json", "vocab.json", "merges.txt",
          "generation_config.json", "chat_template.json"):
    p = "models/qwen2vl7b/" + f
    if not os.path.exists(p):
        subprocess.run(["curl", "-sL", "--max-time", "120", "-o", p, "%s/%s" % (M, f)])

# ② 权重按 shard 下载（Qwen2-VL-7B 用 safetensors 分片）
log("探测权重分片")
idx = "models/qwen2vl7b/model.safetensors.index.json"
if not os.path.exists(idx):
    subprocess.run(["curl", "-sL", "--max-time", "120", "-o", idx,
                    "%s/model.safetensors.index.json" % M])
if os.path.exists(idx):
    try:
        d = json.load(open(idx))
        shards = sorted(set(d["weight_map"].values()))
        log("分片数 %d: %s" % (len(shards), shards[:3]))
        for sh in shards:
            p = "models/qwen2vl7b/" + sh
            if os.path.exists(p) and os.path.getsize(p) > 100e6:
                log("SKIP %s" % sh); continue
            if os.path.exists(p):
                os.remove(p)
            t0 = time.time()
            subprocess.run(["curl", "-sL", "--retry", "5", "--max-time", "1800",
                            "-o", p, "%s/%s" % (M, sh)])
            sz = os.path.getsize(p) if os.path.exists(p) else 0
            log("  %s %.0f MB in %.0fs" % (sh, sz/1e6, time.time()-t0))
    except Exception as e:
        log("index 解析失败: %s" % str(e)[:120])
else:
    log("❌ 拿不到 index.json")

# ③ 实测加载显存（不训练）
log("实测 bf16 加载显存")
try:
    import torch
    from transformers import Qwen2VLForConditionalGeneration
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    m = Qwen2VLForConditionalGeneration.from_pretrained(
        "models/qwen2vl7b", torch_dtype=torch.bfloat16, device_map="cuda",
        low_cpu_mem_usage=True)
    log("加载成功 %.0fs ｜ 显存 %.2f GB ｜ 峰值 %.2f GB"
        % (time.time()-t0, torch.cuda.memory_allocated()/2**30,
           torch.cuda.max_memory_allocated()/2**30))
    n = sum(p.numel() for p in m.parameters())/1e9
    log("参数量 %.2f B" % n)
except Exception as e:
    log("❌ 加载失败: %s" % str(e)[:250])
log("PROBEDONE")
