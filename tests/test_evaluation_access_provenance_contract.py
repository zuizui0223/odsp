import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_evaluation_access_provenance_contract_is_frozen():
    c = json.loads((ROOT / "EVALUATION_ACCESS_PROVENANCE_CONTRACT.json").read_text(encoding="utf-8"))
    assert c["contract_id"] == "odsp-final-evaluation-access-provenance-v1"
    d = c["definition"]
    assert d["direct_final_artifact_reuse_category"] == "final_evaluation_access_leakage"
    assert d["fully_disjoint_declared_access_category"] == "final_evaluation_not_accessed_in_declared_pre_final_stages"
    assert d["unlogged_accesses_are_never_inferred"] is True
    assert d["ledger_completeness_is_not_assumed"] is True
    assert d["aggregate_confidence_score_emitted"] is False
    obligations = c["known_truth_benchmark"]["frozen_obligations"]
    assert len(obligations) == 15
    assert all(v is True for k, v in obligations.items() if k != "aggregate_confidence_score_emitted")
    assert obligations["aggregate_confidence_score_emitted"] is False
    assert all(v is False for v in c["claim_boundary"].values())
    assert all(v is False for v in c["frozen_submission_boundary"].values())
