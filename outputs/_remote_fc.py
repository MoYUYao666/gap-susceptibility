
import os, sys
os.chdir("/root/autodl-tmp/work")
sys.path.insert(0, ".")
print("=== three-model load check ===")
from transformers import CLIPModel
ok_all = True
for d, want in (("models/clip-vit-base-patch32", 32),
                ("models/clip-vit-base-patch16", 16),
                ("models/openclip", 32)):
    big = []
    if os.path.isdir(d):
        for f in os.listdir(d):
            p = os.path.join(d, f)
            if f.endswith((".bin", ".safetensors")) and os.path.getsize(p) > 100e6:
                big.append((f, os.path.getsize(p)))
    if not big:
        print("  %-32s [X] no large weight" % d); ok_all = False; continue
    try:
        m = CLIPModel.from_pretrained(d, local_files_only=True)
        got = m.config.vision_config.patch_size
        n = sum(x.numel() for x in m.parameters()) / 1e6
        good = (got == want)
        ok_all &= good
        print("  %-32s [OK] %s %.0fMB patch=%d(want %d) params=%.1fM %s"
              % (d, big[0][0], big[0][1]/1e6, got, want, n, "OK" if good else "MISMATCH"))
    except Exception as e:
        ok_all = False
        print("  %-32s [X] %s" % (d, str(e)[:110]))
print("READY" if ok_all else "NOTREADY")
