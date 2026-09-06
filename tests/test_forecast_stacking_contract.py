from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_group_safe_forecast_stacking_contract_freezes_roles_and_claims():
    contract = json.loads((ROOT / "GROUP_SAFE_FORECAST_STACKING_CONTRACT.json").read_text(encoding="utf-8"))
    assert contract["contract_id"] == "odsp-group-safe-forecast-stacking-v1"
    assert contract["data_roles"]["stacking_tuning"].startswith("learn convex mixture weights")
    assert contract["stacking_rule"]["validation_used_for_weight_fit"] is False
    assert contract["stacking_rule"]["member_coverage_inherited"] is False
    assert contract["stacking_rule"]["stack_requires_independent_recalibration_for_coverage_claim"] is True
    assert contract["validation_rule"]["generalizing_requires_all_group_gains_positive"] is True
    assert contract["validation_rule"]["pooled_mean_can_rescue_failed_group"] is False
    assert contract["claim_boundary"]["stacking_identifies_true_biological_mechanism"] is False
    assert contract["claim_boundary"]["stacking_guarantees_distribution_shift_robustness"] is False
    assert contract["claim_boundary"]["aggregate_confidence_score_emitted"] is False
    assert contract["frozen_v4_boundary"]["v4_manuscript_modified"] is False
    assert contract["frozen_v4_boundary"]["closed_empirical_endpoint_reopened"] is False
