import numpy as np
import pytest

from odsp.selection_validation_provenance import audit_selection_validation_provenance


def test_clean_and_leaked_selection_provenance():
    final = ("v0", "v1", "v2", "v3")
    clean = audit_selection_validation_provenance(
        final,
        {
            "ranking": ("r0", "r1"),
            " tuning ": ("t0", "t1", "t1"),
        },
        expected_stage_names=("tuning", "ranking"),
    )
    assert clean.separation_category == "selection_validation_disjoint"
    assert clean.selection_validation_separated is True
    assert clean.stage_names == ("ranking", "tuning")
    assert clean.duplicate_selection_row_count == 1
    assert clean.expected_stage_coverage_checked is True

    leaked = audit_selection_validation_provenance(
        final,
        {"ranking": ("r0", "v1"), "tuning": ("t0", "v2", "v2")},
    )
    assert leaked.separation_category == "selection_validation_leakage"
    assert leaked.selection_validation_separated is False
    assert leaked.overlapping_stage_count == 2
    assert leaked.unique_overlapping_final_validation_row_count == 2
    assert leaked.maximum_stage_overlap_count == 1
    assert leaked.duplicate_selection_row_count == 1
    assert leaked.overlapping_row_ids_emitted is False
    assert leaked.automatic_selection_history_inference is False
    assert leaked.automatic_candidate_selection is False


def test_duplicate_final_ids_and_invalid_selection_rows_are_rejected():
    with pytest.raises(ValueError, match="unique"):
        audit_selection_validation_provenance(("v0", "v0"), {"ranking": ("r0",)})
    with pytest.raises(ValueError, match="missing"):
        audit_selection_validation_provenance(("v0", None), {"ranking": ("r0",)})
    with pytest.raises(ValueError, match="missing"):
        audit_selection_validation_provenance(("v0", np.nan), {"ranking": ("r0",)})
    with pytest.raises(ValueError, match="hashable"):
        audit_selection_validation_provenance(("v0", ["v1"]), {"ranking": ("r0",)})
    with pytest.raises(ValueError, match="at least one row"):
        audit_selection_validation_provenance(("v0",), {"ranking": ()})


def test_stage_names_are_canonical_and_unique():
    final = ("v0", "v1")
    with pytest.raises(ValueError, match="unique"):
        audit_selection_validation_provenance(
            final,
            {"ranking": ("r0",), " ranking ": ("r1",)},
        )
    with pytest.raises(ValueError, match="non-empty"):
        audit_selection_validation_provenance(final, {"   ": ("r0",)})


def test_expected_stage_coverage_fails_closed():
    final = ("v0", "v1")
    stages = {"ranking": ("r0",), "tuning": ("t0",)}
    with pytest.raises(ValueError, match="missing"):
        audit_selection_validation_provenance(
            final,
            {"ranking": ("r0",)},
            expected_stage_names=("ranking", "tuning"),
        )
    with pytest.raises(ValueError, match="unexpected extra"):
        audit_selection_validation_provenance(
            final,
            stages,
            expected_stage_names=("ranking",),
        )
    with pytest.raises(ValueError, match="unique"):
        audit_selection_validation_provenance(
            final,
            stages,
            expected_stage_names=("ranking", " ranking "),
        )


def test_serialized_audit_never_emits_selection_or_overlap_row_ids():
    result = audit_selection_validation_provenance(
        ("v0", "v1"),
        {"ranking": ("v0", "r1")},
    ).as_dict()
    assert "selection_row_ids" not in result
    assert "overlapping_row_ids" not in result
    assert "overlapping_validation_row_ids" not in result
    assert all("row_ids" not in row for row in result["stages"])
