import numpy as np
import pytest

import odsp.forecast_assessment_v9 as v9_module
from odsp.forecast_assessment_v8 import assess_state_forecast_v8
from odsp.forecast_assessment_v9 import assess_state_forecast_v9


FINAL_ID = "final-artifact"
FINAL_DIGEST = "sha256:" + "a" * 64
OTHER_DIGEST = "sha256:" + "b" * 64
SUBSTITUTE_DIGEST = "sha256:" + "c" * 64


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


def _binding_inputs(*, mismatch: bool = False):
    ids = {"review": ("artifact-a",)}
    digests = {"review": (SUBSTITUTE_DIGEST if mismatch else OTHER_DIGEST,)}
    manifest = {
        FINAL_ID: FINAL_DIGEST,
        "artifact-a": OTHER_DIGEST,
    }
    return dict(
        artifact_digest_by_id=manifest,
        expected_evaluation_ledger_binding_stage_names=("review",),
        final_evaluation_artifact_id=FINAL_ID,
        final_evaluation_digest=FINAL_DIGEST,
        accessed_artifact_ids_by_stage=ids,
        accessed_artifact_digests_by_stage=digests,
        expected_evaluation_access_stage_names=("review",),
        expected_evaluation_content_stage_names=("review",),
    )


def test_binding_metadata_without_manifest_is_rejected():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    with pytest.raises(ValueError, match="must not be supplied without artifact_digest_by_id"):
        assess_state_forecast_v9(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            expected_evaluation_ledger_binding_stage_names=("review",),
            **_base_kwargs(),
        )


def test_manifest_requires_both_ledgers_and_final_identity():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    with pytest.raises(ValueError, match="evaluation-ledger binding requires"):
        assess_state_forecast_v9(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            artifact_digest_by_id={FINAL_ID: FINAL_DIGEST},
            final_evaluation_artifact_id=FINAL_ID,
            final_evaluation_digest=FINAL_DIGEST,
            accessed_artifact_ids_by_stage={"review": (FINAL_ID,)},
            **_base_kwargs(),
        )


def test_clean_binding_runs_ordinary_v8_path():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    result = assess_state_forecast_v9(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **_binding_inputs(),
        **_base_kwargs(),
    )
    assert result.evaluation_ledger_binding is not None
    assert result.evaluation_ledger_binding.ledger_binding_consistent is True
    assert result.evaluation_ledger_binding.separation_category == "evaluation_ledgers_consistently_bound"
    assert result.downstream_v8_assessment is not None
    assert result.settings["downstream_v8_assessment_run"] is True
    assert result.v9_certification.evaluation_ledger_binding_status == "evaluation_ledgers_consistently_bound"


def test_binding_mismatch_short_circuits_full_v8_path(monkeypatch):
    conditional, marginal, covered, groups, blocks = _small_inputs()
    calls = {"full": 0}

    def forbidden_full(*args, **kwargs):
        calls["full"] += 1
        raise AssertionError("full v8 path must not run after ledger-binding mismatch")

    monkeypatch.setattr(v9_module, "_full_v8", forbidden_full)
    result = assess_state_forecast_v9(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **_binding_inputs(mismatch=True),
        **_base_kwargs(),
    )
    assert calls["full"] == 0
    assert result.evaluation_ledger_binding is not None
    assert result.evaluation_ledger_binding.separation_category == "evaluation_ledger_binding_mismatch"
    assert result.downstream_v8_assessment is None
    assert result.settings["downstream_v8_assessment_run"] is False
    assert result.v9_certification.downstream_v8_status == "not_run_evaluation_ledger_binding_mismatch"
    assert result.v9_certification.evaluation_content_provenance_status == "not_run_evaluation_ledger_binding_mismatch"
    assert result.v9_certification.evaluation_access_provenance_status == "not_run_evaluation_ledger_binding_mismatch"
    assert "evaluation_ledger_binding_mismatch" in result.v9_certification.provenance_blocking_reasons


def test_omitted_binding_layer_preserves_direct_v8_result():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    kwargs = _base_kwargs()
    direct = assess_state_forecast_v8(
        "x", conditional, marginal, covered, groups, blocks, **kwargs
    )
    result = assess_state_forecast_v9(
        "x", conditional, marginal, covered, groups, blocks, **kwargs
    )
    assert result.evaluation_ledger_binding is None
    assert result.downstream_v8_assessment is not None
    assert result.downstream_v8_assessment.as_dict() == direct.as_dict()
    assert result.v9_certification.evaluation_ledger_binding_status == "not_audited"
    assert result.v9_certification.certification_status == direct.v8_certification.certification_status
