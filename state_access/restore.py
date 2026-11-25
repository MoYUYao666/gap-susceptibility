"""Offline, single-state inspection and parameter restoration; never a replay gate."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import types
import zipfile

HERE = Path(__file__).resolve().parent


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def inside(root, name):
    require(isinstance(name, str) and '\\' not in name and ':' not in name,
            'Expected a portable relative path')
    relative = Path(name)
    require(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe relative path')
    path = (Path(root) / relative).resolve()
    require(path.is_relative_to(Path(root).resolve()), 'Path escapes payload root')
    return path


def manifest_rows(path=None):
    if path and Path(path).suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as archive:
            data = archive.read('checkpoints/CheckpointManifest.json')
        manifest = json.loads(data)
    else:
        manifest = read(path or HERE / 'CheckpointManifest.json')
    # Parent can add packaging fields, but existing records cannot be substituted.
    reference = read(HERE / 'CheckpointManifest.json')
    require(manifest['core_spectral'] == reference['core_spectral'] and
            manifest['methods'] == reference['methods'], 'Manifest records differ from v3.4')
    return manifest['core_spectral'] + manifest['methods']


def select(rows, family, unit, state):
    selected = [r for r in rows if (r['family'], r['unit'], r['state']) == (family, unit, state)]
    require(len(selected) == 1, 'Select exactly one manifest record')
    return selected[0]


def payload_record(row):
    record = row.get('checkpoint', row)
    require(re.fullmatch('[0-9a-f]{64}', record['sha256']) is not None, 'Invalid payload SHA256')
    require(type(record['bytes']) is int and 0 < record['bytes'] <= 128 * 1024**2,
            'Checkpoint exceeds the single-state 128 MiB bound')
    return {'sha256': record['sha256'], 'bytes': record['bytes']}


def resolve_payload(row, root, index=None):
    digest = payload_record(row)['sha256']
    # The index is transport-only: no index-provided hash overrides the manifest.
    if index:
        transport = read(index)
        if 'logical_state_records' in transport:
            entries = transport['logical_state_records']
            matches = [x for x in entries if x['member'] == row['local_logical_member']
                       and x['family'] == row['family']]
            require(len(matches) == 1, 'StateIndex logical record missing or duplicated')
            selected = matches[0]
            require(selected['sha256'] == digest and selected['bytes'] == payload_record(row)['bytes'],
                    'StateIndex differs from checkpoint manifest')
            name = selected['object']
            if name is None:
                candidates = {x['object'] for x in entries if x['sha256'] == digest
                              and x['bytes'] == selected['bytes'] and x['object'] is not None}
                require(len(candidates) == 1, 'Alias has no unique materialized hash object')
                name = candidates.pop()
        else:
            name = transport[digest]
    else:
        name = f'states/{digest}.pt'
    return inside(root, name)


def safe_load(path, expected):
    """Established restricted NumPy MT19937 loader, without pickle fallback.

    Use an already authenticated, size-bounded project file. This is not a
    general adversarial archive sandbox or an allocation/CPU-time limiter.
    """
    import numpy as np
    import torch
    path = Path(path)
    require(path.stat().st_size == expected['bytes'] and sha(path) == expected['sha256'],
            'Checkpoint size/SHA mismatch before deserialization')
    allowed = [np._core.multiarray._reconstruct, np.ndarray, np.dtype, np.dtypes.UInt32DType]
    names = {'numpy._core.multiarray._reconstruct', 'numpy.ndarray', 'numpy.dtype',
             'numpy.dtypes.UInt32DType'}
    previous = torch.serialization.get_safe_globals()
    try:
        torch.serialization.clear_safe_globals()
        unsafe = set(torch.serialization.get_unsafe_globals_in_checkpoint(path))
        require(unsafe <= names, 'Unexpected pickle global; no automatic trust escalation')
        with torch.serialization.safe_globals(allowed):
            value = torch.load(path, map_location='cpu', weights_only=True)
    finally:
        torch.serialization.clear_safe_globals()
        torch.serialization.add_safe_globals(previous)
    arrays = [0]

    def check(v, trail=()):
        if isinstance(v, np.ndarray):
            require('rng' in trail and v.dtype == np.dtype('uint32') and v.shape == (624,),
                    'Only NumPy MT19937 uint32[624] under rng is permitted')
            arrays[0] += 1
        elif isinstance(v, torch.Tensor):
            require(v.device.type == 'cpu' and v.layout == torch.strided, 'Expected dense CPU tensor')
        elif type(v) is dict:
            for k, item in v.items():
                require(type(k) in (str, int), 'Unexpected dictionary key')
                check(item, trail + (str(k),))
        elif type(v) in (list, tuple):
            for item in v:
                check(item, trail)
        else:
            require(type(v) in (str, int, float, bool, type(None)), 'Unexpected state object')
    check(value)
    require(sha(path) == expected['sha256'], 'Checkpoint changed during inspection')
    return value, arrays[0]


def validate_record(state, row):
    require(isinstance(state, dict), 'Checkpoint must be a dictionary')
    identity = state['identity']
    if row['family'] == 'methods_fixed24':
        require(state['schema'] == 'A1_NEW_METHOD_STATE_V1', 'Unknown method schema')
        dataset, arm, seed = row['unit'].split('__')
        config = identity['config']
        require(state['arm'] == arm and config['arm'] == arm and config['dataset'] == dataset
                and config['seed'] == int(seed[1:]), 'Method unit mismatch')
        require(identity['config_sha256'] == hashlib.sha256(json.dumps(
            config, sort_keys=True, separators=(',', ':')).encode()).hexdigest(), 'Config digest mismatch')
        if row['epoch'] is not None:
            require(state['progress']['epoch'] == row['epoch'], 'Method epoch mismatch')
    else:
        require(identity['unit'] == row['unit'], 'Core/spectral unit mismatch')
        require(state['schema_version'] == 1 and state['epoch'] == row['epoch']
                and state['global_step'] == row['global_step'], 'Epoch/step/schema mismatch')
        if row['family'] == 'scientific_extension':
            require(state['extension']['reference_sha256'] == identity['reference_sha256'],
                    'Spectral reference identity mismatch')


def modules():
    """Import only bundled, hashed project sources; no caller-provided code."""
    for row in read(HERE / 'SourceProvenance.json')['sources']:
        path = inside(HERE, row['path'])
        require(path.stat().st_size == row['bytes'] and sha(path) == row['sha256'],
                'Bundled project source changed: ' + row['path'])
    name = '_a1_release_support_extensions'
    package = types.ModuleType(name)
    package.__path__ = [str(HERE / 'sources/core_spectral/extensions')]
    sys.modules[name] = package
    spec = importlib.util.spec_from_file_location(name + '.runner',
        HERE / 'sources/core_spectral/extensions/runner.py')
    core = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = core
    spec.loader.exec_module(core)
    spec = importlib.util.spec_from_file_location('_a1_release_support_methods',
        HERE / 'sources/methods/runtime.py')
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    return core, method


def build_shape(state, row):
    """Construct the real recorded CLIP topology on meta, without base weights."""
    import torch
    from transformers import CLIPConfig, CLIPModel
    require(sha(HERE / 'BaseConfig.json') == read(HERE / 'FoundationLock.json')['model_assets']['config.json'],
            'Bundled base configuration differs from foundation lock')
    core, method = modules()
    with torch.device('meta'):
        base = CLIPModel(CLIPConfig.from_dict(read(HERE / 'BaseConfig.json')))
        model, session = wrap(base, state, row, core, method)
    return model, session


def wrap(base, state, row, core, method):
    if row['family'] == 'methods_fixed24':
        return method.MethodCLIP(base, state['arm']), None
    mode = 'lora_both' if row['family'] == 'scientific_extension' else row['unit'].split('__')[1]
    model = core.core_model.AdaptedCLIP(base, mode)
    session = None
    if row['family'] == 'scientific_extension':
        identity = state['identity']
        session = core.ExtensionSession(model, identity['cell']['preset'],
            identity['cell']['gate_mode'], text_eos_token_id=identity['text_eos_token_id'])
    return model, session


def tensor_inventory(actual, saved, name):
    import torch
    require(set(actual) == set(saved), name + ' key inventory mismatch')
    for key, target in actual.items():
        value = saved[key]
        require(isinstance(value, torch.Tensor) and target.shape == value.shape
                and target.dtype == value.dtype and torch.isfinite(value).all().item(),
                name + ' shape/dtype/finiteness mismatch: ' + key)


def inspect_shape(state, row):
    model, session = build_shape(state, row)
    params = {k: p for k, p in model.named_parameters() if p.requires_grad}
    tensor_inventory(params, state['trainable'], 'Trainable')
    if row['family'] == 'methods_fixed24':
        tensor_inventory(dict(model.named_buffers()), state['buffers'], 'Buffer')
        fixed = {k: p for k, p in model.named_parameters()
                 if not p.requires_grad and k.startswith(('routers.', 'rotaries.'))}
        tensor_inventory(fixed, state['fixed_method_parameters'], 'Fixed method parameter')
        frozen = {k: {'shape': list(p.shape), 'dtype': str(p.dtype)}
                  for k, p in model.named_parameters() if not p.requires_grad}
        require(frozen == state['frozen_manifest'], 'Frozen parameter shape manifest mismatch')
    else:
        require(state['trainable_manifest'] == {k: {'shape': list(p.shape), 'dtype': str(p.dtype)}
                for k, p in params.items()}, 'Trainable manifest mismatch')
        if session:
            for key, gate in session.controller.gates.items():
                tensor_inventory(dict(gate.named_buffers()), state['extension']['buffers'][key], 'Gate buffer')
    return {'trainable_tensors': len(params), 'topology_verified': True,
            'foundation_weights_loaded': False, 'parameters_restored': False}


def copy_trainables(model, saved):
    import torch
    params = {k: p for k, p in model.named_parameters() if p.requires_grad}
    tensor_inventory(params, saved, 'Trainable')  # Check every entry before mutation.
    with torch.no_grad():
        for key, parameter in params.items():
            parameter.copy_(saved[key])
    require(all(torch.equal(p.detach().cpu(), saved[k]) for k, p in params.items()),
            'Post-copy trainable equality failed')


def restore_parameters(state, row, base_path):
    """Restore tensors with exact base content binding, but do not certify replay."""
    import torch
    from transformers import CLIPModel
    lock = read(HERE / 'FoundationLock.json')['model_assets']
    identity = state['identity']
    recorded = identity['config']['model_assets'] if row['family'] == 'methods_fixed24' else identity['model_files']
    require(recorded == lock, 'Checkpoint foundation binding differs from shipped lock')
    for name, digest in lock.items():
        require(sha(inside(base_path, name)) == digest, 'External foundation hash mismatch: ' + name)
    # Reject loader overrides not recorded in the pinned foundation lock.
    loader_files = {p.name for p in Path(base_path).iterdir() if p.is_file() and
                    (p.suffix in ('.json', '.bin', '.safetensors') or p.name == 'chat_template.jinja')}
    require(loader_files <= set(lock), 'Unlisted foundation loader override')
    core, method = modules()
    base = CLIPModel.from_pretrained(str(base_path), local_files_only=True, weights_only=True,
        use_safetensors=False, attn_implementation='eager', dtype=torch.float32)
    model, session = wrap(base, state, row, core, method)
    if row['family'] == 'methods_fixed24':
        # Original checks include frozen-content digest, fixed method values and
        # every buffer. The producer-signature gate remains separate (see README).
        method._validate_state(state, model, identity)
    elif session:
        extra = state['extension']
        session.controller.load_references(extra['payload'])
        require(core._buffers_equal(extra['buffers'], session.reference_buffers()),
                'Restored spectral references differ from checkpoint buffers')
    copy_trainables(model, state['trainable'])
    if row['state'] == 'frozen_baseline':
        # Native function role is not the adapted epoch-zero function, even
        # when both roles share identical serialized bytes.
        for module in model.modules():
            if isinstance(module, core.core_model.LoRALinear):
                module.enabled = False
        if session:
            model._release_native_context = session.native()
            model._release_native_context.__enter__()
    model.eval()
    return model, session


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inventory', 'inspect', 'restore'))
    parser.add_argument('--manifest', help='v3.4 ScalarRecords.zip or CheckpointManifest.json')
    parser.add_argument('--family', choices=('scientific_core', 'scientific_extension', 'methods_fixed24'))
    parser.add_argument('--unit')
    parser.add_argument('--state')
    parser.add_argument('--payload-root', type=Path)
    parser.add_argument('--payload-index', type=Path,
                        help='StateIndex.json with logical_state_records, or SHA256 -> relative path JSON')
    parser.add_argument('--payload', type=Path, help='Explicit local file, still checked against record SHA/size')
    parser.add_argument('--base-model', type=Path, help='Already obtained exact locked foundation directory')
    args = parser.parse_args()
    rows = manifest_rows(args.manifest)
    if args.action == 'inventory':
        result = {'logical_records': len(rows),
                  'unique_recorded_serializations': len({payload_record(r)['sha256'] for r in rows}),
                  'unique_non_latest_payloads': len({payload_record(r)['sha256'] for r in rows
                                                    if r['state'] != 'latest'}),
                  'latest_alias_records': sum(r['state'] == 'latest' for r in rows),
                  'units_by_family': {f: len({r['unit'] for r in rows if r['family'] == f})
                    for f in sorted({r['family'] for r in rows})}}
    else:
        # All state commands are CPU-only; no global environment installation/change.
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        import torch
        torch.set_num_threads(2)
        row = select(rows, args.family, args.unit, args.state)
        require(args.payload is not None or args.payload_root is not None, 'A local payload is required')
        path = args.payload or resolve_payload(row, args.payload_root, args.payload_index)
        state, arrays = safe_load(path, payload_record(row))
        validate_record(state, row)
        result = dict(family=row['family'], unit=row['unit'], state=row['state'],
                      payload=payload_record(row), numpy_rng_arrays=arrays, **inspect_shape(state, row))
        if args.action == 'restore':
            require(args.base_model is not None, '--base-model is required for restoration')
            model, session = restore_parameters(state, row, args.base_model)
            result.update(parameters_restored=True, foundation_weights_loaded=True)
        require(not torch.cuda.is_initialized(), 'Unexpected CUDA initialization')
        result.update(cuda_initialized=False, optimizer_restored=False, rng_installed=False,
                      full_forward_replay=False, resume_acceptance=False,
                      producer_signature_acceptance=False)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
