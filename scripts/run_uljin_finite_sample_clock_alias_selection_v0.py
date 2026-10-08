#!/usr/bin/env python3
"""FIRST full 9x200 SOURCE-FREE same-event clock vs phase model-selection panel."""
import hashlib
import json
from pathlib import Path

from odsp.uljin_finite_sample_clock_alias_selection_v0 import (
    run_frozen_finite_sample_panel,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"ULJIN_FINITE_SAMPLE_CLOCK_ALIAS_SELECTION_V0_CONTRACT.json"
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
OUT=ROOT/"ULJIN_FINITE_SAMPLE_CLOCK_ALIAS_SELECTION_V0_FIRST_RECEIPT.json"


def main()->int:
    p=PLAN.read_bytes()
    c=CAL.read_bytes()
    result=run_frozen_finite_sample_panel(json.loads(c),json.loads(p))
    if result["worlds_per_case_executed"]!=200 or result["case_count"]!=9:
        raise ValueError("first precommitted panel not complete")
    result["frozen_contract_sha256"]=hashlib.sha256(p).hexdigest()
    result["original_calendar_sha256"]=hashlib.sha256(c).hexdigest()
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "worlds_per_case":result["worlds_per_case_executed"],
        "cases":[{
            "profile":x["profile"],"n":x["total_expected_events"],
            "clock_only":x["clock_only_selection_frequency"],
            "civil_any":x["clock_shape_selection_frequency"],
            "phase_any":x["solar_shape_selection_frequency"],
            "mean_civil_gain":x["mean_clock_gain_nats_per_original_site_cell"],
            "mean_phase_gain":x["mean_solar_gain_nats_per_original_site_cell"],
        } for x in result["cases"]],
        "real_source_records_opened":False,
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
