"""Custodian-side, offline single-corpus I-to-T scoring of a frozen P3 release."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCORER = Path(__file__).resolve()
SOURCE = HERE/"ProjectedSource.json"
RUNNER = HERE/"runner.py"
GAMMA = ("gamma_n2", "gamma_n4", "gamma_n8", "gamma_n16")
CONTROLS = ("uniform", "random", "target_calibrated")
ARMS = GAMMA + CONTROLS
SEEDS = (0, 1, 2)
RANK_COSTS = (36864, 6144, 12288, 6144)
BUDGET = 245760
CHECKPOINT = "a63082132ba4f97a80bea76823f544493bffa8082296d62d71581a4feff1576f"
REAL = "CUSTODIAN_SCORE_RELEASE"
SYNTHETIC = "SYNTHETIC_TEST_ONLY"


class ContractError(ValueError):
    """A release cannot be scored under the fixed contract."""


def check(ok, message):
    if not ok:
        raise ContractError(message)


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def hash_ok(value):
    return isinstance(value,str) and re.fullmatch("[a-f0-9]{64}",value) is not None


def bound_json(path, commitment, label):
    raw = path.read_bytes()
    check(hash_ok(commitment) and hashlib.sha256(raw).hexdigest()==commitment, f"{label} hash mismatch")
    d = json.loads(raw)
    check(isinstance(d,dict), f"Invalid {label} object")
    return d


def id_list(obj, field):
    ids = obj[field]
    check(isinstance(ids,list) and ids and all(isinstance(i,str) and 0<len(i)<=256 and i==i.strip()
                                             and not any(ord(c)<32 for c in i) for i in ids)
          and len(set(ids))==len(ids), f"Invalid or duplicate {field}")
    return ids


def release_file(root, name):
    check(isinstance(name,str) and re.fullmatch("[A-Za-z0-9][A-Za-z0-9._-]*",name)
          and not name.endswith("."), "Unsafe or noncanonical release path")
    p = root/name
    resolved = p.resolve(strict=True)
    check(resolved.parent==root and resolved==p and p.is_file(),"Aliased or escaping release path")
    return p


def validate_rank(ranks):
    check(isinstance(ranks,list) and len(ranks)==len(RANK_COSTS)
          and all(type(r) is int and r>0 for r in ranks)
          and sum(c*r for c,r in zip(RANK_COSTS,ranks))==BUDGET, "Invalid exact-budget rank")


def validated_manifest(path, expected, *, synthetic):
    d = bound_json(path,expected,"manifest")
    check(d["mode"]==(SYNTHETIC if synthetic else REAL),"Wrong release mode")
    check(type(d["corpus_units"]) is int and d["corpus_units"]==1,"Only a single corpus case study is supported")
    check(isinstance(d["target"],str) and d["target"].strip(),"Missing target identity")
    check(d["scorer_sha256"]==sha(SCORER) and d["runner_sha256"]==sha(RUNNER),"Scorer/runner drift")
    if not synthetic:
        check(not path.is_relative_to(ROOT.resolve()),"Production score release must be outside the training workspace")
        check(d["checkpoint_sha256"]==CHECKPOINT,"Unexpected checkpoint")
        review=bound_json(release_file(path.parent,d["custody_file"]),d["custody_sha256"],"custody receipt")
        selector,custodian=review["selector"],review["custodian"]
        check(isinstance(selector,str) and isinstance(custodian,str)
              and selector==selector.strip() and custodian==custodian.strip()
              and bool(selector) and bool(custodian) and selector.casefold()!=custodian.casefold(),
              "Separate selector and reference custodian are required")
        check(review["target"]==d["target"] and review["reference_sha256"]==d["reference_sha256"]
              and all(review[k] is True for k in ("release_identity_verified","eligibility_reviewed",
                        "train_reference_separation_reviewed","prediction_freeze_reviewed","calibration_reviewed")),
              "Custody review incomplete")
    lists = [id_list(d,k) for k in ("source_ids","train_ids","calibration_ids","query_ids","gallery_ids")]
    joined = [i for group in lists for i in group]
    check(len(set(joined))==len(joined),"Dataset split or ID role overlap")
    margin = d["practical_margin_r1"]
    check(type(margin) in (int,float) and math.isfinite(margin) and 0<margin<=1,"Invalid predeclared practical margin")
    p = bound_json(SOURCE,d["projected_source_sha256"],"projected source")
    cal = bound_json(release_file(path.parent,d["calibration_file"]),d["calibration_sha256"],"calibration")
    check(cal["target"]==d["target"] and id_list(cal,"fit_ids")==d["calibration_ids"],"Calibration fitting IDs differ")
    check(set(cal["ranks_by_seed"])=={str(s) for s in SEEDS},"Calibration seed grid differs")
    if not synthetic:
        check(cal["heldout_access"] is False and all(hash_ok(cal[k]) for k in ("recipe_sha256","inputs_sha256")),
              "Calibration receipt cannot be bound to fitting inputs")
    cells=d["cells"]
    check(isinstance(cells,list) and len(cells)==len(SEEDS)*len(ARMS),"Required cells missing or duplicated")
    index={}
    seen=set()
    for cell in cells:
        key=cell["seed"], cell["arm"]
        check(type(key[0]) is int and key[0] in SEEDS and key[1] in ARMS and key not in index,
              "Required cells missing or duplicated")
        f=release_file(path.parent,cell["file"])
        identity=(f.stat().st_dev,f.stat().st_ino)
        check(f.suffix==".npz" and identity not in seen,"Duplicate or aliased cell path")
        seen.add(identity)
        index[key]=cell,f
    for seed in SEEDS:
        r=p["seed_records"][seed]
        check(r["seed"]==seed,"Projected source seed order drift")
        ranks={**{f"gamma_n{x['size']}":x["rank"] for x in r["projected_source"]},
               "uniform":r["uniform"], "random":r["random"],"target_calibrated":cal["ranks_by_seed"][str(seed)]}
        clocks=set()
        for arm in ARMS:
            c,_=index[seed,arm]
            validate_rank(c["rank"])
            check(c["rank"]==ranks[arm] and type(c["trainables"]) is int and c["trainables"]==BUDGET,
                  "Cell rank or runtime parameter count differs")
            check(type(c["optimizer_steps"]) is int and c["optimizer_steps"]>0
                  and hash_ok(c["train_order_sha256"]) and hash_ok(c["update_schedule_sha256"]),
                  "Missing training order, budget or schedule pin")
            if not synthetic:
                arm_receipt=bound_json(release_file(path.parent,c["receipt_file"]),c["receipt_sha256"],"arm receipt")
                fields=("seed","arm","sha256","rank","trainables","optimizer_steps","train_order_sha256","update_schedule_sha256")
                check(all(arm_receipt[k]==c[k] for k in fields)
                      and arm_receipt["target"]==d["target"] and arm_receipt["checkpoint_sha256"]==d["checkpoint_sha256"]
                      and arm_receipt["runner_sha256"]==d["runner_sha256"]
                      and arm_receipt["heldout_used_for_selection"] is False, "Arm receipt is not bound to the cell")
            clocks.add((c["optimizer_steps"],c["train_order_sha256"],c["update_schedule_sha256"]))
        check(len(clocks)==1,"Per-seed schedule, train order or updates differ")
    return d,index


def take_arrays(path, expected, query, gallery):
    with path.open("rb") as stream:
        check(hash_ok(expected) and hashlib.file_digest(stream,"sha256").hexdigest()==expected,"Cell hash mismatch")
        stream.seek(0)
        with np.load(stream,allow_pickle=False) as data:
            check(len(data.files)==4 and set(data.files)=={"query_ids","gallery_ids","images","texts"},"Wrong cell arrays")
            for key,ids in (("query_ids",query),("gallery_ids",gallery)):
                arr=data[key]
                check(arr.ndim==1 and arr.dtype.kind=="U" and arr.tolist()==ids,f"Ordered {key} differs")
            x,t=data["images"],data["texts"]
        stream.seek(0)
        check(hashlib.file_digest(stream,"sha256").hexdigest()==expected,"Cell hash changed during read")
    check(x.ndim==t.ndim==2 and len(x)==len(query) and len(t)==len(gallery)
          and x.shape[1]==t.shape[1] and x.shape[1]>0 and x.dtype.kind==t.dtype.kind=="f",
          "Invalid embedding tensor shape or dtype")
    x,t=x.astype(np.float64),t.astype(np.float64)
    for a in (x,t):
        v=np.linalg.norm(a,axis=1)
        check(np.isfinite(v).all() and (v>0).all(),"Invalid embedding norm")
        a/=v[:,None]
    return x,t


def hits_in_gallery(x,t,owners,query):
    # Query chunk only: each row is scored against the entire ordered gallery.
    # Limit the dense scratch matrix to about one million double entries per chunk.
    width=max(1,1_000_000//len(t))
    hits=0
    for start in range(0,len(x),width):
        winners=np.argmax(x[start:start+width]@t.T,axis=1)
        hits+=sum(query[start+i]==owners[j] for i,j in enumerate(winners))
    return hits


def score(manifest, expected, references, *, synthetic=False):
    path,references = (Path(p).resolve(strict=True) for p in (manifest,references))
    d,index=validated_manifest(path,expected,synthetic=synthetic)
    check(not references.is_relative_to(path.parent) and (synthetic or not references.is_relative_to(ROOT.resolve())),
          "Evaluation reference must be held outside the release and training trees")
    roster=bound_json(references,d["reference_sha256"],"reference")
    query,gallery=d["query_ids"],d["gallery_ids"]
    owners=roster["owners"]
    check(roster["target"]==d["target"] and roster["gallery_ids"]==gallery and isinstance(owners,list)
          and len(owners)==len(gallery) and set(owners)==set(query),"Reference owners or gallery differ")
    rows, differences = [], []
    for seed in SEEDS:
        count={}
        dimensions=set()
        for arm in ARMS:
            cell, f=index[seed,arm]
            x,t=take_arrays(f,cell["sha256"],query,gallery)
            dimensions.add(x.shape[1])
            check(synthetic or x.shape[1]==512,"Real CLIP ViT-B/32 receipt requires 512-dimensional embeddings")
            count[arm]=hits_in_gallery(x,t,owners,query)
            rows.append({"seed":seed,"arm":arm,"hits":count[arm],"r1":count[arm]/len(query)})
        check(len(dimensions)==1,"Per-arm embedding dimension differs")
        delta={arm:{c:(count[arm]-count[c])/len(query) for c in CONTROLS} for arm in GAMMA}
        differences.append({"seed":seed,"gamma_deltas":delta,
                            "worst_gamma_delta_vs_uniform":min(v["uniform"] for v in delta.values())})
    return {"scope":d["mode"] if synthetic else "SINGLE_CORPUS_DESCRIPTIVE_ONLY",
            "target_scientific_result":None if synthetic else "DESCRIPTIVE_PAIRED_RETRIEVAL_CASE_STUDY",
            "target":d["target"],"manifest_sha256":expected,"query_count":len(query),"caption_count":len(gallery),
            "corpus_units":1,"cross_target_association":None,"predictor_threshold":None,
            "practical_margin_r1":d["practical_margin_r1"],"cells":rows,"by_seed":differences}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    p.add_argument("manifest_sha256")
    p.add_argument("references", type=Path)
    p.add_argument("output", type=Path)
    args=p.parse_args()
    try:
        result=score(args.manifest,args.manifest_sha256,args.references)
        with args.output.open("x",encoding="utf-8",newline="\n") as f:
            json.dump(result,f,indent=2,allow_nan=False)
            f.write("\n")
    except (OSError,ValueError,TypeError,KeyError) as exc:
        # Do not print paths or contextual data from a custodian's private reference file.
        print(f"BLOCKED: {exc}" if isinstance(exc,ContractError) else f"BLOCKED: invalid scoring input ({type(exc).__name__})",
              file=sys.stderr)
        return 2
    print("Custodian scoring complete; single-corpus descriptive output only.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
