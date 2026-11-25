# Cross-modal alignment: code and results

Experiment code, recorded results and offline reproducibility checks.

## Quick check

Use Python 3.12:

```bash
python -m pip install -r requirements.txt
python -B verify_release.py
```

The check validates file hashes and recomputes eight result groups. It does not
download data, load models or run training. See each group README for scope.

## Contents

- `results/`: records, configurations, provenance and replay scripts.
- `MANIFEST.json`: exact file inventory and SHA-256 checksums.
- `MIGRATION_v3.4.json`: replacement of the older order-diagnostics group.

Source datasets, model weights and manuscript materials are not distributed.
State metadata is not a downloadable checkpoint. Recorded numerical failures and
protocol limitations remain documented.

## Version and license

**v3.4** updates the order-diagnostics evidence and portable replay. Earlier tags
remain unchanged. MIT applies only to project-authored software listed by content
hash in `LICENSE_SCOPE.json`, including named archive members. Data and third-party
materials retain their own rights. See `LICENSE_SCOPE.md`.
