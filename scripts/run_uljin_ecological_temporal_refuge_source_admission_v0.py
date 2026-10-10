#!/usr/bin/env python3
"""Outcome-blind source admission of the four-ungulate ecological hypothesis.

Usage: python scripts/run_uljin_ecological_temporal_refuge_source_admission_v0.py
  with NO raw original EcoBank archive: returns mandatory source HOLD.

When original v1.1 event member is independently verified, an explicitly
provided path may enable timestamp-only support counts:
  python scripts/run_uljin_ecological_temporal_refuge_source_admission_v0.py \
    --events path/to/01_core_data/cameratrap_event_records.csv \
    --verified-original-v1p1-member

This NEVER infers camera-hour effort from scheduled or functional nights.
Any real rate-based ecological inference requires a separate normalized
original operation interval member independently verified in source.
"""
import argparse
import csv
import json
from pathlib import Path

from odsp.uljin_ecological_temporal_refuge_v0 import (
    source_timestamp_audit
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_FOUR_UNGULATE_TEMPORAL_REFUGE_ECOLOGY_V0_CONTRACT.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--events",type=Path)
    parser.add_argument("--verified-original-v1p1-member",action="store_true")
    args=parser.parse_args()
    rows=[]
    if args.events:
        if not args.verified_original_v1p1_member:
            parser.error("source original v1.1 member attestation required")
        with args.events.open(encoding="utf-8-sig",newline="") as handle:
            rows=list(csv.DictReader(handle))
    output=source_timestamp_audit(
        json.loads(PLAN.read_text()),
        json.loads(CAL.read_text()),
        rows,
        source_member_verified=bool(
            args.events and args.verified_original_v1p1_member))
    print(json.dumps(output,sort_keys=True,indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
