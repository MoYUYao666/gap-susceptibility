# -*- coding: utf-8 -*-
"""Run the A2 sonar protocol with additional seeds on two backbone architectures (2026-11-08).

The archived protocol run is seed 42 on ViT-B/32 (outputs/sonar_protocol.json) and the new second-backbone run is
seed 42 on ViT-B/16 (outputs/analysis/sonar_protocol_b16.json). This driver adds seeds 43 and 44 to both backbones so
the second-backbone comparison can be reported as a seed-paired mean rather than a single run.
"""
import io
import os
import subprocess
import sys
import time

SRC = "tools/clip_sonar_protocol.py"
TMP = os.path.join("local_runs", "sonar_seed_runs")
BACKBONES = (("clip-vit-base-patch32", "b32"), ("clip-vit-base-patch16", "b16"))
SEEDS = (43, 44)


def main():
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(os.path.join("outputs", "analysis"), exist_ok=True)
    base = io.open(SRC, encoding="utf-8").read()
    for backbone, tag in BACKBONES:
        for seed in SEEDS:
            out = "outputs/analysis/sonar_protocol_%s_seed%d.json" % (tag, seed)
            if os.path.exists(out):
                print("skip", out)
                continue
            text = base.replace("SEED = 42", "SEED = %d" % seed)
            text = text.replace("MDIR = 'models/clip-vit-base-patch32'", "MDIR = 'models/%s'" % backbone)
            text = text.replace("OUT = 'outputs/sonar_protocol.json'", "OUT = '%s'" % out)
            text = text.replace("'outputs/sonar_clip_ft.pt'",
                                "'outputs/%s_ft_seed%d.pt'" % (tag, seed))
            text = text.replace("if os.path.exists('outputs/ocean_clip_flickrft.pt'):",
                                "if False and os.path.exists('outputs/ocean_clip_flickrft.pt'):")
            p = os.path.join(TMP, "sonar_%s_seed%d.py" % (tag, seed))
            io.open(p, "w", encoding="utf-8", newline="").write(text)
            print("run", p, flush=True)
            t0 = time.time()
            with io.open(os.path.join(TMP, "log_%s_seed%d.txt" % (tag, seed)), "wb") as f:
                subprocess.run([sys.executable, "-u", p], stdout=f, stderr=subprocess.STDOUT)
            print("  done in %.1f min" % ((time.time() - t0) / 60), flush=True)
    print("SONAR_SEEDS_DONE")


if __name__ == "__main__":
    main()
