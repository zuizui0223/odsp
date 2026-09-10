import numpy as np

import odsp.forecast_assessment_v7 as v7


def test_access_leakage_does_not_call_full_v6(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("full v6 path must not run after final-evaluation access leakage")

    monkeypatch.setattr(v7, "_full_v6", fail_if_called)

    conditional = np.full(8, 0.2)
    marginal = np.zeros(8)
    covered = (True, True, True, True, True, True, True, False)
    groups = tuple("g" for _ in range(8))
    blocks = tuple(f"b{i}" for i in range(8))

    result = v7.assess_state_forecast_v7(
        "x",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        region_size=np.ones(8),
        validation_gamma=1.0,
        bootstrap_draws=100,
        minimum_blocks_per_group=2,
        final_evaluation_artifact_id="final",
        accessed_artifact_ids_by_stage={"candidate_screening": ("dev", "final")},
        scheme_nested_draws=500,
        scheme_minimum_refits=2,
    )

    assert result.downstream_v6_assessment is None
    assert result.v7_certification.downstream_v6_status == "not_run_final_evaluation_access_leakage"
    assert result.v7_certification.certification_status == "unavailable"
