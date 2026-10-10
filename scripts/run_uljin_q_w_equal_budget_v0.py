#!/usr/bin/env python3
"""First source-free 48x200 gold-standard reference q/w allocation panel."""
from pathlib import Path
import hashlib
import json

from odsp.uljin_q_w_equal_budget_v0 import run_allocation_panel

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/"ULJIN_Q_W_EQUAL_BUDGET_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_DISTANCE_MIX_TIPPING_RADIUS_V0_FIRST_RESULT_LEDGER.json"
OUT=ROOT/"ULJIN_Q_W_EQUAL_BUDGET_V0_FIRST_RECEIPT.json"


def main()->int:
    raw=FROZEN.read_bytes()
    result=run_allocation_panel(
        json.loads(raw),json.loads(PARENT.read_bytes()))
    if (result["truth_case_count"]!=48 or result["world_count"]!=9600
        or not result["original_same_cost_opportunity_accounting_verified"]):
        raise ValueError("frozen 9600-world allocation benchmark incomplete")
    result["frozen_design_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "worlds":result["world_count"],
        "same_total_external_opportunity_budgets_verified":True,
        "results":[{
            "truth":z["truth"],
            "budget":z["reference_budget_opportunities"],
            "strategy":z["strategy"],
            "q_n":z["detector_q_reference_trials_per_eight_cells"],
            "w_n":z["target_near_mix_reference_trials_per_four_cells"],
            "robust_certification":z["robust_latent_encounter_certification_fraction"],
            "median_B":z["median_finite_detector_crossproduct_upper_B"],
            "joint_12_coverage":z["twelve_cell_joint_coverage"],
        } for z in result["all_predeclared_worlds"]],
        "original_EcoBank_wildlife_or_reference_opportunity_records_opened":False
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
