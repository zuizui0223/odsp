from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "MH_ANTWERPEN_STATE_PREDICTION_RECEIPT.json"
CONTRACT = ROOT / "MH_ANTWERPEN_STATE_PREDICTION_CONTRACT.json"


def test_receipt_closes_before_transferability_without_retuning():
    r = json.loads(RECEIPT.read_text(encoding="utf-8"))
    c = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert r["contract_id"] == c["contract_id"]
    assert r["terminal"]["category"] == "empirical_state_prediction_unavailable"
    assert r["terminal"]["reason"] == "fewer_than_minimum_eligible_individuals"
    assert r["terminal"]["frozen_minimum_eligible_individuals"] == c["independence_and_admission"]["minimum_eligible_individuals"] == 4
    assert r["terminal"]["observed_eligible_individuals"] == 3
    assert r["terminal"]["primary_rf_folds_executed"] == 0
    assert r["terminal"]["retuning_performed"] is False
    assert r["not_a_biological_null"] is True


def test_receipt_records_abundant_data_but_only_three_independent_individuals():
    r = json.loads(RECEIPT.read_text(encoding="utf-8"))
    flow = r["data_flow"]
    assert flow["raw_row_count"] == 393122
    assert flow["admissible_before_thinning"] == 386072
    assert flow["thinned_event_count"] == 193370
    assert flow["individual_count_before_admission"] == 3
    assert flow["eligible_individual_count"] == 3
    assert sum(flow["thinned_state_counts"].values()) == flow["thinned_event_count"]
    assert all(item["thinned_events"] >= 300 for item in r["eligible_individuals"])


def test_receipt_pins_public_artifact_and_scientific_boundaries():
    r = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert r["source"]["workflow_run_id"] == 33896256836
    assert r["source"]["artifact_id"] == 9945858782
    assert r["source"]["artifact_digest"] == "sha256:01a88fa59e0583d9ad0f25c8840cb4da95792d8c62a71be04b5b94761bbd8925"
    boundary = r["scientific_boundary"]
    assert boundary["transferability_test_opened"] is False
    assert boundary["minimum_individual_threshold_changed"] is False
    assert boundary["altitude_bins_changed"] is False
    assert boundary["primary_model_changed"] is False
    assert boundary["closed_tawaki_reopened"] is False
    assert boundary["closed_bat_reopened"] is False
    assert boundary["closed_serengeti_reopened"] is False
