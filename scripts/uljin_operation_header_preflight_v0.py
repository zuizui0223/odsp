#!/usr/bin/env python3
"""Source provenance preflight for original EcoBank operation ZIP only.

No direct EcoBank archive URL has been verified. Therefore the default
execution emits SOURCE_ARCHIVE_NOT_MATERIALIZED and DOES NOT call the
internet or replace v1.1 with a differently sourced ZIP.

Option --local-original-zip can inspect a user-supplied original file,
but ONLY its central directory and the operation-log HEADER line. No
wildlife events, no camera operation data records or station IDs are read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from odsp.uljin_operation_log_header_preflight_v0 import (
    inspect_uljin_operation_header_only,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_OPERATION_METADATA_HEADER_PREFLIGHT_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_OPERATION_METADATA_FIRST_HEADER_PREFLIGHT_RECEIPT.json"


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--local-original-zip",type=Path)
    ap.add_argument("--receipt",type=Path,default=OUT)
    args=ap.parse_args()
    raw_plan=CONTRACT.read_bytes()
    frozen=json.loads(raw_plan)
    common={
        "schema_version":1,
        "audit":"uljin_operation_header_preflight_v0",
        "contract_sha256":hashlib.sha256(raw_plan).hexdigest(),
        "workflow_head_sha":os.environ.get("GITHUB_SHA","unknown"),
        "source_download_url_verified":False,
        "animal_detection_file_opened":False,
        "camera_operation_data_rows_read":False,
        "source_origin_independence_verified":False,
        "camera_hourly_uptime_verified":False,
        "station_matched_day_observation_support_verified":False,
        "original_calendar_first_receipt_reclassified":False,
        "ecological_primary_qualified":False,
    }
    if args.local_original_zip is None:
        receipt={**common,
                 "status":"SOURCE_ARCHIVE_NOT_MATERIALIZED",
                 "structural_header_examined":False,
                 "reason":"No authenticated direct EcoBank v1.1 archive bytes provided; never invent source URL"}
        code=0
    else:
        try:
            result=inspect_uljin_operation_header_only(
                args.local_original_zip.read_bytes(),frozen
            )
            receipt={**common,**result,
                     "status":"STRUCTURAL_OPERATION_HEADER_ONLY_NOT_ELIGIBLE_FOR_OUTCOME_ACCESS"}
            code=0
        except Exception as exc:
            receipt={**common,
                     "status":"STRUCTURAL_ARCHIVE_HEADER_HOLD",
                     "error_type":type(exc).__name__,
                     "reason":str(exc)[:220]}
            code=2
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt,sort_keys=True,indent=2,ensure_ascii=False,
                   allow_nan=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status":receipt["status"],
        "wildlife_source_opened":False,
        "hourly_camera_uptime_verified":False,
        "receipt":str(args.receipt),
    },ensure_ascii=False,sort_keys=True),flush=True)
    return code


if __name__=="__main__":
    raise SystemExit(main())
