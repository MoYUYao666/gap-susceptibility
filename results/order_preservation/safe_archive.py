"""Bounded ZIP reader with Windows-portable path, CRC and SHA checks."""
import hashlib
import json
import re
import stat
from pathlib import Path, PurePosixPath
import zipfile

MAX_FILES = 1000
MAX_TOTAL = 512 * 1024**2
MAX_MEMBER = 192 * 1024**2


def require(value, message):
    if not value:
        raise ValueError(message)


def safe_names(infos):
    require(0 < len(infos) <= MAX_FILES, 'Archive member count bound')
    seen = set()
    total = 0
    for item in infos:
        name = item.filename
        require(item.orig_filename == name, 'Archive name normalization forbidden')
        p = PurePosixPath(name)
        require(name and not name.endswith('/') and '\\' not in name and not p.is_absolute(), 'Unsafe archive path')
        require(all(x not in ('', '.', '..') and ':' not in x and x.rstrip(' .') == x for x in name.split('/')), 'Unsafe archive component')
        require(not any(ord(c) < 32 for c in name), 'Control character in member')
        for part in p.parts:
            require(not re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part), 'Windows reserved path')
        key = name.casefold()
        require(key not in seen, 'Duplicate/case-colliding member')
        seen.add(key)
        require(not item.flag_bits & 1, 'Encrypted ZIP forbidden')
        mode = item.external_attr >> 16
        require(not stat.S_ISLNK(mode), 'Symlink ZIP member forbidden')
        require(item.file_size <= MAX_MEMBER, 'Member expansion bound')
        total += item.file_size
    require(total <= MAX_TOTAL, 'Total ZIP expansion bound')
    for name in seen:
        require(not any(parent in seen for parent in (str(p).casefold() for p in PurePosixPath(name).parents if str(p) != '.')), 'File/directory prefix collision')
    return total


def identity(data):
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def inspect(path):
    with zipfile.ZipFile(path) as z:
        total = safe_names(z.infolist())
        require(z.testzip() is None, 'ZIP CRC failure')
        files = {i.filename: identity(z.read(i)) for i in z.infolist()}
    return dict(members=len(files), expanded_bytes=total, files=files)


def extract(path, target, expected=None):
    target = Path(target)
    require(not target.exists(), 'Extraction requires a new target')
    report = inspect(path)
    if expected is not None:
        require(report['files'] == expected, 'Archive member SHA/size mismatch')
    target.mkdir(parents=True)
    root = target.resolve()
    with zipfile.ZipFile(path) as z:
        for item in z.infolist():
            p = target / item.filename
            require(p.resolve().is_relative_to(root), 'Extraction path escape')
            p.parent.mkdir(parents=True, exist_ok=True)
            data = z.read(item)
            p.write_bytes(data)
            require(identity(p.read_bytes()) == report['files'][item.filename], 'Extracted member changed')
    return report


def verify_tree(root):
    root = Path(root)
    doc = json.loads((root / 'MemberSHA256.json').read_bytes())
    for name, expected in doc['files'].items():
        safe_names([zipfile.ZipInfo(name)])
        p = root / name
        require(not p.is_symlink() and p.resolve().is_relative_to(root.resolve()), 'Member alias/escape')
        require(identity(p.read_bytes()) == expected, 'Package member drift: ' + name)
    return len(doc['files'])
