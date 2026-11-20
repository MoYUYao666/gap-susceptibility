"""Replay a bibliographic snapshot and a fixed-record eligibility roster offline."""

import argparse
from collections import Counter, defaultdict
import difflib
import hashlib
import json
from pathlib import Path
import re
from statistics import median

META = ("openalex_id", "doi", "title", "year", "venue", "authors", "n_authors",
        "cited_by", "type", "retracted", "found_by")
REGISTRY = ("title", "year", "container", "type", "title_similarity", "resolves")
DATACITE = ("10.5281", "10.6084", "10.34734", "10.48550", "10.71465")
THEMES = {
    "retrieval": ("retrieval", "image-text", "cross-modal retrieval", "text-image"),
    "captioning": ("caption", "description generation"),
    "vqa/instruction": ("question answering", "vqa", "instruction", "grounding", "grounded"),
    "pretraining": ("clip", "pre-training", "pretraining", "contrastive"),
    "datasets/benchmarks": ("dataset", "benchmark", "corpus"),
    "general VLM": ("vision-language", "vision language", "multimodal", "foundation"),
}
PATTERNS = {
    "RSICD": r"rsicd", "RSITMD": r"rsitmd", "NWPU-Captions": r"nwpu[- ]?captions?",
    "UCM-Captions": r"ucm[- ]?captions?", "Sydney-Captions": r"sydney[- ]?captions?",
    "AID": r"\baid\b", "DIOR": r"\bdior\b", "RS5M": r"rs5m", "RSICap": r"rsicap",
    "LEVIR-CC": r"levir",
}
EXCLUSIONS = {
    "W4408703454": "visual_only_adaptation_arm",
    "W7203720228": "non_english_body",
    "W4405887239": "text_only_adaptation_and_separate_multimodal_quantization",
    "W4402299662": "no_qualifying_adaptation_arm",
    "W4415397576": "no_visual_input_in_evaluated_model",
    "W4407182975": "non_english_body",
    "W7204444546": "no_qualifying_adaptation_arm",
    "W7163673823": "doctoral_thesis",
    "W4417277128": "supplement_abstract",
    "W7142875041": "indexed_repository_record",
}
DATA = ("harvest.json", "deduplicated.json", "doi_screen.json", "selection.json",
        "dataset_mentions.json", "fixed_sample.json")
PAYLOAD = (*DATA, "summary.json", "README.md", "replay.py")
SHA = re.compile(r"[0-9a-f]{64}")
WORK = re.compile(r"W[0-9]+")
DOI = re.compile(r"10\.\d{4,9}/[^\s]+")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def equal(actual, expected, label):
    require(actual == expected, f"{label} does not match recorded evidence")


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def exact_keys(obj, keys, label):
    equal(set(obj), set(keys), f"{label} schema")


def read_json(path):
    def unique(pairs):
        obj = dict(pairs)
        require(len(obj) == len(pairs), f"Duplicate key in {path.name}")
        return obj
    def nonfinite(token):
        raise ValueError(f"Nonfinite JSON constant in {path.name}: {token}")
    return json.loads(path.read_bytes(), object_pairs_hook=unique, parse_constant=nonfinite)


def normalize_title(value):
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", value.lower()).split())


def identifier(value):
    return value.removeprefix("https://openalex.org/")


def harvest_summary(raw, dedup):
    rebuilt = {}
    per_query = {}
    for query, records in raw.items():
        new = 0
        for row in records:
            exact_keys(row, META, "Harvest row")
            key = row["doi"] or row["openalex_id"]
            require(row["title"] and WORK.fullmatch(identifier(row["openalex_id"])),
                    f"Missing title or invalid identity: {key}")
            if row["doi"]:
                require(DOI.fullmatch(row["doi"]), f"Invalid DOI: {key}")
            if key not in rebuilt:
                rebuilt[key] = {**row, "found_by": []}
                new += 1
            if query not in rebuilt[key]["found_by"]:
                rebuilt[key]["found_by"].append(query)
        per_query[query] = {"n": len(records), "new": new}
    equal(rebuilt, dedup, "First-hit deduplication and merged query lists")
    for query, rows in raw.items():
        for row in rows:
            key = row["doi"] or row["openalex_id"]
            require(row["found_by"] in (rebuilt[key]["found_by"], [query]),
                    f"Unexpected archived query tag sequence: {key}")
    with_doi = sum(bool(r["doi"]) for r in dedup.values())
    return dict(n_queries=len(raw), n_raw=sum(len(rows) for rows in raw.values()),
                n_dedup=len(dedup), n_with_doi=with_doi, n_without_doi=len(dedup) - with_doi,
                n_retracted=sum(r["retracted"] for r in dedup.values()),
                overlap_ge2_queries=sum(len(r["found_by"]) >= 2 for r in dedup.values()),
                per_theme=per_query)


def doi_summary(dedup, screen):
    exact_keys(screen, ("title_similarity_threshold", "passed", "failed"), "DOI screen")
    threshold, passed, failed = (screen[k] for k in ("title_similarity_threshold", "passed", "failed"))
    equal(threshold, 0.80, "DOI title threshold")
    candidates = {k for k, r in dedup.items() if r["doi"]}
    require(not (passed.keys() & failed.keys()), "Conflicting DOI screen outcomes")
    equal(passed.keys() | failed.keys(), candidates, "DOI-screen coverage")
    for key, entry in passed.items():
        exact_keys(entry, ("registry", "registry_metadata", "bibkey"), "Passing DOI")
        equal(key, dedup[key]["doi"], "Passing DOI identity")
        equal(entry["registry"], "DataCite" if key.startswith(DATACITE) else "Crossref",
              "Registry routing")
        evidence = entry["registry_metadata"]
        exact_keys(evidence, REGISTRY, "Registry metadata")
        score = difflib.SequenceMatcher(
            None, normalize_title(evidence["title"]), normalize_title(dedup[key]["title"])).ratio()
        require(evidence["resolves"] is True and score >= threshold, f"Invalid DOI pass: {key}")
        equal(round(score, 3), evidence["title_similarity"], f"Archived title similarity for {key}")
    require(len({r["bibkey"] for r in passed.values()}) == len(passed), "Duplicate reference key")
    for key, entry in failed.items():
        exact_keys(entry, ("doi", "title", "error"), "Failing DOI")
        equal((entry["doi"], entry["title"]), (key, dedup[key]["title"]), "Failing DOI identity")
        require(entry["error"] in {"title mismatch", "HTTP Error 404: Not Found"},
                f"Unapproved failure classification: {key}")
    return dict(checked=len(candidates), verified=len(passed), failed=len(failed),
                title_similarity_threshold=threshold, failures=failed)


def theme_of(record):
    queries = [q.lower() for q in record["found_by"]]
    scores = {theme: sum(any(k in q for k in keys) for q in queries)
              for theme, keys in THEMES.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "other"


def trends_summary(dedup, screen, selection, mentions):
    verified = {key: dedup[key] for key in screen["passed"]}
    by_year = defaultdict(Counter)
    citation_years = defaultdict(list)
    citations = []
    publications = Counter()
    core = {}
    for group, records in selection.items():
        ids = set()
        for row in records:
            exact_keys(row, ("key", "matched_terms"), "Selection row")
            require(row["key"] in verified and row["key"] not in ids and row["matched_terms"],
                    f"Invalid selection row: {row['key']}")
            ids.add(row["key"])
        core[group] = ids
    for row in verified.values():
        year, n = row["year"], row["cited_by"] or 0
        if type(year) is int and year >= 2019:
            by_year[str(year)][theme_of(row)] += 1
        if type(year) is int:
            citation_years[str(year)].append(n)
        citations.append(n)
        publications[row["venue"].strip() or "unknown"] += 1
    hits = dict.fromkeys(PATTERNS, 0)
    matched = 0
    for doi, row in mentions.items():
        exact_keys(row, ("openalex_id", "title", "year", "datasets"), "Name-mention row")
        require(DOI.fullmatch(doi) and len(set(row["datasets"])) == len(row["datasets"]),
                f"Invalid mention record: {doi}")
        require(set(row["datasets"]) <= PATTERNS.keys(), f"Unknown dataset label: {doi}")
        matched += bool(row["datasets"])
        for name in row["datasets"]:
            hits[name] += 1
    citations.sort(reverse=True)
    return {
        "source_records": {"verified": len(verified), "deduplicated": len(dedup),
                           "abstracts": len(mentions)},
        "volume_by_year_theme": {y: dict(by_year[y]) for y in sorted(by_year)},
        "year_totals": {y: sum(by_year[y].values()) for y in sorted(by_year)},
        "top_venues": [{"venue": v, "records": n} for v, n in publications.most_common(10)],
        "citations": {"median_by_year": {y: median(citation_years[y]) for y in sorted(citation_years)},
                      "top10_share_of_citations": round(
                          sum(citations[:max(1, len(citations) // 10)]) / max(1, sum(citations)), 3),
                      "records": len(citations), "total_citations": sum(citations)},
        "dataset_name_mentions": {"n_abstracts": len(mentions), "n_with_dataset_mention": matched,
                                  "counts": hits},
        "screened_core": {group: len(ids) for group, ids in core.items()},
        "screened_core_unique": len(set().union(*core.values())),
        "mention_records_outside_verified": len(mentions.keys() - verified.keys()),
    }


def fixed_summary(sample):
    exact_keys(sample, ("sample_seed", "ordered_ids", "rates_authorized", "records"), "Fixed sample")
    rows = sample["records"]
    ids = [row["id"] for row in rows]
    equal(ids, sample["ordered_ids"], "Fixed roster and order")
    require(len(ids) == len(set(ids)) == 40, "Missing or duplicate fixed-sample IDs")
    require(sample["rates_authorized"] is False, "Field rates are not authorized")
    for row in rows:
        exact_keys(row, ("id", "doi", "status", "exclusion", "decision", "edition_sha256",
                         "edition_type", "identity_doi", "related_doi"), "Fixed-sample row")
        ident = row["id"]
        require(WORK.fullmatch(ident) and DOI.fullmatch(row["doi"]), f"Invalid fixed identity: {ident}")
        equal(row["exclusion"], EXCLUSIONS.get(ident), f"Exclusion for {ident}")
        equal(row["status"], "outside_scope" if ident in EXCLUSIONS else "eligible",
              f"Eligibility for {ident}")
        if row["status"] == "eligible" or row["edition_sha256"] is not None:
            require(SHA.fullmatch(row["edition_sha256"] or ""), f"Missing edition digest: {ident}")
        for field in ("identity_doi", "related_doi"):
            require(row[field] is None or DOI.fullmatch(row[field]), f"Invalid {field}: {ident}")
        exact_keys(row["decision"], ("source_path", "sha256", "locator"), "Decision locator")
        require(SHA.fullmatch(row["decision"]["sha256"]), f"Missing decision digest: {ident}")
    eligible = [r["id"] for r in rows if r["status"] == "eligible"]
    excluded = sorted(r["id"] for r in rows if r["status"] == "outside_scope")
    return dict(fixed_sample_n=len(ids), sample_seed=sample["sample_seed"],
                eligibility_counts={"eligible": len(eligible), "outside_scope": len(excluded)},
                eligible_ids=eligible, outside_scope_ids=excluded, unresolved_ids=[],
                rates_authorized=False)


def summarize(data):
    raw, dedup, screen, selection, mentions, sample = (data[name] for name in DATA)
    return {"harvest": harvest_summary(raw, dedup), "doi_screen": doi_summary(dedup, screen),
            "trends": trends_summary(dedup, screen, selection, mentions),
            "fixed_sample": fixed_summary(sample)}


def verify_bundle(directory):
    expected = set(PAYLOAD) | {"provenance.json"}
    # A GitHub integration may add unrelated files next to the bundle.
    for name in expected:
        require((directory / name).is_file(), f"Missing bundle file: {name}")
    provenance = read_json(directory / "provenance.json")
    exact_keys(provenance, ("schema", "sources", "public_sha256"), "Provenance")
    equal(provenance["schema"], "bibliography-evidence/1", "Provenance version")
    exact_keys(provenance["public_sha256"], PAYLOAD, "Payload digests")
    sources = {}
    for item in provenance["sources"]:
        exact_keys(item, ("source_path", "sha256", "destinations", "transform"), "Source mapping")
        path = item["source_path"]
        require(path not in sources and SHA.fullmatch(item["sha256"]) and item["transform"] and
                item["destinations"] and set(item["destinations"]) <= expected,
                f"Invalid provenance entry: {path}")
        sources[path] = item["sha256"]
    files = {name: read_json(directory / name) for name in DATA}
    summary = summarize(files)
    equal(summary, read_json(directory / "summary.json"), "Public summary")
    for row in files["fixed_sample.json"]["records"]:
        locator = row["decision"]
        equal(sources.get(locator["source_path"]), locator["sha256"], "Decision provenance")
        if row["edition_sha256"]:
            require(row["edition_sha256"] in sources.values(), "Missing edition provenance")
    for name, sha in provenance["public_sha256"].items():
        equal(digest((directory / name).read_bytes()), sha, f"Payload hash: {name}")
    return summary


def replay_main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    result = verify_bundle(args.directory)
    sample = result["fixed_sample"]
    screen = result["doi_screen"]
    print(f"PASS: {result['harvest']['n_raw']} harvest hits; {screen['verified']} DOI passes; "
          f"{sample['fixed_sample_n']} fixed IDs; field-rate authorization: false.")


if __name__ == "__main__":
    replay_main()
