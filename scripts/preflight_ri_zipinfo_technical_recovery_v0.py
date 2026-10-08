#!/usr/bin/env python3
"""First ZIP-central-directory-only recovery preflight, no source rows.

This is a separate post-initial-failure TECHNICAL source preflight.
The predeclared recovery contract and safety ceilings were committed
before this script. No model fitting, CSV extraction, score or species
observations are permitted in this stage.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import urllib.request

from odsp.ri_zipinfo_technical_recovery_v0 import (
    MAX_ARCHIVE,
    MAX_MEMBERS,
    MAX_TOTAL_EXPANDED,
    MAX_MEMBER_EXPANDED,
    MAX_EXPANSION_RATIO,
    SOURCE_MD5,
    inspect_ri_pinned_zip_central_directory,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ODSP_RI_SOLAR_V0_ZIPINFO_TECHNICAL_RECOVERY_CONTRACT.json"
RESULT=ROOT/"RI_SOLAR_V0_ZIPINFO_FIRST_TECHNICAL_RECEIPT.json"
FROZEN_URL="https://zenodo.org/records/14508932/files/DataS1.zip?download=1"


def main()->int:
    frozen=CONTRACT.read_bytes()
    contract=json.loads(frozen)
    caps=contract["allowable_zip_structure"]
    if (
        contract["contract_id"]!="odsp-ri-solar-clock-v0-zipinfo-only-recovery-v1"
        or contract["status"]!="FROZEN_AFTER_FIRST_STRUCTURAL_FAILURE_BEFORE_ANY_SOURCE_ROW_ACCESS"
        or contract["source"]["url"]!=FROZEN_URL
        or contract["source"]["expected_archive_md5"]!=SOURCE_MD5
        or caps["max_compressed_archive_bytes"]!=MAX_ARCHIVE
        or caps["max_zip_entry_count"]!=MAX_MEMBERS
        or caps["max_total_uncompressed_bytes"]!=MAX_TOTAL_EXPANDED
        or caps["max_single_uncompressed_member_bytes"]!=MAX_MEMBER_EXPANDED
        or caps["max_aggregate_expansion_ratio"]!=MAX_EXPANSION_RATIO
    ):
        raise ValueError("first technical source preflight does not match pre-outcome recovery freeze")
    status={
        "schema_version":1,
        "type":"ZIP_CENTRAL_DIRECTORY_ONLY_FIRST_TECHNICAL_PREFLIGHT",
        "contract_sha256":hashlib.sha256(frozen).hexdigest(),
        "first_ecological_source_run_id":37743723775,
        "workflow_head_sha":os.environ.get("GITHUB_SHA","unknown"),
        "source_member_contents_read":False,
        "source_detection_rows_read":False,
        "original_scientific_analysis_rerun":False,
        "previous_terminal_unavailable_reclassified":False,
        "ecological_inference_qualified":False,
    }
    try:
        request=urllib.request.Request(
            FROZEN_URL,
            headers={
                "User-Agent":"ODSP/0.11 ZIP-metadata-only science provenance",
                "Accept":"application/zip,application/octet-stream,*/*",
            },
        )
        with urllib.request.urlopen(request,timeout=120) as response:
            raw=response.read(MAX_ARCHIVE+1)
        audit=inspect_ri_pinned_zip_central_directory(raw)
        result={**status,**audit.as_dict(),
                "first_technical_metadata_pass":True}
        return_code=0
    except Exception as exc:
        result={**status,
                "recovery_eligibility":"TECHNICAL_ZIP_RECOVERY_INELIGIBLE_OR_UNAVAILABLE",
                "first_technical_metadata_pass":False,
                "failure_type":type(exc).__name__,
                "failure_reason":str(exc)[:220]}
        return_code=2
    RESULT.write_text(
        json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status":result["recovery_eligibility"],
        "member_count":result.get("member_count"),
        "expanded_total":result.get("total_declared_expanded_bytes"),
        "expanded_max":result.get("largest_declared_member_bytes"),
        "source_rows_read":False,
        "receipt":RESULT.name,
    },sort_keys=True),flush=True)
    return return_code


if __name__=="__main__":
    raise SystemExit(main())
