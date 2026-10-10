#!/usr/bin/env python3
"""First frozen source-free simultaneous q calibration across 82×96 clock bins."""
from pathlib import Path
import hashlib
import json

from odsp.uljin_96bin_simultaneous_q_calibration_v0 import (
    first_calibrated_96bin_panel
)
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_96BIN_SIMULTANEOUS_Q_CALIBRATION_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_COMMON_96BIN_DETECTOR_ENVELOPE_V0_FIRST_RESULT_LEDGER.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_96BIN_SIMULTANEOUS_Q_CALIBRATION_V0_FIRST_RECEIPT.json"

def main()->int:
    pre=PLAN.read_bytes()
    result=first_calibrated_96bin_panel(
        json.loads(pre),json.loads(PARENT.read_bytes()),json.loads(CAL.read_bytes()))
    if result["total_192_precommitted_score_envelopes"]!=192:
        raise ValueError("original 192 q-calibrated forecast comparison matrix incomplete")
    result["frozen_source_free_contract_sha256"]=hashlib.sha256(pre).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    tab=[]
    for config in result["all_8_q_calibration_source_coverage_receipts"]:
        matches=[
            z for z in result["all_192_model_score_envelope_results"]
            if z["true_camera_q_temporal_pattern"]==config["true_q_pattern"]
            and z["external_reference_budget"]==config["reference_budget"]
            and z["calibration_clock_granularity"]==config["calibration_method"]
        ]
        tab.append({
            **config,
            "model_pair_cases":len(matches),
            "certified_A_robust":sum(z.get("certified_model_order")=="A_robustly_better" for z in matches),
            "certified_B_robust":sum(z.get("certified_model_order")=="B_robustly_better" for z in matches),
            "indeterminate_or_UNQUALIFIED_or_HOLD":sum(
                z.get("certified_model_order") not in ("A_robustly_better","B_robustly_better")
                for z in matches)
        })
    print(json.dumps({
        "status":result["status"],
        "reports":result["total_192_precommitted_score_envelopes"],
        "equal_reference_budget_sample_granularities":tab,
        "no_original_source_events_or_reference_trials_opened":True
    },sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
