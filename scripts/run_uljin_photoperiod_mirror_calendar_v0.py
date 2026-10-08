#!/usr/bin/env python3
"""Outcome-free Uljin 2022 astronomical photoperiod-mirror calendar design.

The only inputs are a frozen JSON design and standard astronomy. This
must never be interpreted as 82 actual paired field sites/events or
proof of uptime, temperature effects or novel animal behavior.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from odsp.uljin_photoperiod_mirror_design_v0 import (
    generate_preoutcome_2022_mirror_calendar,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_FIRST_CALENDAR_RECEIPT.json"


def main()->int:
    raw=PLAN.read_bytes()
    panel=generate_preoutcome_2022_mirror_calendar(json.loads(raw))
    panel["frozen_design_sha256"]=hashlib.sha256(raw).hexdigest()
    OUT.write_text(
        json.dumps(panel,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status":panel["status"],
        "candidate_mirror_date_pairs":panel["selected_nonoverlapping_calendar_day_pairs"],
        "worst_daylength_error_minutes":panel["worst_matched_daylength_discrepancy_minutes"],
        "wildlife_rows_accessed":False,
        "camera_hourly_uptime_verified":False,
        "individual_station_support_verified":False,
        "receipt":OUT.name,
    },ensure_ascii=False,sort_keys=True),flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
