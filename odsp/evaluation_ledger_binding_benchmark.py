"""Known-truth benchmark for evaluation artifact-ID/SHA-256 ledger binding."""
from __future__ import annotations

from hashlib import sha256

from .evaluation_ledger_binding import audit_evaluation_ledger_binding


def _digest(label: str) -> str:
    return "sha256:" + sha256(label.encode("utf-8")).hexdigest()


def _fixture():
    final_id = "final-evaluation"
    final_digest = _digest("final-evaluation-content")
    manifest = {
        final_id: final_digest,
        "final-copy-alias": final_digest,
        "screen-a": _digest("screen-a"),
        "screen-b": _digest("screen-b"),
        "model-a": _digest("model-a"),
        "model-b": _digest("model-b"),
        "threshold-a": _digest("threshold-a"),
        "threshold-b": _digest("threshold-b"),
    }
    id_ledger = {
        "candidate_screening": ("screen-a", "screen-a", "screen-b"),
        "model_review": ("model-a", "model-b"),
        "threshold_review": ("threshold-a", "threshold-b"),
    }
    digest_ledger = {
        name: tuple(manifest[artifact_id] for artifact_id in ids)
        for name, ids in id_ledger.items()
    }
    expected = ("candidate_screening", "model_review", "threshold_review")
    return final_id, final_digest, manifest, id_ledger, digest_ledger, expected


def _raises(callable_obj, text: str) -> bool:
    try:
        callable_obj()
    except ValueError as exc:
        return text in str(exc)
    return False


def run_evaluation_ledger_binding_benchmark(*, seed: int = 20260910) -> dict[str, object]:
    if seed != 20260910:
        raise ValueError("the frozen evaluation-ledger binding benchmark uses seed 20260910")

    final_id, final_digest, manifest, id_ledger, digest_ledger, expected = _fixture()
    clean = audit_evaluation_ledger_binding(
        final_id,
        final_digest,
        manifest,
        id_ledger,
        digest_ledger,
        expected_stage_names=expected,
    )

    wrong_final = audit_evaluation_ledger_binding(
        final_id,
        _digest("different-final-content"),
        manifest,
        id_ledger,
        digest_ledger,
        expected_stage_names=expected,
    )

    substituted_digests = dict(digest_ledger)
    screening = list(substituted_digests["candidate_screening"])
    screening[-1] = manifest["model-a"]
    substituted_digests["candidate_screening"] = tuple(screening)
    stage_mismatch = audit_evaluation_ledger_binding(
        final_id,
        final_digest,
        manifest,
        id_ledger,
        substituted_digests,
        expected_stage_names=expected,
    )

    reordered_digests = {
        name: tuple(reversed(values)) for name, values in digest_ledger.items()
    }
    digest_order = audit_evaluation_ledger_binding(
        final_id,
        final_digest,
        manifest,
        id_ledger,
        reordered_digests,
        expected_stage_names=expected,
    )

    reversed_mapping = audit_evaluation_ledger_binding(
        final_id,
        final_digest,
        manifest,
        dict(reversed(tuple(id_ledger.items()))),
        dict(reversed(tuple(digest_ledger.items()))),
        expected_stage_names=tuple(reversed(expected)),
    )

    relabel = {artifact_id: f"relabeled::{idx:02d}" for idx, artifact_id in enumerate(manifest)}
    relabeled_manifest = {
        relabel[artifact_id]: digest for artifact_id, digest in manifest.items()
    }
    relabeled_ids = {
        name: tuple(relabel[artifact_id] for artifact_id in ids)
        for name, ids in id_ledger.items()
    }
    relabeled = audit_evaluation_ledger_binding(
        relabel[final_id],
        final_digest,
        relabeled_manifest,
        relabeled_ids,
        digest_ledger,
        expected_stage_names=expected,
    )

    uppercase_manifest = {
        artifact_id: digest.upper() for artifact_id, digest in manifest.items()
    }
    uppercase_digests = {
        name: tuple(digest.upper() for digest in digests)
        for name, digests in digest_ledger.items()
    }
    uppercase = audit_evaluation_ledger_binding(
        final_id,
        final_digest.upper(),
        uppercase_manifest,
        id_ledger,
        uppercase_digests,
        expected_stage_names=expected,
    )

    unknown_id_rejected = _raises(
        lambda: audit_evaluation_ledger_binding(
            final_id,
            final_digest,
            manifest,
            {**id_ledger, "candidate_screening": ("screen-a", "unknown-artifact")},
            {**digest_ledger, "candidate_screening": (manifest["screen-a"], manifest["screen-b"])},
        ),
        "missing from artifact_digest_by_id",
    )
    missing_final_rejected = _raises(
        lambda: audit_evaluation_ledger_binding(
            final_id,
            final_digest,
            {key: value for key, value in manifest.items() if key != final_id},
            id_ledger,
            digest_ledger,
        ),
        "final_evaluation_artifact_id is missing",
    )
    stage_coverage_rejected = _raises(
        lambda: audit_evaluation_ledger_binding(
            final_id,
            final_digest,
            manifest,
            id_ledger,
            {key: value for key, value in digest_ledger.items() if key != "model_review"},
        ),
        "stage coverage must exactly match",
    )
    empty_stage_rejected = _raises(
        lambda: audit_evaluation_ledger_binding(
            final_id,
            final_digest,
            manifest,
            {**id_ledger, "candidate_screening": ()},
            digest_ledger,
        ),
        "must contain at least one artifact ID",
    )
    invalid_digest_rejected = _raises(
        lambda: audit_evaluation_ledger_binding(
            final_id,
            "sha256:not-a-digest",
            manifest,
            id_ledger,
            digest_ledger,
        ),
        "sha256:<64 hexadecimal characters>",
    )

    serialized = str(clean.as_dict()) + str(stage_mismatch.as_dict())
    hidden_values = set(manifest)
    hidden_values.update(manifest.values())
    no_values_emitted = all(str(value) not in serialized for value in hidden_values)

    checks = {
        "clean_three_stage_ledgers_are_consistently_bound": clean.ledger_binding_consistent and clean.separation_category == "evaluation_ledgers_consistently_bound" and clean.stage_count == 3 and clean.mismatched_stage_count == 0 and clean.binding_discrepancy_occurrence_count == 0,
        "duplicate_accesses_are_legal_and_reported": clean.duplicate_artifact_id_access_count == 1 and clean.duplicate_digest_access_count == 1,
        "final_content_alias_id_is_reported_without_forcing_mismatch": clean.final_content_alias_id_count == 1 and clean.ledger_binding_consistent,
        "wrong_declared_final_digest_is_detected": not wrong_final.final_evaluation_binding_match and not wrong_final.ledger_binding_consistent and wrong_final.separation_category == "evaluation_ledger_binding_mismatch" and wrong_final.mismatched_stage_count == 0,
        "one_stage_digest_substitution_is_detected": stage_mismatch.final_evaluation_binding_match and not stage_mismatch.ledger_binding_consistent and stage_mismatch.mismatched_stage_count == 1 and stage_mismatch.binding_discrepancy_occurrence_count == 1 and stage_mismatch.stages[0].status == "stage_binding_mismatch",
        "digest_order_within_stage_is_invariant": digest_order.as_dict() == clean.as_dict(),
        "stage_mapping_order_is_invariant": reversed_mapping.as_dict() == clean.as_dict(),
        "artifact_id_relabeling_is_invariant": relabeled.as_dict() == clean.as_dict(),
        "sha256_hexadecimal_case_is_canonicalized": uppercase.as_dict() == clean.as_dict(),
        "unknown_accessed_artifact_id_is_rejected": unknown_id_rejected,
        "missing_final_artifact_in_manifest_is_rejected": missing_final_rejected,
        "id_digest_stage_coverage_mismatch_is_rejected": stage_coverage_rejected,
        "empty_access_stage_is_rejected": empty_stage_rejected,
        "invalid_digest_format_is_rejected": invalid_digest_rejected,
        "actual_ids_and_digests_are_not_emitted_and_no_history_or_semantic_inference_occurs": no_values_emitted and not clean.artifact_ids_emitted and not clean.digests_emitted and not clean.automatic_artifact_hashing and not clean.automatic_access_history_inference and not clean.manifest_completeness_assumed and not clean.semantic_equivalence_inferred,
        "aggregate_confidence_score_emitted": not clean.aggregate_confidence_score_emitted and not wrong_final.aggregate_confidence_score_emitted and not stage_mismatch.aggregate_confidence_score_emitted,
    }

    return {
        "seed": seed,
        "clean": clean.as_dict(),
        "wrong_declared_final_digest": wrong_final.as_dict(),
        "stage_digest_substitution": stage_mismatch.as_dict(),
        "digest_order_invariant": digest_order.as_dict(),
        "stage_mapping_order_invariant": reversed_mapping.as_dict(),
        "artifact_id_relabeling_invariant": relabeled.as_dict(),
        "uppercase_digest_invariant": uppercase.as_dict(),
        "unknown_accessed_artifact_id_rejected": unknown_id_rejected,
        "missing_final_artifact_in_manifest_rejected": missing_final_rejected,
        "id_digest_stage_coverage_mismatch_rejected": stage_coverage_rejected,
        "empty_access_stage_rejected": empty_stage_rejected,
        "invalid_digest_format_rejected": invalid_digest_rejected,
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
