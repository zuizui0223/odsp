import json
from pathlib import Path

from odsp.selection_validation_provenance_benchmark import (
    run_selection_validation_provenance_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]


def _stage(audit, name):
    return next(row for row in audit["stages"] if row["stage_name"] == name)


def test_selection_validation_provenance_receipt_replays():
    receipt = json.loads(
        (ROOT / "SELECTION_VALIDATION_PROVENANCE_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    result = run_selection_validation_provenance_benchmark()
    canonical = receipt["canonical_results"]

    assert result["passed"] is canonical["passed"] is True
    assert len(result["checks"]) == canonical["obligation_count"] == 15
    assert all(row["passed"] for row in result["checks"])
    assert result["final_validation_row_count"] == canonical["final_validation_row_count"] == 8
    assert result["selection_stage_count"] == canonical["selection_stage_count"] == 3

    for key in ("clean", "single_leak", "repeated_leak", "multi_stage_leak"):
        row = result[key]
        expected = canonical[key]
        assert row["separation_category"] == expected["separation_category"]
        assert row["overlapping_stage_count"] == expected["overlapping_stage_count"]
        assert row["unique_overlapping_final_validation_row_count"] == expected[
            "unique_overlapping_final_validation_row_count"
        ]
        assert row["maximum_stage_overlap_count"] == expected["maximum_stage_overlap_count"]
        assert row["duplicate_selection_row_count"] == expected["duplicate_selection_row_count"]

    clean = result["clean"]
    assert clean["selection_validation_separated"] is canonical["clean"][
        "selection_validation_separated"
    ] is True
    assert clean["stage_names"] == canonical["clean"]["stage_names"]

    single = result["single_leak"]
    assert single["selection_validation_separated"] is canonical["single_leak"][
        "selection_validation_separated"
    ] is False

    multi = result["multi_stage_leak"]
    expected = canonical["multi_stage_leak"]
    assert _stage(multi, "candidate_ranking")["overlapping_final_validation_row_count"] == expected[
        "candidate_ranking_overlap_count"
    ]
    assert _stage(multi, "early_stopping")["overlapping_final_validation_row_count"] == expected[
        "early_stopping_overlap_count"
    ]
    assert _stage(multi, "hyperparameter_tuning")["overlapping_final_validation_row_count"] == expected[
        "hyperparameter_tuning_overlap_count"
    ]

    for key in (
        "duplicate_final_rejected",
        "empty_stage_rejected",
        "missing_expected_rejected",
        "extra_expected_rejected",
        "extra_actual_rejected",
        "stage_order_invariant",
        "row_relabeling_invariant",
    ):
        assert result[key] is canonical[key] is True

    assert clean["overlapping_row_ids_emitted"] is canonical["overlapping_row_ids_emitted"] is False
    assert clean["automatic_selection_history_inference"] is canonical[
        "automatic_selection_history_inference"
    ] is False
    assert clean["automatic_candidate_selection"] is canonical["automatic_candidate_selection"] is False
    assert clean["aggregate_confidence_score_emitted"] is canonical[
        "aggregate_confidence_score_emitted"
    ] is False
    assert all(value is False for value in receipt["claim_boundary"].values())
    assert all(value is False for value in receipt["frozen_submission_preservation"].values())
