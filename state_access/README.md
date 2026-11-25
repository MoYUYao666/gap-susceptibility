# A1 offline checkpoint restoration support

This small standalone support directory provides authenticated checkpoint
inspection and CPU parameter restoration for the replacement campaign's 42
core/spectral trajectories and the separate 24 source-method trajectories.
It does not select states for publication, download dependencies or models,
extract shards, train, restore optimizer/RNG, or certify numerical replay.
Publication and rights decisions belong to the parent release process.

## Portable layout and commands

Keep `restore.py`, `test_restore.py`, `CheckpointManifest.json`,
`SourceProvenance.json`, `FoundationLock.json`, `BaseConfig.json`, this README,
and the complete `sources/` tree together. `verify_local.py` is an optional
author-only evidence collector with a private output restriction; exclude it
from the public package. No local drive letter is required by `restore.py`.

Use an existing environment with PyTorch, NumPy, transformers and Pillow.
The author environment uses Python 3.12.14, torch 2.9.1+cu130, NumPy 2.5.2,
transformers 5.16.1. CUDA is not initialized. The restricted loader requires
`torch.serialization.get_unsafe_globals_in_checkpoint`, `safe_globals`, and
NumPy 2's `UInt32DType`. Older environments are not certified by this support.
No installation, environment conversion or fallback to unrestricted pickle
is implemented. Run with `-B` to suppress bytecode creation.

After the parent-controlled shard extraction, use the extraction root, which
contains `states/<sha256>.pt` and optionally `references/`. The support never
reads or extracts `assets/` itself. Parent staging at `isolated_local/` is a
valid payload root. Paths in an optional transport index are resolved inside
that root; absolute paths, parent escapes, and escaping symlinks are rejected.

```sh
python -B restore.py inventory
python -B -m unittest discover -s . -p test_restore.py -v

python -B restore.py inspect --family scientific_core \
  --unit cifar100__lora_both__s42 --state epoch_004 \
  --payload-root /local/extracted --payload-index /local/StateIndex.json

python -B restore.py inspect --family scientific_extension \
  --unit cifar100__early__dynamic__s42 --state epoch_004 \
  --payload-root /local/extracted

python -B restore.py restore --family methods_fixed24 \
  --unit dtd__router-static__s42 --state epoch004 \
  --payload-root /local/extracted --base-model /local/clip-vit-base-patch32
```

Each state command handles exactly one checkpoint, capped at 128 MiB serialized
size. It prints JSON to stdout and does not save a restored model or replicate
large payloads. `inspect` constructs the actual CLIP ViT-B/32 topology on the
meta device to compare every trained tensor's key, shape, dtype and finiteness.
It does not load foundation weights or copy checkpoint values into a live base.
`restore` additionally verifies the external foundation asset hashes, builds
the CPU base model, installs fixed spectral references or validates method
fixed buffers/parameters, copies every trainable and checks exact post-copy
equality. It exits after reporting the result. For in-process use,
`restore_parameters(state, row, base_path)` returns `(model, session)`.
Retain the spectral session while using the model; closing it removes gates.

The manifest can also be supplied as `--manifest ScalarRecords.zip` (the
unmodified v3.4 inner archive) or `--manifest CheckpointManifest.json`.
It must contain the same records as the included v3.4 manifest. The public
v3.4 flags saying payloads were excluded describe that historical release;
they are not rewritten here to claim that v3.4 already included model states.

## Manifest to deduplicated object mapping

The bundled manifest has 252 core/spectral logical states and 144 method
records. The latter comprise 120 epoch checkpoints and 24 latest restart
serialization aliases. The method native anchor is the foundation function,
not an additional trained checkpoint. CLI selection uses the exact
`(family, unit, state)` and keeps that logical identity even when bytes match.

The default object location is `states/<manifest-sha256>.pt`. Alternatively,
`--payload-index` accepts a dictionary of hash to relative path, or the parent's
`StateIndex.json` with `logical_state_records` rows:

```json
{
  "logical_state_records": [
    {
      "member": "scientific_core/cifar100__lora_both__s42/epoch_004/checkpoint.pt",
      "family": "scientific_core",
      "alias": false,
      "bytes": 9071508,
      "sha256": "c09751d08dfa96f011894d195edae79c21d475ad7322fbcbe94563865abc0f8c",
      "object": "states/c09751d08dfa96f011894d195edae79c21d475ad7322fbcbe94563865abc0f8c.pt"
    }
  ]
}
```

Index family names are `scientific_core`, `scientific_extension`, and
`methods_fixed24`, rather than the manifest's top-level collection names.
For an `object: null` alias, the resolver requires exactly one non-null object
path elsewhere in the index with the same SHA and size. Neither an index nor
tensor similarity can override the SHA in the v3.4 manifest.

Latest restart serialization aliases are not published objects. Select
`epoch004` for a method's final released epoch; do not substitute `latest` if
its serialized SHA differs, even if its parameters happen to match. Such a
latest record remains inventoried and fails resolution when no matching hash
object was materialized. Native frozen and adapted epoch-zero roles likewise
remain distinct even if they share bytes. For a core/spectral native role the
in-process restored model disables LoRA and, when present, spectral hooks.

`--payload /explicit/local/checkpoint.pt` supports an author's original local
file without an index; its size and SHA still must match the selected record.
That option does not make an unpublished alias publicly accessible.

## Restricted deserialization

The loader authenticates size and SHA before opening a CPU `torch.load` with
`weights_only=True`. It scans pickle globals under a cleared caller allowlist,
permits only the established four NumPy globals (`_reconstruct`, `ndarray`,
`dtype`, `UInt32DType`), and restores the caller's prior allowlist afterward.
NumPy arrays must occur under `rng` and be MT19937 `uint32[624]`; all other
NumPy arrays and unknown objects are rejected. No RNG is installed globally.
There is no `weights_only=False` fallback and no dynamic trust of checkpoint
globals. Use this serially: changing PyTorch's process-global allowlist is not
a concurrent deserialization interface.

The copied project producer sources are exact archival files and may contain
historical trusted-local loading entry points. They are supplied as provenance,
not invoked as public CLI loaders. `restore.py` imports the hashed core runner
and method runtime; it does not call the historical method runner's loader.
Use `restore.py` for loading external checkpoint payloads.

The size cap bounds the supported file inventory, not arbitrary malicious
allocation, decompression or execution time. Only authenticated, reviewed
project state payloads are supported; an untrusted manifest is not a security
root. A release's checksums and rights acceptance remain separate parent gates.

## Spectral references: no References.json dependency

Parameter restoration uses the checkpoint's own `extension.payload` and
`extension.buffers`. It checks `extension.reference_sha256` against the bound
identity, installs the payload using the original `HookController`, then
compares every installed reference buffer exactly with the checkpoint.
External `References.json` is neither required nor opened. Its provenance can
contain attention masks or token lists and must not be copied into this support
or published with it. Only its already recorded hash identity is retained.

The parent's 24 `ReferenceBuffers.pt` objects under
`references/<original campaign relative path>` are supplementary verification
artifacts; they are not needed to restore parameters from a complete state.
The CLI does not require the external JSON to authenticate them. It does not
claim to reproduce calibration collection or the omitted reference provenance.

## Actual source dependencies and acceptance boundaries

`SourceProvenance.json` records hashes and original relative paths for all 11
included project source files. They were checked byte-for-byte against the
corresponding v3.4 ScalarRecords producer sources. The core runner imports five
core runtime files and the hooks/spectral modules; these dependencies are
included together. The method runtime implements the four router/RoPE arms.
The copied method runner supplies the producer source needed for the original
signature checks, but is not the portable CLI's execution entry.

`BaseConfig.json` is the original foundation configuration, checked against
`FoundationLock.json`. Actual restoration requires the exact externally
obtained CLIP foundation weights and loader assets listed by name and SHA in
that lock. They are not supplied or downloaded. Core restoration binds the
checkpoint's `identity.model_files`; method restoration additionally validates
the original frozen-content digest and all fixed method tensors/buffers.

This is **parameter restoration support**, with an explicit producer gate gap.
The original method `restore_for_inference` requires the producer signature,
attention source, software and full configuration. The portable path uses the
original `_validate_state` for exact frozen/tensor validation, and reports
`producer_signature_acceptance: false`; it never claims to pass that full gate
after relocation or under different software. The original core/spectral
acceptance also requires recorded inputs, backend identity, exact processors,
all four score/feature views, and independent replay. These are not supplied
by a parameter-only state release.

Source-level acceptance pointers and their hashes are in `SourceProvenance`:
the processor-corrected `repro/replay_worker.py` restores references before
trainables/optimizer/scheduler/RNG; the method runtime's `_validate_state`,
`restore`, and `restore_for_inference` distinguish tensor validity, full resume,
and inference identity. Historical acceptance receipts are not rerun by this
support. Forward parity still requires the original `atol=2e-6, rtol=0`, and
static sham checks remain bitwise. No tolerance is relaxed here.

The author-only `verify_local.py` writes observed commands, logs and hashes to
the authorized `restore_review` directory. Its review covers all three state
families and ten topology variants, with representative core, spectral and
method CPU parameter restorations. This bounded support review does not replace
the parent's all-record SHA/restricted-load audit, does not prove all-state
model restoration, and does not certify full forward replay or resumed training.
