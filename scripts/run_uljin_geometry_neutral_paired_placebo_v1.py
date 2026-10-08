#!/usr/bin/env python3
"""Full 1800-world post-v0 but pre-placebo-frozen source-free counterfactual."""
import hashlib
import json
from pathlib import Path

from odsp.uljin_geometry_neutral_paired_placebo_v1 import (
    run_paired_geometry_placebo_panel,
)

ROOT=Path(__file__).resolve().parents[1]
CAL=ROOT/"ULJIN_PHOTOPERIOD_MIRROR_2022_V0_DESIGN_CONTRACT.json"
V0=ROOT/"ULJIN_FINITE_SAMPLE_CLOCK_ALIAS_SELECTION_V0_CONTRACT.json"
LEDGER=ROOT/"ULJIN_FINITE_SAMPLE_CLOCK_ALIAS_SELECTION_V0_FIRST_RESULT_LEDGER.json"
PLAN=ROOT/"ULJIN_GEOMETRY_NEUTRAL_PAIRED_PLACEBO_V1_CONTRACT.json"
OUT=ROOT/"ULJIN_GEOMETRY_NEUTRAL_PAIRED_PLACEBO_V1_FIRST_RECEIPT.json"


def main()->int:
    plan_bytes=PLAN.read_bytes()
    result=run_paired_geometry_placebo_panel(
        json.loads(CAL.read_bytes()),json.loads(V0.read_bytes()),
        json.loads(LEDGER.read_bytes()),json.loads(plan_bytes))
    if result["case_count"]!=9 or result["worlds_per_case"]!=200:
        raise ValueError("full panel and no post-outcome subsets required")
    if not result["v0_outcome_replayed_if_full_panel"]:
        raise ValueError("pre-existing first statistical outcome replay missing")
    result["frozen_placebo_contract_sha256"]=hashlib.sha256(plan_bytes).hexdigest()
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({
        "status":result["status"],"cases":[{
            "profile":v["profile"],"n":v["expected_total_events"],
            "actual_only":v["actual_clock_only_selection_frequency"],
            "neutral_only":v["placebo_clock_only_selection_frequency"],
            "paired_excess":v["paired_excess_clock_only_frequency"],
            "paired_mc_se":v["paired_excess_monte_carlo_standard_error"],
        } for v in result["cases"]],
        "source_animal_and_uptime_rows_accessed":False,
        "v0_replay_passed":True,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
