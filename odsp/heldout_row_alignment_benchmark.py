"""Known-truth benchmark for held-out row alignment."""
from __future__ import annotations

import numpy as np

from .heldout_row_alignment import audit_heldout_row_alignment, reorder_validation_rows


def run_heldout_row_alignment_benchmark() -> dict[str, object]:
    base = tuple(f"row-{i:02d}" for i in range(8))
    source_order = (3, 0, 7, 1, 6, 2, 5, 4)
    permuted = tuple(base[i] for i in source_order)

    exact = audit_heldout_row_alignment(base, {"exact": base})
    reorderable = audit_heldout_row_alignment(base, {"permuted": permuted})
    permutation = reorderable.sources[0].permutation_to_base
    assert permutation is not None

    base_values = np.arange(8, dtype=float) + 0.25
    source_values = base_values[np.asarray(source_order)]
    restored_values = reorder_validation_rows(source_values, permutation)

    base_matrix = np.vstack([base_values, base_values + 10.0, base_values - 3.0])
    source_matrix = base_matrix[:, np.asarray(source_order)]
    restored_matrix = reorder_validation_rows(source_matrix, permutation, axis=1)

    missing_ids = base[:-1]
    missing = audit_heldout_row_alignment(base, {"missing": missing_ids})
    missing_extra_ids = base[:-1] + ("row-extra",)
    missing_extra = audit_heldout_row_alignment(base, {"changed": missing_extra_ids})
    duplicate_ids = base[:-1] + (base[0],)
    duplicate = audit_heldout_row_alignment(base, {"duplicate": duplicate_ids})

    duplicate_base_rejected = False
    try:
        audit_heldout_row_alignment(base[:-1] + (base[0],), {"source": base})
    except ValueError:
        duplicate_base_rejected = True

    multiple = audit_heldout_row_alignment(
        base,
        {"exact": base, "permuted": permuted, "changed": missing_extra_ids},
    )
    source_order_a = audit_heldout_row_alignment(
        base,
        {"zeta": permuted, "alpha": base},
    )
    source_order_b = audit_heldout_row_alignment(
        base,
        {"alpha": base, "zeta": permuted},
    )

    relabeled_base = tuple(f"case-{i:02d}" for i in range(8))
    relabeled_permuted = tuple(relabeled_base[i] for i in source_order)
    relabeled = audit_heldout_row_alignment(
        relabeled_base,
        {"permuted": relabeled_permuted},
    )

    checks = {
        "exact_order_is_exact_alignment": exact.alignment_category == "exact_alignment" and exact.alignment_passed,
        "permuted_same_set_is_reorderable_alignment": reorderable.alignment_category == "reorderable_alignment" and reorderable.alignment_passed,
        "permutation_restores_one_dimensional_rows": bool(np.array_equal(restored_values, base_values)),
        "permutation_restores_refit_matrix_columns": bool(np.array_equal(restored_matrix, base_matrix)),
        "missing_row_is_mismatch": missing.alignment_category == "row_mismatch" and missing.sources[0].missing_row_count == 1 and missing.sources[0].extra_row_count == 0,
        "missing_and_extra_rows_are_reported": missing_extra.alignment_category == "row_mismatch" and missing_extra.sources[0].missing_row_count == 1 and missing_extra.sources[0].extra_row_count == 1,
        "duplicate_source_id_is_mismatch": duplicate.alignment_category == "row_mismatch" and duplicate.sources[0].duplicate_row_id_count == 1,
        "duplicate_base_id_is_rejected": duplicate_base_rejected,
        "multiple_sources_fail_closed_on_one_mismatch": multiple.alignment_category == "row_mismatch" and multiple.mismatched_source_count == 1,
        "source_mapping_order_is_invariant": source_order_a.as_dict() == source_order_b.as_dict(),
        "consistent_id_relabeling_preserves_alignment_category": relabeled.alignment_category == reorderable.alignment_category and relabeled.sources[0].permutation_to_base == permutation,
        "row_values_do_not_affect_alignment": reorderable.row_contents_used_for_identity is False,
        "aggregate_confidence_score_emitted": all(not row.aggregate_confidence_score_emitted for row in (exact, reorderable, missing, missing_extra, duplicate, multiple, relabeled)),
    }

    return {
        "base_row_count": len(base),
        "exact": exact.as_dict(),
        "reorderable": reorderable.as_dict(),
        "permutation_to_base": list(permutation),
        "one_dimensional_max_restore_error": float(np.max(np.abs(restored_values - base_values))),
        "matrix_max_restore_error": float(np.max(np.abs(restored_matrix - base_matrix))),
        "missing": missing.as_dict(),
        "missing_extra": missing_extra.as_dict(),
        "duplicate": duplicate.as_dict(),
        "multiple_sources": multiple.as_dict(),
        "source_order_invariance": source_order_a.as_dict() == source_order_b.as_dict(),
        "duplicate_base_rejected": duplicate_base_rejected,
        "checks": [{"name": name, "passed": bool(value)} for name, value in checks.items()],
        "passed": bool(all(checks.values())),
    }
