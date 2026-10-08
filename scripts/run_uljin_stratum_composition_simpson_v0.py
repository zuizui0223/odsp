#!/usr/bin/env python3
"""First pre-result frozen 3 worlds x 2 intensity scales x 100 draws."""
import hashlib
import json
from pathlib import Path

from odsp.uljin_stratum_composition_simpson_v0 import run_panel

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_STRATUM_COMPOSITION_SIMPSON_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_STRATUM_COMPOSITION_SIMPSON_V0_FIRST_RECEIPT.json"


def main()->int:
    raw=PLAN.read_bytes()
    result=run_panel(json.loads(raw))
    if len(result["scenarios"])!=6 or result["worlds_per_scenario"]!=100:
        raise ValueError("original frozen 600-world panel incomplete")
    result["frozen_contract_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "oracle":result["population_oracle"],
        "scenarios":[{
            "id":s["scenario"],
            "scale":s["count_scale"],
            "pooled_positive":s["pooled_positive_heldout_gain_fraction"],
            "pooled_mean_gain":s["mean_pooled_heldout_gain_nats_per_original_cell"],
            "partial_weak_range":s["partial_weak_global_shape_range_mean"],
            "partial_strong_range":s["partial_strong_global_shape_range_mean"],
            "exact_reject":s["exact_conditional_rejection_fraction"],
            "informative":s["mean_informative_heldout_strata"],
        } for s in result["scenarios"]],
        "real_source_rows_opened":False,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
