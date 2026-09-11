import json
from pathlib import Path


CONTRACT = Path(__file__).resolve().parents[1] / "FORECAST_ASSESSMENT_V11_CHECKPOINT_CONTRACT.json"


def test_forecast_assessment_v11_contract_is_frozen():
    contract = json.loads(CONTRACT.read_text())
    assert contract["contract_id"] == "odsp-forecast-assessment-v11-checkpoint-gate"
    assert contract["frozen_date"] == "2026-09-11"
    assert contract["composition_rule"]["checkpoint_provenance_runs_before_full_v10_path"] is True
    assert contract["composition_rule"]["checkpoint_mismatch_prevents_full_v10_path"] is True
    assert contract["composition_rule"]["same_event_sequence_audited_by_checkpoints_is_forwarded_to_v10_when_clean"] is True
    assert contract["decision_rule"]["checkpoint_mismatch_adds_provenance_reason"] == "evaluation_access_checkpoint_mismatch"
    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 19
    assert all(value is True for key, value in obligations.items() if key != "aggregate_confidence_score_emitted")
    assert obligations["aggregate_confidence_score_emitted"] is False
    assert contract["claim_boundary"]["clean_checkpoints_prove_external_timestamping"] is False
    assert contract["claim_boundary"]["clean_checkpoints_prevent_whole_chain_and_checkpoint_cofabrication"] is False
    assert contract["decision_rule"]["aggregate_confidence_score_emitted"] is False
