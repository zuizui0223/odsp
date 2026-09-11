import pytest

from odsp.evaluation_access_checkpoints import audit_evaluation_access_checkpoints


EVENTS = tuple(f"sha256:{index:064x}" for index in range(1, 7))


def test_clean_checkpoint_set_is_consistent():
    result = audit_evaluation_access_checkpoints(
        EVENTS,
        (
            {"event_index": 1, "event_hash": EVENTS[1]},
            {"event_index": 3, "event_hash": EVENTS[3]},
            {"event_index": 5, "event_hash": EVENTS[5]},
        ),
    )
    assert result.checkpoints_consistent is True
    assert result.separation_category == "evaluation_access_checkpoints_consistent"
    assert result.checkpoint_count == 3
    assert result.matched_checkpoint_count == 3
    assert result.mismatched_checkpoint_count == 0
    assert result.terminal_checkpoint_present is True


def test_hash_mismatch_is_provenance_mismatch_not_input_error():
    result = audit_evaluation_access_checkpoints(
        EVENTS,
        (
            {"event_index": 1, "event_hash": EVENTS[1]},
            {"event_index": 3, "event_hash": "sha256:" + "f" * 64},
            {"event_index": 5, "event_hash": EVENTS[5]},
        ),
    )
    assert result.checkpoints_consistent is False
    assert result.separation_category == "evaluation_access_checkpoint_mismatch"
    assert result.mismatched_checkpoint_count == 1


def test_out_of_order_checkpoints_fail_closed():
    result = audit_evaluation_access_checkpoints(
        EVENTS,
        (
            {"event_index": 3, "event_hash": EVENTS[3]},
            {"event_index": 1, "event_hash": EVENTS[1]},
            {"event_index": 5, "event_hash": EVENTS[5]},
        ),
    )
    assert result.mismatched_checkpoint_count == 0
    assert result.checkpoint_order_strictly_increasing is False
    assert result.checkpoints_consistent is False


def test_duplicate_checkpoint_index_is_rejected():
    with pytest.raises(ValueError, match="must be unique"):
        audit_evaluation_access_checkpoints(
            EVENTS,
            (
                {"event_index": 1, "event_hash": EVENTS[1]},
                {"event_index": 1, "event_hash": EVENTS[1]},
            ),
        )
