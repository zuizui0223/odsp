import numpy as np
import pytest

import odsp.forecast_assessment_v10 as v10_module
from odsp.evaluation_access_log_chain import GENESIS_EVENT_HASH, compute_access_event_hash
from odsp.forecast_assessment_v9 import assess_state_forecast_v9
from odsp.forecast_assessment_v10 import assess_state_forecast_v10


FINAL_ID = "final-artifact"
FINAL_DIGEST = "sha256:" + "a" * 64
OTHER_DIGEST = "sha256:" + "b" * 64


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


def _provenance_inputs():
    ids = {"review": ("artifact-a",)}
    digests = {"review": (OTHER_DIGEST,)}
    manifest = {FINAL_ID: FINAL_DIGEST, "artifact-a": OTHER_DIGEST}
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


def _log_inputs(*, bad_terminal: bool = False):
    event_hash = compute_access_event_hash(
        0, "review", "artifact-a", OTHER_DIGEST, GENESIS_EVENT_HASH
    )
    events = (
        {
            "sequence_index": 0,
            "stage_name": "review",
            "artifact_id": "artifact-a",
            "artifact_digest": OTHER_DIGEST,
            "previous_event_hash": GENESIS_EVENT_HASH,
            "event_hash": event_hash,
        },
    )
    return dict(
        evaluation_access_log_events=events,
        committed_access_event_count=1,
        committed_terminal_access_event_hash=(
            "sha256:" + "f" * 64 if bad_terminal else event_hash
        ),
    )


def test_log_metadata_without_events_is_rejected():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    with pytest.raises(ValueError, match="must not be supplied without evaluation_access_log_events"):
        assess_state_forecast_v10(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            committed_access_event_count=1,
            **_base_kwargs(),
        )


def test_log_events_require_commitments_final_identity_and_both_ledgers():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    event_hash = compute_access_event_hash(
        0, "review", "artifact-a", OTHER_DIGEST, GENESIS_EVENT_HASH
    )
    events = (
        {
            "sequence_index": 0,
            "stage_name": "review",
            "artifact_id": "artifact-a",
            "artifact_digest": OTHER_DIGEST,
            "previous_event_hash": GENESIS_EVENT_HASH,
            "event_hash": event_hash,
        },
    )
    with pytest.raises(ValueError, match="evaluation-access log-chain gating requires"):
        assess_state_forecast_v10(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            evaluation_access_log_events=events,
            committed_access_event_count=1,
            committed_terminal_access_event_hash=event_hash,
            final_evaluation_artifact_id=FINAL_ID,
            **_base_kwargs(),
        )


def test_clean_log_chain_runs_ordinary_v9_path():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    result = assess_state_forecast_v10(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **_log_inputs(),
        **_provenance_inputs(),
        **_base_kwargs(),
    )
    assert result.evaluation_access_log_chain is not None
    assert result.evaluation_access_log_chain.log_chain_consistent is True
    assert result.evaluation_access_log_chain.separation_category == "evaluation_access_log_chain_consistent"
    assert result.downstream_v9_assessment is not None
    assert result.settings["downstream_v9_assessment_run"] is True
    assert result.v10_certification.evaluation_access_log_chain_status == "evaluation_access_log_chain_consistent"


def test_log_chain_mismatch_short_circuits_full_v9_path(monkeypatch):
    conditional, marginal, covered, groups, blocks = _small_inputs()
    calls = {"full": 0}

    def forbidden_full(*args, **kwargs):
        calls["full"] += 1
        raise AssertionError("full v9 path must not run after access-log chain mismatch")

    monkeypatch.setattr(v10_module, "_full_v9", forbidden_full)
    result = assess_state_forecast_v10(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        **_log_inputs(bad_terminal=True),
        **_provenance_inputs(),
        **_base_kwargs(),
    )
    assert calls["full"] == 0
    assert result.evaluation_access_log_chain is not None
    assert result.evaluation_access_log_chain.separation_category == "evaluation_access_log_chain_mismatch"
    assert result.downstream_v9_assessment is None
    assert result.settings["downstream_v9_assessment_run"] is False
    assert result.v10_certification.downstream_v9_status == "not_run_evaluation_access_log_chain_mismatch"
    assert result.v10_certification.evaluation_ledger_binding_status == "not_run_evaluation_access_log_chain_mismatch"
    assert "evaluation_access_log_chain_mismatch" in result.v10_certification.provenance_blocking_reasons


def test_omitted_log_chain_preserves_direct_v9_result():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    kwargs = _base_kwargs()
    provenance = _provenance_inputs()
    direct = assess_state_forecast_v9(
        "x", conditional, marginal, covered, groups, blocks, **provenance, **kwargs
    )
    result = assess_state_forecast_v10(
        "x", conditional, marginal, covered, groups, blocks, **provenance, **kwargs
    )
    assert result.evaluation_access_log_chain is None
    assert result.downstream_v9_assessment is not None
    assert result.downstream_v9_assessment.as_dict() == direct.as_dict()
    assert result.v10_certification.evaluation_access_log_chain_status == "not_audited"
    assert result.v10_certification.certification_status == direct.v9_certification.certification_status
