# Cross-modal alignment: code and results

This repository contains experiment code, corrected derived results, and offline reproducibility checks.

## Quick check

Use Python 3.12 or newer (the release was checked with Python 3.14):

```bash
python -m pip install -r requirements.txt
python -B verify_release.py
```

The check validates file hashes and recomputes the published summaries. It does not download data, load models, or run training.

## Contents

- `results/`: versioned records, summaries, provenance, and replay scripts.
- Each result group documents its scope and contains available producer code.
- `MIGRATION.json`: the disposition of files from the previous main snapshot.
- `MANIFEST.json`: the exact file inventory and SHA-256 checksums.

Source datasets, model weights, and manuscript materials are not distributed. Training dependencies are separate from the offline check; see the relevant group README. Results retain their documented protocol limitations.

## Version

**v3.3** replaces superseded and unverified legacy files in the current tree with audited bundles. Earlier tags remain unchanged. Removing an unverified file is not a finding that its contents are false.

## License

MIT applies only to the project-authored Python files listed in `LICENSE_SCOPE.json`; see `LICENSE` and `LICENSE_SCOPE.md`. Data, result records, unlisted code and third-party materials are not relicensed by this notice. Existing version tags and archived snapshots remain unchanged.
