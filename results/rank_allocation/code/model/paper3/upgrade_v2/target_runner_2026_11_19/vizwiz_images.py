"""Verify official VizWiz ZIP indices with bounded HTTP byte-range reads."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from tempfile import TemporaryDirectory
from zipfile import ZipFile

BASE = "https://vizwiz.cs.colorado.edu/VizWiz_final/images/"
PINS = {"train": (11298421598, '"2a1703b5e-59afdc1e58080"'),
        "test": (3975272799, '"ecf1d95f-59afd88518300"')}
MAX_READ = 16 * 1024 * 1024
REQUEST_BYTES = 512 * 1024


def check_response(headers, start, end, size, etag, data):
    status = re.findall(r"(?im)^HTTP/\S+ (\d{3})(?: |\r?$)", headers)
    if (not status or status[-1] != "206" or len(data) != end + 1 - start
            or re.findall(r"(?im)^Content-Range:[ \t]*([^\r\n]+)", headers) != [f"bytes {start}-{end}/{size}"]
            or re.findall(r"(?im)^ETag:[ \t]*([^\r\n]+)", headers) != [etag]):
        raise ValueError("Wrong HTTP status, archive pin, range or byte count")


class RangeArchive:
    def __init__(self, size, fetch):
        self.size = size
        self.fetch = fetch
        self.position = 0

    def tell(self):
        return self.position

    def seekable(self):
        return True

    def seek(self, offset, whence=io.SEEK_SET):
        location = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.size}[whence] + offset
        if location < 0:
            raise ValueError("Negative file position")
        self.position = location
        return self.position

    def read(self, count=-1):
        start = self.position
        count = max(0, self.size - start if count < 0 else min(count, self.size - start))
        if not count:
            return b""
        if count > MAX_READ:
            raise ValueError("Oversized archive read")
        data = self.fetch(start, start+count-1)
        if len(data) != count:
            raise ValueError("Truncated archive read")
        self.position += count
        return data


def official_fetch(split, *, parallel=True):
    size, etag = PINS[split]
    url = BASE + split + ".zip"

    def fetch_one(segment):
        start, end = segment
        with TemporaryDirectory(prefix="p3-vizwiz-range-") as temp:
            headers = Path(temp)/"headers"
            body = Path(temp)/"body"
            subprocess.run(["curl.exe", "--fail", "--silent", "--show-error", "--connect-timeout", "12",
                            "--max-time", "60", "--max-filesize", str(end-start+1), "--header", f"If-Range: {etag}",
                            "--range", f"{start}-{end}", "-D", str(headers), "-o", str(body), url], check=True)
            data = body.read_bytes()
            check_response(headers.read_text(encoding="iso-8859-1"), start, end, size, etag, data)
            return data

    def fetch(start, end):
        if not 0 <= start <= end < size or end - start >= MAX_READ:
            raise ValueError("Read outside the pinned archive and byte limit")
        segments = [(i, min(i + REQUEST_BYTES - 1, end)) for i in range(start, end + 1, REQUEST_BYTES)]
        if len(segments) == 1:
            return fetch_one(segments[0])
        if not parallel:
            return b"".join(map(fetch_one, segments))
        with ThreadPoolExecutor(max_workers=4) as pool:
            return b"".join(pool.map(fetch_one, segments))

    return fetch


def open_official(split):
    return ZipFile(RangeArchive(PINS[split][0], official_fetch(split)))


def image_members(archive, split):
    rows = []
    for member in archive.infolist():
        p = PurePosixPath(member.filename)
        if not member.is_dir() and re.fullmatch(fr"VizWiz_{split}_\d+\.jpg", p.name):
            if p.is_absolute() or ".." in p.parts or "\\" in member.filename or member.flag_bits & 1:
                raise ValueError("Unsafe ZIP image member")
            rows.append((p.name, member.filename, member.file_size, member.compress_size, member.CRC))
    if not rows or len({row[0] for row in rows}) != len(rows):
        raise ValueError("Missing or ambiguous official image members")
    return sorted(rows)


def inspect(split):
    with open_official(split) as archive:
        rows = image_members(archive, split)
        size, etag = PINS[split]
        result = {"url": BASE + split + ".zip", "bytes": size, "etag": etag, "unique_image_members": len(rows),
                  "index_sha256": hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()}
        if split == "train":
            _, path, bytes_expected, _, crc = rows[0]
            payload = archive.read(path)  # ZipFile validates the member CRC.
            if len(payload) != bytes_expected or not payload.startswith(b"\xff\xd8"):
                raise ValueError("Unexpected training image payload")
            result["train_member_probe"] = {"file": path, "bytes": bytes_expected, "crc32": f"{crc:08x}",
                                             "sha256": hashlib.sha256(payload).hexdigest()}
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    if args.receipt.exists():
        parser.error("Select a new receipt path")
    result = {"scope": "OFFICIAL_IMAGE_ZIP_INDEX_AND_ONE_TRAIN_MEMBER_ONLY",
              "archives": {split: inspect(split) for split in PINS},
              "annotation_bytes_read": False, "test_image_members_read": False, "scientific_result": None}
    with args.receipt.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
    print("PASS: both official ZIP indices and one training-image CRC verified over HTTP ranges")


if __name__ == "__main__":
    main()
