#!/usr/bin/env python3
"""First pre-frozen exact CP versus Hoeffding detector-q comparison."""
import hashlib
import json
from pathlib import Path

from odsp.uljin_exact_cp_vs_hoeffding_q_v0 import (
    compare_all_fixed_reference_calibrations
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_EXACT_CP_VS_HOEFFDING_Q_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_INDEPENDENT_Q_SPLIT_ALPHA_V0_FIRST_RESULT_LEDGER.json"
OUT=ROOT/"ULJIN_EXACT_CP_VS_HOEFFDING_Q_V0_FIRST_RECEIPT.json"


def main()->int:
    frozen=PLAN.read_bytes()
    result=compare_all_fixed_reference_calibrations(
        json.loads(frozen),json.loads(PARENT.read_bytes()))
    if (len(result["all_16_fixed_calibration_cases"])!=16
        or result["total_combined_false_certification_error_upper_bound"]!=.05):
        raise ValueError("incomplete first predeclared joint detector-q design panel")
    result["original_pre_result_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    summary=[]
    for x in result["all_16_fixed_calibration_cases"]:
        summary.append({
            "truth":x["synthetic_world"],
            "n_per_detector_calibration_cell":x["reference_binomial_opportunities_per_cell"],
            "B_Hoeffding":x["Hoeffding"]["reference_detector_gamma_max"],
            "B_exact_CP":x["exact_CP"]["reference_detector_gamma_max"],
            "robust_Hoeffding":x["Hoeffding"]["certifies_encounter_OR_above_one"],
            "robust_exact_CP":x["exact_CP"]["certifies_encounter_OR_above_one"],
        })
    print(json.dumps({
        "status":result["status"],
        "cases":summary,
        "first_certifying_reference_n_for_strong_artificial_effect":
            result["strong_animal_effect_first_certifying_reference_n_per_cell_on_frozen_grid"],
        "joint_false_certification_bound":.05,
        "no_EcoBank_camera_or_animal_data_accessed":True,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
