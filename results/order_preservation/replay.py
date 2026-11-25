"""Offline scalar, configuration and identity replay with no model or training."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def require(value, message):
    if not value:
        raise ValueError(message)


def identity(path):
    with Path(path).open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return dict(bytes=Path(path).stat().st_size, sha256=digest)


def verify_inputs():
    records = json.loads((HERE / 'Records.json').read_text(encoding='utf-8'))
    spec = importlib.util.spec_from_file_location('public_safe_archive', HERE / 'safe_archive.py')
    safe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(safe)
    for name, expected in records['archives'].items():
        safe.safe_names([__import__('zipfile').ZipInfo(name)])
        path = HERE / name
        require(identity(path) == expected['archive'], 'Archive identity mismatch: ' + name)
        actual = safe.inspect(path)
        require(actual['files'] == expected['members'], 'Archive member mismatch: ' + name)
    return records, safe


def execute(output):
    output = Path(output).resolve()
    require(not output.exists() and not output.is_relative_to(HERE), 'Output must be a new directory outside the input group')
    records, safe = verify_inputs()
    output.mkdir(parents=True)
    roles = records['roles']
    for role, name in roles.items():
        safe.extract(HERE / name, output / role, records['archives'][name]['members'])
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
        OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2')
    commands = [
        ['statistical/replay_current.py', '--output', 'scalar_results'],
        ['recipes/portable.py', 'replay', '--root', 'recipes', '--output', 'recipe_results'],
        ['acquisition/validate_inputs_v3.py', '--manifest-sha256', records['input_manifest_sha256']],
        ['scalar_results/baseline/run_canonical_scalar.py'],
        ['-m', 'unittest', 'discover', '-s', 'statistical', '-p', 'test_current.py', '-v'],
        ['-m', 'unittest', 'discover', '-s', 'recipes', '-p', 'test_portable.py', '-v'],
        ['-m', 'unittest', 'discover', '-s', 'acquisition', '-p', 'test_portable_v3.py', '-v'],
    ]
    completed = []
    for arguments in commands:
        command = [sys.executable, '-B', '-I', '-X', 'utf8', *arguments]
        process = subprocess.run(command, cwd=output, env=environment, capture_output=True,
            text=True, encoding='utf-8', timeout=600)
        completed.append(dict(command=arguments, exit_code=process.returncode,
            stdout=process.stdout, stderr=process.stderr))
        (output / 'Commands.json').write_text(json.dumps(completed, indent=2) + '\n', encoding='utf-8')
        require(process.returncode == 0, 'Replay command failed: ' + repr(arguments) + '\n' + process.stdout + process.stderr)
    scalar = json.loads((output / 'scalar_results/Replay.json').read_text(encoding='utf-8'))
    require(scalar['status'] == 'PASS_CURRENT_STATISTICAL_TIER_SCALAR_REPLAY', 'Scalar replay did not pass')
    report = dict(status='PASS_CURRENT_PUBLIC_SCALAR_RECIPE_AND_IDENTITY_REPLAY',
        code='v3.4', command_count=len(completed), scalar_status=scalar['status'],
        new_model_inference=False, new_training=False, network_required=False,
        boundary='Recorded scalar arithmetic and recipe/input-identity validation only; no arrays, states, full retraining or cross-hardware certification.')
    (output / 'PublicReplay.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New external directory to retain extracted inputs and replay tables')
    parser.add_argument('--integrity-only', action='store_true')
    args = parser.parse_args()
    if args.integrity_only:
        records, _ = verify_inputs()
        print(json.dumps(dict(status='PASS_ARCHIVE_IDENTITIES', archives=len(records['archives'])), indent=2))
    elif args.output:
        execute(args.output)
    else:
        with tempfile.TemporaryDirectory(prefix='alignment_v34_') as temporary:
            execute(Path(temporary) / 'work')


if __name__ == '__main__':
    main()
