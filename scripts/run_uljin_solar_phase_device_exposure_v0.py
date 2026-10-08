#!/usr/bin/env python3
"""First source-free exact solar-phase operating-effort test on fixed dates."""
import hashlib
import json
from pathlib import Path

from odsp.uljin_solar_phase_device_exposure_v0 import (
    phase_exposure_first_known_truth_control,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_SOLAR_PHASE_DEVICE_EXPOSURE_V0_CONTRACT.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_SOLAR_PHASE_DEVICE_EXPOSURE_V0_FIRST_RECEIPT.json"


def main():
    frozen=PLAN.read_bytes()
    result=phase_exposure_first_known_truth_control(
        json.loads(CAL.read_text()),json.loads(frozen)
    )
    result["frozen_design_sha256"]=hashlib.sha256(frozen).hexdigest()
    OUT.write_text(
        json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n"
    )
    print(json.dumps({
        "status":result["status"],
        "original_pairs":result["original_unmodified_astronomy_pairs"],
        "civil_clock_bin_changes_for_identical_solar_phase":
            result["clock_bin_artifact_without_solar_geometry_control"],
        "source_wildlife_or_operation_rows_accessed":False,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
