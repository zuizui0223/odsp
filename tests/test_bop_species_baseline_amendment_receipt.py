from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "BOP_RODENT_SPECIES_BASELINE_AMENDMENT_RECEIPT.json"
PRIMARY = ROOT / "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json"
MATRIX = ROOT / "N2_STATE_PREDICTION_EVIDENCE_MATRIX.json"


def _read(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_receipt_preserves_frozen_primary_endpoint():
    receipt = _read(RECEIPT)
    primary = _read(PRIMARY)
    assert receipt["post_outcome_amendment"] is True
    assert receipt["frozen_primary_endpoint"]["terminal_category"] == primary["primary_random_forest"]["terminal_category"]
    assert receipt["frozen_primary_endpoint"]["positive_individual_count"] == primary["primary_random_forest"]["positive_individual_count"] == 27
    assert receipt["frozen_primary_endpoint"]["eligible_individual_count"] == primary["primary_random_forest"]["eligible_individual_count"] == 30
    assert math.isclose(
        receipt["frozen_primary_endpoint"]["mean_total_gain"],
        primary["primary_random_forest"]["mean_gain_descriptive"],
        rel_tol=0.0,
        abs_tol=1e-15,
    )
    assert receipt["frozen_primary_endpoint"]["terminal_decision_recomputed"] is False
    assert receipt["frozen_primary_endpoint"]["terminal_decision_changed"] is False


def test_overall_decomposition_is_additive_and_context_dominates_descriptive_mean():
    receipt = _read(RECEIPT)
    summary = receipt["overall_summary"]
    assert summary["individual_count"] == 30
    assert math.isclose(
        summary["mean_total_gain"],
        summary["mean_species_component"] + summary["mean_context_within_species_component"],
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert summary["mean_context_within_species_component"] > summary["mean_species_component"]
    assert summary["positive_context_component_count"] == 23
    assert summary["positive_species_component_count"] == 23
    assert summary["max_abs_pooled_baseline_reconstruction_error"] < 1e-10
    assert summary["max_abs_additivity_error"] < 1e-10


def test_species_state_counts_sum_to_frozen_eligible_event_count():
    receipt = _read(RECEIPT)
    primary = _read(PRIMARY)
    total = sum(
        sum(species_row["state_counts"].values())
        for species_row in receipt["species_summary"].values()
    )
    assert total == primary["data_flow"]["eligible_event_count"] == 154655


def test_pygargus_gain_is_not_primarily_species_baseline_effect():
    receipt = _read(RECEIPT)
    row = receipt["species_summary"]["Circus pygargus"]
    assert row["individual_count"] == 9
    assert math.isclose(
        row["mean_total_gain"],
        row["mean_species_component"] + row["mean_context_within_species_component"],
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    assert row["mean_context_within_species_component"] > row["mean_species_component"]
    assert row["positive_context_component_count"] == 9


def test_buteo_exposes_heterogeneous_component_pattern():
    receipt = _read(RECEIPT)
    row = receipt["species_summary"]["Buteo buteo"]
    assert row["mean_total_gain"] > 0
    assert row["mean_species_component"] > 0
    assert row["mean_context_within_species_component"] < 0
    assert row["positive_context_component_count"] == 0


def test_amendment_did_not_refit_reaccess_or_retune():
    receipt = _read(RECEIPT)
    assert receipt["model_refit_performed"] is False
    assert receipt["raw_source_data_reaccessed"] is False
    assert receipt["retuning_performed"] is False


def test_anonymous_evidence_matrix_exposes_amendment_without_reclassifying_bop():
    receipt = _read(RECEIPT)
    matrix = _read(MATRIX)
    bop = next(
        row for row in matrix["prospective_state_prediction_endpoints"]
        if row["endpoint"] == "BOP_RODENT"
    )
    amendment = bop["descriptive_species_baseline_amendment"]
    assert amendment["post_outcome_amendment"] is True
    assert amendment["primary_comparator_and_terminal_rule_unchanged"] is True
    assert bop["primary_random_forest"]["terminal_category"] == "empirical_state_prediction_mixed"
    assert math.isclose(
        amendment["overall_mean_species_component"],
        receipt["overall_summary"]["mean_species_component"],
        rel_tol=0.0,
        abs_tol=1e-15,
    )
    assert math.isclose(
        amendment["overall_mean_context_within_species_component"],
        receipt["overall_summary"]["mean_context_within_species_component"],
        rel_tol=0.0,
        abs_tol=1e-15,
    )
    for species, receipt_row in receipt["species_summary"].items():
        assert amendment["species"][species]["state_counts"] == receipt_row["state_counts"]
