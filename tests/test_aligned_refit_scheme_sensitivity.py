import numpy as np
import pytest

from odsp.aligned_refit_scheme_sensitivity import audit_aligned_refit_scheme_sensitivity


def _small_inputs():
    schemes = {
        "bootstrap": np.asarray([[0.2, 0.2, 0.2, 0.2], [0.21, 0.21, 0.21, 0.21]]),
        "seed": np.asarray([[0.2, 0.2, 0.2, 0.2], [0.19, 0.19, 0.19, 0.19]]),
    }
    groups = ("g", "g", "g", "g")
    blocks = ("b0", "b1", "b2", "b3")
    base_ids = ("r0", "r1", "r2", "r3")
    return schemes, groups, blocks, base_ids


def test_row_mismatch_fails_before_statistical_audit():
    schemes, groups, blocks, base_ids = _small_inputs()
    result = audit_aligned_refit_scheme_sensitivity(
        schemes,
        groups,
        blocks=blocks,
        validation_row_ids=base_ids,
        validation_row_ids_by_scheme={
            "bootstrap": base_ids,
            "seed": ("r0", "r1", "r2", "other"),
        },
        minimum_refits=2,
        minimum_blocks_per_group=2,
        nested_draws=20,
    )
    assert result.status == "row_mismatch"
    assert result.statistical_audit_run is False
    assert result.scheme_audit is None
    assert result.scheme_robust_admissible is False
    assert result.row_alignment.mismatched_source_count == 1
    assert result.row_alignment.sources[1].missing_row_count == 1
    assert result.row_alignment.sources[1].extra_row_count == 1


def test_scheme_row_id_mapping_must_cover_all_schemes():
    schemes, groups, blocks, base_ids = _small_inputs()
    with pytest.raises(ValueError, match="cover every"):
        audit_aligned_refit_scheme_sensitivity(
            schemes,
            groups,
            blocks=blocks,
            validation_row_ids=base_ids,
            validation_row_ids_by_scheme={"bootstrap": base_ids},
        )


def test_scheme_matrix_column_count_must_match_declared_row_ids():
    schemes, groups, blocks, base_ids = _small_inputs()
    with pytest.raises(ValueError, match="column count"):
        audit_aligned_refit_scheme_sensitivity(
            schemes,
            groups,
            blocks=blocks,
            validation_row_ids=base_ids,
            validation_row_ids_by_scheme={
                "bootstrap": base_ids,
                "seed": base_ids[:-1],
            },
        )


def test_base_groups_blocks_and_weights_must_share_canonical_length():
    schemes, groups, blocks, base_ids = _small_inputs()
    with pytest.raises(ValueError, match="groups and blocks"):
        audit_aligned_refit_scheme_sensitivity(
            schemes,
            groups[:-1],
            blocks=blocks,
            validation_row_ids=base_ids,
            validation_row_ids_by_scheme={name: base_ids for name in schemes},
        )
    with pytest.raises(ValueError, match="sample_weight"):
        audit_aligned_refit_scheme_sensitivity(
            schemes,
            groups,
            blocks=blocks,
            validation_row_ids=base_ids,
            validation_row_ids_by_scheme={name: base_ids for name in schemes},
            sample_weight=(1.0, 1.0, 1.0),
        )
