"""Known-truth benchmark for evaluation-access provenance."""
from __future__ import annotations

from .evaluation_access_provenance import audit_evaluation_access_provenance


def _clean() -> dict[str, tuple[str, ...]]:
    return {
        "candidate_ranking": ("dev-rank", "cv-summary"),
        "early_stopping": ("train-curve", "train-curve"),
        "hyperparameter_tuning": ("cv-fold-a", "cv-fold-b", "cv-fold-c"),
    }


def run_evaluation_access_provenance_benchmark() -> dict[str, object]:
    final_id = "final-evaluation::sealed-v1"
    expected = ("candidate_ranking", "early_stopping", "hyperparameter_tuning")
    clean = audit_evaluation_access_provenance(final_id, _clean(), expected_stage_names=expected)

    single_map = _clean()
    single_map["candidate_ranking"] = ("dev-rank", final_id)
    single = audit_evaluation_access_provenance(final_id, single_map, expected_stage_names=expected)

    repeated_map = _clean()
    repeated_map["candidate_ranking"] = (final_id, final_id, "dev-rank")
    repeated = audit_evaluation_access_provenance(final_id, repeated_map, expected_stage_names=expected)

    multi_map = {
        "candidate_ranking": (final_id, "dev-rank"),
        "early_stopping": ("train-curve", final_id),
        "hyperparameter_tuning": (final_id, final_id, "cv-fold-a"),
    }
    multi = audit_evaluation_access_provenance(final_id, multi_map, expected_stage_names=expected)

    missing_final_rejected = False
    try:
        audit_evaluation_access_provenance(None, _clean())
    except ValueError:
        missing_final_rejected = True

    empty_stage_rejected = False
    try:
        audit_evaluation_access_provenance(final_id, {**_clean(), "threshold": ()})
    except ValueError:
        empty_stage_rejected = True

    missing_expected_rejected = False
    try:
        reduced = _clean(); reduced.pop("early_stopping")
        audit_evaluation_access_provenance(final_id, reduced, expected_stage_names=expected)
    except ValueError:
        missing_expected_rejected = True

    extra_expected_rejected = False
    try:
        audit_evaluation_access_provenance(final_id, _clean(), expected_stage_names=expected + ("threshold",))
    except ValueError:
        extra_expected_rejected = True

    extra_actual_rejected = False
    try:
        audit_evaluation_access_provenance(final_id, {**_clean(), "threshold": ("dev-threshold",)}, expected_stage_names=expected)
    except ValueError:
        extra_actual_rejected = True

    ordered_a = audit_evaluation_access_provenance(final_id, {
        "hyperparameter_tuning": _clean()["hyperparameter_tuning"],
        "candidate_ranking": _clean()["candidate_ranking"],
        "early_stopping": _clean()["early_stopping"],
    }, expected_stage_names=expected)
    ordered_b = audit_evaluation_access_provenance(final_id, _clean(), expected_stage_names=tuple(reversed(expected)))

    relabeled = audit_evaluation_access_provenance(
        "sealed-final-B",
        {
            "candidate_ranking": ("sealed-final-B", "dev-rank-B"),
            "early_stopping": ("curve-B", "sealed-final-B"),
            "hyperparameter_tuning": ("sealed-final-B", "sealed-final-B", "cv-B"),
        },
        expected_stage_names=expected,
    )

    serialized = multi.as_dict()
    emitted_keys = set(serialized)
    for row in serialized["stages"]:
        emitted_keys.update(row)
    ids_not_emitted = not any(key in {"accessed_artifact_ids", "artifact_ids", "final_evaluation_artifact_id"} for key in emitted_keys)

    checks = {
        "fully_disjoint_declared_access_is_clean": clean.separation_category == "final_evaluation_not_accessed_in_declared_pre_final_stages" and not clean.final_evaluation_accessed,
        "duplicate_nonfinal_accesses_are_legal_and_reported": clean.duplicate_access_count == 1,
        "single_stage_final_artifact_access_is_detected": single.separation_category == "final_evaluation_access_leakage" and single.leaking_stage_count == 1 and single.final_evaluation_access_occurrence_count == 1,
        "repeated_final_artifact_access_counts_once_globally": repeated.final_evaluation_accessed and repeated.leaking_stage_count == 1 and repeated.final_evaluation_access_occurrence_count == 2 and repeated.maximum_stage_final_access_count == 2,
        "multi_stage_final_artifact_access_counts_are_correct": multi.leaking_stage_count == 3 and multi.final_evaluation_access_occurrence_count == 4 and multi.maximum_stage_final_access_count == 2,
        "missing_final_artifact_id_is_rejected": missing_final_rejected,
        "empty_access_stage_is_rejected": empty_stage_rejected,
        "missing_expected_stage_is_rejected": missing_expected_rejected,
        "extra_expected_stage_is_rejected": extra_expected_rejected,
        "extra_actual_stage_is_rejected": extra_actual_rejected,
        "stage_mapping_order_is_invariant": ordered_a.as_dict() == ordered_b.as_dict(),
        "consistent_artifact_id_relabeling_preserves_provenance_result": relabeled.leaking_stage_count == multi.leaking_stage_count and relabeled.final_evaluation_access_occurrence_count == multi.final_evaluation_access_occurrence_count and relabeled.separation_category == multi.separation_category,
        "actual_artifact_ids_are_not_emitted": ids_not_emitted and not multi.accessed_artifact_ids_emitted,
        "automatic_access_history_inference_is_absent": not multi.automatic_access_history_inference and not multi.ledger_completeness_assumed and not multi.automatic_candidate_selection,
        "aggregate_confidence_score_emitted": not clean.aggregate_confidence_score_emitted and not multi.aggregate_confidence_score_emitted,
    }
    return {
        "pre_final_stage_count": len(expected),
        "clean": clean.as_dict(),
        "single_leak": single.as_dict(),
        "repeated_leak": repeated.as_dict(),
        "multi_stage_leak": multi.as_dict(),
        "missing_final_rejected": missing_final_rejected,
        "empty_stage_rejected": empty_stage_rejected,
        "missing_expected_rejected": missing_expected_rejected,
        "extra_expected_rejected": extra_expected_rejected,
        "extra_actual_rejected": extra_actual_rejected,
        "stage_order_invariant": ordered_a.as_dict() == ordered_b.as_dict(),
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
