#!/usr/bin/env python3
"""First frozen no-wildlife target-distance partial identification receipt."""
from pathlib import Path
import hashlib
import json
from odsp.uljin_distance_mix_tipping_radius_v0 import run_frozen_distance_radius

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_DISTANCE_MIX_TIPPING_RADIUS_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_IID_REFERENCE_Q_TRANSPORT_V1_FIRST_RESULT_LEDGER.json"
OUT=ROOT/"ULJIN_DISTANCE_MIX_TIPPING_RADIUS_V0_FIRST_RECEIPT.json"


def main()->int:
    frozen=CONTRACT.read_bytes()
    result=run_frozen_distance_radius(json.loads(frozen),
                                     json.loads(PARENT.read_bytes()))
    if result["total_predeclared_delta_x_calibration_x_table_scores"]!=150:
        raise ValueError("frozen 150 analytical sensitivity cells incomplete")
    result["pre_first_output_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    summary=[]
    for row in result["all_5_original_observation_tables"]:
        summary.append({
            "table":row["hypothetical_observed_table"],
            "observed_count_OR":row["raw_observed_count_OR"],
            "exact_one_sided_97p5pct_lower_count_OR":
                row["exact_one_sided_97p5pct_detected_count_OR_lower"],
            "oracle_critical_delta":row[
                "oracle_target_mix_tipping_delta_analytic_or_null"],
            "critical_delta_by_detector_q_calibration":{
                ("oracle" if v["q_calibration_source"]=="oracle"
                 else str(v["q_reference_trial_opportunities_per_eight_q_cell"])):
                    v["critical_delta_supremum_or_null_if_delta0_fails"]
                for v in row["source_q_uncertainty_sensitivity"]
            }
        })
    print(json.dumps({
        "status":result["status"],
        "delta_grid":result["exact_oracle_detector_B_at_each_radius"],
        "radius_limit_summaries":summary,
        "no_ecobank_camera_or_animal_records_accessed":True,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
