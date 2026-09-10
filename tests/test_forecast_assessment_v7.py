import numpy as np
import pytest

from odsp.forecast_assessment_v6 import assess_state_forecast_v6
from odsp.forecast_assessment_v7 import assess_state_forecast_v7


def _small_inputs():
    conditional = np.full(8, 0.2)
    marginal = np.zeros(8)
    covered = (True, True, True, True, True, True, True, False)
    groups = tuple("g" for _ in range(8))
    blocks = tuple(f"b{i}" for i in range(8))
    row_ids = tuple(f"r{i}" for i in range(8))
    clean_access = {
        "candidate_screening": ("dev-report-a", "dev-report-b"),
        "model_review": ("training-report", "calibration-report"),
    }
    return conditional, marginal, covered, groups, blocks, row_ids, clean_access


def _base_kwargs():
    return dict(
        region_size=np.ones(8),
        validation_gamma=1.0,
        bootstrap_draws=100,
        minimum_blocks_per_group=2,
        scheme_nested_draws=500,
        scheme_minimum_refits=2,
    )


def test_access_provenance_requires_final_artifact_id():
    conditional, marginal, covered, groups, blocks, _row_ids, clean_access = _small_inputs()
    with pytest.raises(ValueError, match="final_evaluation_artifact_id"):
        assess_state_forecast_v7(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            accessed_artifact_ids_by_stage=clean_access,
            **_base_kwargs(),
        )


def test_access_metadata_without_ledger_is_rejected():
    conditional, marginal, covered, groups, blocks, *_rest = _small_inputs()
    with pytest.raises(ValueError, match="must not be supplied"):
        assess_state_forecast_v7(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            final_evaluation_artifact_id="final",
            **_base_kwargs(),
        )
    with pytest.raises(ValueError, match="must not be supplied"):
        assess_state_forecast_v7(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            expected_evaluation_access_stage_names=("candidate_screening",),
            **_base_kwargs(),
        )


def test_final_evaluation_access_leakage_short_circuits_downstream_v6():
    conditional, marginal, covered, groups, blocks, _row_ids, _clean_access = _small_inputs()
    result = assess_state_forecast_v7(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_artifact_id="final",
        accessed_artifact_ids_by_stage={
            "candidate_screening": ("dev-report", "final"),
            "model_review": ("training-report",),
        },
        **_base_kwargs(),
    )
    assert result.evaluation_access_provenance is not None
    assert result.evaluation_access_provenance.separation_category == "final_evaluation_access_leakage"
    assert result.downstream_v6_assessment is None
    assert result.settings["downstream_v6_assessment_run"] is False
    assert result.v7_certification.downstream_v6_status == "not_run_final_evaluation_access_leakage"
    assert result.v7_certification.selection_validation_provenance_status == "not_run_final_evaluation_access_leakage"
    assert result.v7_certification.training_validation_provenance_status == "not_run_final_evaluation_access_leakage"
    assert result.v7_certification.heldout_row_provenance_status == "not_run_final_evaluation_access_leakage"
    assert result.v7_certification.certification_status == "unavailable"
    assert result.v7_certification.provenance_blocking_reasons == ("final_evaluation_access_leakage",)


def test_clean_access_runs_ordinary_v6_path():
    conditional, marginal, covered, groups, blocks, _row_ids, clean_access = _small_inputs()
    result = assess_state_forecast_v7(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_artifact_id="final",
        accessed_artifact_ids_by_stage=clean_access,
        expected_evaluation_access_stage_names=("candidate_screening", "model_review"),
        **_base_kwargs(),
    )
    assert result.evaluation_access_provenance is not None
    assert result.evaluation_access_provenance.final_evaluation_accessed is False
    assert result.downstream_v6_assessment is not None
    assert result.settings["downstream_v6_assessment_run"] is True
    assert result.v7_certification.evaluation_access_provenance_status == "final_evaluation_not_accessed_in_declared_pre_final_stages"
    assert result.v7_certification.certification_status == result.downstream_v6_assessment.v6_certification.certification_status


def test_omitted_access_layer_preserves_direct_v6_result():
    conditional, marginal, covered, groups, blocks, *_rest = _small_inputs()
    kwargs = _base_kwargs()
    direct = assess_state_forecast_v6(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **kwargs,
    )
    result = assess_state_forecast_v7(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **kwargs,
    )
    assert result.evaluation_access_provenance is None
    assert result.downstream_v6_assessment is not None
    assert result.downstream_v6_assessment.as_dict() == direct.as_dict()
    assert result.v7_certification.evaluation_access_provenance_status == "not_audited"
    assert result.v7_certification.certification_status == direct.v6_certification.certification_status
