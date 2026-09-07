import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_refit_training_validation_provenance_contract_is_frozen():
    contract = json.loads(
        (ROOT / "REFIT_TRAINING_VALIDATION_PROVENANCE_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-refit-training-validation-provenance-v1"
    definition = contract["definition"]
    assert definition["validation_row_ids_are_canonical_and_unique"] is True
    assert definition["training_membership_is_declared_per_scheme_per_refit"] is True
    assert definition["duplicate_training_row_ids_are_allowed_and_reported"] is True
    assert definition["duplicate_training_rows_do_not_multiply_unique_overlap_count"] is True
    assert definition["any_direct_training_validation_row_overlap_category"] == "leakage_detected"
    assert definition["all_declared_training_memberships_disjoint_category"] == "training_validation_disjoint"
    assert definition["declared_expected_scheme_and_refit_coverage_must_match_exactly"] is True
    assert definition["actual_overlapping_row_ids_are_not_emitted"] is True
    assert definition["omitted_training_membership_is_never_inferred"] is True
    assert definition["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 15
    assert all(
        value is True
        for key, value in obligations.items()
        if key != "aggregate_confidence_score_emitted"
    )
    assert obligations["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_v4_boundary"].values())
