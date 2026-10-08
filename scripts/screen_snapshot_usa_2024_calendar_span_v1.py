#!/usr/bin/env python3
"""Prospectively frozen calendar-span structural screen; no animal records.

No Sequence_ID, Species, Start_Time/End_Time or Survey_Nights values are read.
The physical camera deployment CSV is a retrospective PUBLIC data product,
so no historical untouched data claim follows from this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request

from odsp.snapshot_usa_2024_calendar_span_v1 import (
    MAX_CSV_BYTES,
    audit_calendar_metadata,
    validate_calendar_screen_contract,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ODSP_SNAPSHOT_USA_2024_CALENDAR_SPAN_V1_CONTRACT.json"
URL="https://datadryad.org/downloads/file_stream/4788613"


def frozen_metadata_download(contract: dict) -> bytes:
    uri=contract["source"]["frozen_download_url"]
    if uri!=URL:
        raise ValueError("not the frozen Dryad deployment URL")
    with urllib.request.urlopen(
        urllib.request.Request(
            uri,
            headers={
                "User-Agent":"ODSP/0.11 Snapshot-USA placement/retrieval metadata only",
                "Accept":"text/csv,application/octet-stream,*/*",
            },
        ),
        timeout=65,
    ) as response:
        data=response.read(MAX_CSV_BYTES+1)
    if len(data)>MAX_CSV_BYTES:
        raise ValueError("deployment CSV exceeded frozen byte ceiling")
    if data[:2]==b"PK" or data[:1] in (b"<",b"{",b"["):
        raise ValueError("unexpected archive/HTML/JSON instead of deployment CSV")
    return data


def main() -> int:
    ap=argparse.ArgumentParser()
    source=ap.add_mutually_exclusive_group(required=True)
    source.add_argument("--frozen-download", action="store_true")
    source.add_argument("--local-fixture", type=Path)
    ap.add_argument("--receipt", type=Path, required=True)
    args=ap.parse_args()

    frozen=CONTRACT.read_bytes()
    contract=json.loads(frozen)
    validate_calendar_screen_contract(contract)
    prior={
        "screen_id":"odsp-snapshot-usa-2024-calendar-span-deployment-screen-v1",
        "contract_sha256":hashlib.sha256(frozen).hexdigest(),
        "source_mode":"frozen_deployment_file" if args.frozen_download else "synthetic_fixture",
        "source_url":URL if args.frozen_download else None,
        "head_sha":os.environ.get("GITHUB_SHA","unknown"),
        "sequence_file_read":False,
        "image_derived_survey_nights_used":False,
        "historical_source_row_nonaccess_attested":False,
        "actual_camera_uptime_inferred":False,
        "iid_sampling_proven":False,
        "prior_ecological_endpoint_reclassified":False,
        "primary_route_qualified":False,
    }
    try:
        raw=(
            frozen_metadata_download(contract)
            if args.frozen_download else args.local_fixture.read_bytes()
        )
        result={
            **prior,
            **audit_calendar_metadata(
                raw,contract,contract_sha256=prior["contract_sha256"]
            ),
        }
        rc=0
    except Exception as e:
        result={
            **prior,
            "structural_status":"SOURCE_METADATA_UNAVAILABLE_OR_INVALID",
            "error_type":type(e).__name__,
            "error_message":str(e)[:200],
            "source_data_sha256":None,
        }
        rc=2
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(
        json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status":result["structural_status"],
        "candidate_groups":result.get("predeclared_groups"),
        "species_or_sequence_records_opened":False,
        "survey_nights_used":False,
        "receipt_path":str(args.receipt),
    },ensure_ascii=False),flush=True)
    return rc


if __name__=="__main__":
    raise SystemExit(main())
