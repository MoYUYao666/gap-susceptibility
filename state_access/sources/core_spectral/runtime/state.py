"""Hashed, atomic epoch transactions and weights-only checkpoint recovery."""
import contextlib
import json
import os
import platform
import random
import shutil
import socket
from pathlib import Path

import numpy as np
import torch

from model import get_trainable_state, restore_trainable, trainable_manifest
from records import canonical, digest_file


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('wb') as handle:
        handle.write(canonical(value) + b'\n')
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary,path)


def atomic_text(path,value):
    path = Path(path)
    temporary = path.with_name(path.name+'.tmp')
    with temporary.open('w',encoding='ascii',newline='\n') as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary,path)


def rng_state(device):
    algorithm, keys, position, has_gauss, cached = np.random.get_state()
    return dict(python=random.getstate(), numpy=dict(algorithm=algorithm,
        keys=torch.tensor(keys.astype(np.int64)), position=position,
        has_gauss=has_gauss, cached=cached), torch_cpu=torch.get_rng_state(),
        torch_cuda=torch.cuda.get_rng_state_all() if device.type == 'cuda' else [])


def restore_rng(state, device):
    random.setstate(state['python'])
    data = state['numpy']
    np.random.set_state((data['algorithm'],data['keys'].numpy().astype(np.uint32),
                         data['position'],data['has_gauss'],data['cached']))
    torch.set_rng_state(state['torch_cpu'])
    if device.type == 'cuda':
        torch.cuda.set_rng_state_all(state['torch_cuda'])


def checkpoint_state(model, optimizer, scheduler, epoch, global_step, identity, device):
    return dict(schema_version=1, trainable=get_trainable_state(model),
        trainable_manifest=trainable_manifest(model), optimizer=optimizer.state_dict(),
        scheduler=scheduler.state_dict(), rng=rng_state(device), epoch=epoch,
        global_step=global_step, identity=identity)


def seal_directory(staging, target, receipt):
    staging, target = Path(staging), Path(target)
    if target.exists():
        raise FileExistsError(f'Committed output already exists: {target}')
    files = {path.relative_to(staging).as_posix():dict(sha256=digest_file(path),bytes=path.stat().st_size)
             for path in sorted(staging.rglob('*')) if path.is_file() and path.name not in ('Receipt.json','Receipt.sha256')}
    if not files:
        raise ValueError('Cannot commit empty epoch')
    atomic_json(staging/'Receipt.json',dict(receipt,files=files))
    atomic_text(staging/'Receipt.sha256',digest_file(staging/'Receipt.json')+'\n')
    os.replace(staging,target)


def verify_directory(directory):
    directory = Path(directory)
    if (directory/'Receipt.sha256').read_text(encoding='ascii').strip() != digest_file(directory/'Receipt.json'):
        raise ValueError(f'Receipt self hash mismatch: {directory}')
    receipt = json.loads((directory/'Receipt.json').read_text(encoding='utf-8'))
    actual = {path.relative_to(directory).as_posix() for path in directory.rglob('*') if path.is_file()
              and path.name not in ('Receipt.json','Receipt.sha256')}
    if not receipt['files'] or actual != set(receipt['files']):
        raise ValueError(f'Incomplete or unexpected committed files: {directory}')
    for relative, entry in receipt['files'].items():
        path = (directory/relative).resolve()
        if not path.is_relative_to(directory.resolve()) or not path.is_file():
            raise ValueError('Unsafe receipt path')
        if path.stat().st_size != entry['bytes'] or digest_file(path) != entry['sha256']:
            raise ValueError(f'Committed artifact hash mismatch: {path}')
    return receipt


def load_checkpoint(directory):
    verify_directory(directory)
    return torch.load(Path(directory)/'checkpoint.pt', map_location='cpu',weights_only=True)


def restore_checkpoint(checkpoint, model, optimizer, scheduler, identity, device):
    if checkpoint['identity'] != identity:
        raise ValueError('Checkpoint identity mismatch')
    if checkpoint['trainable_manifest'] != trainable_manifest(model):
        raise ValueError('Checkpoint trainable manifest mismatch')
    restore_trainable(model,checkpoint['trainable'])
    optimizer.load_state_dict(checkpoint['optimizer'])
    scheduler.load_state_dict(checkpoint['scheduler'])
    restore_rng(checkpoint['rng'],device)


def process_is_alive(pid):
    """A nondestructive process check, including on Windows (no os.kill there)."""
    if type(pid) is not int or pid <= 0:
        raise ValueError('Invalid lock PID')
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.OpenProcess.argtypes = (wintypes.DWORD,wintypes.BOOL,wintypes.DWORD)
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = (wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD))
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
        handle = kernel.OpenProcess(0x1000,False,pid)
        if not handle:
            if ctypes.get_last_error() == 87:
                return False
            raise RuntimeError('Cannot establish Windows lock owner status')
        try:
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle,ctypes.byref(code)):
                raise RuntimeError('Cannot query Windows lock owner')
            return code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid,0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextlib.contextmanager
def unit_lock(directory, resume):
    directory = Path(directory)
    lock = directory/'RUNNING.json'
    if lock.exists() and resume:
        existing = json.loads(lock.read_text(encoding='utf-8'))
        if existing['host'] != socket.gethostname():
            raise RuntimeError('Lock belongs to another host; verify owner before removing it')
        if not process_is_alive(existing['pid']):
            lock.unlink()
        else:
            raise RuntimeError('Unit is already running')
    descriptor = os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        with os.fdopen(descriptor,'wb') as handle:
            handle.write(canonical(dict(pid=os.getpid(),host=socket.gethostname())))
        yield
    finally:
        lock.unlink(missing_ok=True)


def discard_uncommitted(directory):
    """Only exact transaction staging children, never arbitrary parent paths."""
    directory = Path(directory).resolve()
    for path in directory.glob('.*.partial'):
        resolved = path.resolve()
        if resolved.parent != directory or path.is_symlink() or not path.is_dir():
            raise ValueError('Unsafe incomplete transaction')
        shutil.rmtree(resolved)


def environment(device):
    import transformers
    data = dict(python=platform.python_version(),torch=str(torch.__version__),
        transformers=transformers.__version__, numpy=np.__version__,
        device=str(device),threads=torch.get_num_threads(),platform=platform.platform(),
        precision='float32',deterministic_algorithms=True)
    if device.type == 'cuda':
        properties = torch.cuda.get_device_properties(device)
        data.update(gpu_name=properties.name,total_memory=properties.total_memory,
            capability=list(torch.cuda.get_device_capability(device)),
            cuda=torch.version.cuda,cudnn=torch.backends.cudnn.version(),
            precision='float32',
            visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
            device_count=torch.cuda.device_count())
    return data
