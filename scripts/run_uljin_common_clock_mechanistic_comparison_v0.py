#!/usr/bin/env python3
"""First source-free fair observed CIVIL 15min bin model comparison."""
import json
import hashlib
from pathlib import Path

from odsp.uljin_common_clock_mechanistic_comparison_v0 import (
    run_frozen_common_clock_panel,
)

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"ULJIN_COMMON_CLOCK_MECHANISTIC_COMPARISON_V0_CONTRACT.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_COMMON_CLOCK_MECHANISTIC_COMPARISON_V0_FIRST_RECEIPT.json"


def main()->int:
    raw=CONTRACT.read_bytes()
    result=run_frozen_common_clock_panel(json.loads(CAL.read_bytes()),
                                         json.loads(raw))
    result["frozen_method_contract_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    summary={}
    for row in result["scenarios"]:
        k=f'{row["truth"]}|{row["counts_per_site_date"]}'
        summary.setdefault(k,{m:0 for m in result["candidate_models"]})
        summary[k][row["best_descriptive_heldout_model"]]+=1
    print(json.dumps({
        "status":result["status"],
        "all_original_mirror_pairs":result["original_calendar_pairs"],
        "same_original_civil_15min_bins":result["common_civil_clock_bin_count"],
        "all30_synthetic_worlds_retained":len(result["scenarios"]),
        "winner_counts_not_significance":summary,
        "wildlife_device_or_station_source_opened":False,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
