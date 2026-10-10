#!/usr/bin/env python3
"""FIRST pre-frozen 96 paired common-clock detector station×branch comparisons."""
import hashlib
import json
from collections import Counter
from pathlib import Path
from odsp.uljin_station_season_camera_q_v0 import run_frozen_station_branch_panel

ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/"ULJIN_STATION_SEASON_CAMERA_Q_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_SITE_SPECIFIC_CAMERA_Q_V0_FIRST_RESULT_LEDGER.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_STATION_SEASON_CAMERA_Q_V0_FIRST_RECEIPT.json"


def main()->int:
    frozen=FROZEN.read_bytes()
    out=run_frozen_station_branch_panel(
        json.loads(frozen),json.loads(PARENT.read_bytes()),
        json.loads(CAL.read_bytes()))
    if out["total_original_paired_cases"]!=96 or len(
        out["frozen_external_reference_calibration_receipts"])!=8:
        raise ValueError("frozen paired station×branch detector q matrix incomplete")
    out["frozen_method_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+"\n")
    summaries=Counter(
        (case["camera_q_temporal_world"],method,arm["scope"],
         arm["majority_new_site_certified"])
        for case in out["frozen_paired_comparisons"]
        for method,arm in case["two_equal_cost_calibration_arms"].items()
    )
    print(json.dumps({
        "status":out["status"],
        "all_original_model_pairs":out["total_original_paired_cases"],
        "equal_budget_calibration_arms":192,
        "summary":[{"true_q_world":k[0],"source":k[1],
                    "source_target_admission":k[2],
                    "site_majority_certified":k[3],"count":n}
                   for k,n in sorted(summaries.items(),key=lambda z:str(z[0]))],
        "independent_source_reference_q_opportunities_are_synthetic":True,
        "real_ungulate_event_or_camera_operation_not_accessed":True
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
