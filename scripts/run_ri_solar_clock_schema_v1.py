#!/usr/bin/env python3
"""One-shot post-schema-exposure RI solar-vs-clock exploratory v1.

The previous preregistered v0 failed at source headers. This v1 is a
separate source-mapping amendment frozen AFTER v0 may have parsed raw CSV
rows in memory but BEFORE this v1 produces any animal-score result.
Never call this untouched external or retrospectively confirmatory.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import urllib.request

from odsp.ri_solar_clock_schema_v1 import (
    _validate_contract, run_exploratory_ri_solar_clock_v1,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"RI_SOLAR_CLOCK_SCHEMA_V1_EXPLORATORY_CONTRACT.json"
RECEIPT=ROOT/"RI_SOLAR_CLOCK_SCHEMA_V1_FIRST_EXPLORATORY_RESULT.json"
SOURCE_URL="https://zenodo.org/records/14508932/files/DataS1.zip?download=1"
SOURCE_MD5="c66943e6c2a9aab0abce2a1eba8ce02e"


def download_pinned_source()->bytes:
    request=urllib.request.Request(
        SOURCE_URL,
        headers={
            "User-Agent":"ODSP/0.11 explicit post-schema-exposure solar-clock ecology",
            "Accept":"application/zip,application/octet-stream,*/*",
        },
    )
    with urllib.request.urlopen(request,timeout=150) as response:
        raw=response.read(75_000_001)
    if len(raw)>75_000_000 or hashlib.md5(raw).hexdigest()!=SOURCE_MD5:
        raise ValueError("pinned 12.1 MB source archive rejected: byte cap or MD5 mismatch")
    return raw


def main()->int:
    frozen=CONTRACT.read_bytes()
    plan=json.loads(frozen)
    _validate_contract(plan)
    if (
        plan["data"]["original_md5"]!=SOURCE_MD5
        or plan["data"]["source_url"]!=SOURCE_URL
        or plan["source_v0"]["prior_real_data_run"]!=37744643137
    ):
        raise ValueError("pre-result source identity differs from v1 freeze")
    base={
        "schema_version":1,
        "method_version":"odsp-ri-solar-vs-clock-schema-v1-exploratory",
        "contract_sha256":hashlib.sha256(frozen).hexdigest(),
        "workflow_head_sha":os.environ.get("GITHUB_SHA","unknown"),
        "previous_source_v0_stopped_at_schema":True,
        "source_schema_chosen_after_prior_v0_parsed_rows":True,
        "original_v0_terminal_result_changed":False,
        "ecological_primary_confirmatory_claim":False,
        "camera_timezone_independently_verified":False,
        "model_refit_process_probability_tested":False,
    }
    try:
        raw=download_pinned_source()
        result=run_exploratory_ri_solar_clock_v1(raw,plan)
        out={**base,**result,
             "source_archive_sha256":hashlib.sha256(raw).hexdigest(),
             "source_archive_md5":SOURCE_MD5,
             "source_changed_after_first_v1_outcome":False}
        rc=0
    except Exception as exc:
        out={
            **base,
            "status":"EXPLORATORY_V1_UNAVAILABLE",
            "failure_type":type(exc).__name__,
            "failure_detail":str(exc)[:300],
            "source_replacement_or_posthoc_alias_rescue":False,
            "any_ecological_direction_claimed":False,
        }
        rc=2
    RECEIPT.write_text(
        json.dumps(out,sort_keys=True,indent=2,ensure_ascii=False,
                   allow_nan=False)+"\n",encoding="utf-8",
    )
    print(json.dumps({
        "status":out["status"],
        "paired_solar_over_clock":{
            s:info["metrics"]["solar_over_clock"]["mean"]
            for s,info in out.get("primary_heldout_solar_clock",{})
                .get("season_groups",{}).items()
        },
        "site_count":out.get("heldout_site_count"),
        "exploratory_only":True,
        "receipt":RECEIPT.name,
    },ensure_ascii=False,sort_keys=True),flush=True)
    return rc


if __name__=="__main__":
    raise SystemExit(main())
