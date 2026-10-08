#!/usr/bin/env python3
"""Single-use post-exposure RI v3 source attrition audit, no model fitting."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import urllib.request

from odsp.ri_camera_v3_attrition_only_v0 import (
    inspect_source_attrition_without_ecological_scores,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"RI_CAMERA_V3_ATTRITION_ONLY_CONTRACT.json"
V1=ROOT/"RI_SOLAR_CLOCK_SCHEMA_V1_EXPLORATORY_CONTRACT.json"
RECEIPT=ROOT/"RI_CAMERA_V3_ATTRITION_FIRST_RECEIPT.json"
URL="https://zenodo.org/records/14508932/files/DataS1.zip?download=1"
MD5="c66943e6c2a9aab0abce2a1eba8ce02e"


def main()->int:
    frozen=PLAN.read_bytes()
    plan=json.loads(frozen)
    original=json.loads(V1.read_text())
    record={
        "schema_version":1,
        "audit_plan_sha256":hashlib.sha256(frozen).hexdigest(),
        "v1_exploratory_contract_sha256":hashlib.sha256(V1.read_bytes()).hexdigest(),
        "workflow_head_sha":os.environ.get("GITHUB_SHA","unknown"),
        "prior_v0_v1_results_reclassified":False,
        "animal_taxa_or_timestamp_values_reported":False,
        "ecological_scores_or_effect_sizes_computed":False,
        "entire_public_source_previously_unopened_claimed":False,
    }
    try:
        if (
            plan["source"]["download_url"]!=URL
            or plan["source"]["md5"]!=MD5
            or original["data"]["source_url"]!=URL
        ):
            raise ValueError("source differs from predeclared attrition audit")
        request=urllib.request.Request(
            URL,headers={"User-Agent":"ODSP/0.11 post-exposure source attrition only"}
        )
        with urllib.request.urlopen(request,timeout=180) as data:
            raw=data.read(75_000_001)
        if len(raw)>75_000_000 or hashlib.md5(raw).hexdigest()!=MD5:
            raise ValueError("source compressed size/MD5 mismatch")
        profile=inspect_source_attrition_without_ecological_scores(
            raw,original,plan
        )
        record={**record,**profile,"status":"ATTRITION_DIAGNOSTIC_COMPLETE"}
        code=0
    except Exception as exc:
        record={
            **record,"status":"ATTRITION_DIAGNOSTIC_UNAVAILABLE",
            "failure_type":type(exc).__name__,
            "failure_detail":str(exc)[:250],
        }
        code=2
    RECEIPT.write_text(
        json.dumps(record,sort_keys=True,indent=2,ensure_ascii=False,
                   allow_nan=False)+"\n",encoding="utf-8"
    )
    print(json.dumps({
        "status":record["status"],
        "detection_rows":record.get("detection_rows"),
        "stage_counts":record.get("first_rejection_stage_counts"),
        "year_season_metadata":record.get("detection_YearSeason_metadata_labels"),
        "date_time_format_shapes":record.get("Date_Time_text_shape_counts"),
        "ecological_scores_computed":False,
    },ensure_ascii=False,sort_keys=True),flush=True)
    return code


if __name__=="__main__":
    raise SystemExit(main())
