import numpy as np
import pytest

from odsp.heldout_row_alignment import (
    audit_heldout_row_alignment,
    reorder_validation_rows,
)


def test_exact_and_reorderable_alignment():
    base = ("a", "b", "c", "d")
    exact = audit_heldout_row_alignment(base, {"base-copy": base})
    assert exact.alignment_category == "exact_alignment"
    assert exact.alignment_passed is True
    assert exact.sources[0].permutation_to_base == (0, 1, 2, 3)

    source = ("c", "a", "d", "b")
    audit = audit_heldout_row_alignment(base, {"source": source})
    assert audit.alignment_category == "reorderable_alignment"
    assert audit.alignment_passed is True
    assert audit.sources[0].permutation_to_base == (1, 3, 0, 2)
    values = np.asarray([30, 10, 40, 20])
    assert np.array_equal(reorder_validation_rows(values, (1, 3, 0, 2)), [10, 20, 30, 40])


def test_mismatch_reports_missing_extra_and_duplicates():
    base = ("a", "b", "c", "d")
    audit = audit_heldout_row_alignment(base, {"changed": ("a", "b", "c", "x")})
    row = audit.sources[0]
    assert audit.alignment_category == "row_mismatch"
    assert audit.alignment_passed is False
    assert row.same_row_set is False
    assert row.missing_row_count == 1
    assert row.extra_row_count == 1
    assert row.permutation_to_base is None

    duplicate = audit_heldout_row_alignment(base, {"duplicate": ("a", "b", "c", "a")})
    assert duplicate.sources[0].duplicate_row_id_count == 1
    assert duplicate.alignment_category == "row_mismatch"


def test_invalid_canonical_ids_are_rejected():
    with pytest.raises(ValueError, match="unique"):
        audit_heldout_row_alignment(("a", "b", "a"), {"source": ("a", "b", "c")})
    with pytest.raises(ValueError, match="missing"):
        audit_heldout_row_alignment(("a", None), {"source": ("a", "b")})
    with pytest.raises(ValueError, match="missing"):
        audit_heldout_row_alignment(("a", np.nan), {"source": ("a", "b")})
    with pytest.raises(ValueError, match="hashable"):
        audit_heldout_row_alignment(("a", ["b"]), {"source": ("a", "b")})


def test_source_names_are_canonical_and_results_are_sorted():
    base = ("a", "b")
    audit = audit_heldout_row_alignment(base, {" zeta ": ("b", "a"), "alpha": base})
    assert audit.source_names == ("alpha", "zeta")
    assert audit.alignment_category == "reorderable_alignment"
    with pytest.raises(ValueError, match="unique"):
        audit_heldout_row_alignment(base, {"x": base, " x ": base})


def test_reorder_validation_rows_supports_refit_matrix_columns():
    matrix = np.asarray([[30, 10, 40, 20], [31, 11, 41, 21]])
    restored = reorder_validation_rows(matrix, (1, 3, 0, 2), axis=1)
    expected = np.asarray([[10, 20, 30, 40], [11, 21, 31, 41]])
    assert np.array_equal(restored, expected)


def test_reorder_validation_rows_rejects_invalid_permutation():
    with pytest.raises(ValueError, match="length"):
        reorder_validation_rows([1, 2, 3], (0, 1))
    with pytest.raises(ValueError, match="exactly once"):
        reorder_validation_rows([1, 2, 3], (0, 0, 2))
    with pytest.raises(ValueError, match="bounds"):
        reorder_validation_rows([[1, 2], [3, 4]], (0, 1), axis=2)
