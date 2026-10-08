#!/usr/bin/env python3
"""One-shot header-only RI v3 probe: never extract CSV data rows."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import urllib.request

from odsp.ri_camera_v3_header_probe import (
    inspect_camera_archive_headers_only,
)
from odsp.ri_zipinfo_technical_recovery_v0 import MAX_ARCHIVE

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"RI_CAMERA_V3_HEADER_ONLY_PROBE_CONTRACT.json"
ORIGINAL=ROOT/"ODSP_RI_SOLAR_CLOCK_TRANSFER_V0_CONTRACT.json"
RECEIPT=ROOT/"RI_CAMERA_V3_HEADER_ONLY_FIRST_RECEIPT.json"
URL="https://zenodo.org/records/14508932/files/DataS1.zip?download=1"


def main()->int:
    raw_contract=PLAN.read_bytes()
    frozen=json.loads(raw_contract)
    original=json.loads(ORIGINAL.read_text())
    receipt={
        "schema_version":1,
        "plan_sha256":hashlib.sha256(raw_contract).hexdigest(),
        "original_alias_contract_sha256":hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
        "workflow_head_sha":os.environ.get("GITHUB_SHA","unknown"),
        "v0_frozen_scientific_methods_changed":False,
        "previous_v0_data_rows_may_have_been_read":True,
        "actual_ecological_row_values_read_by_this_probe":False,
        "new_empirical_results_claimed":False,
    }
    try:
        if (
            frozen["contract_id"]!="odsp-ri-camera-v3-header-only-recovery-v0"
            or frozen["source"]["url"]!=URL
            or frozen["source"]["max_zip_compressed_bytes"]!=MAX_ARCHIVE
            or original["source"]["download_url"]!=URL
        ):
            raise ValueError("not the frozen RI v3 header-only contract")
        req=urllib.request.Request(URL,headers={
            "User-Agent":"ODSP/0.11 ZIP headers only source semantics",
            "Accept":"application/zip,application/octet-stream,*/*",
        })
        with urllib.request.urlopen(req,timeout=150) as connection:
            raw=connection.read(MAX_ARCHIVE+1)
        if len(raw)>MAX_ARCHIVE:
            raise ValueError("archive exceeds frozen byte ceiling")
        inspected=inspect_camera_archive_headers_only(
            raw,frozen,original["source_schema_predeclared_aliases"]
        )
        receipt={**receipt,**inspected,"status":"HEADER_ONLY_PROBE_COMPLETE"}
        rc=0
    except Exception as exc:
        receipt={
            **receipt,
            "status":"HEADER_ONLY_PROBE_UNAVAILABLE",
            "error_type":type(exc).__name__,
            "error_message":str(exc)[:220],
        }
        rc=2
    RECEIPT.write_text(
        json.dumps(receipt,sort_keys=True,indent=2,allow_nan=False)+"\n"
    )
    print(json.dumps({
        "status":receipt["status"],
        "sources":{k:v["header_names"] for k,v in receipt.get("source_headers",{}).items()},
        "data_rows_read_by_this_probe":False,
        "receipt":RECEIPT.name,
    },ensure_ascii=False,sort_keys=True),flush=True)
    return rc


if __name__=="__main__":
    raise SystemExit(main())
