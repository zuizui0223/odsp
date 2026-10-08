#!/usr/bin/env python3
"""First original 64-subset exact measurement budget and rank receipt."""
import hashlib
import json
from pathlib import Path
from odsp.uljin_minimal_threeway_measurement_v0 import evaluate_all_minimal_measurements

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_MINIMAL_THREEWAY_MEASUREMENT_V0_CONTRACT.json"
PARENT=ROOT/"ULJIN_THREEWAY_MARGIN_FIBER_BOUNDS_V1_FIRST_RESULT_LEDGER.json"
OUT=ROOT/"ULJIN_MINIMAL_THREEWAY_MEASUREMENT_V0_FIRST_RECEIPT.json"


def main()->int:
    frozen=CONTRACT.read_bytes()
    result=evaluate_all_minimal_measurements(json.loads(frozen),
                                              json.loads(PARENT.read_bytes()))
    if result["exhaustive_subset_count"]!=64:
        raise ValueError("predeclared exhaustive design set incomplete")
    result["frozen_design_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "all_subsets":result["exhaustive_subset_count"],
        "minimum_extra_cell_counts":
            result["minimum_number_of_additional_cell_counts_to_identify_any_fiber_world"],
        "one_night_cell_ambiguous_full_tables":next(
            row["feasible_tables_in_sign_ambiguous_classes"]
            for row in result["single_cell_designs"]
            if row["additional_early_rising_phase_bins"]==[5]
        ),
        "not_a_probability_or_power_calculation":True,
        "real_source_data_accessed":False,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
