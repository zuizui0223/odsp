"""Known-truth benchmark for evaluation-access hash-chain provenance."""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from hashlib import sha256

from .evaluation_access_log_chain import (
    GENESIS_EVENT_HASH,
    audit_evaluation_access_log_chain,
    compute_access_event_hash,
)


def _digest(label: str) -> str:
    return "sha256:" + sha256(label.encode("utf-8")).hexdigest()


def _build_chain(specs: tuple[tuple[str, str, str], ...]) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    previous = GENESIS_EVENT_HASH
    for index, (stage, artifact_id, digest) in enumerate(specs):
        event_hash = compute_access_event_hash(index, stage, artifact_id, digest, previous)
        events.append(
            {
                "sequence_index": index,
                "stage_name": stage,
                "artifact_id": artifact_id,
                "artifact_digest": digest,
                "previous_event_hash": previous,
                "event_hash": event_hash,
            }
        )
        previous = event_hash
    return events


def _ledgers(events: list[dict[str, object]]) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    ids: dict[str, list[str]] = defaultdict(list)
    digests: dict[str, list[str]] = defaultdict(list)
    for event in events:
        stage = str(event["stage_name"])
        ids[stage].append(str(event["artifact_id"]))
        digests[stage].append(str(event["artifact_digest"]))
    return (
        {key: tuple(value) for key, value in ids.items()},
        {key: tuple(value) for key, value in digests.items()},
    )


def _audit(
    events: list[dict[str, object]],
    ids: dict[str, tuple[str, ...]],
    digests: dict[str, tuple[str, ...]],
    *,
    count: int = 6,
    terminal: str | None = None,
):
    return audit_evaluation_access_log_chain(
        events,
        count,
        events[-1]["event_hash"] if terminal is None else terminal,
        ids,
        digests,
    )


def _raises(callable_obj, text: str) -> bool:
    try:
        callable_obj()
    except ValueError as exc:
        return text in str(exc)
    return False


def run_evaluation_access_log_chain_benchmark(*, seed: int = 20260910) -> dict[str, object]:
    if seed != 20260910:
        raise ValueError("the frozen evaluation-access log-chain benchmark uses seed 20260910")

    duplicate_digest = _digest("candidate-summary")
    specs = (
        ("candidate_screening", "artifact-a", duplicate_digest),
        ("candidate_screening", "artifact-a", duplicate_digest),
        ("model_review", "artifact-b", _digest("model-b")),
        ("model_review", "artifact-c", _digest("model-c")),
        ("threshold_review", "artifact-d", _digest("threshold-d")),
        ("threshold_review", "artifact-e", _digest("threshold-e")),
    )
    clean_events = _build_chain(specs)
    clean_ids, clean_digests = _ledgers(clean_events)
    terminal = str(clean_events[-1]["event_hash"])
    clean = _audit(clean_events, clean_ids, clean_digests, terminal=terminal)

    mutated_events = deepcopy(clean_events)
    mutated_events[2]["artifact_id"] = "artifact-b-mutated"
    mutated_ids, mutated_digests = _ledgers(mutated_events)
    payload_mutation = _audit(
        mutated_events, mutated_ids, mutated_digests, terminal=terminal
    )

    swapped_events = deepcopy(clean_events)
    swapped_events[1], swapped_events[2] = swapped_events[2], swapped_events[1]
    swapped_ids, swapped_digests = _ledgers(swapped_events)
    order_swap = _audit(swapped_events, swapped_ids, swapped_digests, terminal=terminal)

    dropped_middle_events = deepcopy(clean_events)
    del dropped_middle_events[2]
    dropped_middle_ids, dropped_middle_digests = _ledgers(dropped_middle_events)
    dropped_middle = _audit(
        dropped_middle_events,
        dropped_middle_ids,
        dropped_middle_digests,
        terminal=terminal,
    )

    dropped_tail_events = deepcopy(clean_events[:-1])
    dropped_tail_ids, dropped_tail_digests = _ledgers(dropped_tail_events)
    dropped_tail = _audit(
        dropped_tail_events,
        dropped_tail_ids,
        dropped_tail_digests,
        terminal=terminal,
    )

    inserted_events = deepcopy(clean_events)
    inserted_previous = str(inserted_events[1]["event_hash"])
    inserted_hash = compute_access_event_hash(
        2,
        "model_review",
        "artifact-inserted",
        _digest("inserted"),
        inserted_previous,
    )
    inserted_events.insert(
        2,
        {
            "sequence_index": 2,
            "stage_name": "model_review",
            "artifact_id": "artifact-inserted",
            "artifact_digest": _digest("inserted"),
            "previous_event_hash": inserted_previous,
            "event_hash": inserted_hash,
        },
    )
    inserted_ids, inserted_digests = _ledgers(inserted_events)
    inserted_without_rehash = _audit(
        inserted_events, inserted_ids, inserted_digests, terminal=terminal
    )

    wrong_count = _audit(
        clean_events, clean_ids, clean_digests, count=7, terminal=terminal
    )
    wrong_terminal = _audit(
        clean_events,
        clean_ids,
        clean_digests,
        terminal="sha256:" + "f" * 64,
    )

    id_substitution = deepcopy(clean_ids)
    rows = list(id_substitution["model_review"])
    rows[0] = "artifact-substituted"
    id_substitution["model_review"] = tuple(rows)
    id_ledger_mismatch = _audit(
        clean_events, id_substitution, clean_digests, terminal=terminal
    )

    digest_substitution = deepcopy(clean_digests)
    rows = list(digest_substitution["threshold_review"])
    rows[0] = _digest("substituted-digest")
    digest_substitution["threshold_review"] = tuple(rows)
    digest_ledger_mismatch = _audit(
        clean_events, clean_ids, digest_substitution, terminal=terminal
    )

    reversed_ids = dict(reversed(tuple(clean_ids.items())))
    reversed_digests = dict(reversed(tuple(clean_digests.items())))
    reordered_mapping = _audit(
        clean_events, reversed_ids, reversed_digests, terminal=terminal
    )

    uppercase_events = deepcopy(clean_events)
    for event in uppercase_events:
        event["artifact_digest"] = str(event["artifact_digest"]).upper()
        event["previous_event_hash"] = str(event["previous_event_hash"]).upper()
        event["event_hash"] = str(event["event_hash"]).upper()
    uppercase_ids, uppercase_digests = _ledgers(uppercase_events)
    uppercase = audit_evaluation_access_log_chain(
        uppercase_events,
        6,
        terminal.upper(),
        uppercase_ids,
        uppercase_digests,
    )

    invalid_metadata_rejected = _raises(
        lambda: audit_evaluation_access_log_chain(
            [
                {
                    "sequence_index": True,
                    "stage_name": "candidate_screening",
                    "artifact_id": "artifact-a",
                    "artifact_digest": duplicate_digest,
                    "previous_event_hash": GENESIS_EVENT_HASH,
                    "event_hash": clean_events[0]["event_hash"],
                }
            ],
            1,
            clean_events[0]["event_hash"],
            {"candidate_screening": ("artifact-a",)},
            {"candidate_screening": (duplicate_digest,)},
        ),
        "sequence_index",
    )

    serialized = str(clean.as_dict())
    protected_values = set()
    for event in clean_events:
        protected_values.add(str(event["artifact_id"]))
        protected_values.add(str(event["artifact_digest"]).lower())
        protected_values.add(str(event["previous_event_hash"]).lower())
        protected_values.add(str(event["event_hash"]).lower())
    no_values_emitted = all(value not in serialized for value in protected_values)

    checks = {
        "clean_six_event_chain_is_consistent": clean.event_count == 6 and clean.stage_count == 3 and clean.log_chain_consistent and clean.separation_category == "evaluation_access_log_chain_consistent" and clean.committed_event_count_match and clean.terminal_event_hash_match and clean.sequence_contiguous and clean.previous_hash_chain_match and clean.recomputed_event_hash_match and clean.stage_artifact_id_ledger_match and clean.stage_digest_ledger_match,
        "duplicate_access_is_legal_and_reported": clean.duplicate_artifact_id_access_count == 1 and clean.duplicate_digest_access_count == 1,
        "event_payload_mutation_is_detected": payload_mutation.separation_category == "evaluation_access_log_chain_mismatch" and not payload_mutation.recomputed_event_hash_match and payload_mutation.stage_artifact_id_ledger_match and payload_mutation.stage_digest_ledger_match,
        "event_order_swap_is_detected": order_swap.separation_category == "evaluation_access_log_chain_mismatch" and not order_swap.sequence_contiguous and not order_swap.previous_hash_chain_match,
        "dropped_middle_event_is_detected": dropped_middle.separation_category == "evaluation_access_log_chain_mismatch" and not dropped_middle.committed_event_count_match and not dropped_middle.sequence_contiguous and not dropped_middle.previous_hash_chain_match,
        "dropped_tail_is_detected_by_commitment": dropped_tail.separation_category == "evaluation_access_log_chain_mismatch" and not dropped_tail.committed_event_count_match and not dropped_tail.terminal_event_hash_match,
        "inserted_event_without_rehash_is_detected": inserted_without_rehash.separation_category == "evaluation_access_log_chain_mismatch" and not inserted_without_rehash.committed_event_count_match and (not inserted_without_rehash.sequence_contiguous or not inserted_without_rehash.previous_hash_chain_match),
        "wrong_committed_event_count_is_detected": wrong_count.separation_category == "evaluation_access_log_chain_mismatch" and not wrong_count.committed_event_count_match,
        "wrong_terminal_hash_is_detected": wrong_terminal.separation_category == "evaluation_access_log_chain_mismatch" and not wrong_terminal.terminal_event_hash_match,
        "stage_artifact_id_ledger_substitution_is_detected": id_ledger_mismatch.separation_category == "evaluation_access_log_chain_mismatch" and not id_ledger_mismatch.stage_artifact_id_ledger_match and id_ledger_mismatch.stage_digest_ledger_match and id_ledger_mismatch.mismatched_stage_count == 1,
        "stage_digest_ledger_substitution_is_detected": digest_ledger_mismatch.separation_category == "evaluation_access_log_chain_mismatch" and digest_ledger_mismatch.stage_artifact_id_ledger_match and not digest_ledger_mismatch.stage_digest_ledger_match and digest_ledger_mismatch.mismatched_stage_count == 1,
        "stage_mapping_order_is_invariant": reordered_mapping.as_dict() == clean.as_dict(),
        "sha256_hexadecimal_case_is_canonicalized": uppercase.as_dict() == clean.as_dict(),
        "invalid_event_metadata_is_rejected": invalid_metadata_rejected,
        "actual_ids_digests_and_event_hashes_are_not_emitted": no_values_emitted and not clean.artifact_ids_emitted and not clean.digests_emitted and not clean.event_hashes_emitted,
        "no_external_anchor_or_history_inference_is_claimed": not clean.automatic_external_anchor_verification and not clean.automatic_access_history_inference and not clean.real_world_log_completeness_assumed,
        "aggregate_confidence_score_emitted": not clean.aggregate_confidence_score_emitted and not payload_mutation.aggregate_confidence_score_emitted and not order_swap.aggregate_confidence_score_emitted and not dropped_middle.aggregate_confidence_score_emitted and not dropped_tail.aggregate_confidence_score_emitted and not inserted_without_rehash.aggregate_confidence_score_emitted,
    }

    return {
        "seed": seed,
        "clean": clean.as_dict(),
        "payload_mutation": payload_mutation.as_dict(),
        "order_swap": order_swap.as_dict(),
        "dropped_middle": dropped_middle.as_dict(),
        "dropped_tail": dropped_tail.as_dict(),
        "inserted_without_rehash": inserted_without_rehash.as_dict(),
        "wrong_count": wrong_count.as_dict(),
        "wrong_terminal": wrong_terminal.as_dict(),
        "id_ledger_mismatch": id_ledger_mismatch.as_dict(),
        "digest_ledger_mismatch": digest_ledger_mismatch.as_dict(),
        "reordered_mapping": reordered_mapping.as_dict(),
        "uppercase": uppercase.as_dict(),
        "invalid_event_metadata_rejected": invalid_metadata_rejected,
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
