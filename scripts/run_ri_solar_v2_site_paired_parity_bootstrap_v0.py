#!/usr/bin/env python3
"""Paired physical-site uncertainty for RI four-model comparison, post-result.

Reruns the EXACT original v2 and checks original first mean & 5%-bootstrap
lower bounds BEFORE the new exploratory conditional model contrast interval.
No extra source selection, no new species list, no significance test.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import urllib.request

from odsp.ri_solar_v2_site_paired_parity_bootstrap_v0 import (
    original_all_site_score_rows,paired_site_season_parity_interval,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"RI_SOLAR_V2_SITE_PAIRED_SEASON_PARITY_BOOTSTRAP_CONTRACT.json"
ORIGINAL=ROOT/"RI_SOLAR_CLOCK_YEARSEASON_V2_EXPLORATORY_CONTRACT.json"
OUTPUT=ROOT/"RI_SOLAR_V2_SITE_PAIRED_PARITY_BOOTSTRAP_FIRST_RECEIPT.json"
URL="https://zenodo.org/records/14508932/files/DataS1.zip?download=1"
MD5="c66943e6c2a9aab0abce2a1eba8ce02e"


def pinned_download()->bytes:
    request=urllib.request.Request(
        URL,headers={
            "User-Agent":"ODSP/0.11 transparent postoutcome paired site uncertainty",
            "Accept":"application/zip,application/octet-stream,*/*",
        },
    )
    with urllib.request.urlopen(request,timeout=170) as response:
        raw=response.read(75_000_001)
    if len(raw)>75_000_000 or hashlib.md5(raw).hexdigest()!=MD5:
        raise ValueError("original Zenodo source byte ceiling/MD5 changed")
    return raw


def main()->int:
    original=json.loads(ORIGINAL.read_text())
    frozen=PLAN.read_bytes()
    plan=json.loads(frozen)
    base={
        "schema_version":1,
        "analysis_id":plan["analysis_id"],
        "head_sha":os.environ.get("GITHUB_SHA","unknown"),
        "design_contract_sha256":hashlib.sha256(frozen).hexdigest(),
        "original_data_already_exposed_in_prior_versions":True,
        "original_v2_scientific_conclusion_unchanged":True,
        "new_bootstrap_postoutcome_descriptive_only":True,
        "primary_confirmatory_route_qualified":False,
        "external_site_iid_sampling_proven":False,
        "real_camera_hourly_effort_proven":False,
    }
    try:
        if (
            plan["source"]["download_url"]!=URL
            or plan["source"]["md5"]!=MD5
            or original["data"]["source_url"]!=URL
        ):
            raise ValueError("new source version or URL prohibited")
        raw=pinned_download()
        scored,replay=original_all_site_score_rows(raw,original,plan)
        observed=paired_site_season_parity_interval(scored,plan)
        out={**base,**observed,
             "original_score_replay_audit":replay,
             "source_md5":MD5,
             "source_sha256":hashlib.sha256(raw).hexdigest()}
        code=0
    except Exception as exc:
        out={**base,
            "status":"SITE_PAIRED_PARITY_BOOTSTRAP_UNAVAILABLE",
            "error_type":type(exc).__name__,
            "error_message":str(exc)[:260],
            "conditional_clock_advantage_inferred":False,
            "no_postresult_retuning":True}
        code=2
    OUTPUT.write_text(
        json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False,
                   allow_nan=False)+"\n",encoding="utf-8"
    )
    print(json.dumps({
        "status":out["status"],
        "first_result_exactly_replayed":out.get(
            "original_result_exactly_replayed_before_new_interval",False
        ),
        "conditional_contrasts":{
            s:{
                "mean":v["conditional_solar_season_minus_clock_season_mean"],
                "exploratory_interval":[
                    v["paired_site_multiplier_bootstrap_95_percentile_lower"],
                    v["paired_site_multiplier_bootstrap_95_percentile_upper"],
                ]}
            for s,v in out.get("season_groups",{}).items()
        },
        "confirmed_causal_mechanism":False,
        "receipt":OUTPUT.name,
    },ensure_ascii=False,sort_keys=True),flush=True)
    return code


if __name__=="__main__":
    raise SystemExit(main())
