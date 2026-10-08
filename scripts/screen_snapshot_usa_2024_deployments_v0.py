#!/usr/bin/env python3
"""Snapshot USA 2024 deployment-only source screen (zero sequence-file access).

The exact Dryad deployment URL and allowed field values are frozen in a
pre-access contract committed before this script. The script has no route for
downloading, parsing or opening the species/datetime sequence CSV.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

from odsp.snapshot_usa_2024_structural_screen_v0 import (
    _validate_contract,
    audit_deployment_bytes,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ODSP_SNAPSHOT_USA_2024_DEPLOYMENT_SCREEN_V0_CONTRACT.json"
MAX_BYTES=10_000_000


def download_frozen_deployment_csv(contract: dict[str, object]) -> bytes:
    """Fetch ONLY the contract URL, with a hard byte-size cap."""
    url=contract["published_source"]["metadata_download_url"]
    if url != "https://datadryad.org/downloads/file_stream/4788613":
        raise ValueError("unexpected frozen deployment source URL")
    request=urllib.request.Request(
        url,
        headers={
            "User-Agent":"ODSP/0.11 research structural-metadata-only",
            "Accept":"text/csv,application/octet-stream,*/*",
        },
        method="GET",
    )
    with urllib.request.urlopen(request,timeout=60) as response:
        raw=response.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:
        raise ValueError("deployment metadata exceeds allowed 10 MB")
    if raw[:2]==b"PK" or raw[:1] in (b"<",b"{",b"["):
        raise ValueError("unexpected ZIP/HTML/JSON instead of deployment CSV")
    return raw


def main() -> int:
    parser=argparse.ArgumentParser()
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--frozen-download",action="store_true")
    source.add_argument("--local-fixture",type=Path)
    parser.add_argument("--receipt",type=Path,required=True)
    args=parser.parse_args()

    raw_plan=PLAN.read_bytes()
    contract=json.loads(raw_plan)
    _validate_contract(contract)
    receipt_base={
        "screen":"snapshot_usa_2024_deployments_outcome_blind_v0",
        "contract_sha256":hashlib.sha256(raw_plan).hexdigest(),
        "source_url":contract["published_source"]["metadata_download_url"],
        "source_mode":"frozen_public_metadata_download" if args.frozen_download else "local_test_fixture",
        "source_code_head_sha":os.environ.get("GITHUB_SHA","unknown"),
        "species_detection_response_file_downloaded":False,
        "sequence_timestamp_rows_read":False,
        "iid_site_sampling_proven":False,
        "primary_qualification":False,
        "existing_empirical_endpoints_reclassified":False,
    }
    try:
        raw=(
            download_frozen_deployment_csv(contract)
            if args.frozen_download else args.local_fixture.read_bytes()
        )
        receipt={**receipt_base,**audit_deployment_bytes(
            raw,contract,contract_sha256=receipt_base["contract_sha256"]
        )}
        exit_code=0
    except Exception as exc:
        receipt={
            **receipt_base,
            "status":"SOURCE_METADATA_UNAVAILABLE_OR_INVALID",
            "error_type":type(exc).__name__,
            "error_message":str(exc)[:280],
            "source_deployment_csv_sha256":None,
            "outcome_rows_read":False,
            "structural_counts_qualified":False,
        }
        exit_code=2
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status":receipt["status"],
        "deployment_records":receipt.get("deployment_record_count"),
        "groups":receipt.get("predeclared_habitat_groups"),
        "response_rows_accessed":False,
        "receipt":str(args.receipt),
    },ensure_ascii=False),flush=True)
    return exit_code


if __name__=="__main__":
    raise SystemExit(main())
