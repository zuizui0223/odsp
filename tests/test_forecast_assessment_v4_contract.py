import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_assessment_v4_contract_is_frozen():
    contract = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V4_CONTRACT.json").read_text(encoding="utf-8")
    )
    assert contract["contract_id"] == "odsp-forecast-assessment-v4-row-provenance"
    composition = contract["composition_rule"]
    assert composition["v2_assessment_is_computed_once_and_preserved"] is True
    assert composition["existing_v3_certification_rule_reused_unchanged"] is True
    assert composition["existing_aligned_refit_scheme_audit_reused_unchanged"] is True
    assert composition["row_mismatch_withholds_scheme_aware_v3_assessment"] is True
    assert composition["row_mismatch_preserves_v2_evidence"] is True
    assert composition["row_mismatch_is_never_converted_to_scheme_uncertainty"] is True
    assert composition["aggregate_confidence_score_emitted"] is False

    rule = contract["decision_rule"]
    assert rule["successful_alignment_inherits_v3_certification_exactly"] is True
    assert rule["otherwise_row_mismatch_gives_v4_certification"] == "unavailable"
    assert rule["row_mismatch_blocking_reason"] == "heldout_row_mismatch"
    assert rule["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 12
    assert all(value is True for key, value in obligations.items() if key != "aggregate_confidence_score_emitted")
    assert obligations["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_manuscript_boundary"].values())
