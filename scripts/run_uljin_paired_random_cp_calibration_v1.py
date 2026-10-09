#!/usr/bin/env python3
"""First frozen 16x600 randomized paired detector-q interval comparison."""
import hashlib
import json
from pathlib import Path
from odsp.uljin_paired_random_cp_calibration_v1 import paired_randomized_cp_panel

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_PAIRED_RANDOM_CP_VS_HOEFFDING_V1_CONTRACT.json"
PARENT=ROOT/"ULJIN_INDEPENDENT_Q_SPLIT_ALPHA_V0_FIRST_RESULT_LEDGER.json"
CP_PARENT=ROOT/"ULJIN_EXACT_CP_VS_HOEFFDING_Q_V0_FIRST_RESULT_LEDGER.json"
OUT=ROOT/"ULJIN_PAIRED_RANDOM_CP_VS_HOEFFDING_V1_FIRST_RECEIPT.json"


def main()->int:
    frozen=CONTRACT.read_bytes()
    result=paired_randomized_cp_panel(
        json.loads(frozen),json.loads(PARENT.read_bytes()),
        json.loads(CP_PARENT.read_bytes()))
    if (result["total_worlds"]!=9600 or result["case_count"]!=16
        or not result["replayed_parent_first_Hoeffding_outcomes_without_retuning"]):
        raise ValueError("full frozen 9600 paired worlds not validated")
    result["pre_first_outcome_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "all_prior_hoeffding_results_replayed":True,
        "worlds":result["total_worlds"],
        "cases":[{
            "truth":row["truth"],"n_per_q_cell":row["reference_opportunities_per_q_cell"],
            "CP_reject":row["CP"]["certification_fraction"],
            "Hoeffding_reject":row["Hoeffding"]["certification_fraction"],
            "paired_gain":row["paired_CP_minus_Hoeffding_certification_fraction"],
            "CP_only":row["CP_only_certification_count"],
            "Hoeffding_only":row["Hoeffding_only_certification_count"],
            "CP_hold":row["CP"]["no_finite_q_crossproduct_HOLD_fraction"],
        } for row in result["simulated_case_results"]],
        "empirical_power_not_ecological_field_data":True,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
