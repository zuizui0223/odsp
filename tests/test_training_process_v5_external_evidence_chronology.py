from __future__ import annotations
import json
from pathlib import Path

P=Path("TRAINING_PROCESS_V5_EXTERNAL_EVIDENCE_CHRONOLOGY_CLARIFICATION.json")

def test_external_evidence_chronology_distinguishes_embedding_from_replay():
    p=json.loads(P.read_text(encoding="utf-8"))
    i=p["interpretation"]
    assert i["exact_route_evidence_hashes_existed_before_route_promotion_commit"] is True
    assert i["exact_route_evidence_hashes_existed_before_registration_merge"] is True
    assert i["standalone_independent_hash_replay_completed_before_registration_merge"] is False
    assert i["standalone_independent_hash_replay_completed_after_registration_merge"] is True
    assert i["post_merge_replay_matched_pre_registration_registry_hashes"] is True
    assert i["route_evidence_artifacts_changed_to_make_replay_pass"] is False

def test_chronology_clarification_is_not_new_qualification_evidence():
    b=json.loads(P.read_text(encoding="utf-8"))["boundary"]
    assert b["this_receipt_changes_route_evidence_chain"] is False
    assert b["this_receipt_changes_statistical_qualification"] is False
    assert b["purpose_is_chronology_clarity_only"] is True
