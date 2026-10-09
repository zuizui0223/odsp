#!/usr/bin/env python3
"""First prospective exact within-site detector crossproduct sensitivity receipt."""
import hashlib
import json
from pathlib import Path
from odsp.uljin_detector_bias_robust_or_v0 import evaluate_frozen_detector_sensitivity

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_DETECTOR_BIAS_ROBUST_OR_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_DETECTOR_BIAS_ROBUST_OR_V0_FIRST_RECEIPT.json"

def main()->int:
    original=PLAN.read_bytes()
    result=evaluate_frozen_detector_sensitivity(json.loads(original))
    if len(result["all_five_precommitted_tables"])!=5:
        raise ValueError("all frozen sensitivity cases required")
    result["pre_result_frozen_contract_sha256"]=hashlib.sha256(original).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "cases":[{
            "id":row["synthetic_table_id"],
            "raw_OR":row["raw_observed_count_OR"],
            "effort_adjusted_OR":row["effort_adjusted_observed_rate_OR"],
            "lower95_OR_without_detector_bias":row["detector_cap_sensitivity_grid"][0][
                "one_sided_95pct_lower_latent_encounter_OR"],
            "robust_at_B_1p5":row["detector_cap_sensitivity_grid"][2][
                "can_reject_latent_OR_le_1_given_calibrated_B"],
        } for row in result["all_five_precommitted_tables"]],
        "not_empirical_animal_inference":True
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
