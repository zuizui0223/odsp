"""Known-truth benchmark for exact-content evaluation provenance."""
from __future__ import annotations

from hashlib import sha256

from .evaluation_content_provenance import audit_evaluation_content_provenance


def _digest(label: str) -> str:
    return "sha256:" + sha256(label.encode("utf-8")).hexdigest()


def _clean_ledger() -> dict[str, tuple[str, ...]]:
    duplicate = _digest("candidate-summary")
    return {
        "candidate_screening": (duplicate, duplicate, _digest("feature-diagnostics")),
        "model_review": (_digest("training-report"), _digest("calibration-report")),
        "threshold_review": (_digest("development-thresholds"), _digest("selection-notes")),
    }


def _raises(callable_obj, text: str) -> bool:
    try:
        callable_obj()
    except ValueError as exc:
        return text in str(exc)
    return False


def run_evaluation_content_provenance_benchmark(*, seed: int = 20260910) -> dict[str, object]:
    if seed != 20260910:
        raise ValueError("the frozen evaluation-content provenance benchmark uses seed 20260910")

    final_digest = _digest("final-evaluation-content")
    expected = ("candidate_screening", "model_review", "threshold_review")
    clean_ledger = _clean_ledger()
    clean = audit_evaluation_content_provenance(
        final_digest,
        clean_ledger,
        expected_stage_names=expected,
    )

    single_ledger = dict(clean_ledger)
    rows = list(single_ledger["candidate_screening"])
    rows[-1] = final_digest
    single_ledger["candidate_screening"] = tuple(rows)
    single = audit_evaluation_content_provenance(
        final_digest,
        single_ledger,
        expected_stage_names=expected,
    )

    repeated_ledger = dict(clean_ledger)
    repeated_ledger["candidate_screening"] = (
        _digest("candidate-summary"),
        final_digest,
        final_digest,
    )
    repeated = audit_evaluation_content_provenance(
        final_digest,
        repeated_ledger,
        expected_stage_names=expected,
    )

    multi_ledger = {
        "candidate_screening": (final_digest, final_digest, _digest("candidate-other")),
        "model_review": (_digest("model-other"), final_digest),
        "threshold_review": (final_digest, _digest("threshold-other")),
    }
    multi = audit_evaluation_content_provenance(
        final_digest,
        multi_ledger,
        expected_stage_names=expected,
    )

    uppercase = audit_evaluation_content_provenance(
        final_digest.upper(),
        {
            "candidate_screening": (final_digest.upper(), _digest("upper-other")),
            "model_review": (_digest("upper-model"),),
            "threshold_review": (_digest("upper-threshold"),),
        },
        expected_stage_names=expected,
    )

    reversed_clean = audit_evaluation_content_provenance(
        final_digest,
        dict(reversed(tuple(clean_ledger.items()))),
        expected_stage_names=tuple(reversed(expected)),
    )

    invalid_format_rejected = _raises(
        lambda: audit_evaluation_content_provenance(
            "sha256:not-a-digest", clean_ledger
        ),
        "sha256:<64 hexadecimal characters>",
    )
    wrong_algorithm_rejected = _raises(
        lambda: audit_evaluation_content_provenance(
            "md5:" + "a" * 32, clean_ledger
        ),
        "sha256:<64 hexadecimal characters>",
    )
    missing_digest_rejected = _raises(
        lambda: audit_evaluation_content_provenance(None, clean_ledger),
        "must not be missing",
    )
    empty_stage_rejected = _raises(
        lambda: audit_evaluation_content_provenance(
            final_digest, {"candidate_screening": ()}
        ),
        "must contain at least one digest",
    )
    missing_expected_stage_rejected = _raises(
        lambda: audit_evaluation_content_provenance(
            final_digest,
            {"candidate_screening": (_digest("a"),)},
            expected_stage_names=("candidate_screening", "model_review"),
        ),
        "missing declared stage",
    )
    unexpected_extra_stage_rejected = _raises(
        lambda: audit_evaluation_content_provenance(
            final_digest,
            {
                "candidate_screening": (_digest("a"),),
                "model_review": (_digest("b"),),
            },
            expected_stage_names=("candidate_screening",),
        ),
        "unexpected extra stage",
    )

    serialized = str(single.as_dict())
    digest_values = {final_digest}
    for values in single_ledger.values():
        digest_values.update(value.lower() for value in values)
    no_digest_values_emitted = all(value not in serialized for value in digest_values)

    checks = {
        "clean_three_stage_ledger_is_content_disjoint": clean.stage_count == 3 and clean.separation_category == "final_evaluation_content_not_accessed_in_declared_pre_final_stages" and not clean.final_evaluation_content_accessed and clean.leaking_stage_count == 0 and clean.final_evaluation_content_match_occurrence_count == 0,
        "duplicate_nonfinal_digest_is_legal_and_reported": clean.duplicate_digest_count == 1 and clean.stages[0].duplicate_digest_count == 1,
        "single_exact_copy_is_detected": single.separation_category == "final_evaluation_content_leakage" and single.leaking_stage_count == 1 and single.final_evaluation_content_match_occurrence_count == 1 and single.unique_final_evaluation_content_match_count == 1 and single.maximum_stage_final_content_match_count == 1,
        "repeated_exact_copy_counts_occurrences_without_extra_unique_content": repeated.leaking_stage_count == 1 and repeated.final_evaluation_content_match_occurrence_count == 2 and repeated.unique_final_evaluation_content_match_count == 1 and repeated.maximum_stage_final_content_match_count == 2,
        "multi_stage_exact_copy_is_detected_and_counted": multi.leaking_stage_count == 3 and multi.final_evaluation_content_match_occurrence_count == 4 and multi.unique_final_evaluation_content_match_count == 1 and multi.maximum_stage_final_content_match_count == 2,
        "hexadecimal_case_is_canonicalized": uppercase.separation_category == "final_evaluation_content_leakage" and uppercase.final_evaluation_content_match_occurrence_count == 1,
        "invalid_digest_format_is_rejected": invalid_format_rejected,
        "wrong_digest_algorithm_is_rejected": wrong_algorithm_rejected,
        "missing_digest_is_rejected": missing_digest_rejected,
        "empty_stage_is_rejected": empty_stage_rejected,
        "missing_expected_stage_is_rejected": missing_expected_stage_rejected,
        "unexpected_extra_stage_is_rejected": unexpected_extra_stage_rejected,
        "stage_mapping_order_is_invariant": clean.as_dict() == reversed_clean.as_dict(),
        "actual_digests_are_not_emitted_and_no_semantic_or_history_inference_occurs": no_digest_values_emitted and not single.digests_emitted and not single.automatic_artifact_hashing and not single.automatic_access_history_inference and not single.ledger_completeness_assumed and not single.semantic_equivalence_inferred,
        "aggregate_confidence_score_emitted": not clean.aggregate_confidence_score_emitted and not single.aggregate_confidence_score_emitted and not repeated.aggregate_confidence_score_emitted and not multi.aggregate_confidence_score_emitted and not uppercase.aggregate_confidence_score_emitted,
    }

    return {
        "seed": seed,
        "clean": clean.as_dict(),
        "single_exact_copy": single.as_dict(),
        "repeated_exact_copy": repeated.as_dict(),
        "multi_stage_exact_copy": multi.as_dict(),
        "uppercase_exact_copy": uppercase.as_dict(),
        "invalid_digest_format_rejected": invalid_format_rejected,
        "wrong_digest_algorithm_rejected": wrong_algorithm_rejected,
        "missing_digest_rejected": missing_digest_rejected,
        "empty_stage_rejected": empty_stage_rejected,
        "missing_expected_stage_rejected": missing_expected_stage_rejected,
        "unexpected_extra_stage_rejected": unexpected_extra_stage_rejected,
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
