#!/usr/bin/env python3
"""First frozen independent distance-stratified detector transport test."""
from pathlib import Path
import hashlib
import json
from odsp.uljin_q_transport_distance_mix_v0 import run_frozen_transport_panel

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_Q_TRANSPORT_DISTANCE_MIX_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_Q_TRANSPORT_DISTANCE_MIX_V0_FIRST_RECEIPT.json"


def main()->int:
    raw=PLAN.read_bytes()
    result=run_frozen_transport_panel(json.loads(raw))
    if result["world_count"]!=12 or result["replicates_per_world"]!=200:
        raise ValueError("frozen source-free distance transport panel incomplete")
    result["pre_result_contract_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "source_animal_or_camera_reference_access":False,
        "worlds":[{
            "world":r["world"],"n_q_each_distance_season_cell":
                r["n_q_opportunities_per_8_stratum_cells"],
            "true_detector_gamma":r["true_detector_gamma"],
            "pooled_naive_reject_fraction":
                r["naive_reference_CP_false_or_true_certification_fraction"],
            "stratified_reject_fraction":
                r["stratified_target_standardized_CP_certification_fraction"],
            "joint_12_q_w_coverage":r["all_12_q_and_mix_joint_coverage"],
            "transport_HOLD":r["transported_q_bound_zero_HOLD_fraction"]
        } for r in result["first_frozen_worlds"]],
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
