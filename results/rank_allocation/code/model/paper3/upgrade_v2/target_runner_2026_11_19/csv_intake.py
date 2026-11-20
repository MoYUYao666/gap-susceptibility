"""Stage pinned train-only VizWiz data; never consume held-out caption fields."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from subprocess import CalledProcessError
from threading import local
from zipfile import ZipFile
import zlib

from PIL import Image

from score_release import sha
from vizwiz_images import MAX_READ, PINS, RangeArchive, image_members, official_fetch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW_SHA = "253552720a88f73c667f00b3c91c30902377f87767b294c1cdf8b9ad97af1155"
REQUIRED = ("ID", "IMG", "IS_REJECTED", "IMG_CAPTION", "IMG_CAPTION_SPELLCHECKED", "TRAIN_VAL_TEST")
PRE_CANNED = "quality issues are too severe to recognize visual content"
IMAGE_PATTERN = r"VizWiz_{split}_[0-9]+\.jpg"
CAL_COUNT, FIT_COUNT = 16, 512


def digest(data):
    return hashlib.sha256(data).hexdigest()


def precanned(raw):
    return " ".join(raw.casefold().split()).removesuffix(".") == PRE_CANNED


def train_rows(path):
    audit, ids, rows = Counter(), set(), {}
    with path.open(encoding="latin-1", newline="") as f:
        reader = csv.reader(f, strict=True)
        cols = next(reader)
        if len(cols) != len(set(cols)) or not set(REQUIRED).issubset(cols):
            raise ValueError("Unexpected CSV schema")
        aid, img, rejected, raw, corrected, split = map(cols.index, REQUIRED)
        for row in reader:
            if len(row) != len(cols):
                raise ValueError("Nonrectangular metadata CSV")
            if row[split].strip().casefold() != "train":
                continue
            audit["train_marker_rows"] += 1
            name = row[img]
            if not re.fullmatch(IMAGE_PATTERN.format(split="train"), name):
                audit["train_marker_wrong_image_prefix"] += 1
                if re.fullmatch(IMAGE_PATTERN.format(split="test"), name):
                    audit["train_marker_test_prefix"] += 1
                continue
            if not re.fullmatch(r"[0-9]+", row[aid]):
                raise ValueError("Invalid train annotation ID")
            index = int(row[aid])
            if index in ids:
                raise ValueError("Duplicate train annotation ID")
            ids.add(index)
            if row[rejected] not in ("0", "1"):
                raise ValueError("Unknown train rejection flag")
            if row[rejected] == "1" or precanned(row[raw]) or precanned(row[corrected]) or not row[corrected].strip():
                audit["train_filtered_caption_rows"] += 1
                continue
            caption = row[corrected].encode("latin-1").decode("cp1252").strip()
            if not caption or any(ord(c) < 32 and c not in "\n\r\t" for c in caption):
                raise ValueError("Invalid spelling-checked caption encoding or control character")
            audit["train_eligible_caption_rows"] += 1
            if name not in rows or index < rows[name][0]:
                rows[name] = (index, caption)
    if not rows:
        raise ValueError("No eligible training rows")
    return rows, {**audit, "eligible_train_names_before_zip_join": len(rows),
                  "evaluation_caption_fields_accessed": False}


def sorted_candidates(names, archive_names, split):
    return sorted(set(names) & archive_names, key=lambda n: (digest(f"P3-VizWiz-Pilot-v1:{split}:{n}".encode()), n))


def fingerprint(payload):
    with Image.open(io.BytesIO(payload)) as img:
        rgb = img.convert("RGB")
        header = f"RGB:{rgb.width}:{rgb.height}:".encode("ascii")
        px = digest(header + rgb.tobytes())
        pixels = rgb.convert("L").resize((9, 8), Image.Resampling.LANCZOS).tobytes()
    bits = 0
    for y in range(8):
        for x in range(8):
            i = 9*y+x
            bits = 2*bits + (pixels[i] > pixels[i+1])
    return {"raw_sha256": digest(payload), "pixel_sha256": px, "dhash64": f"{bits:016x}"}


def overlap(record, admitted):
    for k, label in (("raw_sha256", "raw_duplicate"), ("pixel_sha256", "pixel_duplicate")):
        if any(row[k] == record[k] for row in admitted):
            return label
    value = int(record["dhash64"], 16)
    if any((value ^ int(row["dhash64"], 16)).bit_count() <= 4 for row in admitted):
        return "dhash_near_duplicate"
    return None


class ZipMembers:
    """Reuse only central metadata; validate each independent range window with zipfile CRC."""

    def __init__(self, split, *, fetch_index=None, fetch_data=None, size=None, expected_digest=None):
        self.size = PINS[split][0] if size is None else size
        fetch_index = fetch_index or official_fetch(split)
        self.fetch_data = fetch_data or official_fetch(split, parallel=False)
        self.index = {}
        self.worker = local()

        def capture(start, end):
            key = start, end
            if key not in self.index:
                self.index[key] = fetch_index(start, end)
            return self.index[key]

        with ZipFile(RangeArchive(self.size, capture)) as z:
            rows = image_members(z, split)
            self.index_sha256 = digest(json.dumps(rows, separators=(",", ":")).encode())
            if expected_digest is not None and self.index_sha256 != expected_digest:
                raise ValueError("ZIP member index differs from the pinned release")
            offsets = sorted({i.header_offset for i in z.infolist()})
            ends = dict(zip(offsets, offsets[1:] + [self.size], strict=True))
            self.members = {}
            for name, path, nbytes, _, crc in rows:
                start = z.getinfo(path).header_offset
                self.members[name] = (path, nbytes, crc, start, ends[start])

    def read(self, name):
        path, nbytes, _, start, end = self.members[name]
        if not 0 < end-start <= MAX_READ or not 0 < nbytes <= MAX_READ:
            raise ValueError("ZIP member outside bounded extraction range")
        if not hasattr(self.worker, "zip"):
            def serve(lo, hi):
                if (lo, hi) in self.index:
                    return self.index[lo, hi]
                base, data = self.worker.window
                if not base <= lo <= hi < base + len(data):
                    raise ValueError("Member read exceeded the pinned window")
                return data[lo-base:hi-base+1]
            self.worker.zip = ZipFile(RangeArchive(self.size, serve))
        for attempt in range(3):
            try:
                self.worker.window = start, self.fetch_data(start, end-1)
                break
            except CalledProcessError:
                if attempt == 2:
                    raise
        try:
            payload = self.worker.zip.read(path)
            if len(payload) != nbytes or not payload.startswith(b"\xff\xd8"):
                raise ValueError("Unexpected JPEG payload")
            return payload
        finally:
            self.worker.window = 0, b""


def emit(path, record):
    with path.open("x", encoding="utf-8", newline="\n") as out:
        json.dump(record, out, indent=2, ensure_ascii=False, allow_nan=False)
        out.write("\n")


def read_or_get_image(archive, path):
    cached = path.exists()
    payload = path.read_bytes() if cached else archive.read(path.name)
    _, nbytes, crc, _, _ = archive.members[path.name]
    if len(payload) != nbytes or zlib.crc32(payload) != crc:
        raise ValueError("Cached image size or CRC differs from official member")
    marks = fingerprint(payload)
    if not cached:
        pending = path.with_suffix(".part")
        with pending.open("xb") as f:
            f.write(payload)
        pending.rename(path)
    return marks


def acquire(csv_path, out, *, smoke, workers):
    if out == ROOT or out.is_relative_to(ROOT):
        raise ValueError("Dataset and private manifests must stay outside the project tree")
    if sha(csv_path) != RAW_SHA:
        raise ValueError("Publisher CSV SHA-256 mismatch")
    rows, audit = train_rows(csv_path)
    receipt = out/("IntakeSmoke.json" if smoke else "TrainManifest.json")
    if receipt.exists():
        raise ValueError("Frozen manifest already exists; do not overwrite")
    cache = out/"train_images"
    cache.mkdir(parents=True, exist_ok=True)
    source = ROOT/"data/marine_captions"
    pinned = json.loads((HERE/"FitSmoke.json").read_bytes())["inputs_sha256"]
    source_marks = [fingerprint((source/name).read_bytes()) for name in sorted(pinned)]
    if {n: m["raw_sha256"] for n, m in zip(sorted(pinned), source_marks, strict=True)} != pinned:
        raise ValueError("Source pool hash mismatch")
    print("Train-only CSV parse verified; fetching the pinned train ZIP index.", flush=True)
    index = json.loads((HERE/"VizWizImageIndex.json").read_bytes())
    archive = ZipMembers("train", expected_digest=index["archives"]["train"]["index_sha256"])
    candidates = sorted_candidates(rows, set(archive.members), "train")
    limit = 4 if smoke else CAL_COUNT+FIT_COUNT
    if len(candidates) < limit:
        raise ValueError("Insufficient train candidates")
    picks, rejects = [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for base in range(0, len(candidates), workers):
            window = candidates[base:base+workers]
            batch = pool.map(lambda n: read_or_get_image(archive, cache/n), window)
            for name, marks in zip(window, batch, strict=True):
                reason = overlap(marks, [*source_marks, *picks])
                if reason:
                    rejects.append({"image": name, "reason": reason})
                    continue
                row_id, text = rows[name]
                picks.append({"image": name, "annotation_id": row_id, "caption": text,
                              "caption_sha256": digest(text.encode()), **marks})
                if len(picks) == limit:
                    break
            print(f"Verified ordered train staging: {len(picks)}/{limit} admitted; {len(rejects)} excluded.", flush=True)
            if len(picks) == limit:
                break
    if len(picks) != limit:
        raise ValueError("Too few content-separated train images")
    cal_n = 2 if smoke else CAL_COUNT
    emit(receipt, {"mode": "VIZWIZ_TRAIN_ACQUISITION_SMOKE" if smoke else "VIZWIZ_TRAIN_ONLY_MANIFEST",
                   "scientific_result": None, "csv_sha256": RAW_SHA, "train_zip_index_sha256": archive.index_sha256,
                   "csv_routing": audit, "candidate_count": len(candidates),
                   "candidate_order_sha256": digest("\n".join(candidates).encode()),
                   "source_image_sha256": pinned, "transport_workers": workers,
                   "script_sha256": {n: sha(HERE/n) for n in ("csv_intake.py", "vizwiz_images.py", "CsvIntakePlan.md",
                                     "FitPlan.md", "ProjectedSource.json", "fit.py", "runner.py", "qualify.py", "score_release.py")},
                   "calibration": picks[:cal_n], "train": picks[cal_n:], "exclusions": rejects})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("staging", type=Path)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--workers", type=int, choices=(1, 2, 3, 4), default=4)
    args = parser.parse_args()
    acquire(args.csv.resolve(strict=True), args.staging.resolve(), smoke=args.smoke, workers=args.workers)


if __name__ == "__main__":
    main()
