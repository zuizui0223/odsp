#!/usr/bin/env python3
"""One-shot public RI 2018-2023 solar-vs-clock ecological transfer run.

Study frozen separately in ODSP_RI_SOLAR_CLOCK_TRANSFER_V0_CONTRACT.json
before accessing the archive image-detection row values in this branch.
Even if successful this is EXPLORATORY due unverified camera time-zone
provenance, nonrandom target-species camera placement and retrospective
public outcome availability. It cannot qualify process-v5 or p_success.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request

from odsp.ri_solar_source_v0 import execute_frozen_ri_solar_transfer, SOURCE_MD5

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ODSP_RI_SOLAR_CLOCK_TRANSFER_V0_CONTRACT.json"
FROZEN_URL="https://zenodo.org/records/14508932/files/DataS1.zip?download=1"


def download_source() -> bytes:
    req=urllib.request.Request(
        FROZEN_URL,
        headers={
            "User-Agent":"ODSP/0.11 ecological hypothesis-test retrospective public camera survey",
            "Accept":"application/zip,application/octet-stream,*/*",
        }
    )
    with urllib.request.urlopen(req,timeout=180) as response:
        payload=response.read(75_000_001)
    if len(payload)>75_000_000:
        raise ValueError("RI camera-trap zip archive exceeds hard 75 MB ceiling")
    if hashlib.md5(payload).hexdigest()!=SOURCE_MD5:
        raise ValueError("downloaded RI public archive MD5 differs from frozen version")
    return payload


def main() -> int:
    parser=argparse.ArgumentParser()
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--public-archive",action="store_true")
    source.add_argument("--local-archive",type=Path)
    parser.add_argument("--receipt",type=Path,required=True)
    args=parser.parse_args()

    raw_contract=CONTRACT.read_bytes()
    plan=json.loads(raw_contract)
    if (
        plan["study_id"]!="odsp-ri-solar-vs-clock-site-year-transfer-v0"
        or plan["status"]!="PRE_DETECTION_OUTCOME_ACCESS_DESIGN_FREEZE"
        or plan["source"]["archive_md5"]!=SOURCE_MD5
        or plan["source"]["download_url"]!=FROZEN_URL
        or plan["design"]["heldout_season_years"]!=[2022,2023]
        or plan["design"]["last_training_season_year"]!=2021
        or plan["design"]["duplicate_photo_suppression_minutes"]!=30
        or plan["validation"]["bootstrap_draws"]!=2000
        if "bootstrap_draws" in plan["validation"] else False
    ):
        # No permissive source/analysis fallback after archive results.
        raise ValueError("frozen source/design identity changed")
    receipt_base={
        "schema_version":1,"study_id":plan["study_id"],
        "design_contract_sha256":hashlib.sha256(raw_contract).hexdigest(),
        "analysis_head_sha":os.environ.get("GITHUB_SHA","unknown"),
        "score_target":"six equal four-hour local civil clock bins",
        "published_archive_2018_2023":True,
        "historical_true_external_outcome_nonaccess_verified":False,
        "site_sampling_randomized_verified":False,
        "camera_timestamp_timezone_verified":False,
        "underlying_activity_vs_detection_identified":False,
        "causal_solar_entraintment_identified":False,
        "historical_odsp_endpoints_reclassified":False,
        "registered_primary_route":False,
    }
    try:
        content=download_source() if args.public_archive else args.local_archive.read_bytes()
        outcome=execute_frozen_ri_solar_transfer(content,plan)
        receipt={**receipt_base,**outcome,
            "archive_md5":hashlib.md5(content).hexdigest(),
            "model_choice_post_outcome":False
        }
        code=0
    except Exception as exc:
        receipt={
            **receipt_base,
            "status":"EXPLORATORY_SOURCE_OR_ANALYSIS_UNAVAILABLE",
            "failure_type":type(exc).__name__,
            "failure_detail":str(exc)[:300],
            "empirical_solar_transfer_claim":False,
            "source_replacement_after_failure":False,
        }
        code=2
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False,
                   allow_nan=False)+"\n",
        encoding="utf-8"
    )
    print(json.dumps({
        "status":receipt["status"],
        "source_archive":plan["source"]["archive"],
        "primary_transfer_mean": (
            {s:g["metrics"]["solar_over_clock"]["mean"]
                for s,g in receipt.get("transferability",{})
                    .get("season_groups",{}).items()}
        ),
        "archive_not_originally_unopened":True,
        "result_file":str(args.receipt),
    },ensure_ascii=False),flush=True)
    return code


if __name__=="__main__":
    raise SystemExit(main())
