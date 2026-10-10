#!/usr/bin/env python3
"""First prospective 96-case station-camera q transport exact majority ledger."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from odsp.uljin_site_specific_camera_q_transport_v0 import (
    run_first_site_q_transport_panel
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_SITE_SPECIFIC_CAMERA_Q_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_JOINT_Q_SITE_MAJORITY_V0_FIRST_RESULT_LEDGER.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_SITE_SPECIFIC_CAMERA_Q_V0_FIRST_RECEIPT.json"


def main()->int:
    raw=PLAN.read_bytes()
    result=run_first_site_q_transport_panel(
        json.loads(raw),json.loads(PARENT.read_bytes()),
        json.loads(CAL.read_bytes()))
    if result["total_precommitted_scenarios"]!=96:
        raise ValueError("first site q source-transport panel incomplete")
    result["pre_first_source_free_outcome_contract_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    statuses=Counter(
        (x["true_camera_site_q_pattern"],method,
         arm["scope"],arm["site_majority_certified"])
        for x in result["all_96_precommitted_model_comparisons"]
        for method,arm in
            x["both_equal_cost_reference_calibration_methods"].items()
    )
    receipts=result["all_8_independent_reference_calibration_receipts"]
    print(json.dumps({
        "status":result["status"],
        "all_frozen_96_cases":result["total_precommitted_scenarios"],
        "results_by_source_scope_and_majority":[
            {"site_q_truth":key[0],"source_calibration_method":key[1],
             "source_site_scope":key[2],"site_majority_certified":key[3],
             "number_comparisons":v}
            for key,v in sorted(statuses.items(),key=lambda x:str(x[0]))],
        "source_reference_coverage_audits":receipts,
        "no_original_Uljin_events_or_real_q_references":True
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
