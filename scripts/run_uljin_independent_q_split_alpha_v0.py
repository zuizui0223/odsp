#!/usr/bin/env python3
"""First complete frozen 16x600 independent detector calibration screen."""
import hashlib
import json
from pathlib import Path
from odsp.uljin_independent_q_split_alpha_v0 import (
    frozen_joint_calibration_panel,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_INDEPENDENT_Q_SPLIT_ALPHA_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_INDEPENDENT_Q_SPLIT_ALPHA_V0_FIRST_RECEIPT.json"

def main()->int:
    frozen=PLAN.read_bytes()
    result=frozen_joint_calibration_panel(json.loads(frozen))
    if (result["case_count"]!=16 or result["worlds_per_case"]!=600
        or result["guaranteed_total_false_certification_upper_bound"]!=.05):
        raise ValueError("frozen 9600 calibration and exact test worlds not complete")
    result["pre_result_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "combined_type_I_alpha_bound":result["guaranteed_total_false_certification_upper_bound"],
        "cases":[{
            "world":v["synthetic_truth"],
            "reference_per_cell":v["independent_reference_opportunities_per_4_cells"],
            "joint_q_coverage":v["empirical_joint_q_band_coverage"],
            "hold_q_lower_zero":v["fraction_with_insufficient_positive_q_lower_bounds"],
            "robust_reject_fraction":v["fraction_robustly_rejecting_latent_OR_le_1"],
            "naive_ignore_detector_reject_fraction":v[
                "naive_unadjusted_fisher_5pct_rejection_fraction"],
            "median_finite_B":v["median_finite_detector_gamma_upper"],
        } for v in result["all_precommitted_cases"]],
        "real_wildlife_calibration_or_camera_source_records_read":False,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
