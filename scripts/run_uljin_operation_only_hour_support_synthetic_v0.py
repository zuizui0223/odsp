#!/usr/bin/env python3
"""Proof-of-contract on INVENTED Uljin camera operation rows, not real data.

This first synthetic receipt is explicitly NOT a station availability
report. The original EcoBank operation ZIP/source bytes remain missing;
true camera uptime, field log provenance and wildlife outcome embargo
cannot be resolved by fabricating identical coverage in a test.
"""
import hashlib
import json
from pathlib import Path

from odsp.uljin_operation_only_mirror_hour_support_v0 import (
    summarize_mirror_camera_hour_support,
)

ROOT=Path(__file__).resolve().parents[1]
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
PLAN=ROOT/"ULJIN_OPERATION_ONLY_MIRRORED_DAY_EXPOSURE_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_OPERATION_ONLY_HOUR_SUPPORT_SYNTHETIC_FIRST_RECEIPT.json"


def main():
    frozen=PLAN.read_bytes()
    demo=[
        {"Station":region,
         "DeploymentStart":"2022-04-01T00:00:00+09:00",
         "DeploymentEnd":"2022-10-01T00:00:00+09:00"}
        for region in ("UJ1-demo","UJ2-demo")
    ]
    result=summarize_mirror_camera_hour_support(
        json.loads(CAL.read_text()),json.loads(frozen),
        demo,[],
    )
    if (result["status"]!=
            "SYNTHETIC_OPERATION_INPUT_COUNTS_NOT_EMPIRICAL_ELIGIBILITY"
        or result["original_unchanged_astronomical_date_pairs"]!=41
        or result["original_EcoBank_v1p1_operation_logs_verified"] is not False
        or result["species_detection_data_opened"] is not False):
        raise ValueError("synthetic source-only guard violated")
    output={
        "schema_version":1,
        "audit":"original_41_mirror_dates_hourly_uptime_synthetic_ONLY",
        "contract_sha256":hashlib.sha256(frozen).hexdigest(),
        "status":"PASS_SYNTHETIC_INTERVAL_ARITHMETIC_NO_REAL_SOURCE",
        "original_EcoBank_file_accessed":False,
        "source_log_lineage_independent_verified":False,
        "actual_station_eligibility_calculated":False,
        "animal_detection_or_species_observations_read":False,
        "synthetic_demo":result,
        "qualified_ecological_inference":False,
    }
    OUT.write_text(json.dumps(output,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "status":output["status"],
        "original_pairs":result["original_unchanged_astronomical_date_pairs"],
        "real_station_hour_support_known":False,
        "real_wildlife_data_accessed":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
