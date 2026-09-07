import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_aligned_refit_scheme_sensitivity_contract_is_frozen():
    contract = json.loads(
        (ROOT / "ALIGNED_REFIT_SCHEME_SENSITIVITY_CONTRACT.json").read_text(encoding="utf-8")
    )
    assert contract["contract_id"] == "odsp-aligned-refit-scheme-sensitivity-v1"
    definition = contract["definition"]
    assert definition["existing_refit_scheme_decision_rule_reused_unchanged"] is True
    assert definition["canonical_validation_row_ids_required"] is True
    assert definition["validation_row_ids_required_for_every_declared_scheme"] is True
    assert definition["reorderable_alignment_reorders_scheme_matrix_columns_to_base_order"] is True
    assert definition["row_mismatch_prevents_statistical_scheme_audit"] is True
    assert definition["existing_refit_scheme_contract_modified"] is False
    assert definition["automatic_scheme_selection"] is False
    assert definition["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 12
    assert all(value is True for key, value in obligations.items() if key != "aggregate_confidence_score_emitted")
    assert obligations["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_v4_boundary"].values())
