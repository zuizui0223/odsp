import numpy as np
import pytest

from odsp.refit_training_validation_provenance import (
    audit_refit_training_validation_provenance,
)


def test_direct_overlap_is_fail_closed_and_counts_only_unique_validation_rows():
    result = audit_refit_training_validation_provenance(
        ("v0", "v1", "v2"),
        {
            " bootstrap ": {
                " r0 ": ("t0", "v1", "v1", "t1"),
                "r1": ("t2", "t3"),
            }
        },
        expected_refit_ids_by_scheme={"bootstrap": ("r0", "r1")},
    )
    assert result.separation_category == "leakage_detected"
    assert result.training_validation_separated is False
    assert result.overlapping_refit_count == 1
    assert result.affected_scheme_count == 1
    assert result.unique_overlapping_validation_row_count == 1
    assert result.maximum_refit_overlap_count == 1
    assert result.overlapping_row_ids_emitted is False
    row = result.schemes[0].refits[0]
    assert row.refit_id == "r0"
    assert row.overlapping_validation_row_count == 1
    assert row.duplicate_training_row_count == 1


def test_training_duplicates_without_validation_overlap_are_allowed():
    result = audit_refit_training_validation_provenance(
        ("v0", "v1"),
        {"bootstrap": {"r0": ("t0", "t0", "t1")}},
    )
    assert result.training_validation_separated is True
    assert result.separation_category == "training_validation_disjoint"
    assert result.duplicate_training_row_count == 1
    assert result.schemes[0].refits[0].status == "training_validation_disjoint"


def test_expected_refit_coverage_must_match_exactly():
    validation = ("v0", "v1")
    training = {"seed": {"r0": ("t0",), "r1": ("t1",)}}
    with pytest.raises(ValueError, match="refit coverage"):
        audit_refit_training_validation_provenance(
            validation,
            training,
            expected_refit_ids_by_scheme={"seed": ("r0",)},
        )
    with pytest.raises(ValueError, match="scheme coverage"):
        audit_refit_training_validation_provenance(
            validation,
            training,
            expected_refit_ids_by_scheme={"other": ("r0", "r1")},
        )


def test_invalid_row_ids_and_empty_memberships_are_rejected():
    with pytest.raises(ValueError, match="unique"):
        audit_refit_training_validation_provenance(
            ("v0", "v0"), {"seed": {"r0": ("t0",)}}
        )
    with pytest.raises(ValueError, match="missing"):
        audit_refit_training_validation_provenance(
            ("v0", np.nan), {"seed": {"r0": ("t0",)}}
        )
    with pytest.raises(ValueError, match="hashable"):
        audit_refit_training_validation_provenance(
            ("v0", ["v1"]), {"seed": {"r0": ("t0",)}}
        )
    with pytest.raises(ValueError, match="at least one row ID"):
        audit_refit_training_validation_provenance(
            ("v0",), {"seed": {"r0": ()}}
        )


def test_scheme_and_refit_ids_are_canonicalized_and_sorted():
    result = audit_refit_training_validation_provenance(
        ("v0",),
        {
            " zeta ": {" r2 ": ("t2",), "r1": ("t1",)},
            "alpha": {"b": ("t3",), " a ": ("t4",)},
        },
    )
    assert result.scheme_names == ("alpha", "zeta")
    assert tuple(row.refit_id for row in result.schemes[0].refits) == ("a", "b")
    assert tuple(row.refit_id for row in result.schemes[1].refits) == ("r1", "r2")
