#!/usr/bin/env python3
"""Source-free and outcome-free solar clock offset of the original 41 pairs."""
import hashlib
import json
from pathlib import Path
from odsp.uljin_original_pairs_equation_of_time_v0 import compare_original_41_mirror_noons

ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
FROZEN=ROOT/"ULJIN_ORIGINAL_41_EQUATION_OF_TIME_AUDIT_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_ORIGINAL_41_EQUATION_OF_TIME_FIRST_RECEIPT.json"

def main():
    contents=FROZEN.read_bytes()
    result=compare_original_41_mirror_noons(
        json.loads(MAIN.read_text()),json.loads(contents)
    )
    result["design_contract_sha256"]=hashlib.sha256(contents).hexdigest()
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "original_pair_count":result["fixed_original_calendar_pairs"],
        "solar_noon_shift_minutes_min":result["min_abs_solar_noon_clock_shift_minutes"],
        "solar_noon_shift_minutes_max":result["max_abs_solar_noon_clock_shift_minutes"],
        "real_camera_events_accessed":False,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
