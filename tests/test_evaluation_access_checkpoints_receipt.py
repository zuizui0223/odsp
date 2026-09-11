import json
from pathlib import Path

from odsp.evaluation_access_checkpoints_benchmark import run_evaluation_access_checkpoints_benchmark


RECEIPT = Path(__file__).resolve().parents[1] / "EVALUATION_ACCESS_CHECKPOINT_VALIDATION_RECEIPT.json"


def test_evaluation_access_checkpoint_first_green_receipt_replays():
    receipt = json.loads(RECEIPT.read_text())
    canonical = receipt["canonical_results"]
    result = run_evaluation_access_checkpoints_benchmark(seed=20260911)

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 16
    assert all(row["passed"] for row in result["checks"])

    for case in (
        "clean",
        "middle_mismatch",
        "terminal_mismatch",
        "order_mismatch",
        "missing_terminal",
        "additional_checkpoint",
    ):
        observed = result[case]
        expected = canonical[case]
        assert observed["separation_category"] == expected["category"]
        for key, value in expected.items():
            if key != "category":
                assert observed[key] == value

    for key in (
        "duplicate_index_rejected",
        "out_of_range_rejected",
        "negative_index_rejected",
        "too_few_rejected",
        "invalid_event_hash_rejected",
        "invalid_checkpoint_hash_rejected",
    ):
        assert result[key] is canonical[key] is True

    clean = result["clean"]
    for key in (
        "checkpoint_indices_emitted",
        "checkpoint_hashes_emitted",
        "automatic_external_timestamp_verification",
        "automatic_witness_identity_verification",
        "checkpoint_preexistence_assumed",
        "real_world_log_completeness_assumed",
        "aggregate_confidence_score_emitted",
    ):
        assert clean[key] is canonical[key] is False

    for value in receipt["claim_boundary"].values():
        assert value is False
    for value in receipt["frozen_submission_preservation"].values():
        assert value is False
