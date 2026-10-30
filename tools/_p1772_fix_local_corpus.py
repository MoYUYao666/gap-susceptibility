# -*- coding: utf-8 -*-
r"""Repair the local corpus builder: the Flickr30k CSV carries one row per image whose `raw` column is a JSON list
of the five captions (there is no `captions` column on this mirror), so the parser must read `raw` and json-decode it.
"""
import io
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = "tools/_p1771_local_b1_siglip.py"
t = io.open(P, encoding="utf-8").read()

start = t.index("    order, groups = [], {}")
end = t.index("    log(\"corpus built: %d images\" % len(done))")
new = '''    rows = []
    for fn, raw in zip(df["filename"].tolist(), df["raw"].tolist()):
        raw = str(raw)
        try:
            caps = json.loads(raw) if raw.strip().startswith("[") else [raw]
        except Exception:
            caps = [raw]
        rows.append({"image": str(fn), "captions": [str(c) for c in caps]})
        if len(rows) >= 1000:
            break
    log("annotation rows selected: %d (%d captions)" % (len(rows), sum(len(r["captions"]) for r in rows)))

    zp = hf_hub_download("nlphuji/flickr30k", "flickr30k-images.zip", repo_type="dataset")
    log("images zip: %.1f MB" % (os.path.getsize(zp) / 2 ** 20))
    need = {r["image"] for r in rows}
    done = set()
    with zipfile.ZipFile(zp) as z:
        for name in z.namelist():
            base = os.path.basename(name)
            if base in need and base not in done:
                with z.open(name) as src, open(os.path.join(img, base), "wb") as dst:
                    dst.write(src.read())
                done.add(base)
    json.dump([r for r in rows if r["image"] in done], io.open(js, "w", encoding="utf-8"), indent=0)
'''
t = t[:start] + new + t[end:]
io.open(P, "w", encoding="utf-8", newline="").write(t)
import ast
ast.parse(t)
print("corpus builder repaired (raw JSON captions)")
