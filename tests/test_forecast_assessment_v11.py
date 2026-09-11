import numpy as np
import pytest

import odsp.forecast_assessment_v11 as v11_module
from odsp.evaluation_access_log_chain import GENESIS_EVENT_HASH, compute_access_event_hash
from odsp.forecast_assessment_v10 import assess_state_forecast_v10
from odsp.forecast_assessment_v11 import assess_state_forecast_v11


FINAL_ID = "final-artifact"
FINAL_DIGEST = "sha256:" + "a" * 64
DIGEST_A = "sha256:" + "b" * 64
DIGEST_B = "sha256:" + "c" * 64


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


def _events():
    first_hash = compute_access_event_hash(
        0, "review", "artifact-a", DIGEST_A, GENESIS_EVENT_HASH
    )
    second_hash = compute_access_event_hash(
        1, "review", "artifact-b", DIGEST_B, first_hash
    )
    return [
        {
            "sequence_index": 0,
            "stage_name": "review",
            "artifact_id": "artifact-a",
            "artifact_digest": DIGEST_A,
            "previous_event_hash": GENESIS_EVENT_HASH,
            "event_hash": first_hash,
        },
        {
            "sequence_index": 1,
            "stage_name": "review",
            "artifact_id": "artifact-b",
            "artifact_digest": DIGEST_B,
            "previous_event_hash": first_hash,
            "event_hash": second_hash,
        },
    ]


def _full_provenance():
    events = _events()
    ids = {"review": ("artifact-a", "artifact-b")}
    digests = {"review": (DIGEST_A, DIGEST_B)}
    return dict(
        evaluation_access_log_events=events,
        committed_access_event_count=2,
        committed_terminal_access_event_hash=events[-1]["event_hash"],
        artifact_digest_by_id={
            FINAL_ID: FINAL_DIGEST,
            "artifact-a": DIGEST_A,
            "artifact-b": DIGEST_B,
        },
        expected_evaluation_ledger_binding_stage_names=("review",),
        final_evaluation_digest=FINAL_DIGEST,
        accessed_artifact_digests_by_stage=digests,
        expected_evaluation_content_stage_names=("review",),
        final_evaluation_artifact_id=FINAL_ID,
        accessed_artifact_ids_by_stage=ids,
        expected_evaluation_access_stage_names=("review",),
    )


def _checkpoints(*, mismatch=False):
    events = _events()
    terminal_hash = "sha256:" + "f" * 64 if mismatch else events[1]["event_hash"]
    return (
        {"event_index": 0, "event_hash": events[0]["event_hash"]},
        {"event_index": 1, "event_hash": terminal_hash},
    )


def test_checkpoint_layer_requires_event_log():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    with pytest.raises(ValueError, match="evaluation_access_log_events are required"):
        assess_state_forecast_v11(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            evaluation_access_checkpoints=_checkpoints(),
            **_base_kwargs(),
        )


def test_checkpoint_extraction_rejects_missing_event_hash():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    with pytest.raises(ValueError, match="must contain event_hash"):
        assess_state_forecast_v11(
            "x",
            conditional,
            marginal,
            covered,
            groups,
            blocks,
            evaluation_access_checkpoints=(
                {"event_index": 0, "event_hash": "sha256:" + "a" * 64},
                {"event_index": 1, "event_hash": "sha256:" + "b" * 64},
            ),
            evaluation_access_log_events=[{"sequence_index": 0}, {"sequence_index": 1}],
            **_base_kwargs(),
        )


def test_clean_checkpoints_run_ordinary_v10_path():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    result = assess_state_forecast_v11(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        evaluation_access_checkpoints=_checkpoints(),
        **_full_provenance(),
        **_base_kwargs(),
    )
    assert result.evaluation_access_checkpoints is not None
    assert result.evaluation_access_checkpoints.checkpoints_consistent is True
    assert result.evaluation_access_checkpoints.separation_category == "evaluation_access_checkpoints_consistent"
    assert result.downstream_v10_assessment is not None
    assert result.settings["downstream_v10_assessment_run"] is True
    assert result.v11_certification.evaluation_access_checkpoint_status == "evaluation_access_checkpoints_consistent"


def test_checkpoint_mismatch_short_circuits_full_v10_path(monkeypatch):
    conditional, marginal, covered, groups, blocks = _small_inputs()
    calls = {"full": 0}

    def forbidden_full(*args, **kwargs):
        calls["full"] += 1
        raise AssertionError("full v10 path must not run after checkpoint mismatch")

    monkeypatch.setattr(v11_module, "_full_v10", forbidden_full)
    result = assess_state_forecast_v11(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        evaluation_access_checkpoints=_checkpoints(mismatch=True),
        **_full_provenance(),
        **_base_kwargs(),
    )
    assert calls["full"] == 0
    assert result.evaluation_access_checkpoints is not None
    assert result.evaluation_access_checkpoints.separation_category == "evaluation_access_checkpoint_mismatch"
    assert result.downstream_v10_assessment is None
    assert result.settings["downstream_v10_assessment_run"] is False
    assert result.v11_certification.downstream_v10_status == "not_run_evaluation_access_checkpoint_mismatch"
    assert result.v11_certification.evaluation_access_log_chain_status == "not_run_evaluation_access_checkpoint_mismatch"
    assert "evaluation_access_checkpoint_mismatch" in result.v11_certification.provenance_blocking_reasons


def test_omitted_checkpoint_layer_preserves_direct_v10_result():
    conditional, marginal, covered, groups, blocks = _small_inputs()
    kwargs = _base_kwargs()
    provenance = _full_provenance()
    direct = assess_state_forecast_v10(
        "x", conditional, marginal, covered, groups, blocks, **provenance, **kwargs
    )
    result = assess_state_forecast_v11(
        "x", conditional, marginal, covered, groups, blocks, **provenance, **kwargs
    )
    assert result.evaluation_access_checkpoints is None
    assert result.downstream_v10_assessment is not None
    assert result.downstream_v10_assessment.as_dict() == direct.as_dict()
    assert result.v11_certification.evaluation_access_checkpoint_status == "not_audited"
    assert result.v11_certification.certification_status == direct.v10_certification.certification_status
