import numpy as np
import pytest

from odsp.forecast_assessment_v5 import assess_state_forecast_v5


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
    refit_ids = {
        "bootstrap": ("bootstrap-0", "bootstrap-1"),
        "seed": ("seed-0", "seed-1"),
    }
    training = {
        "bootstrap": {
            "bootstrap-0": ("train-a", "train-b"),
            "bootstrap-1": ("train-c", "train-d"),
        },
        "seed": {
            "seed-0": ("train-e", "train-f"),
            "seed-1": ("train-g", "train-h"),
        },
    }
    return conditional, marginal, covered, groups, blocks, row_ids, schemes, refit_ids, training


def _base_kwargs():
    return dict(
        region_size=np.ones(8),
        validation_gamma=1.0,
        bootstrap_draws=100,
        minimum_blocks_per_group=2,
        scheme_nested_draws=500,
        scheme_minimum_refits=2,
    )


def test_declared_schemes_require_training_and_row_provenance():
    conditional, marginal, covered, groups, blocks, row_ids, schemes, refit_ids, training = _small_inputs()
    with pytest.raises(ValueError, match="validation_row_ids"):
        assess_state_forecast_v5(
            "x", conditional, marginal, covered, groups, blocks,
            refit_schemes=schemes, **_base_kwargs(),
        )
    with pytest.raises(ValueError, match="validation_row_ids_by_scheme"):
        assess_state_forecast_v5(
            "x", conditional, marginal, covered, groups, blocks,
            validation_row_ids=row_ids,
            refit_schemes=schemes,
            **_base_kwargs(),
        )
    with pytest.raises(ValueError, match="refit_ids_by_scheme"):
        assess_state_forecast_v5(
            "x", conditional, marginal, covered, groups, blocks,
            validation_row_ids=row_ids,
            validation_row_ids_by_scheme={name: row_ids for name in schemes},
            refit_schemes=schemes,
            **_base_kwargs(),
        )
    with pytest.raises(ValueError, match="training_row_ids_by_scheme"):
        assess_state_forecast_v5(
            "x", conditional, marginal, covered, groups, blocks,
            validation_row_ids=row_ids,
            validation_row_ids_by_scheme={name: row_ids for name in schemes},
            refit_schemes=schemes,
            refit_ids_by_scheme=refit_ids,
            **_base_kwargs(),
        )


def test_training_leakage_stops_downstream_v4_scheme_path():
    conditional, marginal, covered, groups, blocks, row_ids, schemes, refit_ids, training = _small_inputs()
    leaky = {name: dict(rows) for name, rows in training.items()}
    leaky["seed"]["seed-1"] = ("train-g", row_ids[0])
    result = assess_state_forecast_v5(
        "x", conditional, marginal, covered, groups, blocks,
        validation_row_ids=row_ids,
        validation_row_ids_by_scheme={name: row_ids for name in schemes},
        refit_schemes=schemes,
        refit_ids_by_scheme=refit_ids,
        training_row_ids_by_scheme=leaky,
        **_base_kwargs(),
    )
    assert result.training_validation_provenance is not None
    assert result.training_validation_provenance.separation_category == "leakage_detected"
    assert result.provenance_qualified_v4_assessment is None
    assert result.settings["downstream_v4_scheme_assessment_run"] is False
    assert result.v5_certification.certification_status == "unavailable"
    assert result.v5_certification.provenance_blocking_reasons == ("training_validation_leakage",)
    assert not any(
        reason.startswith("refit_scheme")
        for reason in result.v5_certification.statistical_blocking_reasons
    )


def test_clean_training_runs_downstream_v4_scheme_path():
    conditional, marginal, covered, groups, blocks, row_ids, schemes, refit_ids, training = _small_inputs()
    result = assess_state_forecast_v5(
        "x", conditional, marginal, covered, groups, blocks,
        validation_row_ids=row_ids,
        validation_row_ids_by_scheme={name: row_ids for name in schemes},
        refit_schemes=schemes,
        refit_ids_by_scheme=refit_ids,
        reference_refit_ids_by_scheme={name: ids[0] for name, ids in refit_ids.items()},
        training_row_ids_by_scheme=training,
        **_base_kwargs(),
    )
    assert result.training_validation_provenance is not None
    assert result.training_validation_provenance.training_validation_separated is True
    assert result.provenance_qualified_v4_assessment is not None
    assert result.settings["downstream_v4_scheme_assessment_run"] is True
    assert result.v5_certification.training_validation_provenance_status == "training_validation_disjoint"


def test_omitted_scheme_preserves_base_v4_and_rejects_scheme_metadata():
    conditional, marginal, covered, groups, blocks, row_ids, _schemes, _refit_ids, training = _small_inputs()
    result = assess_state_forecast_v5(
        "x", conditional, marginal, covered, groups, blocks, **_base_kwargs()
    )
    assert result.training_validation_provenance is None
    assert result.provenance_qualified_v4_assessment is None
    assert result.v5_certification.certification_status == result.base_v4_assessment.v4_certification.certification_status

    with pytest.raises(ValueError, match="must not be supplied"):
        assess_state_forecast_v5(
            "x", conditional, marginal, covered, groups, blocks,
            training_row_ids_by_scheme=training,
            **_base_kwargs(),
        )
