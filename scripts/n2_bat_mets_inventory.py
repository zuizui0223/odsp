#!/usr/bin/env python3
"""Inventory the selected bat Data Repository package without reading bitstreams.

This stage may fetch and parse the METS metadata document for the already-frozen
Movebank Data Repository item. It reports file identifiers, names, URLs, media
types, byte sizes, and repository checksums when those are present in METS.
It MUST NOT fetch any listed bitstream or inspect tracking-event values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DOI = "10.5441/001/1.52nn82r9"
HANDLE = "10255/move.1055"
METS_URL = f"https://datarepository.movebank.org/metadata/handle/{HANDLE}/mets.xml"
XLINK = "{http://www.w3.org/1999/xlink}href"
METS = "{http://www.loc.gov/METS/}"


def fetch_metadata(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "odsp-n2-bat-mets-inventory/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read()
        content_type = str(response.headers.get("Content-Type", ""))
    if not data.lstrip().startswith(b"<"):
        raise RuntimeError("METS endpoint did not return XML-like content")
    if "html" in content_type.lower() and b"<mets" not in data.lower():
        raise RuntimeError("METS endpoint returned HTML rather than metadata XML")
    return data


def _filename_from_href(href: str) -> str:
    path = urllib.parse.urlparse(href).path
    return urllib.parse.unquote(path.rsplit("/", 1)[-1])


def parse_mets_inventory(data: bytes) -> list[dict[str, object]]:
    root = ET.fromstring(data)
    files: list[dict[str, object]] = []
    for file_group in root.iter(f"{METS}fileGrp"):
        group_use = str(file_group.attrib.get("USE", ""))
        for file_node in file_group.findall(f"{METS}file"):
            loc = file_node.find(f"{METS}FLocat")
            if loc is None:
                continue
            href = str(loc.attrib.get(XLINK, "")).strip()
            if not href:
                continue
            size_raw = str(file_node.attrib.get("SIZE", "")).strip()
            size = int(size_raw) if size_raw.isdigit() else None
            files.append(
                {
                    "file_group_use": group_use,
                    "file_id": str(file_node.attrib.get("ID", "")),
                    "mime_type": str(file_node.attrib.get("MIMETYPE", "")),
                    "size_bytes": size,
                    "checksum": str(file_node.attrib.get("CHECKSUM", "")),
                    "checksum_type": str(file_node.attrib.get("CHECKSUMTYPE", "")),
                    "loctype": str(loc.attrib.get("LOCTYPE", "")),
                    "href": href,
                    "filename": _filename_from_href(href),
                }
            )
    return sorted(
        files,
        key=lambda item: (
            str(item["file_group_use"]),
            str(item["filename"]),
            str(item["file_id"]),
        ),
    )


def build_report() -> dict[str, object]:
    data = fetch_metadata(METS_URL)
    files = parse_mets_inventory(data)
    if not files:
        raise RuntimeError("METS contained no resolvable file locations")
    return {
        "inventory_id": "odsp-n2-bat-mets-inventory-v1",
        "doi": DOI,
        "handle": HANDLE,
        "mets_url": METS_URL,
        "mets_sha256": hashlib.sha256(data).hexdigest(),
        "file_count": len(files),
        "files": files,
        "bitstreams_downloaded": False,
        "tracking_values_downloaded": False,
        "outcome_metrics_computed": False,
        "scientific_terminal_decision": False,
        "forbidden_at_this_stage": [
            "bitstream contents",
            "tracking row counts derived from bitstreams",
            "height values or distributions",
            "H(Z|X,Y)",
            "effective states",
            "axis_thickness_map",
            "projection loss",
            "held-out score",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "inventory_id": report["inventory_id"],
                "file_count": report["file_count"],
                "bitstreams_downloaded": False,
                "outcome_metrics_computed": False,
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
