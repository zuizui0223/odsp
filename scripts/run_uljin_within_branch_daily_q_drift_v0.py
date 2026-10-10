#!/usr/bin/env python3
"""FIRST frozen within-branch daily q drift source calibration and site test."""
import hashlib
import json
from pathlib import Path
from odsp.uljin_within_branch_daily_q_drift_v0 import (
    first_frozen_daily_drift_panel
)
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_WITHIN_BRANCH_DAILY_Q_DRIFT_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_STATION_SEASON_CAMERA_Q_V0_FIRST_RESULT_LEDGER.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_WITHIN_BRANCH_DAILY_Q_DRIFT_V0_FIRST_RECEIPT.json"


def main()->int:
    frozen=CONTRACT.read_bytes()
    result=first_frozen_daily_drift_panel(
        json.loads(frozen),json.loads(PARENT.read_bytes()),json.loads(CAL.read_bytes()))
    if (result["total_frozen_case_x_eps"]!=384 or
        result["pr260_original_station_branch_eps0_positive_count_replayed"]!=13):
        raise ValueError("complete frozen 384 daily drift q site tests missing")
    result["pre_first_output_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "scored_case_x_eps":result["total_frozen_case_x_eps"],
        "exact_original_parent_PR260_certifications_replayed":
            result["pr260_original_station_branch_eps0_positive_count_replayed"],
        "first_frozen_daily_drift_sensitivity":result[
            "summary_by_daily_truth_and_attested_external_eps"],
        "real_ungulate_q_or_camera_logs_read":False
    },sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
