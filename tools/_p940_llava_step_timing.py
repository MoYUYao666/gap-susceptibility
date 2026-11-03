# -*- coding: utf-8 -*-
r"""Add per-step timing, a live ETA and epoch checkpointing to the LLaVA sweep script.

Why: the script printed one line per epoch, so a run that was merely slow looked identical to one that
was stuck. Measured on the run started at 13:02:42 on 2026-10-15: epoch 1 of `text_only_s42` finished at
14:28:22, i.e. 5140 s for 200 steps of batch 2 = **25.7 s per step**, and the queue is 12 runs at 3
epochs each, which projects to roughly 34 hours for the remaining 8 runs. Nothing was wrong with the
process; it simply had no way to show progress.

What is added, all inside the existing training loop:

* a heartbeat line every `--report-every` steps: step index, loss, seconds for that step, running mean,
  and the projected finish time of the whole run;
* an epoch summary with the three components separated -- batch construction (image decode and processor),
  forward/backward/step, and the held-out measurement -- because that is what tells you which part to fix;
* `train_progress.json` next to the per-run records, rewritten as the run proceeds, so progress is visible
  from the filesystem even when the log is not being followed;
* an optional epoch checkpoint (`--resume`) so an interrupted run can continue instead of restarting.

    python tools/_p940_llava_step_timing.py [--apply]
"""
from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "tools" / "_p820_llava_sites.py"
B = chr(92)

ARG_ANCHOR = '    ap.add_argument("--apply", action="store_true")\n'
ARG_NEW = (ARG_ANCHOR
           + '    ap.add_argument("--report-every", type=int, default=10,\n'
           + '                    help="print a step heartbeat every N optimisation steps")\n'
           + '    ap.add_argument("--resume", action="store_true",\n'
           + '                    help="continue an interrupted run from its epoch checkpoint")\n')

LOOP_OLD = """                mm.train()
                t0 = time.time()
                for ep in range(a.epochs):
                    order = list(train_ids)
                    random.shuffle(order)
                    tot = 0.0
                    nb = 0
                    for s in range(0, len(order), a.batch):
                        chunk = order[s:s + a.batch]
                        caps = [by_img[i][0] for i in chunk]
                        inp = make_batch(chunk, caps, with_labels=True)
                        inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in inp.items()}
                        out = mm(**inp)
                        opt.zero_grad(set_to_none=True)
                        out.loss.backward()
                        opt.step()
                        tot += float(out.loss)
                        nb += 1
                    print(f"  epoch {ep + 1}/{a.epochs}  loss {tot / max(1, nb):.4f}")
                train_s = time.time() - t0"""

LOOP_NEW = '''                mm.train()
                t0 = time.time()
                # ---- step timing, added 2026-10-15 -------------------------------------------------
                # The old loop printed once per epoch, so an 86-minute epoch was indistinguishable
                # from a hang. Every step now records where its time went, and a heartbeat plus a
                # progress file make the run observable while it is still going.
                steps_total = a.epochs * -(-len(train_ids) // a.batch)
                step_i = 0
                run_t0 = time.time()
                t_batch = t_compute = 0.0
                t_epoch_start = run_t0
                ep_start = 0
                prog_path = OUT_DIR / "train_progress.json"
                resume_path = OUT_DIR / f"{name}_ckpt.pt"
                start_ep = 0
                if a.resume and resume_path.exists():
                    try:
                        ck = torch.load(resume_path, map_location="cpu")
                        mm.load_state_dict(ck["model"], strict=False)
                        opt.load_state_dict(ck["opt"])
                        start_ep = int(ck["epoch"])
                        print(f"  resumed from epoch {start_ep} ({resume_path.name})")
                    except Exception as exc:
                        print(f"  resume failed ({type(exc).__name__}: {exc}); starting fresh")
                        start_ep = 0
                for ep in range(start_ep, a.epochs):
                    order = list(train_ids)
                    random.shuffle(order)
                    tot = 0.0
                    nb = 0
                    ep_start = time.time()
                    for s in range(0, len(order), a.batch):
                        chunk = order[s:s + a.batch]
                        caps = [by_img[i][0] for i in chunk]
                        tb0 = time.time()
                        inp = make_batch(chunk, caps, with_labels=True)
                        inp = {k: (v.to(0) if hasattr(v, "to") else v) for k, v in inp.items()}
                        tb1 = time.time()
                        out = mm(**inp)
                        opt.zero_grad(set_to_none=True)
                        out.loss.backward()
                        opt.step()
                        tc1 = time.time()
                        t_batch += tb1 - tb0
                        t_compute += tc1 - tb1
                        tot += float(out.loss)
                        nb += 1
                        step_i += 1
                        if a.report_every and step_i % a.report_every == 0:
                            el = time.time() - run_t0
                            per = el / max(1, step_i)
                            eta = time.time() + per * (steps_total - step_i)
                            print(f"    step {step_i}/{steps_total}  loss {tot / nb:.4f}  "
                                  f"{per:.1f} s/step  elapsed {el / 60:.1f} min  "
                                  f"eta {time.strftime('%H:%M', time.localtime(eta))}", flush=True)
                            prog_path.write_text(
                                json.dumps({"run": name, "step": step_i, "steps_total": steps_total,
                                            "epoch": ep + 1, "loss_running": tot / nb,
                                            "sec_per_step": round(per, 2),
                                            "elapsed_s": round(el, 1),
                                            "eta": time.strftime("%Y-%m-%d %H:%M", time.localtime(eta)),
                                            "t_batch_s": round(t_batch, 1),
                                            "t_compute_s": round(t_compute, 1)},
                                           indent=1), encoding="utf-8")
                    ep_s = time.time() - ep_start
                    print(f"  epoch {ep + 1}/{a.epochs}  loss {tot / max(1, nb):.4f}  "
                          f"[{ep_s / 60:.1f} min, {nb} steps, {ep_s / max(1, nb):.1f} s/step]",
                          flush=True)
                    try:
                        torch.save({"model": {k: v for k, v in mm.state_dict().items()},
                                    "opt": opt.state_dict(), "epoch": ep + 1}, resume_path)
                    except Exception as exc:
                        print(f"  checkpoint not written ({type(exc).__name__}: {exc})")
                train_s = time.time() - t0
                print(f"  training breakdown: batch prep {t_batch:.1f} s, compute {t_compute:.1f} s")'''

MEASURE_ANCHOR = """            after = measure(mm, eval_ids)"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    t = SCRIPT.read_text(encoding="utf-8")
    if "--report-every" in t:
        print("  already instrumented")
        return 0
    assert t.count(ARG_ANCHOR) == 1, "the argument anchor was not found exactly once"
    assert t.count(LOOP_OLD) == 1, "the training loop was not found exactly once"
    out = t.replace(ARG_ANCHOR, ARG_NEW, 1).replace(LOOP_OLD, LOOP_NEW, 1)

    # the measurement between runs also costs time; report it separately
    assert out.count(MEASURE_ANCHOR) == 1
    out = out.replace(MEASURE_ANCHOR,
                      "            _tm = time.time()\n"
                      "            after = measure(mm, eval_ids)\n"
                      "            print(f\"  held-out measurement: {time.time() - _tm:.1f} s \"\n"
                      "                  f\"over {len(eval_ids)} pairs\", flush=True)", 1)

    print("  added: --report-every / --resume, per-step heartbeat with ETA, train_progress.json,")
    print("         per-epoch checkpoint, and a batch-vs-compute time split")
    print(f"  script grows {len(t.splitlines())} -> {len(out.splitlines())} lines")
    if not a.apply:
        print("  (dry run)")
        return 0
    SCRIPT.write_text(out, encoding="utf-8", newline="")

    check = SCRIPT.read_text(encoding="utf-8")
    assert "--report-every" in check and "train_progress.json" in check
    import ast
    ast.parse(check)
    print("  written and parses")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
