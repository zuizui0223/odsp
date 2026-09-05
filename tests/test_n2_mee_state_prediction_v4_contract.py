from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "N2_MEE_STATE_PREDICTION_V4_CONTRACT.json"
MATRIX = ROOT / "N2_STATE_PREDICTION_EVIDENCE_MATRIX.json"
MH = ROOT / "MH_ANTWERPEN_STATE_PREDICTION_RECEIPT.json"
BOP = ROOT / "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v4_contract_pins_prediction_endpoints_without_relaxing_them():
    contract = _load(CONTRACT)
    matrix = _load(MATRIX)
    mh = _load(MH)
    bop = _load(BOP)

    assert contract["primary_prediction_target"] == ["P(A|X)", "P(A|B)"]
    assert contract["method_position"]["new_occurrence_sdm_algorithm"] is False

    c_mh = contract["prospective_prediction_endpoints"]["MH_ANTWERPEN"]
    assert c_mh["terminal_category"] == mh["terminal"]["category"] == "empirical_state_prediction_unavailable"
    assert c_mh["eligible_individuals"] == mh["terminal"]["observed_eligible_individuals"] == 3
    assert c_mh["frozen_minimum_individuals"] == mh["terminal"]["frozen_minimum_eligible_individuals"] == 4
    assert c_mh["primary_transfer_folds_executed"] == mh["terminal"]["primary_rf_folds_executed"] == 0

    c_bop = contract["prospective_prediction_endpoints"]["BOP_RODENT"]
    rf = bop["primary_random_forest"]
    assert c_bop["terminal_category"] == rf["terminal_category"] == "empirical_state_prediction_mixed"
    assert c_bop["eligible_individuals"] == rf["eligible_individual_count"] == 30
    assert c_bop["positive_log_gain_individuals"] == rf["positive_individual_count"] == 27
    assert c_bop["nonpositive_log_gain_individuals"] == rf["nonpositive_individual_count"] == 3
    assert c_bop["positive_brier_improvement_individuals"] == rf["positive_brier_improvement_count"] == 30

    assert matrix["prospective_state_prediction_endpoints"][1]["primary_random_forest"]["terminal_category"] == c_bop["terminal_category"]


def test_v4_contract_preserves_v3_and_scientific_boundaries():
    contract = _load(CONTRACT)
    assert not any(contract["v3_preservation"].values())
    boundary = contract["scientific_boundary"]
    assert boundary == {
        "closed_tawaki_reopened": False,
        "closed_bat_reopened": False,
        "closed_serengeti_reopened": False,
        "closed_mh_endpoint_rescued": False,
        "bop_mixed_terminal_relaxed_to_generalizing": False,
        "universal_positive_transfer_claimed": False,
        "causal_prediction_claimed": False,
        "fundamental_niche_claimed": False,
        "absolute_altitude_relabelled_as_height_above_ground": False,
        "n2_output_automatically_promoted_to_n3": False,
    }


def test_v4_contract_requires_anonymous_bundle_internal_test():
    contract = _load(CONTRACT)
    review = contract["anonymous_review_bundle"]
    assert review["raw_terminal_receipts_with_internal_workflow_or_pr_provenance_included"] is False
    assert review["sanitized_scientific_state_prediction_summary_included"] is True
    assert review["bundle_internal_pytest_required"] is True
    assert review["author_identity_allowed"] is False
    assert review["repository_or_pr_identity_allowed"] is False
