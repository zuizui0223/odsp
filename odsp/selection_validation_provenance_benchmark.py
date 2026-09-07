"""Known-truth benchmark for selection/final-validation provenance."""
from __future__ import annotations

from .selection_validation_provenance import audit_selection_validation_provenance


def _clean_stages() -> dict[str, tuple[str, ...]]:
    return {
        "candidate_ranking": ("rank-a", "rank-b", "rank-c"),
        "early_stopping": ("stop-a", "stop-b"),
        "hyperparameter_tuning": ("tune-a", "tune-b", "tune-b", "tune-c"),
    }


def _multi_leak_stages(final_rows: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    return {
        "candidate_ranking": ("rank-a", final_rows[0], final_rows[1]),
        "early_stopping": ("stop-a", final_rows[4]),
        "hyperparameter_tuning": (final_rows[1], final_rows[2], final_rows[3]),
    }


def run_selection_validation_provenance_benchmark() -> dict[str, object]:
    final_rows = tuple(f"validation-{i:02d}" for i in range(8))
    expected = ("candidate_ranking", "early_stopping", "hyperparameter_tuning")

    clean = audit_selection_validation_provenance(
        final_rows,
        _clean_stages(),
        expected_stage_names=expected,
    )

    single_stages = _clean_stages()
    single_stages["candidate_ranking"] = ("rank-a", final_rows[2], "rank-c")
    single = audit_selection_validation_provenance(
        final_rows,
        single_stages,
        expected_stage_names=expected,
    )

    repeated_stages = _clean_stages()
    repeated_stages["candidate_ranking"] = (
        "rank-a",
        final_rows[2],
        final_rows[2],
        "rank-c",
    )
    repeated = audit_selection_validation_provenance(
        final_rows,
        repeated_stages,
        expected_stage_names=expected,
    )

    multi_stages = _multi_leak_stages(final_rows)
    multi = audit_selection_validation_provenance(
        final_rows,
        multi_stages,
        expected_stage_names=expected,
    )

    duplicate_final_rejected = False
    try:
        audit_selection_validation_provenance(
            final_rows[:-1] + (final_rows[0],),
            _clean_stages(),
        )
    except ValueError:
        duplicate_final_rejected = True

    empty_stage_rejected = False
    try:
        audit_selection_validation_provenance(
            final_rows,
            {**_clean_stages(), "threshold_choice": ()},
        )
    except ValueError:
        empty_stage_rejected = True

    missing_expected_rejected = False
    try:
        reduced = _clean_stages()
        reduced.pop("early_stopping")
        audit_selection_validation_provenance(
            final_rows,
            reduced,
            expected_stage_names=expected,
        )
    except ValueError:
        missing_expected_rejected = True

    extra_expected_rejected = False
    try:
        audit_selection_validation_provenance(
            final_rows,
            _clean_stages(),
            expected_stage_names=expected + ("threshold_choice",),
        )
    except ValueError:
        extra_expected_rejected = True

    extra_actual_rejected = False
    try:
        audit_selection_validation_provenance(
            final_rows,
            {**_clean_stages(), "threshold_choice": ("threshold-a",)},
            expected_stage_names=expected,
        )
    except ValueError:
        extra_actual_rejected = True

    ordered_a = audit_selection_validation_provenance(
        final_rows,
        {
            "hyperparameter_tuning": _clean_stages()["hyperparameter_tuning"],
            "candidate_ranking": _clean_stages()["candidate_ranking"],
            "early_stopping": _clean_stages()["early_stopping"],
        },
        expected_stage_names=expected,
    )
    ordered_b = audit_selection_validation_provenance(
        final_rows,
        _clean_stages(),
        expected_stage_names=tuple(reversed(expected)),
    )

    relabeled_final = tuple(f"case-{i:02d}" for i in range(8))
    relabeled = audit_selection_validation_provenance(
        relabeled_final,
        _multi_leak_stages(relabeled_final),
        expected_stage_names=expected,
    )

    emitted_keys = set(multi.as_dict())
    for row in multi.as_dict()["stages"]:
        emitted_keys.update(row)
    ids_not_emitted = not any(
        key in {"overlapping_row_ids", "overlapping_validation_row_ids", "selection_row_ids"}
        for key in emitted_keys
    )

    checks = {
        "fully_disjoint_selection_is_clean": clean.separation_category == "selection_validation_disjoint" and clean.selection_validation_separated and clean.overlapping_stage_count == 0,
        "duplicate_selection_rows_are_legal_and_reported": clean.duplicate_selection_row_count == 1 and clean.stages[2].duplicate_selection_row_count == 1,
        "single_stage_single_row_overlap_is_detected": single.separation_category == "selection_validation_leakage" and not single.selection_validation_separated and single.overlapping_stage_count == 1 and single.unique_overlapping_final_validation_row_count == 1 and single.maximum_stage_overlap_count == 1,
        "repeated_same_leaked_row_counts_once_globally": repeated.unique_overlapping_final_validation_row_count == 1 and repeated.maximum_stage_overlap_count == 1 and repeated.duplicate_selection_row_count == 2,
        "multi_stage_leakage_counts_are_correct": multi.overlapping_stage_count == 3 and multi.unique_overlapping_final_validation_row_count == 5 and multi.maximum_stage_overlap_count == 3,
        "duplicate_final_validation_ids_are_rejected": duplicate_final_rejected,
        "empty_selection_stage_is_rejected": empty_stage_rejected,
        "missing_expected_stage_is_rejected": missing_expected_rejected,
        "extra_expected_stage_is_rejected": extra_expected_rejected,
        "extra_actual_stage_is_rejected": extra_actual_rejected,
        "selection_stage_mapping_order_is_invariant": ordered_a.as_dict() == ordered_b.as_dict(),
        "consistent_row_id_relabeling_preserves_provenance_result": relabeled.as_dict() == multi.as_dict(),
        "actual_overlapping_row_ids_are_not_emitted": ids_not_emitted and not multi.overlapping_row_ids_emitted,
        "automatic_selection_history_inference_is_absent": not multi.automatic_selection_history_inference and not multi.automatic_candidate_selection,
        "aggregate_confidence_score_emitted": not clean.aggregate_confidence_score_emitted and not multi.aggregate_confidence_score_emitted,
    }

    return {
        "final_validation_row_count": len(final_rows),
        "selection_stage_count": len(expected),
        "clean": clean.as_dict(),
        "single_leak": single.as_dict(),
        "repeated_leak": repeated.as_dict(),
        "multi_stage_leak": multi.as_dict(),
        "duplicate_final_rejected": duplicate_final_rejected,
        "empty_stage_rejected": empty_stage_rejected,
        "missing_expected_rejected": missing_expected_rejected,
        "extra_expected_rejected": extra_expected_rejected,
        "extra_actual_rejected": extra_actual_rejected,
        "stage_order_invariant": ordered_a.as_dict() == ordered_b.as_dict(),
        "row_relabeling_invariant": relabeled.as_dict() == multi.as_dict(),
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
