from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "N2_STATE_PREDICTION_EVIDENCE_MATRIX.json"
MH = ROOT / "MH_ANTWERPEN_STATE_PREDICTION_RECEIPT.json"
BOP = ROOT / "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json"
PRED = ROOT / "STATE_RESOLVED_PREDICTION_VALIDATION_RECEIPT.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_matrix_pins_synthetic_prediction_validation():
    matrix = _load(MATRIX)
    pred = _load(PRED)
    syn = matrix["synthetic_prediction_validation"]
    cells = {
        (c["family"], c["sample_size_per_base"]): c
        for c in pred["finite_sample_benchmark"]["cells"]
    }

    assert syn["replicates_per_cell"] == pred["finite_sample_benchmark"]["replicates_per_cell"] == 128
    assert syn["stable_generalizing"]["mean_gain_n50"] == cells[("stable_generalizing", 50)]["mean_log_score_gain"]
    assert syn["stable_generalizing"]["mean_gain_n1000"] == cells[("stable_generalizing", 1000)]["mean_log_score_gain"]
    assert syn["shifted_non_generalizing"]["mean_gain_n50"] == cells[("shifted_non_generalizing", 50)]["mean_log_score_gain"]
    assert syn["shifted_non_generalizing"]["mean_gain_n1000"] == cells[("shifted_non_generalizing", 1000)]["mean_log_score_gain"]
    assert syn["unorganized"]["mean_gain_n1000"] == cells[("unorganized", 1000)]["mean_log_score_gain"]


def test_matrix_pins_mh_unavailability_without_reinterpretation():
    matrix = _load(MATRIX)
    mh = _load(MH)
    row = matrix["prospective_state_prediction_endpoints"][0]

    assert row["endpoint"] == "MH_ANTWERPEN"
    assert row["terminal_category"] == mh["terminal"]["category"] == "empirical_state_prediction_unavailable"
    assert row["eligible_individuals"] == mh["terminal"]["observed_eligible_individuals"] == 3
    assert row["frozen_minimum_individuals"] == mh["terminal"]["frozen_minimum_eligible_individuals"] == 4
    assert row["thinned_events"] == mh["data_flow"]["thinned_event_count"] == 193370
    assert row["transferability_test_opened"] is False
    assert mh["terminal"]["primary_rf_folds_executed"] == 0


def test_matrix_pins_bop_primary_and_sensitivity_results():
    matrix = _load(MATRIX)
    bop = _load(BOP)
    row = matrix["prospective_state_prediction_endpoints"][1]
    rf = row["primary_random_forest"]
    source_rf = bop["primary_random_forest"]

    assert row["endpoint"] == "BOP_RODENT"
    assert row["eligible_individuals"] == bop["data_flow"]["eligible_individual_count"] == 30
    assert row["admitted_species"] == bop["data_flow"]["admitted_species_count"] == 4
    assert rf["terminal_category"] == source_rf["terminal_category"] == "empirical_state_prediction_mixed"
    assert rf["positive_gain_individuals"] == source_rf["positive_individual_count"] == 27
    assert rf["nonpositive_gain_individuals"] == source_rf["nonpositive_individual_count"] == 3
    assert rf["positive_brier_improvement_individuals"] == source_rf["positive_brier_improvement_count"] == 30
    assert rf["mean_gain_descriptive"] == source_rf["mean_gain_descriptive"]
    assert rf["mean_brier_improvement_descriptive"] == source_rf["mean_brier_improvement_descriptive"]
    assert rf["mean_top1_accuracy_descriptive"] == source_rf["mean_top1_accuracy_descriptive"]

    sens = row["multinomial_logit_sensitivity"]
    source_sens = bop["multinomial_logit_sensitivity"]
    assert sens["positive_gain_individuals"] == source_sens["positive_individual_count"] == 22
    assert sens["mean_gain_descriptive"] == source_sens["mean_gain_descriptive"]


def test_matrix_retains_fail_closed_claim_ceiling():
    matrix = _load(MATRIX)
    assert matrix["method_position"]["odsp_is_occurrence_sdm_algorithm"] is False
    assert "universal positive transfer across organisms or taxa" in matrix["claim_ceiling"]["not_supported"]
    assert "automatic N2-to-N3 state promotion" in matrix["claim_ceiling"]["not_supported"]
