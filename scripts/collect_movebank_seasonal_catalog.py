"""Collect and replay the public Movebank Data Repository package inventory.

This is package metadata, not an event-level or seasonal-series eligibility audit.
No credentials or biological event values are requested.
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import tarfile
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path


COLLECTION_UUID = "e1ae0743-5f80-4700-b21f-0535a10daee9"
API_URL = "https://datarepository.movebank.org/server/api/discover/search/objects"
PAGE_SIZE = 25


def _values(metadata, key):
    return [entry["value"] for entry in metadata.get(key, [])]


def _reported_count(metadata, key):
    entries = _values(metadata, key)
    if not entries:
        return None
    if len(entries) != 1:
        raise ValueError(f"Ambiguous {key}: {entries}")
    try:
        return int(entries[0].replace(",", ""))
    except ValueError as exc:
        raise ValueError(f"Invalid {key}: {entries[0]}") from exc


def build_catalog(raw_pages, snapshot_date=None):
    """Validate complete discovery responses and return catalog and provenance."""
    if snapshot_date is not None:
        date.fromisoformat(snapshot_date)
    if not raw_pages:
        raise ValueError("No discovery pages")
    rows = []
    page_hashes = []
    observed_page_numbers = set()
    observed_uuids = set()
    expected_total = expected_pages = None
    source_hash = hashlib.sha256()
    for position, raw in enumerate(raw_pages):
        source_hash.update(raw)
        response = json.loads(raw)
        if response.get("scope") != COLLECTION_UUID:
            raise ValueError(f"Wrong collection scope on page {position}")
        result = response["_embedded"]["searchResult"]
        page = result["page"]
        number = page["number"]
        total = page["totalElements"]
        pages = page["totalPages"]
        if number in observed_page_numbers or number != position:
            raise ValueError(f"Duplicate or out-of-order page index: {number}")
        observed_page_numbers.add(number)
        if page["size"] != PAGE_SIZE or pages != math.ceil(total / PAGE_SIZE):
            raise ValueError(f"Invalid page size or page count on page {number}")
        if expected_total is None:
            expected_total, expected_pages = total, pages
        elif (total, pages) != (expected_total, expected_pages):
            raise ValueError(f"Changing totals on page {number}")
        objects = result["_embedded"]["objects"]
        expected_on_page = min(PAGE_SIZE, total - PAGE_SIZE * number)
        if len(objects) != expected_on_page:
            raise ValueError(f"Partial page {number}: {len(objects)} of {expected_on_page}")
        page_hashes.append({
            "page": number,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
        for hit in objects:
            item = hit["_embedded"]["indexableObject"]
            uid = item["uuid"]
            if item["id"] != uid or uid in observed_uuids:
                raise ValueError(f"Duplicate or inconsistent package UUID: {uid}")
            observed_uuids.add(uid)
            if item["entityType"] != "Datapackage":
                raise ValueError(f"Unexpected entity type for {uid}")
            metadata = item["metadata"]
            rows.append({
                "package_uuid": uid,
                "title": item["name"],
                "handle": item["handle"],
                "repository_item_url": f"https://datarepository.movebank.org/server/api/core/items/{uid}",
                "dois": _values(metadata, "dc.identifier.doi"),
                "licenses": _values(metadata, "dc.rights"),
                "license_uris": _values(metadata, "dc.rights.uri"),
                "publication_dates": _values(metadata, "dc.date.issued"),
                "repository_accession_dates": _values(metadata, "dc.date.accessioned"),
                "repository_last_modified": item["lastModified"],
                "scientific_names": _values(metadata, "dwc.ScientificName"),
                "sensor_names": _values(metadata, "sensor.name"),
                "repository_study_ids": _values(metadata, "mdr.study.id"),
                "reported_animal_count": _reported_count(metadata, "mdr.animal.count"),
                "reported_location_count": _reported_count(metadata, "mdr.location.count"),
                "page_index": number,
            })
    if len(raw_pages) != expected_pages or len(rows) != expected_total:
        raise ValueError("Missing discovery page or package")
    catalog = {
        "collection_uuid": COLLECTION_UUID,
        "package_count": len(rows),
        "metadata_semantics": {
            "unit": "repository data packages; neither independent biological studies nor qualified seasonal series",
            "publication_dates": "repository dc.date.issued values; not observation start or end dates",
            "repository_accession_dates": "repository dc.date.accessioned values; not observation coverage",
            "reported_animal_count": "repository mdr.animal.count; not necessarily unique animals across packages or versions",
            "reported_location_count": "repository mdr.location.count; not deduplicated across packages or versions",
            "licenses": "all dc.rights values; review each package and files before reuse",
            "dois": "all dc.identifier.doi values, without selecting one as canonical",
        },
        "packages": rows,
    }
    manifest = {
        "api_url": API_URL,
        "source_query_template": f"{API_URL}?scope={COLLECTION_UUID}&size={PAGE_SIZE}&page={{page}}",
        "scope_collection_uuid": COLLECTION_UUID,
        "snapshot_date": snapshot_date,
        "snapshot_date_precision": "calendar day; per-request times were not recorded",
        "biological_outcomes_computed": False,
        "page_size": PAGE_SIZE,
        "page_count": len(raw_pages),
        "reported_total_elements": expected_total,
        "unique_package_uuids": len(observed_uuids),
        "raw_pages_sha256_concatenated": source_hash.hexdigest(),
        "raw_page_hashes": page_hashes,
    }
    return catalog, manifest


def write_raw_archive(raw_pages, destination):
    """Store original page bytes in a reproducible gzip-compressed tar archive."""
    destination = Path(destination)
    with destination.open("wb") as stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w") as archive:
                for number, raw in enumerate(raw_pages):
                    info = tarfile.TarInfo(f"page_{number:03d}.json")
                    info.size = len(raw)
                    info.mode = 0o644
                    archive.addfile(info, io.BytesIO(raw))


def read_raw_archive(source):
    with tarfile.open(source, "r:gz") as archive:
        members = archive.getmembers()
        if any(not m.isfile() or m.name != f"page_{i:03d}.json" for i, m in enumerate(members)):
            raise ValueError("Archive has missing, duplicate, or unexpected page names")
        return [archive.extractfile(m).read() for m in members]


def fetch_pages(timeout=60, retries=3):
    """Read the anonymous scoped discovery endpoint sequentially."""
    raw_pages = []
    total_pages = 1
    page = 0
    while page < total_pages:
        url = f"{API_URL}?scope={COLLECTION_UUID}&size={PAGE_SIZE}&page={page}"
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    raw = response.read()
                break
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt == retries - 1:
                    raise RuntimeError(f"Failed to fetch page {page} after {retries} attempts") from exc
                time.sleep(min(2 ** attempt, 8))
        raw_pages.append(raw)
        if page == 0:
            first = json.loads(raw)
            if first.get("scope") != COLLECTION_UUID:
                raise ValueError("Wrong collection scope on first page")
            total_pages = first["_embedded"]["searchResult"]["page"]["totalPages"]
        page += 1
    return raw_pages


def write_outputs(raw_pages, out_dir, snapshot_date):
    catalog, manifest = build_catalog(raw_pages, snapshot_date=snapshot_date)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / "raw_pages.tar.gz"
    write_raw_archive(raw_pages, archive)
    manifest["raw_archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    (out_dir / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (out_dir / "catalog.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(catalog["packages"][0]))
        writer.writeheader()
        for row in catalog["packages"]:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, list) else value for key, value in row.items()})
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--fetch", action="store_true", help="fetch anonymous public API pages")
    source.add_argument("--replay", type=Path, metavar="ARCHIVE", help="replay a saved raw_pages.tar.gz")
    source.add_argument("--import-pages", type=Path, metavar="DIR", help="import previously saved page_NNN.json files")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--snapshot-date", required=True, help="UTC calendar date of the raw page snapshot (YYYY-MM-DD)")
    args = parser.parse_args()
    if args.fetch:
        pages = fetch_pages()
    elif args.replay:
        pages = read_raw_archive(args.replay)
    else:
        paths = sorted(args.import_pages.glob("page_*.json"))
        pages = [path.read_bytes() for path in paths]
    manifest = write_outputs(pages, args.out, args.snapshot_date)
    print(json.dumps({key: manifest[key] for key in ("page_count", "reported_total_elements", "unique_package_uuids", "raw_pages_sha256_concatenated", "raw_archive_sha256")}, indent=2))


if __name__ == "__main__":
    main()
