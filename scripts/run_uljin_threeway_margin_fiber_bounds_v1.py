#!/usr/bin/env python3
"""First frozen exhaustive 2x2x6 positive integer margin fiber result."""
import hashlib
import json
from pathlib import Path
from odsp.uljin_threeway_margin_fiber_bounds_v1 import exhaustive_fiber_bounds
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_THREEWAY_MARGIN_FIBER_BOUNDS_V1_CONTRACT.json"
PARENT=ROOT/"ULJIN_THREEWAY_MARGIN_IDENTIFIABILITY_V0_FIRST_RESULT_LEDGER.json"
OUT=ROOT/"ULJIN_THREEWAY_MARGIN_FIBER_BOUNDS_V1_FIRST_RECEIPT.json"

def main()->int:
    frozen=PLAN.read_bytes()
    result=exhaustive_fiber_bounds(json.loads(frozen),json.loads(PARENT.read_bytes()))
    result["frozen_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "admissible_integer_full_tables":
            result["admissible_positive_integer_complete_table_count"],
        "sign_counts":result["by_direction"]["autumn_relative_early_minus_late"],
        "min_early_odds":result["min_early_site_first_vs_last_branch_odds_ratio"]["odds_ratio"],
        "max_early_odds":result["max_early_site_first_vs_last_branch_odds_ratio"]["odds_ratio"],
        "not_a_statistical_confidence_interval":True,
        "wildlife_source_rows_accessed":False,
    },sort_keys=True))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
