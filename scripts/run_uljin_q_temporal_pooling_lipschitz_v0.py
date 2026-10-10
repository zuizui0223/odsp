#!/usr/bin/env python3
"""First complete source-free 384 temporal pooling and daily camera q scores."""
from collections import Counter
from pathlib import Path
import hashlib
import json

from odsp.uljin_q_temporal_pooling_lipschitz_v0 import (
    full_frozen_temporal_pooling_panel
)
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_Q_TEMPORAL_POOLING_LIPSCHITZ_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_WITHIN_BRANCH_DAILY_Q_DRIFT_V0_FIRST_RESULT_LEDGER.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_Q_TEMPORAL_POOLING_LIPSCHITZ_V0_FIRST_RECEIPT.json"


def main()->int:
    raw=PLAN.read_bytes()
    d=full_frozen_temporal_pooling_panel(
        json.loads(raw),json.loads(PARENT.read_bytes()),
        json.loads(CAL.read_bytes()))
    if (d["total_predeclared_time_pooling_results"]!=384
        or len(d["all_16_external_q_reference_calibration_receipts"])!=16):
        raise ValueError("frozen 384 correct q interval temporal pooling comparisons lost")
    d["frozen_pre_first_outcome_contract_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.write_text(json.dumps(d,sort_keys=True,indent=2,allow_nan=False)+"\n")
    outcome=Counter(
        (r["q_true_world"],r["independent_source_budget"],int(m),
         a["status"],a["site_majority_certified"])
        for r in d["all_first_96_model_cases_x_four_q_temporal_scales"]
        for m,a in r["four_predeclared_grouped_q_calibration_results"].items()
    )
    print(json.dumps({
        "status":d["status"],
        "all_synthetic_pairs":96,
        "all_corrected_clock_q_calibration_arms":384,
        "source_status_majority_counts":[{
            "true_camera_day_q_world":key[0],
            "external_true_passage_budget":key[1],
            "pool_calendar_days":key[2],
            "source_validity":key[3],
            "site_majority_certified":key[4],
            "cases":count,
        } for key,count in sorted(outcome.items(),key=lambda z:str(z[0]))],
        "no_original_animal_or_camera_operation_records_opened":True,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
