#!/usr/bin/env python3
"""First frozen ecological out-of-family clock-anchor and detection-alias audit."""
from pathlib import Path
import hashlib
import json

from odsp.uljin_out_of_family_ecological_time_v1 import score_frozen_out_of_family

ROOT=Path(__file__).resolve().parents[1]
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
PLAN=ROOT/"ULJIN_OUT_OF_FAMILY_ECOLOGICAL_TIME_V1_CONTRACT.json"
PARENT=ROOT/"ULJIN_COMMON_CLOCK_MECHANISTIC_COMPARISON_V0_FIRST_RESULT_LEDGER.json"
OUT=ROOT/"ULJIN_OUT_OF_FAMILY_ECOLOGICAL_TIME_V1_FIRST_RECEIPT.json"


def main()->int:
    raw=PLAN.read_bytes()
    result=score_frozen_out_of_family(json.loads(CAL.read_bytes()),
                                       json.loads(raw),
                                       json.loads(PARENT.read_bytes()))
    result["pre_result_contract_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    winner={}
    regrets={}
    for row in result["all_30_synthetic_scenarios"]:
        key=f'{row["truth_world"]}|{row["counts_per_site_date"]}'
        winner.setdefault(key,{m:0 for m in result["parent_candidate_models_unchanged"]})
        winner[key][row["best_descriptive_heldout_family"]]+=1
        regrets.setdefault(key,[]).append(min(row[
            "all_expected_conditional_KL_regrets_nats_per_event"].values()))
    print(json.dumps({
        "status":result["status"],
        "worlds":len(result["all_30_synthetic_scenarios"]),
        "winners_not_significance":winner,
        "mean_minimum_KL_regret":{key:sum(vals)/len(vals) for key,vals in regrets.items()},
        "detector_vs_animal_observed_laws_and_counts_identical":
            result["seasonal_biological_shift_and_detector_only_observed_counts_exactly_equal_with_paired_rng"],
        "real_source_animal_or_operator_data_read":False
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
