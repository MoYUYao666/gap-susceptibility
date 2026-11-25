# Version 3.5 state assets

The GitHub v3.5 release assets contain 12 independently hashed ZIP shards.
StateIndex.json binds every shard/member and maps the recorded logical states to
SHA-addressed native files. State binaries are release assets, not Git blobs.

From the repository root, using Python 3.12 for transport:

```sh
python -B state_access/state_assets.py download --assets /local/assets --jobs 4
python -B state_access/state_assets.py extract --assets /local/assets --output /local/extracted
python -B state_access/restore.py inventory
python -B state_access/restore.py inspect --family scientific_core --unit cifar100__lora_both__s42 --state epoch_004 --payload-root /local/extracted --payload-index state_access/StateIndex.json
python -B state_access/restore.py restore --family scientific_core --unit cifar100__lora_both__s42 --state epoch_004 --payload-root /local/extracted --base-model /local/clip-vit-base-patch32
```

Transport verification uses only the Python standard library. Restoration needs
the separately obtained exact base assets and the recorded torch/NumPy/
transformers environment described in README.md. Do not initialize a random base
and call that restoration. All loaded files must match the trusted version index.

For configuration YAML/JSON, seeds and evaluation/measurement source scripts,
see results/order_preservation/ScalarRecords.zip. RecordedRecipes.zip contains
the locked spectral recipes; InputIdentities.zip supplies legitimate input
acquisition/identity checks. These unchanged v3.4 components remain scoped as
recorded there. Their historical payload_included=false flags are not claims
about the separate v3.5 state assets. All eight statistical replay groups remain
available through python -B verify_release.py.

Parameter restoration is supported; optimizer/RNG tensors are preserved but the
portable CLI does not install them or certify training continuation. Original
resume implementations are shipped under sources/ and retain their stricter
producer/configuration/backend/input gates. Local prior native/resume acceptance
is separate from this release's CPU parameter checks. This release does not
replace unavailable historical checkpoints, supply the source data or per-example
arrays, prove cross-hardware parity, or reproduce all training from scratch.
Use matching final epoch states rather than unpublished latest aliases.

GitHub source archives and any later DOI source snapshot may not contain these
separate release assets. Use the v3.5 asset index and SHA checksums for state
access; do not claim that a DOI includes binaries without checking its inventory.
