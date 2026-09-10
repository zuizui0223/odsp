import json
from pathlib import Path

from odsp.evaluation_content_provenance_benchmark import (
    run_evaluation_content_provenance_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]


def test_evaluation_content_provenance_receipt_replays():
    receipt = json.loads(
        (ROOT / "EVALUATION_CONTENT_PROVENANCE_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    result = run_evaluation_content_provenance_benchmark(seed=20260910)
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 15
    assert all(row["passed"] for row in result["checks"])

    clean = result["clean"]
    assert clean["separation_category"] == canonical["clean_category"]
    assert clean["stage_count"] == canonical["clean_stage_count"]
    assert clean["leaking_stage_count"] == canonical["clean_leaking_stage_count"]
    assert clean["final_evaluation_content_match_occurrence_count"] == canonical["clean_match_occurrence_count"]
    assert clean["unique_final_evaluation_content_match_count"] == canonical["clean_unique_match_count"]
    assert clean["duplicate_digest_count"] == canonical["clean_duplicate_digest_count"]

    single = result["single_exact_copy"]
    assert single["separation_category"] == canonical["single_copy_category"]
    assert single["leaking_stage_count"] == canonical["single_copy_leaking_stage_count"]
    assert single["final_evaluation_content_match_occurrence_count"] == canonical["single_copy_match_occurrence_count"]
    assert single["unique_final_evaluation_content_match_count"] == canonical["single_copy_unique_match_count"]
    assert single["maximum_stage_final_content_match_count"] == canonical["single_copy_maximum_stage_match_count"]

    repeated = result["repeated_exact_copy"]
    assert repeated["leaking_stage_count"] == canonical["repeated_copy_leaking_stage_count"]
    assert repeated["final_evaluation_content_match_occurrence_count"] == canonical["repeated_copy_match_occurrence_count"]
    assert repeated["unique_final_evaluation_content_match_count"] == canonical["repeated_copy_unique_match_count"]
    assert repeated["maximum_stage_final_content_match_count"] == canonical["repeated_copy_maximum_stage_match_count"]

    multi = result["multi_stage_exact_copy"]
    assert multi["leaking_stage_count"] == canonical["multi_stage_copy_leaking_stage_count"]
    assert multi["final_evaluation_content_match_occurrence_count"] == canonical["multi_stage_copy_match_occurrence_count"]
    assert multi["unique_final_evaluation_content_match_count"] == canonical["multi_stage_copy_unique_match_count"]
    assert multi["maximum_stage_final_content_match_count"] == canonical["multi_stage_copy_maximum_stage_match_count"]

    assert result["uppercase_exact_copy"]["separation_category"] == canonical["uppercase_hex_copy_category"]
    for key in (
        "invalid_digest_format_rejected",
        "wrong_digest_algorithm_rejected",
        "missing_digest_rejected",
        "empty_stage_rejected",
        "missing_expected_stage_rejected",
        "unexpected_extra_stage_rejected",
    ):
        assert result[key] is canonical[key] is True

    for key in (
        "digests_emitted",
        "automatic_artifact_hashing",
        "automatic_access_history_inference",
        "ledger_completeness_assumed",
        "semantic_equivalence_inferred",
        "aggregate_confidence_score_emitted",
    ):
        assert canonical[key] is False

    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_submission_preservation"].values())
    repair = receipt["pre_green_fixture_repair"]
    assert repair["contract_modified"] is False
    assert repair["decision_rule_modified"] is False
    assert repair["threshold_modified"] is False
