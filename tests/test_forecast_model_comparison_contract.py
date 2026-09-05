from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_model_comparison_contract_freezes_decision_order_and_claim_boundary():
    contract = json.loads(
        (ROOT / "FORECAST_MODEL_COMPARISON_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-forecast-model-comparison-v1"
    assert contract["default_coverage_tolerance"] == 0.03
    benchmark = contract["known_truth_benchmark"]
    assert benchmark["gain_tolerance"] == 1e-12
    assert len(benchmark["obligations"]) == 8

    correction = contract["contract_correction_provenance"]
    assert correction["candidate_rank_changed"] is False
    assert correction["candidate_admission_changed"] is False
    assert correction["coverage_threshold_changed"] is False
    assert correction["synthetic_generator_changed"] is False

    boundary = contract["claim_boundary"]
    assert boundary["best_candidate_is_true_biological_model"] is False
    assert boundary["coverage_implies_transferability"] is False
    assert boundary["transferability_implies_calibration"] is False
    assert boundary["sharpness_can_override_bad_coverage"] is False
    assert boundary["pooled_mean_can_override_group_failure"] is False
    assert boundary["comparison_establishes_causality"] is False
    assert boundary["aggregate_confidence_score_emitted"] is False
    frozen = contract["frozen_v4_preservation"]
    assert all(value is False for value in frozen.values())
