"""Schema-only, event-outcome-blind source preflight for Kays et al. 2020 seasonal.zip.

Not an ecological estimator. Original source bytes are required; a locally
computed SHA256 records transfer integrity, not independent official attestation.
No animal source rows, species identities, coordinates, timestamps or rates
are read or reported. No source gets promoted to Tier-A from this preflight.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import posixpath
import re
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

OFFICIAL_FILE_URL = "https://datadryad.org/downloads/file_stream/235082"
OFFICIAL_API_DOWNLOAD_URL = "https://datadryad.org/api/v2/files/235082/download"
MAX_DOWNLOAD_BYTES = 12_000_000
MAX_EXPANDED_BYTES = 120_000_000
MAX_MEMBERS = 100


def _normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _safe_member(name: str) -> bool:
    parts = name.replace("\\", "/").split("/")
    return (
        name != ""
        and not name.startswith(("/", "\\"))
        and all(part not in (".", "..") for part in parts)
        and ":" not in parts[0]
        and posixpath.normpath(name) not in (".", "..")
    )


def schema_only_receipt(payload: bytes) -> dict:
    """Inspect ZIP member metadata and FIRST CSV header only, never data rows."""
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        raise ValueError("NOT_ZIP_BYTES")
    receipt = {
        "source": OFFICIAL_FILE_URL,
        "download_sha256_unattested": hashlib.sha256(payload).hexdigest(),
        "source_zip_member_headers": [],
        "source_structural_state": "HOLD_SCHEMA_ONLY_NOT_EVENT_OR_EFFORT_VERIFIED",
        "source_scientific_status": "NO_BIOLOGICAL_OUTCOME_COMPUTED",
        "verified_physical_camera_uptime": False,
        "verified_same_station_both_photoperiod_branches": False,
    }
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        members = zf.infolist()
        if len(members) > MAX_MEMBERS:
            raise ValueError("TOO_MANY_ZIP_MEMBERS")
        if sum(m.file_size for m in members) > MAX_EXPANDED_BYTES:
            raise ValueError("ZIP_EXPANDED_SIZE_TOO_LARGE")
        for member in members:
            if not _safe_member(member.filename):
                raise ValueError("UNSAFE_ZIP_PATH")
            # Disallow symlink entries, even though nothing is extracted.
            if member.create_system == 3 and (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("UNSAFE_ZIP_SYMLINK")
            if member.is_dir() or not member.filename.casefold().endswith(".csv"):
                continue
            if member.file_size > MAX_EXPANDED_BYTES:
                raise ValueError("CSV_MEMBER_TOO_LARGE")
            with zf.open(member) as handle:
                # Only the first line can enter memory, bounded independently.
                header_bytes = handle.readline(32_769)
                if len(header_bytes) > 32_768:
                    raise ValueError("OVERLONG_CSV_HEADER")
                header = next(csv.reader([header_bytes.decode("utf-8-sig")]))
            keys = {_normalized_key(k) for k in header}
            receipt["source_zip_member_headers"].append({
                "file_basename": posixpath.basename(member.filename),
                "column_names_only": header,
                "date_or_timestamp_header_candidate": bool(keys & {
                    "date", "datetime", "timestamp", "dateandtime", "datetaken",
                    "eventstart", "starttime", "timeofcapture",
                }),
                "physical_site_id_header_candidate": bool(keys & {
                    "siteid", "station", "stationid", "cameraid",
                    "deploymentid", "locationid", "transectid", "sitelabel",
                }),
                "deployment_start_header_candidate": bool(keys & {
                    "deploymentstart", "startdate", "dateset", "startdatetime",
                    "camstartdate", "setupdatetime",
                }),
                "deployment_end_header_candidate": bool(keys & {
                    "deploymentend", "enddate", "dateret", "enddatetime",
                    "camenddate", "retrievaldatetime",
                }),
            })
    return receipt


def official_schema_preflight(url: str | None = None) -> dict:
    """Try only two documented first-party Dryad paths; never bypass access control."""
    if url is not None and url not in (OFFICIAL_FILE_URL, OFFICIAL_API_DOWNLOAD_URL):
        return {"status": "HOLD_UNREGISTERED_DOWNLOAD_URL", "source": url}
    sources = [url] if url else [OFFICIAL_FILE_URL, OFFICIAL_API_DOWNLOAD_URL]
    attempts = []
    for source in sources:
        try:
            req = urllib.request.Request(
                source,
                headers={
                    "User-Agent": "Mozilla/5.0 (ODSP-public-source-preflight/0.1)",
                    "Accept": "application/zip, application/octet-stream, */*",
                },
            )
            with urllib.request.urlopen(req, timeout=35) as response:
                payload = response.read(MAX_DOWNLOAD_BYTES + 1)
            if len(payload) > MAX_DOWNLOAD_BYTES:
                attempts.append({"source": source, "state": "DOWNLOAD_EXCEEDS_SIZE_CAP"})
                continue
            receipt = schema_only_receipt(payload)
            receipt["source"] = source
            receipt["status"] = "HOLD_SCHEMA_ONLY_NEEDS_SOURCE_INDEPENDENT_HARDWARE_ON_HOURS"
            receipt["retrieval_attempts"] = attempts + [{"source": source, "state": "ZIP_HEADERS_READ"}]
            return receipt
        except (OSError, urllib.error.URLError, zipfile.BadZipFile, UnicodeError, ValueError) as exc:
            attempts.append({
                "source": source,
                "state": "UNAVAILABLE",
                "error_type": type(exc).__name__,
                "http_status_if_any": getattr(exc, "code", None),
            })
    return {
        "status": "HOLD_OFFICIAL_ARCHIVE_NOT_SCHEMA_INSPECTED",
        "source": OFFICIAL_FILE_URL,
        "retrieval_attempts": attempts,
        "scientific_status": "NO_NEW_BIOLOGICAL_RESULT",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--local-zip", type=Path, help="User-provided official ZIP; no private coordinates emitted")
    args = parser.parse_args()
    if args.local_zip:
        # Local bytes are not assumed original until host/version attestation.
        payload = args.local_zip.read_bytes()
        try:
            receipt = schema_only_receipt(payload)
            receipt["status"] = "HOLD_LOCAL_BYTES_OFFICIAL_ORIGIN_NOT_ATTESTED"
        except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as exc:
            receipt = {"status": "HOLD_INVALID_LOCAL_SOURCE", "error_type": type(exc).__name__}
    else:
        receipt = official_schema_preflight()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Kays 2020 seasonality source schema gate: {receipt['status']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
