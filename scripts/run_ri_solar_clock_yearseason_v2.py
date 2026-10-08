#!/usr/bin/env python3
"""One-shot post-exposure exploratory v2, 2018-2023 RI solar vs clock.

v0/v1 remain unavailable. This version differs in source YearSeason
grammar only: winter/summer wNN/sNN. No other scientific threshold,
feature set, training split, solar mapping, control or score is retuned.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import urllib.request

from odsp.ri_solar_clock_yearseason_v2 import (
    _validate_contract, run_exploratory_ri_solar_clock_v2,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN_PATH=ROOT/"RI_SOLAR_CLOCK_YEARSEASON_V2_EXPLORATORY_CONTRACT.json"
RECEIPT=ROOT/"RI_SOLAR_CLOCK_YEARSEASON_V2_FIRST_RESULT.json"
SOURCE="https://zenodo.org/records/14508932/files/DataS1.zip?download=1"
SOURCE_MD5="c66943e6c2a9aab0abce2a1eba8ce02e"


def _download():
    req=urllib.request.Request(
        SOURCE,headers={"User-Agent":"ODSP/0.11 transparently post-exposure RI v2 ecological analysis"}
    )
    with urllib.request.urlopen(req,timeout=170) as response:
        raw=response.read(75_000_001)
    if len(raw)>75_000_000 or hashlib.md5(raw).hexdigest()!=SOURCE_MD5:
        raise ValueError("RI v3 pinned public archive violates 75 MB or MD5 contract")
    return raw


def main()->int:
    frozen=PLAN_PATH.read_bytes()
    plan=json.loads(frozen)
    _validate_contract(plan)
    if (
        plan["data"]["source_url"]!=SOURCE
        or plan["data"]["original_md5"]!=SOURCE_MD5
        or plan["source_v0"]["separate_attrition_quality_run"]!=37747269596
        or plan["parser_policy"]["yearseason_code_mapping"]["pattern"]
            !=r"^(w|s)(18|19|20|21|22|23)$"
    ):
        raise ValueError("source version or season mapping differs from v2 frozen amendment")
    base={
        "schema_version":2,
        "study_id":plan["study_id"],
        "method":"post-schema-exposure solar-vs-clock exploratory v2",
        "plan_sha256":hashlib.sha256(frozen).hexdigest(),
        "head_sha":os.environ.get("GITHUB_SHA","unknown"),
        "archive_already_exposed_by_prior_unavailable_versions":True,
        "yearseason_codes_chosen_after_attrition_diagnostic":True,
        "v0_v1_terminal_unavailable_results_preserved":True,
        "source_camera_timezone_verified":False,
        "ecological_transfer_confirmatory":False,
        "future_refit_probability_confirmatory":False,
    }
    try:
        content=_download()
        result=run_exploratory_ri_solar_clock_v2(content,plan)
        receipt={
            **base,**result,
            "source_sha256":hashlib.sha256(content).hexdigest(),
            "source_md5_verified":True,
            "postresult_model_choice_tuning":False,
        }
        rc=0
    except Exception as exc:
        receipt={
            **base,
            "status":"EXPLORATORY_V2_UNAVAILABLE",
            "failure_type":type(exc).__name__,
            "failure_detail":str(exc)[:280],
            "ecological_direction_reported":False,
            "retuning_v2_to_rescue_failure":False,
        }
        rc=2
    RECEIPT.write_text(
        json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False,
                   allow_nan=False)+"\n",encoding="utf-8"
    )
    print(json.dumps({
        "status":receipt["status"],
        "future_site_count":receipt.get("heldout_site_count"),
        "scored_detections":receipt.get("scored_heldout_events"),
        "solar_over_clock":{
            group:data["metrics"]["solar_over_clock"]
            for group,data in receipt.get("primary_heldout_solar_clock",{})
                .get("season_groups",{}).items()
        },
        "exploratory_only":True,
        "result":RECEIPT.name,
    },ensure_ascii=False,sort_keys=True),flush=True)
    return rc


if __name__=="__main__":
    raise SystemExit(main())
