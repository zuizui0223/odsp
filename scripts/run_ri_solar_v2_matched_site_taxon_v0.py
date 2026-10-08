#!/usr/bin/env python3
"""Post-result RI matched site/taxon diagnostic, NOT confirmatory ecology.

The source is the exact RI v3 ZIP and v2 score implementation. Abort if
the reproduced original first site-level winter/summer mean, 19,916
scored events or 43 heldout sites differ from the pinned first outcome.
No new test selection, null or bootstrap and no primary reclassification.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import urllib.request

from odsp.ri_solar_v2_matched_site_taxon_v0 import (
    run_original_v2_matched_diagnostic,
)

ROOT=Path(__file__).resolve().parents[1]
SOURCE_PLAN=ROOT/"RI_SOLAR_CLOCK_YEARSEASON_V2_EXPLORATORY_CONTRACT.json"
MATCH_PLAN=ROOT/"RI_SOLAR_V2_MATCHED_SITE_TAXON_V0_CONTRACT.json"
RECEIPT=ROOT/"RI_SOLAR_V2_MATCHED_SITE_TAXON_FIRST_RECEIPT.json"
SOURCE_URL="https://zenodo.org/records/14508932/files/DataS1.zip?download=1"
MD5="c66943e6c2a9aab0abce2a1eba8ce02e"


def download_pinned_archive()->bytes:
    req=urllib.request.Request(
        SOURCE_URL,headers={
            "User-Agent":"ODSP/0.11 openly postoutcome matched ecological diagnostics",
            "Accept":"application/zip,application/octet-stream,*/*",
        }
    )
    with urllib.request.urlopen(req,timeout=180) as response:
        content=response.read(75_000_001)
    if len(content)>75_000_000 or hashlib.md5(content).hexdigest()!=MD5:
        raise ValueError("historical RI v3 MD5 or byte ceiling mismatch")
    return content


def main()->int:
    frozen=MATCH_PLAN.read_bytes()
    plan=json.loads(frozen)
    original=json.loads(SOURCE_PLAN.read_text())
    if (
        plan.get("source",{}).get("url")!=SOURCE_URL
        or plan.get("source",{}).get("archive_md5")!=MD5
        or original.get("data",{}).get("source_url")!=SOURCE_URL
    ):
        raise ValueError("source identity differs from frozen matched-site design")
    base={
        "schema_version":1,
        "analysis_id":plan["analysis_id"],
        "plan_sha256":hashlib.sha256(frozen).hexdigest(),
        "workflow_head_sha":os.environ.get("GITHUB_SHA","unknown"),
        "source_schema_is_original_v2":True,
        "historical_v0_v1_v2_status_changed":False,
        "original_v2_outcomes_opened_before_this_new_plan":True,
        "postoutcome_inference_only":True,
        "confirmatory_claim":False,
        "site_random_sampling_verified":False,
        "camera_detection_effort_calibrated":False,
    }
    try:
        raw=download_pinned_archive()
        result=run_original_v2_matched_diagnostic(raw,original,plan)
        out={**base,**result,
             "source_archive_sha256":hashlib.sha256(raw).hexdigest()}
        exit_code=0
    except Exception as exc:
        out={**base,
             "status":"MATCHED_SOURCE_OR_ORIGINAL_REPLAY_UNAVAILABLE",
             "failure_type":type(exc).__name__,
             "failure_detail":str(exc)[:240],
             "matched_pair_sign_reported":False,
             "original_v2_frozen_outcome_reclassified":False}
        exit_code=2
    RECEIPT.write_text(json.dumps(
        out,indent=2,sort_keys=True,allow_nan=False,ensure_ascii=False
    )+"\n",encoding="utf-8")
    matched=out.get("matched_pair_description",{})
    print(json.dumps({
        "status":out["status"],
        "matched_site_taxon_pairs":matched.get("matched_site_taxon_pairs"),
        "distinct_sites":matched.get("physical_sites_with_at_least_one_paired_taxon"),
        "all_pairs":matched.get("all_reported_matched_pairs"),
        "taxon_balanced":matched.get("taxon_balanced_matched_pairs"),
        "original_reproduced":out.get("original_v2_scoring_means_reproduced_before_decomposition",False),
        "exploratory_only":True,
        "receipt":RECEIPT.name,
    },sort_keys=True,ensure_ascii=False),flush=True)
    return exit_code

if __name__=="__main__":
    raise SystemExit(main())
