#!/usr/bin/env python3
"""Frozen source-free original-41 smooth solar alias oracle receipt."""
import hashlib
import json
from pathlib import Path

from odsp.uljin_all_41_smooth_solar_alias_v0 import (
    evaluate_all_41_smooth_solar_aliasing,
)

ROOT=Path(__file__).resolve().parents[1]
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
PLAN=ROOT/"ULJIN_ALL_41_SMOOTH_SOLAR_ALIAS_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_ALL_41_SMOOTH_SOLAR_ALIAS_V0_FIRST_RECEIPT.json"


def main() -> int:
    frozen=PLAN.read_bytes()
    cal=CAL.read_bytes()
    result=evaluate_all_41_smooth_solar_aliasing(json.loads(cal),json.loads(frozen))
    result["source_free_contract_sha256"]=hashlib.sha256(frozen).hexdigest()
    result["original_astronomical_contract_sha256"]=hashlib.sha256(cal).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "all_original_pairs":result["original_unchanged_calendar_pairs"],
        "profiles":{name:{
            "median_clock_gain_nats":v["median_clock_gain_nats"],
            "median_clock_gain_per_expected_event_nats":
                v["median_clock_gain_per_expected_event_nats"],
            "positive_pairs":v["positive_clock_oracle_pair_count"],
            "max_solar_gain_nats":v["maximum_abs_solar_oracle_gain_nats"],
        } for name,v in result["profiles"].items()},
        "wildlife_source_rows_accessed":False,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
