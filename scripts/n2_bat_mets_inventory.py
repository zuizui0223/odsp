#!/usr/bin/env python3
"""Inventory the selected bat repository package without reading bitstreams.

This stage resolves the already-frozen Movebank Data Repository handle through
DSpace REST metadata only. It may read item, bundle, and bitstream *metadata*
(name, size, checksum, MIME metadata, and content URL), but it MUST NOT fetch any
bitstream content or inspect tracking-event values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

DOI = "10.5441/001/1.52nn82r9"
HANDLE = "10255/move.1055"
REPOSITORY = "https://datarepository.movebank.org"
PID_URL = f"{REPOSITORY}/server/api/pid/find?id={urllib.parse.quote(HANDLE, safe='')}"


def fetch_json(url: str) -> tuple[dict[str, object], bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "odsp-n2-bat-repository-inventory/1.0",
            "Accept": "application/hal+json, application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read()
        final_url = response.geturl()
        content_type = str(response.headers.get("Content-Type", ""))
    try:
        payload = json.loads(data.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(
            f"repository metadata endpoint returned non-JSON content: {content_type}"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("repository metadata endpoint returned non-object JSON")
    return payload, data, final_url


def _link(payload: dict[str, object], name: str) -> str:
    links = payload.get("_links")
    if not isinstance(links, dict):
        return ""
    value = links.get(name)
    if isinstance(value, dict):
        href = value.get("href")
        return "" if href is None else str(href)
    return ""


def _embedded_list(payload: dict[str, object], name: str) -> list[dict[str, object]]:
    embedded = payload.get("_embedded")
    if not isinstance(embedded, dict):
        return []
    value = embedded.get(name)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _safe_checksum(bitstream: dict[str, object]) -> tuple[str, str]:
    checksum = bitstream.get("checkSum")
    if not isinstance(checksum, dict):
        checksum = bitstream.get("checksum")
    if not isinstance(checksum, dict):
        return "", ""
    algorithm = checksum.get("checkSumAlgorithm")
    if algorithm is None:
        algorithm = checksum.get("algorithm")
    value = checksum.get("value")
    return (
        "" if algorithm is None else str(algorithm),
        "" if value is None else str(value),
    )


def inventory_from_dspace() -> dict[str, object]:
    item, item_bytes, item_url = fetch_json(PID_URL)
    bundles_url = _link(item, "bundles")
    if not bundles_url:
        raise RuntimeError("resolved DSpace item does not expose a bundles link")

    bundles_payload, bundles_bytes, bundles_final = fetch_json(bundles_url)
    bundles = _embedded_list(bundles_payload, "bundles")
    if not bundles:
        raise RuntimeError("DSpace item exposes no bundle metadata")

    files: list[dict[str, object]] = []
    metadata_sha256: dict[str, str] = {
        "item": hashlib.sha256(item_bytes).hexdigest(),
        "bundles": hashlib.sha256(bundles_bytes).hexdigest(),
    }

    for bundle in bundles:
        bundle_name = str(bundle.get("name", ""))
        bitstreams_url = _link(bundle, "bitstreams")
        if not bitstreams_url:
            continue
        bitstreams_payload, bitstreams_bytes, bitstreams_final = fetch_json(
            bitstreams_url
        )
        bundle_key = str(bundle.get("uuid") or bundle.get("id") or bundle_name)
        metadata_sha256[f"bitstreams:{bundle_key}"] = hashlib.sha256(
            bitstreams_bytes
        ).hexdigest()
        bitstreams = _embedded_list(bitstreams_payload, "bitstreams")
        for bitstream in bitstreams:
            checksum_type, checksum = _safe_checksum(bitstream)
            content_url = _link(bitstream, "content")
            files.append(
                {
                    "bundle_name": bundle_name,
                    "bitstream_id": str(
                        bitstream.get("uuid") or bitstream.get("id") or ""
                    ),
                    "filename": str(bitstream.get("name", "")),
                    "description": str(bitstream.get("description") or ""),
                    "mime_type": str(
                        bitstream.get("mimeType")
                        or bitstream.get("mime_type")
                        or ""
                    ),
                    "size_bytes": (
                        int(bitstream["sizeBytes"])
                        if isinstance(bitstream.get("sizeBytes"), int)
                        else None
                    ),
                    "checksum_type": checksum_type,
                    "checksum": checksum,
                    "content_url": content_url,
                    "metadata_url": _link(bitstream, "self"),
                    "bitstream_content_fetched": False,
                }
            )

    files.sort(
        key=lambda item: (
            str(item["bundle_name"]),
            str(item["filename"]),
            str(item["bitstream_id"]),
        )
    )
    if not files:
        raise RuntimeError("DSpace metadata contained no bitstream entries")

    return {
        "inventory_id": "odsp-n2-bat-repository-inventory-v2",
        "doi": DOI,
        "handle": HANDLE,
        "transport": "dspace_rest_pid_metadata_only",
        "pid_url": PID_URL,
        "resolved_item_url": item_url,
        "bundles_url": bundles_final,
        "metadata_response_sha256": metadata_sha256,
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
    report = inventory_from_dspace()
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
