#!/usr/bin/env python3
"""First locked 12-case exact multi-site power and pooled-null calibration."""
import hashlib
import json
from pathlib import Path
from odsp.uljin_stratified_exact_conditional_power_v0 import (
    run_stratified_exact_panel,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_STRATIFIED_EXACT_CONDITIONAL_POWER_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_STRATIFIED_EXACT_CONDITIONAL_POWER_V0_FIRST_RECEIPT.json"

def main()->int:
    original=PLAN.read_bytes()
    result=run_stratified_exact_panel(json.loads(original))
    if (result["case_count"]!=12 or result["truth_effect_rows"]!=48 or
        not result["site_stratified_conditional_null_size_valid_all_cases"]):
        raise ValueError("pre-frozen exact test/calibration report incomplete")
    result["frozen_design_sha256"]=hashlib.sha256(original).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "case_count":result["case_count"],
        "truth_effect_rows":result["truth_effect_rows"],
        "witness_stratified_p":result["witness"]["stratified_exact_one_sided_p"],
        "witness_naive_pooled_p":result["witness"]["naive_pooled_one_sided_fisher_p"],
        "naive_pooled_max_null_rejection_in_compositional_stress":
            result["max_naive_pooled_null_rejection_in_compositional_stress"],
        "stratified_conditional_size_valid_all":True,
        "source_outcome_accessed":False
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
