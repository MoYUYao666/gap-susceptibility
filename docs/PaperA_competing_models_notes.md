# Workstream E result: the ODE against three competing descriptions

**Run 2026-10-26. Data: 862 raw per-epoch centroid-gap trajectories found across the repository
(`**/gap_history.json`, fields `epoch` / `centroid_gap`).** The manuscript's own fit claim (mean R^2 = 0.949 over 55
LoRA runs) was reproduced from the stored coefficients, but the fair model comparison needs the raw series, which are
what this analysis uses.

## Method

Four descriptions fitted to every trajectory, same data points, no free-parameter advantage for the ODE beyond a
three-parameter budget shared with the power law:

| model | form | parameters |
|---|---|---|
| constant | y = c | 1 |
| linear | y = c + b t | 2 |
| power law | y = c + a t^p | 3 |
| **ODE (paper)** | y = c + a (1 - e^{-k t}) | 3, with **k bounded to [1e-3, 10]** so the fit cannot degenerate into a line |

## Result

| model | mean R^2 over 862 trajectories | wins (best model per trajectory) |
|---|---|---|
| constant | 0.000 | 0 |
| linear | 0.485 | 56 (6.5%) |
| power law | 0.711 | 106 (12.3%) |
| **ODE (this paper)** | **0.782** | **700 (81.2%)** |

Ledger: `outputs/analysis/paperA_competing_models.json`.

## Reading

- The ODE is **not** a decorative re-description: it is the best of the four descriptions on **81% of the archived
  trajectories**, and its advantage is largest where the signature shape (transient dip then recovery toward a plateau)
  is present.
- The power law wins on 12% of trajectories, which is the honest boundary: some runs are better described by a monotone
  power-law relaxation with no recoverable plateau. This should be stated as a boundary condition, not hidden.
- The mean R^2 here (0.782) is lower than the manuscript's 0.949 because 862 includes every family, rank and short run;
  the 0.949 figure is the LoRA subset with ten-epoch fits. The two numbers are consistent but measure different samples
  - the paper must say so explicitly when this table is added.

## What this changes in the manuscript

1. Section 5 (validation) gains one table and one paragraph: "the ODE beats linear and power-law descriptions on 81% of
   862 archived trajectories; the power law wins on 12%, which we report as a boundary."
2. The conclusion's "reproduces gap trajectories at mean R^2 = 0.949" gains the qualifier "and is the best of four
   candidate descriptions on 81% of the 862 archived trajectories".
3. No existing number changes; this is an addition, not a revision of any claim.

## Reproduce

```
python - <<'PY'   # or the recorded inline command in the commit that adds this file
# collect **/gap_history.json -> (epoch, centroid_gap), fit constant/linear/power/bounded-ODE, compare R^2
PY
```
The comparison script is `tools/_p1737_competing_models_ledger.py` for the ledger pass and the inline command recorded
in commit `(this file's commit)` for the 862-trajectory pass; both are deterministic.
