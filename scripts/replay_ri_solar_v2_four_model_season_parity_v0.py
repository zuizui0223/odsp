#!/usr/bin/env python3
"""Replay original Rhode Island 4-model predictions from first result ONLY.

No public Zenodo ZIP is downloaded, no model refit, no new result
hypothesis test. This companion was designed after the first ecological
v2 score exposure and is explicitly descriptive.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from odsp.ri_solar_v2_four_model_season_parity_v0 import audit_four_model_parity

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/".analysis_input"/"RI_SOLAR_CLOCK_YEARSEASON_V2_FIRST_RESULT.json"
PLAN=ROOT/"RI_SOLAR_V2_FOUR_MODEL_SEASON_PARITY_AUDIT_CONTRACT.json"
OUTPUT=ROOT/"RI_SOLAR_V2_FOUR_MODEL_SEASON_PARITY_FIRST_RECEIPT.json"


def main() -> int:
    raw_plan=PLAN.read_bytes()
    audited=audit_four_model_parity(
        INPUT.read_bytes(),
        json.loads(raw_plan),
    )
    audited["plan_sha256"]=hashlib.sha256(raw_plan).hexdigest()
    OUTPUT.write_text(
        json.dumps(audited,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)+"\n",
        encoding="utf-8",
    )
    summary={
        "original_status":audited["original_scientific_status"],
        "same_target":"six local civil-clock bins",
        "winter_pooled_solar_minus_clock":
            audited["comparisons"]["winter"]["original_same_site_weighted_pooled_solar_minus_clock"],
        "winter_season_conditional_solar_minus_clock":
            audited["comparisons"]["winter"]["season_conditional_solar_minus_clock"],
        "summer_pooled_solar_minus_clock":
            audited["comparisons"]["summer"]["original_same_site_weighted_pooled_solar_minus_clock"],
        "summer_season_conditional_solar_minus_clock":
            audited["comparisons"]["summer"]["season_conditional_solar_minus_clock"],
        "both_season_clock_conditional_means_higher":
            audited["clock_season_model_higher_mean_than_solar_season_in_both_groups"],
        "independent_confirmation":False,
        "significance_of_adjusted_contrast_estimated":False,
        "receipt":OUTPUT.name,
    }
    print(json.dumps(summary,sort_keys=True,allow_nan=False,ensure_ascii=False),flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
