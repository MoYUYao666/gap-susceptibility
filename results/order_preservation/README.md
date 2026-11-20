# Order perturbations and checkpoint diagnostics

Run `python -B replay.py` from this folder (Python 3.11+ and NumPy). This
read-only replay checks files, matched gaps, paired intervals and archived
checkpoint selection. No model, dataset, training or network is needed.

- Under the unnormalized dot-product intervention, a small winner margin is
  necessary, not sufficient, for a flip. Joint zero-mean constraints can
  restrict possible flips; separate class renormalization changes the problem.
- Pair intervals distinguish signed endpoint differences from the oriented
  positive spread. Correctness flags contain no images, labels or sample IDs.
- Kendall order readouts are label-free for a fixed reference and top-k
  convention. Target-margin selection needs labels. Regret is retrospective
  replay against a labelled oracle, not evidence of a prospective stopping
  advantage. Small and large holdouts are reported separately. The campaign
  comparisons do not isolate training duration.

`coverage.json` lists evidence and exclusions. Upstream reproduction requires
the respective original weights, evaluation splits, and classifier prompts;
these are not distributed here. See `production/README.md` for the two
optional upstream producers.
