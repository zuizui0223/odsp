from hashlib import sha256

import pytest

from odsp.evaluation_access_log_chain import (
    GENESIS_EVENT_HASH,
    audit_evaluation_access_log_chain,
    compute_access_event_hash,
)


def _digest(text: str) -> str:
    return "sha256:" + sha256(text.encode()).hexdigest()


def _event():
    digest = _digest("artifact")
    event_hash = compute_access_event_hash(0, "review", "artifact-a", digest, GENESIS_EVENT_HASH)
    return {
        "sequence_index": 0,
        "stage_name": "review",
        "artifact_id": "artifact-a",
        "artifact_digest": digest,
        "previous_event_hash": GENESIS_EVENT_HASH,
        "event_hash": event_hash,
    }


def test_clean_single_event_chain_passes():
    event = _event()
    result = audit_evaluation_access_log_chain(
        [event],
        1,
        event["event_hash"],
        {"review": ("artifact-a",)},
        {"review": (event["artifact_digest"],)},
    )
    assert result.log_chain_consistent is True
    assert result.separation_category == "evaluation_access_log_chain_consistent"


def test_payload_mutation_without_rehash_fails():
    event = _event()
    event["artifact_id"] = "artifact-b"
    result = audit_evaluation_access_log_chain(
        [event],
        1,
        event["event_hash"],
        {"review": ("artifact-b",)},
        {"review": (event["artifact_digest"],)},
    )
    assert result.log_chain_consistent is False
    assert result.recomputed_event_hash_match is False


def test_ledger_substitution_fails_without_emitting_values():
    event = _event()
    result = audit_evaluation_access_log_chain(
        [event],
        1,
        event["event_hash"],
        {"review": ("artifact-substituted",)},
        {"review": (event["artifact_digest"],)},
    )
    assert result.stage_artifact_id_ledger_match is False
    assert result.separation_category == "evaluation_access_log_chain_mismatch"
    assert result.artifact_ids_emitted is False
    assert result.digests_emitted is False
    assert result.event_hashes_emitted is False


def test_invalid_event_schema_is_rejected():
    event = _event()
    del event["event_hash"]
    with pytest.raises(ValueError, match="exactly the canonical event fields"):
        audit_evaluation_access_log_chain(
            [event],
            1,
            _digest("terminal"),
            {"review": ("artifact-a",)},
            {"review": (_digest("artifact"),)},
        )
