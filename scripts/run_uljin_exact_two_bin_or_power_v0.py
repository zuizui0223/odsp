#!/usr/bin/env python3
"""First frozen exact conditional sample-size curve, source-free."""
import hashlib
import json
from pathlib import Path
from odsp.uljin_exact_two_bin_or_power_v0 import frozen_two_bin_exact_power_panel

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_EXACT_TWO_BIN_OR_POWER_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_EXACT_TWO_BIN_OR_POWER_V0_FIRST_RECEIPT.json"

def main()->int:
    frozen=PLAN.read_bytes()
    result=frozen_two_bin_exact_power_panel(json.loads(frozen))
    if len(result["grid"])!=28 or not result["all_n_null_size_at_most_alpha"]:
        raise ValueError("first exact conditional test calibration incomplete")
    result["frozen_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "first_n_80pct":result["minimum_n_per_season_at_first_80_percent_power"],
        "sustained_n_80pct":
            result["minimum_n_per_season_sustained_80_percent_through_640"],
        "max_null_size":result["largest_exact_null_rejection_size"],
        "not_actual_wildlife_required_n":True,
        "original_wildlife_source_accessed":False
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
