import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_assessment_v9_ledger_binding_contract_is_frozen():
    contract = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V9_LEDGER_BINDING_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-forecast-assessment-v9-ledger-binding-gate"

    composition = contract["composition_rule"]
    assert composition["forecast_assessment_v8_code_or_contract_is_not_modified"] is True
    assert composition["evaluation_ledger_binding_contract_is_reused_unchanged"] is True
    assert composition["ledger_binding_runs_before_full_v8_path"] is True
    assert composition["ledger_binding_mismatch_prevents_full_v8_path"] is True
    assert composition["downstream_v8_assessment_is_absent_on_binding_mismatch"] is True
    assert composition["content_artifact_access_selection_training_row_alignment_and_scheme_statistics_are_not_run_on_binding_mismatch"] is True
    assert composition["binding_inputs_are_the_same_ledgers_forwarded_to_v8_when_binding_is_clean"] is True
    assert composition["aggregate_confidence_score_emitted"] is False

    inputs = contract["input_rule"]
    assert inputs["binding_requires_final_artifact_id_final_digest_manifest_id_ledger_and_digest_ledger_together"] is True
    assert inputs["binding_manifest_is_not_inferred"] is True
    assert inputs["access_or_content_ledgers_are_not_reconstructed_from_the_manifest"] is True

    decision = contract["decision_rule"]
    assert decision["binding_mismatch_on_otherwise_certifiable_base_gives_unavailable"] is True
    assert decision["binding_mismatch_adds_provenance_reason"] == "evaluation_ledger_binding_mismatch"
    assert decision["clean_binding_plus_content_leakage_inherits_v8_provenance_unavailable"] is True
    assert decision["clean_binding_plus_scheme_sensitive_inherits_v8_not_certified"] is True
    assert decision["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 17
    assert all(
        value is True
        for key, value in obligations.items()
        if key != "aggregate_confidence_score_emitted"
    )
    assert obligations["aggregate_confidence_score_emitted"] is False

    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_submission_boundary"].values())
