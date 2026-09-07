import numpy as np
import pytest

from odsp.forecast_assessment_v4 import assess_state_forecast_v4


def _small_inputs():
    conditional = np.full(8, 0.2)
    marginal = np.zeros(8)
    covered = (True, True, True, True, True, True, True, False)
    groups = tuple("g" for _ in range(8))
    blocks = tuple(f"b{i}" for i in range(8))
    row_ids = tuple(f"r{i}" for i in range(8))
    schemes = {
        "bootstrap": np.vstack([conditional, conditional + 0.01]),
        "seed": np.vstack([conditional, conditional - 0.01]),
    }
    return conditional, marginal, covered, groups, blocks, row_ids, schemes


def test_declared_schemes_require_row_provenance():
    conditional, marginal, covered, groups, blocks, _row_ids, schemes = _small_inputs()
    with pytest.raises(ValueError, match="require validation_row_ids"):
        assess_state_forecast_v4(
            "x", conditional, marginal, covered, groups, blocks,
            region_size=np.ones(8), refit_schemes=schemes,
            validation_gamma=1.0, bootstrap_draws=20, minimum_blocks_per_group=2,
        )


def test_row_mismatch_withholds_v3_but_keeps_base_v2():
    conditional, marginal, covered, groups, blocks, row_ids, schemes = _small_inputs()
    bad = list(row_ids)
    bad[-1] = "other"
    result = assess_state_forecast_v4(
        "x", conditional, marginal, covered, groups, blocks,
        region_size=np.ones(8),
        refit_schemes=schemes,
        validation_row_ids=row_ids,
        validation_row_ids_by_scheme={"bootstrap": row_ids, "seed": tuple(bad)},
        validation_gamma=1.0,
        bootstrap_draws=20,
        minimum_blocks_per_group=2,
        scheme_nested_draws=20,
        scheme_minimum_refits=2,
    )
    assert result.base_v2_assessment is not None
    assert result.aligned_refit_scheme_audit is not None
    assert result.aligned_refit_scheme_audit.statistical_audit_run is False
    assert result.v3_assessment is None
    assert result.v4_certification.row_provenance_status == "row_mismatch"
    assert result.v4_certification.v3_assessment_status == "withheld_row_mismatch"
    assert "heldout_row_mismatch" in result.v4_certification.extended_blocking_reasons


def test_omitted_scheme_does_not_require_provenance():
    conditional, marginal, covered, groups, blocks, _row_ids, _schemes = _small_inputs()
    result = assess_state_forecast_v4(
        "x", conditional, marginal, covered, groups, blocks,
        region_size=np.ones(8), validation_gamma=1.0,
        bootstrap_draws=20, minimum_blocks_per_group=2,
    )
    assert result.aligned_refit_scheme_audit is None
    assert result.v3_assessment is not None
    assert result.v4_certification.row_provenance_status == "not_required"


def test_scheme_row_id_mapping_without_schemes_is_rejected():
    conditional, marginal, covered, groups, blocks, row_ids, _schemes = _small_inputs()
    with pytest.raises(ValueError, match="requires refit_schemes"):
        assess_state_forecast_v4(
            "x", conditional, marginal, covered, groups, blocks,
            region_size=np.ones(8),
            validation_row_ids_by_scheme={"bootstrap": row_ids},
            validation_gamma=1.0, bootstrap_draws=20, minimum_blocks_per_group=2,
        )
