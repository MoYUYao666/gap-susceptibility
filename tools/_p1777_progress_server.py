# -*- coding: utf-8 -*-
r"""Live experiment monitor: a tiny local web page listing every running experiment with its progress.

It reads only things that already exist on disk, so nothing has to be instrumented:
  * local_runs/work/outputs/**/results.json      finished local arms (count and newest mtime)
  * local_runs/logs/*.log                        per-arm logs (size and mtime tell whether a run is alive)
  * local_runs/logs/b1_real.log                  the local runner's own stage log
  * outputs/paperA_c_prereg*/*.json              the earlier cloud arms
  * nvidia-smi                                   GPU utilisation, when available

Usage:
    D:\Anaconda\envs\pytorch\python.exe tools/_p1777_progress_server.py [--port 8787]
Then open http://127.0.0.1:8787/ and dock it next to the harness with Edge's Split screen (Ctrl+Shift+S).
"""
import argparse
import glob
import io
import json
import os
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(REPO)
START = time.time()


def newest(paths):
    ps = [p for p in paths if os.path.isfile(p)]
    if not ps:
        return None
    p = max(ps, key=os.path.getmtime)
    return {"path": os.path.relpath(p, REPO).replace("\\", "/"),
            "mtime": time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(p))),
            "age_s": int(time.time() - os.path.getmtime(p))}


def gpu():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
                              "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=8).stdout
        used, total, util = [x.strip() for x in out.strip().splitlines()[0].split(",")]
        return {"mem_used_mb": int(used), "mem_total_mb": int(total), "util_pct": int(util)}
    except Exception:
        return None


def collect():
    data = {"generated_at": time.strftime("%H:%M:%S"), "uptime_s": int(time.time() - START), "jobs": []}

    # ---- local SigLIP arms (real corpus first, synthetic pilot kept separate)
    for label, outdir in (("SigLIP arms (real Flickr30k)", "local_runs/work/outputs/c_prereg_siglip"),
                          ("SigLIP pilot (synthetic)", "local_runs/synthetic_pilot_results")):
        if not os.path.isdir(outdir):
            continue
        res = glob.glob(os.path.join(outdir, "**", "results.json"), recursive=True)
        sites = {}
        for p in res:
            site = p.replace("\\", "/").split(outdir.replace("\\", "/") + "/")[-1].split("/")[0]
            sites[site] = sites.get(site, 0) + 1
        logs = glob.glob("local_runs/logs/siglip_*.log")
        # the logs are shared between the real run and the archived pilot, so only the live set reports activity
        active = [p for p in logs if time.time() - os.path.getmtime(p) < 900] if outdir.endswith("c_prereg_siglip") else []
        data["jobs"].append({"name": label, "done": len(res), "target": 9,
                             "per_site": sites, "active": len(active),
                             "newest": newest(logs)})

    # ---- cloud pre-registration arms (finished batches)
    for label, outdir, target in (("CLIP B/32 arms (cloud)", "outputs/paperA_c_prereg", 15),
                                  ("OpenCLIP B/32 arms (cloud)", "outputs/paperA_c_prereg_openclip", 15),
                                  ("CLIP B/16 arms (cloud)", "outputs/paperA_c_prereg_b16", 15)):
        res = glob.glob(os.path.join(outdir, "*.json"))
        if res:
            data["jobs"].append({"name": label, "done": len(res), "target": target, "per_site": {},
                                 "active": 0, "newest": newest(res)})

    # ---- the local runner's stage log
    runner = "local_runs/logs/b1_real.log"
    if os.path.isfile(runner):
        tail = [ln for ln in io.open(runner, encoding="utf-8", errors="replace").read().splitlines() if ln.strip()][-3:]
        data["jobs"].append({"name": "local runner log", "done": None, "target": None, "per_site": {},
                             "active": 0, "newest": newest([runner]), "tail": tail})

    data["gpu"] = gpu()
    return data


PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>experiments</title>
<style>
 body{font:13px/1.45 -apple-system,Segoe UI,Roboto,sans-serif;margin:0;padding:12px;background:#111418;color:#e6e8eb}
 h1{font-size:14px;margin:0 0 10px;color:#9aa4b2;font-weight:600}
 .card{background:#171b21;border:1px solid #232a33;border-radius:8px;padding:10px;margin-bottom:10px}
 .name{font-weight:600;margin-bottom:6px}
 .bar{height:6px;background:#232a33;border-radius:3px;overflow:hidden;margin:6px 0}
 .fill{height:100%;background:#3fb950;transition:width .4s}
 .meta{color:#8b949e;font-size:12px}
 .tail{color:#c9d1d9;font-size:11px;background:#0d1117;border-radius:5px;padding:6px;margin-top:6px;white-space:pre-wrap}
 .tag{display:inline-block;background:#22303d;color:#79c0ff;border-radius:4px;padding:0 5px;margin-right:4px}
</style></head><body>
<h1>LIVE EXPERIMENTS <span class="meta" id="stamp"></span></h1>
<div id="jobs"></div>
<script>
async function tick(){
  const r = await fetch('/progress.json', {cache:'no-store'});
  const d = await r.json();
  document.getElementById('stamp').textContent = d.generated_at + (d.gpu ? `  ·  GPU ${d.gpu.mem_used_mb}/${d.gpu.mem_total_mb} MB · ${d.gpu.util_pct}%` : '');
  const box = document.getElementById('jobs'); box.innerHTML = '';
  for (const j of d.jobs){
    const pct = (j.done!=null && j.target) ? Math.min(100, 100*j.done/j.target) : null;
    const div = document.createElement('div'); div.className='card';
    let html = `<div class="name">${j.name}</div>`;
    if (pct!=null) html += `<div class="bar"><div class="fill" style="width:${pct}%"></div></div>
      <div class="meta">${j.done}/${j.target} ${j.active? '· '+j.active+' running':''}</div>`;
    for (const [k,v] of Object.entries(j.per_site||{})) html += `<span class="tag">${k} ${v}</span>`;
    if (j.newest) html += `<div class="meta">log ${j.newest.mtime} (${j.newest.age_s}s ago)</div>`;
    if (j.tail) html += `<div class="tail">${j.tail.join('\\n')}</div>`;
    div.innerHTML = html; box.appendChild(div);
  }
}
tick(); setInterval(tick, 3000);
</script></body></html>"""


LAST_REQUEST = {"at": time.time()}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        LAST_REQUEST["at"] = time.time()
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.startswith("/progress.json"):
            self._send(200, json.dumps(collect()), "application/json")
        elif self.path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        else:
            self._send(404, "not found", "text/plain")

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--idle-exit", type=int, default=0,
                    help="exit after this many seconds without a request (0 = never)")
    a = ap.parse_args()

    if a.idle_exit > 0:
        def watchdog():
            while True:
                time.sleep(5)
                if time.time() - LAST_REQUEST["at"] > a.idle_exit:
                    print("idle for %ds, exiting" % a.idle_exit, flush=True)
                    os._exit(0)
        threading.Thread(target=watchdog, daemon=True).start()

    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print("progress monitor: http://127.0.0.1:%d/ (idle exit %ss)" % (a.port, a.idle_exit or "off"), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
