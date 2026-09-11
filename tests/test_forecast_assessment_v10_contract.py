import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_forecast_assessment_v10_log_chain_contract_is_frozen():
    contract = json.loads(
        (ROOT / "FORECAST_ASSESSMENT_V10_LOG_CHAIN_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-forecast-assessment-v10-access-log-chain-gate"

    composition = contract["composition_rule"]
    assert composition["forecast_assessment_v9_code_or_contract_is_not_modified"] is True
    assert composition["evaluation_access_log_chain_contract_is_reused_unchanged"] is True
    assert composition["log_chain_runs_before_full_v9_path"] is True
    assert composition["log_chain_mismatch_prevents_full_v9_path"] is True
    assert composition["same_stage_id_and_digest_ledgers_audited_by_log_chain_are_forwarded_to_v9_when_clean"] is True
    assert composition["log_chain_mismatch_is_provenance_failure_not_statistical_uncertainty"] is True
    assert composition["aggregate_confidence_score_emitted"] is False

    inputs = contract["input_rule"]
    assert all(inputs.values())

    decision = contract["decision_rule"]
    assert decision["log_chain_mismatch_on_otherwise_certifiable_base_gives_unavailable"] is True
    assert decision["log_chain_mismatch_adds_provenance_reason"] == "evaluation_access_log_chain_mismatch"
    assert decision["log_chain_mismatch_does_not_add_statistical_reason"] is True
    assert decision["clean_log_chain_plus_ledger_binding_mismatch_inherits_v9_unavailable"] is True
    assert decision["clean_log_chain_plus_content_leakage_inherits_v9_unavailable"] is True
    assert decision["clean_log_chain_plus_selection_leakage_inherits_v9_unavailable"] is True
    assert decision["clean_log_chain_plus_training_leakage_inherits_v9_unavailable"] is True
    assert decision["clean_log_chain_plus_row_mismatch_inherits_v9_unavailable"] is True
    assert decision["clean_log_chain_plus_scheme_sensitive_inherits_v9_not_certified"] is True
    assert decision["aggregate_confidence_score_emitted"] is False

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 18
    assert all(
        value is True
        for key, value in obligations.items()
        if key != "aggregate_confidence_score_emitted"
    )
    assert obligations["aggregate_confidence_score_emitted"] is False

    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_submission_boundary"].values())
