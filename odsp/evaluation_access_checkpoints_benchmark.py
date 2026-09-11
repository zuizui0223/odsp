"""Known-truth benchmark for evaluation-access checkpoint provenance."""
from __future__ import annotations

from hashlib import sha256

from .evaluation_access_checkpoints import audit_evaluation_access_checkpoints


def _digest(label: str) -> str:
    return "sha256:" + sha256(label.encode("utf-8")).hexdigest()


def _raises(callable_obj, text: str) -> bool:
    try:
        callable_obj()
    except ValueError as exc:
        return text in str(exc)
    return False


def run_evaluation_access_checkpoints_benchmark(*, seed: int = 20260911) -> dict[str, object]:
    if seed != 20260911:
        raise ValueError("the frozen evaluation-access checkpoint benchmark uses seed 20260911")

    event_hashes = tuple(_digest(f"event-{index}") for index in range(6))
    clean_checkpoints = (
        {"event_index": 1, "event_hash": event_hashes[1]},
        {"event_index": 3, "event_hash": event_hashes[3]},
        {"event_index": 5, "event_hash": event_hashes[5]},
    )
    clean = audit_evaluation_access_checkpoints(event_hashes, clean_checkpoints)

    middle_rows = list(clean_checkpoints)
    middle_rows[1] = {"event_index": 3, "event_hash": _digest("wrong-middle")}
    middle_mismatch = audit_evaluation_access_checkpoints(event_hashes, middle_rows)

    terminal_rows = list(clean_checkpoints)
    terminal_rows[-1] = {"event_index": 5, "event_hash": _digest("wrong-terminal")}
    terminal_mismatch = audit_evaluation_access_checkpoints(event_hashes, terminal_rows)

    order_rows = (clean_checkpoints[1], clean_checkpoints[0], clean_checkpoints[2])
    order_mismatch = audit_evaluation_access_checkpoints(event_hashes, order_rows)

    missing_terminal = audit_evaluation_access_checkpoints(
        event_hashes, clean_checkpoints[:2]
    )

    duplicate_index_rejected = _raises(
        lambda: audit_evaluation_access_checkpoints(
            event_hashes,
            (
                {"event_index": 1, "event_hash": event_hashes[1]},
                {"event_index": 1, "event_hash": event_hashes[1]},
            ),
        ),
        "must be unique",
    )
    out_of_range_rejected = _raises(
        lambda: audit_evaluation_access_checkpoints(
            event_hashes,
            (
                {"event_index": 1, "event_hash": event_hashes[1]},
                {"event_index": 6, "event_hash": _digest("outside")},
            ),
        ),
        "outside the supplied event hash range",
    )
    negative_index_rejected = _raises(
        lambda: audit_evaluation_access_checkpoints(
            event_hashes,
            (
                {"event_index": -1, "event_hash": event_hashes[0]},
                {"event_index": 5, "event_hash": event_hashes[5]},
            ),
        ),
        "zero-based non-negative integer",
    )
    too_few_rejected = _raises(
        lambda: audit_evaluation_access_checkpoints(
            event_hashes,
            ({"event_index": 5, "event_hash": event_hashes[5]},),
        ),
        "at least two",
    )
    invalid_event_hash_rejected = _raises(
        lambda: audit_evaluation_access_checkpoints(
            ("sha256:not-a-digest", event_hashes[1]),
            (
                {"event_index": 0, "event_hash": event_hashes[0]},
                {"event_index": 1, "event_hash": event_hashes[1]},
            ),
        ),
        "sha256:<64 hexadecimal characters>",
    )
    invalid_checkpoint_hash_rejected = _raises(
        lambda: audit_evaluation_access_checkpoints(
            event_hashes,
            (
                {"event_index": 1, "event_hash": "sha256:not-a-digest"},
                {"event_index": 5, "event_hash": event_hashes[5]},
            ),
        ),
        "sha256:<64 hexadecimal characters>",
    )

    uppercase = audit_evaluation_access_checkpoints(
        tuple(value.upper() for value in event_hashes),
        tuple(
            {
                "event_index": row["event_index"],
                "event_hash": str(row["event_hash"]).upper(),
            }
            for row in clean_checkpoints
        ),
    )

    additional = audit_evaluation_access_checkpoints(
        event_hashes,
        (
            {"event_index": 1, "event_hash": event_hashes[1]},
            {"event_index": 2, "event_hash": event_hashes[2]},
            {"event_index": 3, "event_hash": event_hashes[3]},
            {"event_index": 5, "event_hash": event_hashes[5]},
        ),
    )

    serialized = str(clean.as_dict())
    no_hash_values_emitted = all(value not in serialized for value in event_hashes)

    checks = {
        "clean_three_checkpoint_set_is_consistent": clean.event_count == 6 and clean.checkpoint_count == 3 and clean.matched_checkpoint_count == 3 and clean.mismatched_checkpoint_count == 0 and clean.checkpoint_order_strictly_increasing and clean.terminal_checkpoint_present and clean.checkpoints_consistent and clean.separation_category == "evaluation_access_checkpoints_consistent",
        "middle_checkpoint_hash_substitution_is_detected": middle_mismatch.separation_category == "evaluation_access_checkpoint_mismatch" and middle_mismatch.matched_checkpoint_count == 2 and middle_mismatch.mismatched_checkpoint_count == 1 and middle_mismatch.terminal_checkpoint_present,
        "terminal_checkpoint_hash_substitution_is_detected": terminal_mismatch.separation_category == "evaluation_access_checkpoint_mismatch" and terminal_mismatch.mismatched_checkpoint_count == 1 and terminal_mismatch.terminal_checkpoint_present,
        "checkpoint_order_swap_is_detected": order_mismatch.separation_category == "evaluation_access_checkpoint_mismatch" and order_mismatch.mismatched_checkpoint_count == 0 and not order_mismatch.checkpoint_order_strictly_increasing and order_mismatch.terminal_checkpoint_present,
        "missing_terminal_checkpoint_is_detected": missing_terminal.separation_category == "evaluation_access_checkpoint_mismatch" and missing_terminal.mismatched_checkpoint_count == 0 and not missing_terminal.terminal_checkpoint_present,
        "duplicate_checkpoint_index_is_rejected": duplicate_index_rejected,
        "out_of_range_checkpoint_index_is_rejected": out_of_range_rejected,
        "negative_checkpoint_index_is_rejected": negative_index_rejected,
        "too_few_checkpoints_are_rejected": too_few_rejected,
        "invalid_event_hash_is_rejected": invalid_event_hash_rejected,
        "invalid_checkpoint_hash_is_rejected": invalid_checkpoint_hash_rejected,
        "sha256_hexadecimal_case_is_canonicalized": uppercase.as_dict() == clean.as_dict(),
        "consistent_additional_intermediate_checkpoint_is_allowed": additional.checkpoints_consistent and additional.checkpoint_count == 4 and additional.matched_checkpoint_count == 4,
        "actual_checkpoint_indices_and_hashes_are_not_emitted": no_hash_values_emitted and not clean.checkpoint_indices_emitted and not clean.checkpoint_hashes_emitted,
        "no_external_timestamp_or_witness_or_preexistence_is_claimed": not clean.automatic_external_timestamp_verification and not clean.automatic_witness_identity_verification and not clean.checkpoint_preexistence_assumed and not clean.real_world_log_completeness_assumed,
        "aggregate_confidence_score_emitted": not clean.aggregate_confidence_score_emitted and not middle_mismatch.aggregate_confidence_score_emitted and not terminal_mismatch.aggregate_confidence_score_emitted and not order_mismatch.aggregate_confidence_score_emitted and not missing_terminal.aggregate_confidence_score_emitted and not additional.aggregate_confidence_score_emitted,
    }

    return {
        "seed": seed,
        "clean": clean.as_dict(),
        "middle_mismatch": middle_mismatch.as_dict(),
        "terminal_mismatch": terminal_mismatch.as_dict(),
        "order_mismatch": order_mismatch.as_dict(),
        "missing_terminal": missing_terminal.as_dict(),
        "additional_checkpoint": additional.as_dict(),
        "duplicate_index_rejected": duplicate_index_rejected,
        "out_of_range_rejected": out_of_range_rejected,
        "negative_index_rejected": negative_index_rejected,
        "too_few_rejected": too_few_rejected,
        "invalid_event_hash_rejected": invalid_event_hash_rejected,
        "invalid_checkpoint_hash_rejected": invalid_checkpoint_hash_rejected,
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
