#!/usr/bin/env python3
"""Original 41-pair, common 96-civil-bin detector q comparison receipt."""
from pathlib import Path
import hashlib
import json
from odsp.uljin_common_96bin_detector_envelope_v0 import frozen_full_96bin_panel

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_COMMON_96BIN_DETECTOR_ENVELOPE_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_Q_W_VARIANCE_BUDGET_V0_FIRST_RESULT_LEDGER.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_COMMON_96BIN_DETECTOR_ENVELOPE_V0_FIRST_RECEIPT.json"

def main()->int:
    raw=PLAN.read_bytes()
    result=frozen_full_96bin_panel(
        json.loads(raw),json.loads(PARENT.read_bytes()),json.loads(CAL.read_bytes()))
    if (result["total_frozen_reported_q_envelopes"]!=240 or
        not result["same_q_for_competing_models_and_same_clock_outcomes"]):
        raise ValueError("original q uncertainty common-clock comparisons incomplete")
    result["frozen_pre_result_contract_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    summaries=[]
    for row in result["every_fixed_model_pair_case"]:
        nominal=row["nominal_original_clock_scoring_A_minus_B"]
        def find(d,s):
            return next(x for x in row["all_10_q_envelopes"]
                        if x["q_target_near_mix_max_deviation"]==d
                        and x["q_common_detector_structure"]==s)
        summaries.append({
            "truth":row["true_model"],"events_per_site_day":
                row["synthetic_events_per_site_date"],
            "A":row["comparator_A"],"B":row["comparator_B"],
            "nominal_gap":nominal,
            "independent_96bins_at_delta_0p1":find(.1,"independent_civil_96bins"),
            "six_4h_blocks_at_delta_0p1":find(.1,"fixed_civil_6blocks")
        })
    print(json.dumps({
        "status":result["status"],
        "same_96bin_clock_outcomes":True,
        "first_all_240_full_envelopes_archived":True,
        "descriptive_24_comparisons":summaries,
        "source_ecobank_wildlife_or_actual_q_not_read":True
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
