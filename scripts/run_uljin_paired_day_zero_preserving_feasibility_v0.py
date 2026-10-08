#!/usr/bin/env python3
"""Public aggregate-only source-free zero-event feasibility scenario.

This is NOT an empirical frequency of double detections or power
estimate for the EcoBank data. Site-specific rates, between-species
imbalance, temporal dependence and operating-hour support are unknown.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from odsp.uljin_paired_day_zero_preserving_feasibility_v0 import (
    hypothetical_station_species_pair_feasibility,
    fixed_clock_bin_poisson_log_score,
)
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_PAIRED_DAY_ZERO_PRESERVING_FEASIBILITY_V0_CONTRACT.json"
OUT=ROOT/"ULJIN_PAIRED_DAY_ZERO_PRESERVING_FEASIBILITY_FIRST_RECEIPT.json"


def main()->None:
    raw=PLAN.read_bytes()
    result=hypothetical_station_species_pair_feasibility(json.loads(raw))
    zero=[0]*6
    result["synthetic_all_zero_device_24h_low_rate_logscore"]=fixed_clock_bin_poisson_log_score(
        zero,[4.]*6,[.01]*6
    )
    result["synthetic_all_zero_device_24h_high_rate_logscore"]=fixed_clock_bin_poisson_log_score(
        zero,[4.]*6,[.02]*6
    )
    result["synthetic_all_zero_no_camera_uptime_logscore"]=fixed_clock_bin_poisson_log_score(
        zero,[0.]*6,[.01]*6
    )
    result["plan_sha256"]=hashlib.sha256(raw).hexdigest()
    if not (
        result["hypothetical_expected_station_species_date_pairs_with_both_days_detected"]<25
        and result["real_animal_records_opened"] is False
    ):
        raise ValueError("known-truth original hypothetical source scenario failed")
    OUT.write_text(
        json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status":result["status"],
        "hypothetical_expected_fully_detected_station_species_day_pairs":
            result["hypothetical_expected_station_species_date_pairs_with_both_days_detected"],
        "zero_detection_with_camera_uptime_penalizes_false_high_rate":
            result["synthetic_all_zero_device_24h_high_rate_logscore"]<
            result["synthetic_all_zero_device_24h_low_rate_logscore"],
        "actual_stations_or_species_checked":False,
    },sort_keys=True))


if __name__=="__main__":
    main()
