import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_evaluation_content_provenance_contract_is_frozen():
    contract = json.loads(
        (ROOT / "EVALUATION_CONTENT_PROVENANCE_CONTRACT.json").read_text(encoding="utf-8")
    )
    assert contract["contract_id"] == "odsp-evaluation-content-provenance"
    assert contract["input_rule"]["digest_algorithm"] == "sha256"
    assert contract["input_rule"]["artifact_bytes_are_not_loaded_or_hashed_automatically"] is True
    assert contract["input_rule"]["semantic_equivalence_is_not_inferred"] is True
    assert contract["decision_rule"]["exact_final_digest_match_category"] == "final_evaluation_content_leakage"
    assert contract["decision_rule"]["no_final_digest_match_category"] == "final_evaluation_content_not_accessed_in_declared_pre_final_stages"
    assert contract["decision_rule"]["one_exact_digest_match_is_sufficient_for_leakage"] is True
    assert contract["decision_rule"]["digest_match_is_provenance_evidence_not_statistical_evidence"] is True

    obligations = contract["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 15
    assert all(
        value is True
        for key, value in obligations.items()
        if key != "aggregate_confidence_score_emitted"
    )
    assert obligations["aggregate_confidence_score_emitted"] is False
    assert all(value is False for value in contract["claim_boundary"].values())
    assert all(value is False for value in contract["frozen_submission_boundary"].values())
