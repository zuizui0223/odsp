import json
from pathlib import Path

from odsp.evaluation_access_log_chain_benchmark import run_evaluation_access_log_chain_benchmark


ROOT = Path(__file__).resolve().parents[1]


def test_evaluation_access_log_chain_receipt_replays():
    receipt = json.loads(
        (ROOT / "EVALUATION_ACCESS_LOG_CHAIN_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    result = run_evaluation_access_log_chain_benchmark(seed=20260910)
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 17
    assert all(row["passed"] for row in result["checks"])

    clean = result["clean"]
    assert clean["separation_category"] == canonical["clean_category"]
    assert clean["event_count"] == canonical["clean_event_count"] == 6
    assert clean["stage_count"] == canonical["clean_stage_count"] == 3
    assert clean["duplicate_artifact_id_access_count"] == canonical["clean_duplicate_artifact_id_access_count"] == 1
    assert clean["duplicate_digest_access_count"] == canonical["clean_duplicate_digest_access_count"] == 1
    for field in (
        "committed_event_count_match",
        "terminal_event_hash_match",
        "sequence_contiguous",
        "previous_hash_chain_match",
        "recomputed_event_hash_match",
        "stage_artifact_id_ledger_match",
        "stage_digest_ledger_match",
    ):
        assert clean[field] is canonical[f"clean_{field}"] is True

    payload = result["payload_mutation"]
    assert payload["recomputed_event_hash_match"] is canonical["payload_mutation_recomputed_event_hash_match"] is False

    order = result["order_swap"]
    assert order["sequence_contiguous"] is canonical["order_swap_sequence_contiguous"] is False
    assert order["previous_hash_chain_match"] is canonical["order_swap_previous_hash_chain_match"] is False

    dropped_middle = result["dropped_middle"]
    assert dropped_middle["committed_event_count_match"] is canonical["dropped_middle_committed_event_count_match"] is False
    assert dropped_middle["sequence_contiguous"] is canonical["dropped_middle_sequence_contiguous"] is False
    assert dropped_middle["previous_hash_chain_match"] is canonical["dropped_middle_previous_hash_chain_match"] is False

    dropped_tail = result["dropped_tail"]
    assert dropped_tail["committed_event_count_match"] is canonical["dropped_tail_committed_event_count_match"] is False
    assert dropped_tail["terminal_event_hash_match"] is canonical["dropped_tail_terminal_event_hash_match"] is False

    inserted = result["inserted_without_rehash"]
    assert inserted["committed_event_count_match"] is canonical["inserted_without_rehash_committed_event_count_match"] is False
    assert inserted["sequence_contiguous"] is canonical["inserted_without_rehash_sequence_contiguous"] is False
    assert inserted["previous_hash_chain_match"] is canonical["inserted_without_rehash_previous_hash_chain_match"] is False

    assert result["wrong_count"]["committed_event_count_match"] is canonical["wrong_count_committed_event_count_match"] is False
    assert result["wrong_terminal"]["terminal_event_hash_match"] is canonical["wrong_terminal_terminal_event_hash_match"] is False

    id_mismatch = result["id_ledger_mismatch"]
    assert id_mismatch["stage_artifact_id_ledger_match"] is canonical["id_ledger_mismatch_stage_artifact_id_ledger_match"] is False
    assert id_mismatch["stage_digest_ledger_match"] is canonical["id_ledger_mismatch_stage_digest_ledger_match"] is True
    assert id_mismatch["mismatched_stage_count"] == canonical["id_ledger_mismatch_stage_count"] == 1

    digest_mismatch = result["digest_ledger_mismatch"]
    assert digest_mismatch["stage_artifact_id_ledger_match"] is canonical["digest_ledger_mismatch_stage_artifact_id_ledger_match"] is True
    assert digest_mismatch["stage_digest_ledger_match"] is canonical["digest_ledger_mismatch_stage_digest_ledger_match"] is False
    assert digest_mismatch["mismatched_stage_count"] == canonical["digest_ledger_mismatch_stage_count"] == 1

    assert result["uppercase"] == result["clean"]
    assert canonical["uppercase_case_matches_clean"] is True
    assert result["invalid_event_metadata_rejected"] is canonical["invalid_event_metadata_rejected"] is True

    for field in (
        "artifact_ids_emitted",
        "digests_emitted",
        "event_hashes_emitted",
        "automatic_external_anchor_verification",
        "automatic_access_history_inference",
        "real_world_log_completeness_assumed",
        "aggregate_confidence_score_emitted",
    ):
        assert clean[field] is canonical[field] is False

    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_submission_preservation"].values())
