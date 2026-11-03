# -*- coding: utf-8 -*-
"""Add per-step instrumentation to run_training.py (correct anchors)."""
import ast
import io

P = "paper3/scripts/run_training.py"
t = io.open(P, encoding="utf-8").read()
if "--instrument" not in t:
    anchor = "parser.add_argument('--per-step'"
    add = ("parser.add_argument('--instrument', action='store_true', default=False,\n"
           "                    help='log per-step loss/gradient statistics')\n")
    assert t.count(anchor) == 1
    t = t.replace(anchor, add + anchor, 1)
    anchor2 = "# Train for N epochs, compute E(t) per epoch"
    assert t.count(anchor2) == 1
    t = t.replace(anchor2, "_instr = []\n" + anchor2, 1)
    old = "        loss.backward()\n"
    new = ("        loss.backward()\n"
           "        if args.instrument:\n"
           "            _gn = 0.0\n"
           "            _mx = 0.0\n"
           "            for _p in model.parameters():\n"
           "                if _p.grad is not None:\n"
           "                    _gn += float(_p.grad.detach().float().pow(2).sum())\n"
           "                    _mx = max(_mx, float(_p.grad.detach().abs().max()))\n"
           "            _instr.append({\"epoch\": epoch, \"step\": step, \"loss\": float(loss.item()),\n"
           "                           \"grad_norm\": _gn ** 0.5, \"grad_max\": _mx,\n"
           "                           \"logit_max\": float(out.logits.detach().abs().max()),\n"
           "                           \"finite\": bool(torch.isfinite(loss).item())})\n")
    assert t.count(old) == 1
    t = t.replace(old, new, 1)
    anchor3 = 'log(f"\\n{\'=\'*50}")'
    assert t.count(anchor3) == 1, t.count(anchor3)
    save = ('if args.instrument:\n'
            '    _out = os.path.join("outputs", "analysis",\n'
            '                        "p3_instrument_r%d_lr%s.json" % (args.rank, args.lr))\n'
            '    os.makedirs(os.path.dirname(_out), exist_ok=True)\n'
            '    json.dump({"meta": {"script": "paper3/scripts/run_training.py", "rank": args.rank,\n'
            '                        "lr": args.lr, "epochs": args.epochs, "num_samples": args.num_samples,\n'
            '                        "block_config": args.block_config, "data_path": args.data_path},\n'
            '               "steps": _instr}, open(_out, "w", encoding="utf-8"), indent=1)\n'
            '    log("instrumented log: " + _out)\n')
    t = t.replace(anchor3, save + anchor3, 1)
    io.open(P, "w", encoding="utf-8", newline="").write(t)
    ast.parse(t)
    print("instrument mode added")
else:
    print("already present")
