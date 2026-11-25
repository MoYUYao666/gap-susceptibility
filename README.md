# Cross-modal alignment: code and results

Experiment code, recorded results and offline reproducibility checks.

```sh
python -m pip install -r requirements.txt
python -B verify_release.py
```

Python 3.12; the check validates hashes and replays eight recorded result groups
without training or model loading. See each group README for its scope.

Version **v3.5.1** adds versioned project state assets and CPU restoration support.
See `state_access/ACCESS.md` for download, verification and restoration commands.
States are separate release assets; source datasets and foundation weights are
not supplied. Manuscript and editorial materials are not distributed.

`MANIFEST.json` binds repository files; `state_access/StateIndex.json` binds the
state shards and logical mapping. Earlier tags and releases remain unchanged.
MIT applies only to named project software in `LICENSE_SCOPE.json`; data and
checkpoints retain separate terms. See `LICENSE_SCOPE.md` and the state notice.
