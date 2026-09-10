import numpy as np
import pytest

import odsp.forecast_assessment_v8 as v8_module
from odsp.forecast_assessment_v7 import assess_state_forecast_v7
from odsp.forecast_assessment_v8 import assess_state_forecast_v8


def _small_inputs():
    conditional = np.full(8, 0.2)
    marginal = np.zeros(8)
    covered = (True, True, True, True, True, True, True, False)
    groups = tuple("g" for _ in range(8))
    blocks = tuple(f"b{i}" for i in range(8))
    return conditional, marginal, covered, groups, blocks


def _base_kwargs():
    return dict(
        region_size=np.ones(8),
        validation_gamma=1.0,
        bootstrap_draws=100,
        minimum_blocks_per_group=2,
        scheme_nested_draws=500,
        scheme_minimum_refits=2,
    )


def _digest(char: str) -> str:
    return "sha256:" + char * 64


def test_content_provenance_requires_final_digest():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    with pytest.raises(ValueError, match="final_evaluation_digest"):
        assess_state_forecast_v8(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            accessed_artifact_digests_by_stage={"ranking": (_digest("a"),)},
            **_base_kwargs(),
        )


def test_content_leakage_short_circuits_full_v7_path(monkeypatch):
    conditional, marginal, covered, groups, blocks = _small_inputs()
    calls = {"count": 0}

    def forbidden(*args, **kwargs):
        calls["count"] += 1
        raise AssertionError("full v7 path must not run after content leakage")

    monkeypatch.setattr(v8_module, "_full_v7", forbidden)
    final_digest = _digest("a")
    result = assess_state_forecast_v8(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_digest=final_digest,
        accessed_artifact_digests_by_stage={"ranking": (_digest("b"), final_digest)},
        **_base_kwargs(),
    )
    assert calls["count"] == 0
    assert result.evaluation_content_provenance is not None
    assert result.evaluation_content_provenance.separation_category == "final_evaluation_content_leakage"
    assert result.downstream_v7_assessment is None
    assert result.settings["downstream_v7_assessment_run"] is False
    assert result.v8_certification.downstream_v7_status == "not_run_final_evaluation_content_leakage"
    assert result.v8_certification.evaluation_access_provenance_status == "not_run_final_evaluation_content_leakage"
    assert result.v8_certification.selection_validation_provenance_status == "not_run_final_evaluation_content_leakage"
    assert result.v8_certification.certification_status == "unavailable"
    assert result.v8_certification.provenance_blocking_reasons == ("final_evaluation_content_leakage",)


def test_clean_content_runs_ordinary_v7_path():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    final_digest = _digest("a")
    result = assess_state_forecast_v8(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        final_evaluation_digest=final_digest,
        accessed_artifact_digests_by_stage={"ranking": (_digest("b"), _digest("c"))},
        **_base_kwargs(),
    )
    assert result.evaluation_content_provenance is not None
    assert result.evaluation_content_provenance.final_evaluation_content_accessed is False
    assert result.downstream_v7_assessment is not None
    assert result.settings["downstream_v7_assessment_run"] is True
    assert result.v8_certification.evaluation_content_provenance_status == "final_evaluation_content_not_accessed_in_declared_pre_final_stages"
    assert result.v8_certification.certification_status == result.downstream_v7_assessment.v7_certification.certification_status


def test_omitted_content_layer_preserves_direct_v7_result():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    kwargs = _base_kwargs()
    direct = assess_state_forecast_v7(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **kwargs,
    )
    result = assess_state_forecast_v8(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **kwargs,
    )
    assert result.evaluation_content_provenance is None
    assert result.downstream_v7_assessment is not None
    assert result.downstream_v7_assessment.as_dict() == direct.as_dict()
    assert result.v8_certification.evaluation_content_provenance_status == "not_audited"
    assert result.v8_certification.certification_status == direct.v7_certification.certification_status


def test_content_metadata_without_ledger_is_rejected():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    with pytest.raises(ValueError, match="must not be supplied"):
        assess_state_forecast_v8(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            expected_evaluation_content_stage_names=("ranking",),
            **_base_kwargs(),
        )
