import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_selection_validation_provenance_contract_is_frozen():
    contract = json.loads(
        (ROOT / "SELECTION_VALIDATION_PROVENANCE_CONTRACT.json").read_text(encoding="utf-8")
    )
    assert contract["contract_id"] == "odsp-selection-final-validation-provenance-v1"
    definition = contract["definition"]
    assert definition["final_validation_row_ids_are_canonical_and_unique"] is True
    assert definition["selection_rows_are_declared_by_named_stage"] is True
    assert definition["duplicate_selection_rows_are_allowed_and_reported"] is True
    assert definition["direct_overlap_category"] == "selection_validation_leakage"
    assert definition["fully_disjoint_category"] == "selection_validation_disjoint"
    assert definition["optional_expected_stage_names_require_exact_coverage"] is True
    assert definition["actual_overlapping_row_ids_are_not_emitted"] is True
    assert definition["missing_selection_history_is_never_inferred"] is True
    assert definition["automatic_candidate_selection"] is False
    assert definition["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 15
    assert all(value is True for key, value in obligations.items() if key != "aggregate_confidence_score_emitted")
    assert obligations["aggregate_confidence_score_emitted"] is False

    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_submission_boundary"].values())
