# -*- coding: utf-8 -*-
r"""Minimal ASAR reader: list and extract files from the packaged DSH app.

ASAR layout: [uint32 4][uint32 header_size][uint32 payload_size][uint32 str_len][header JSON padded] then file data.
Used here only to read the app's own documentation and typings, so the progress panel can be written against the real
client-plugin API instead of guessed.
"""
import io
import json
import os
import struct
import sys

ASAR = r"E:\DSH\resources\app.asar"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tmp_asar")


def read_header(path=ASAR):
    with open(path, "rb") as fh:
        head = fh.read(16)
        _a, header_size, _payload, str_len = struct.unpack("<4I", head)
        raw = fh.read(str_len)
    header = json.loads(raw.decode("utf-8"))
    base = 16 + str_len
    return header, base


def walk(node, prefix=""):
    for name, meta in node.get("files", {}).items():
        p = prefix + "/" + name if prefix else name
        if "files" in meta:
            yield from walk(meta, p)
        else:
            yield p, meta


def extract(meta, base, dest):
    with open(ASAR, "rb") as fh:
        fh.seek(base + int(meta["offset"]))
        data = fh.read(int(meta["size"]))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as out:
        out.write(data)
    return len(data)


def main():
    header, base = read_header()
    files = list(walk(header))
    print("files in asar:", len(files))
    pats = sys.argv[1:] or ["dsh-client-modules", "sidebar", "plugin"]
    for p, meta in files:
        low = p.lower()
        if any(k.lower() in low for k in pats):
            print("  %-96s %8d" % (p, int(meta["size"])))


if __name__ == "__main__":
    main()
