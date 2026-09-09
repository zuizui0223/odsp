import numpy as np
import pytest

from odsp.forecast_assessment_v5 import assess_state_forecast_v5
from odsp.forecast_assessment_v6 import assess_state_forecast_v6


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
    clean_selection = {
        "candidate_ranking": ("rank-a", "rank-b"),
        "hyperparameter_tuning": ("tune-a", "tune-b"),
    }
    return (
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        row_ids,
        schemes,
        refit_ids,
        training,
        clean_selection,
    )


def _base_kwargs():
    return dict(
        region_size=np.ones(8),
        validation_gamma=1.0,
        bootstrap_draws=100,
        minimum_blocks_per_group=2,
        scheme_nested_draws=500,
        scheme_minimum_refits=2,
    )


def test_selection_provenance_requires_final_validation_ids():
    conditional, marginal, covered, groups, blocks, *_rest = _small_inputs()
    with pytest.raises(ValueError, match="validation_row_ids"):
        assess_state_forecast_v6(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            selection_row_ids_by_stage={"ranking": ("rank-a",)},
            **_base_kwargs(),
        )


def test_selection_leakage_short_circuits_full_v5_path():
    conditional, marginal, covered, groups, blocks, row_ids, schemes, *_rest = _small_inputs()
    result = assess_state_forecast_v6(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=row_ids,
        selection_row_ids_by_stage={"ranking": ("rank-a", row_ids[0])},
        refit_schemes=schemes,
        **_base_kwargs(),
    )
    assert result.selection_validation_provenance is not None
    assert result.selection_validation_provenance.separation_category == "selection_validation_leakage"
    assert result.downstream_v5_assessment is None
    assert result.settings["downstream_v5_assessment_run"] is False
    assert result.v6_certification.downstream_v5_status == "not_run_selection_validation_leakage"
    assert result.v6_certification.training_validation_provenance_status == "not_run_selection_validation_leakage"
    assert result.v6_certification.certification_status == "unavailable"
    assert "selection_validation_leakage" in result.v6_certification.provenance_blocking_reasons
    assert not any(
        reason.startswith("refit_scheme") or reason.startswith("training_validation")
        for reason in result.v6_certification.statistical_blocking_reasons
    )


def test_clean_selection_runs_ordinary_v5_path():
    (
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        row_ids,
        schemes,
        refit_ids,
        training,
        clean_selection,
    ) = _small_inputs()
    result = assess_state_forecast_v6(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=row_ids,
        selection_row_ids_by_stage=clean_selection,
        expected_selection_stage_names=("candidate_ranking", "hyperparameter_tuning"),
        refit_schemes=schemes,
        validation_row_ids_by_scheme={name: row_ids for name in schemes},
        refit_ids_by_scheme=refit_ids,
        reference_refit_ids_by_scheme={name: ids[0] for name, ids in refit_ids.items()},
        training_row_ids_by_scheme=training,
        **_base_kwargs(),
    )
    assert result.selection_validation_provenance is not None
    assert result.selection_validation_provenance.selection_validation_separated is True
    assert result.downstream_v5_assessment is not None
    assert result.settings["downstream_v5_assessment_run"] is True
    assert result.v6_certification.selection_validation_provenance_status == "selection_validation_disjoint"
    assert result.v6_certification.certification_status == result.downstream_v5_assessment.v5_certification.certification_status


def test_omitted_selection_layer_preserves_direct_v5_result():
    (
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        row_ids,
        schemes,
        refit_ids,
        training,
        _clean_selection,
    ) = _small_inputs()
    kwargs = _base_kwargs()
    direct = assess_state_forecast_v5(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=row_ids,
        refit_schemes=schemes,
        validation_row_ids_by_scheme={name: row_ids for name in schemes},
        refit_ids_by_scheme=refit_ids,
        reference_refit_ids_by_scheme={name: ids[0] for name, ids in refit_ids.items()},
        training_row_ids_by_scheme=training,
        **kwargs,
    )
    result = assess_state_forecast_v6(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        validation_row_ids=row_ids,
        refit_schemes=schemes,
        validation_row_ids_by_scheme={name: row_ids for name in schemes},
        refit_ids_by_scheme=refit_ids,
        reference_refit_ids_by_scheme={name: ids[0] for name, ids in refit_ids.items()},
        training_row_ids_by_scheme=training,
        **kwargs,
    )
    assert result.selection_validation_provenance is None
    assert result.downstream_v5_assessment is not None
    assert result.downstream_v5_assessment.as_dict() == direct.as_dict()
    assert result.v6_certification.selection_validation_provenance_status == "not_audited"
    assert result.v6_certification.certification_status == direct.v5_certification.certification_status


def test_selection_metadata_without_ledger_is_rejected():
    conditional, marginal, covered, groups, blocks, *_rest = _small_inputs()
    with pytest.raises(ValueError, match="must not be supplied"):
        assess_state_forecast_v6(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            expected_selection_stage_names=("ranking",),
            **_base_kwargs(),
        )
