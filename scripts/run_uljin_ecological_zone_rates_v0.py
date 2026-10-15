#!/usr/bin/env python3
"""Real-source readiness for two ecological matched-daylength temporal refuges.

Outputs mandatory HOLD unless BOTH the original Version 1.1 ungulate
event member AND independently attested original camera operation log
have been verified. Does not infer camera activity from trap-nights.

Operation JSON is explicitly a NORMALIZED audit product, not assumed
raw EcoBank camera_operation_log.csv schema. Its independent provenance
and hour precision require verification upstream:

  [
    {"Station":"UJ1_01","Date":"2022-05-01",
     "operating_intervals_clock_minutes":[[0,300],[420,1440]]}, ...
  ]

The complete station×all original 82 dates roster is REQUIRED and
missing entries are not guessed to be camera-off. No station GPS read.
"""
from pathlib import Path
import argparse
import csv
import json

from odsp.uljin_ecological_refuge_rate_signatures_v0 import (
    compute_matched_daylength_zone_signatures,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_ECOLOGICAL_ZONE_SIGNATURE_V0_CONTRACT.json"
HYPOTHESIS=ROOT/"ULJIN_FOUR_UNGULATE_TEMPORAL_REFUGE_ECOLOGY_V0_CONTRACT.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"


def normalized_camera_operation(rows):
    if not isinstance(rows,list):
        raise ValueError("source-audited normalized camera operation must be a JSON array")
    ops={}
    for row in rows:
        if not isinstance(row,dict) or not {
            "Station","Date","operating_intervals_clock_minutes"
        }.issubset(row):
            raise ValueError("source original station/date/hour-interval fields absent")
        key=(row["Station"],row["Date"])
        if key in ops:
            raise ValueError("duplicate station/date original camera operation entry")
        ops[key]=row["operating_intervals_clock_minutes"]
    return ops


def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--original-events",type=Path)
    parser.add_argument("--normalized-original-operation-json",type=Path)
    parser.add_argument("--verified-original-v1p1-events",action="store_true")
    parser.add_argument("--verified-independent-operation-hours",action="store_true")
    args=parser.parse_args()
    verified=(
        bool(args.original_events)
        and bool(args.normalized_original_operation_json)
        and args.verified_original_v1p1_events
        and args.verified_independent_operation_hours
    )
    if verified:
        with args.original_events.open(encoding="utf-8-sig",newline="") as handle:
            records=list(csv.DictReader(handle))
        operations=normalized_camera_operation(
            json.loads(args.normalized_original_operation_json.read_text()))
    else:
        records=[]
        operations={}
    result=compute_matched_daylength_zone_signatures(
        json.loads(PLAN.read_text()),json.loads(HYPOTHESIS.read_text()),
        json.loads(CAL.read_text()),records,operations,
        independently_verified_v1p1_event_member=verified,
        independently_verified_original_operation_log=verified
    )
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
