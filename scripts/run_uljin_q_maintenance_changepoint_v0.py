#!/usr/bin/env python3
"""First frozen source-free camera maintenance step with matched-cost references."""
from collections import Counter
import hashlib
import json
from pathlib import Path
from odsp.uljin_q_maintenance_changepoint_v0 import (
    first_frozen_maintenance_panel
)
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_Q_MAINTENANCE_CHANGEPOINT_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_Q_TEMPORAL_POOLING_LIPSCHITZ_V0_FIRST_RESULT_LEDGER.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_Q_MAINTENANCE_CHANGEPOINT_V0_FIRST_RECEIPT.json"

def main()->int:
    frozen=PLAN.read_bytes()
    result=first_frozen_maintenance_panel(
        json.loads(frozen),json.loads(PARENT.read_bytes()),
        json.loads(CAL.read_bytes()))
    assert result["total_predeclared_method_results"]==288
    result["pre_result_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    summary=Counter(
        (row["q_truth"],row["reference_total_gold_passages"],
         method,arm["status"],arm["site_majority_certified"])
        for row in result["all_96_paired_clock_model_comparisons"]
        for method,arm in row["three_equal_cost_calibration_methods"].items()
    )
    print(json.dumps({
        "status":result["status"],
        "original_paired_cases":96,"equal_source_budget_arms":288,
        "result_statuses":[
            {"q_world":k[0],"reference_budget":k[1],"method":k[2],
             "scope":k[3],"site_majority_certified":k[4],"count":v}
            for k,v in sorted(summary.items(),key=lambda x:str(x[0]))],
        "no_original_ungulate_hardware_or_maintenance_source_data_read":True
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
