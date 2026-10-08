#!/usr/bin/env python3
"""Frozen synthetic time-coordinate equivalence and invariance panel.

Produces one JSON receipt with two opposed KNOWN-TRUTH worlds and a
deterministic equal-identity comparison. Uses no camera detection data.
It never alters the original RI negative/season-parity empirical result.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from odsp.ri_temporal_coordinate_equivalence_synthetic_v0 import (
    synthetic_population_coordinate_test,
)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/"RI_TEMPORAL_COORDINATE_EQUIVALENCE_SYNTHETIC_V0_CONTRACT.json"
RECEIPT=ROOT/"RI_TEMPORAL_COORDINATE_EQUIVALENCE_SYNTHETIC_V0_FIRST_RECEIPT.json"


def main()->int:
    frozen=PLAN.read_bytes()
    result=synthetic_population_coordinate_test(json.loads(frozen))
    result["frozen_synthetic_plan_sha256"]=hashlib.sha256(frozen).hexdigest()
    outcome_a=result["known_solar_invariant_truth"]["equal_context_mean_advantage"]
    outcome_b=result["known_clock_invariant_truth"]["equal_context_mean_advantage"]
    result["dual_opposed_invariance_controls_passed"]=bool(
        outcome_a>0.001 and outcome_b>0.001
    )
    if not result["dual_opposed_invariance_controls_passed"]:
        raise ValueError("predeclared two-way synthetic model truth controls failed")
    RECEIPT.write_text(
        json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status":result["status"],
        "mean_expected_solar_truth_solar_model_advantage_nats":outcome_a,
        "mean_expected_clock_truth_clock_model_advantage_nats":outcome_b,
        "dual_opposed_invariance_controls_passed":True,
        "wildlife_source_data_accessed":False,
        "receipt":RECEIPT.name,
    },sort_keys=True),flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
