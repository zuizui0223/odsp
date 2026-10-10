#!/usr/bin/env python3
"""First frozen 192 site-majority tests from independent CP camera-q references."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from odsp.uljin_joint_q_site_majority_v0 import frozen_site_majority_full_panel

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_JOINT_Q_SITE_MAJORITY_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_96BIN_SIMULTANEOUS_Q_CALIBRATION_V0_FIRST_RESULT_LEDGER.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_JOINT_Q_SITE_MAJORITY_V0_FIRST_RECEIPT.json"


def main()->int:
    frozen=CONTRACT.read_bytes()
    result=frozen_site_majority_full_panel(
        json.loads(frozen),json.loads(PARENT.read_bytes()),
        json.loads(CAL.read_bytes()))
    if result["total_predeclared_cases"]!=192:
        raise ValueError("lost original 192 detector-calibrated site tests")
    result["pre_first_outcome_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    statuses=Counter((r["true_camera_q_temporal_pattern"],
                      r["reference_calibration_time_structure"],
                      r["admission_status"],
                      r["inferential_site_majority_decision"])
                     for r in result["all_192_predefined_source_free_q_and_site_cases"])
    rows=[{
        "q_pattern":k[0],"q_resolution":k[1],"admission":k[2],
        "site_majority_decision":k[3],"cases":v,
    } for k,v in sorted(statuses.items(),key=lambda x:str(x[0]))]
    print(json.dumps({
        "status":result["status"],
        "rows":result["total_predeclared_cases"],
        "detector_q_and_site_error_alpha":result[
            "combined_per_scenario_false_certification_alpha_bound"],
        "exact_site_sign_p_13_of_16":result["exact_sign_p_for_13_of_16"],
        "exact_site_sign_p_14_of_16":result["exact_sign_p_for_14_of_16"],
        "count_by_source_scope_and_site_decision":rows,
        "real_original_species_device_or_sensor_references_read":False,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
