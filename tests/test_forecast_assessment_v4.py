import numpy as np
import pytest

pytest.importorskip("sklearn")

from odsp.forecast_assessment_v4 import assess_state_forecast_v4


def _base_inputs():
    n = 16
    conditional = np.full(n, 0.2)
    marginal = np.zeros(n)
    covered = np.asarray([True] * 14 + [False] * 2)
    groups = tuple("g" for _ in range(n))
    blocks = tuple(f"b-{i:02d}" for i in range(n))
    region_size = np.full(n, 4.0)
    row_ids = tuple(f"r-{i:02d}" for i in range(n))
    schemes = {
        "bootstrap": np.vstack([conditional, conditional + 0.01]),
        "seed": np.vstack([conditional, conditional - 0.01]),
    }
    return conditional, marginal, covered, groups, blocks, region_size, row_ids, schemes


def test_scheme_request_requires_base_validation_row_ids():
    conditional, marginal, covered, groups, blocks, region_size, row_ids, schemes = _base_inputs()
    with pytest.raises(ValueError, match="validation_row_ids are required"):
        assess_state_forecast_v4(
            "candidate",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            region_size=region_size,
            refit_schemes=schemes,
            validation_row_ids_by_scheme={name: row_ids for name in schemes},
        )


def test_scheme_request_requires_per_scheme_validation_row_ids():
    conditional, marginal, covered, groups, blocks, region_size, row_ids, schemes = _base_inputs()
    with pytest.raises(ValueError, match="validation_row_ids_by_scheme is required"):
        assess_state_forecast_v4(
            "candidate",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            region_size=region_size,
            validation_row_ids=row_ids,
            refit_schemes=schemes,
        )


def test_omitted_scheme_layer_leaves_provenance_not_audited():
    conditional, marginal, covered, groups, blocks, region_size, _row_ids, _schemes = _base_inputs()
    result = assess_state_forecast_v4(
        "candidate",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        region_size=region_size,
        minimum_blocks_per_group=8,
        bootstrap_draws=100,
        seed=20260907,
    )
    assert result.aligned_refit_scheme_audit is None
    assert result.aligned_v3_certification is None
    assert result.v4_certification.row_provenance_status == "not_audited"
    assert result.v4_certification.aligned_scheme_audit_status == "not_audited"
    assert result.v4_certification.certification_status == result.base_v3_assessment.v3_certification.certification_status
    assert result.aggregate_confidence_score_emitted is False
