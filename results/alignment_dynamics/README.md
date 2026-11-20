# Adaptation-site and trajectory diagnostics

Run `python -B replay.py` from this folder (Python 3.11+ and NumPy). It verifies
files and replays the checked summary without writing or using a network.

- The anchored ODE and intercept-fitted line use the same 55 LoRA trajectories
  from 96 fit inputs. These are same-trajectory fits, not forecasts.
- The 104 strict-freezing configuration records are a separate inventory,
  not additional fit inputs or an independent sample. No grand total is used.
- The chain rule gives the instantaneous energy change in actual optimizer
  coordinates. A scalar ODE additionally needs local closure; an SGD
  single-step check does not establish it. The complete post-training pilot
  records use the opposite alpha sign to the negative-gradient convention.
  That re-signing does not turn an embedding probe into a calibrated
  parameter derivative. Native free-offset rates and anchored fits differ.
- Precision and training set size differ in the decoder comparison. Legacy
  non-strict, strict-freezing, restored COCO and retrospective configurations
  remain separate. Temporal interpolation is not prospective validation.

`coverage.json` lists evidence and exclusions. Full upstream model evaluation
requires the original splits, transforms, model checkpoints and training
dependencies (PyTorch and the respective model libraries); none are needed
for replay. The included tracker consumes already-computed embeddings.
The optional LLaVA producer is separate: see `production/README.md`.
