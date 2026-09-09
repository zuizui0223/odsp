import numpy as np

import odsp.forecast_assessment_v6 as v6


def test_selection_leakage_never_calls_full_v5_path(monkeypatch):
    conditional = np.full(8, 0.2)
    marginal = np.zeros(8)
    covered = (True, True, True, True, True, True, True, False)
    groups = tuple("g" for _ in range(8))
    blocks = tuple(f"b{i}" for i in range(8))
    row_ids = tuple(f"r{i}" for i in range(8))

    calls = []

    def forbidden_full_v5(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("full v5 path must not run after selection leakage")

    monkeypatch.setattr(v6, "_full_v5", forbidden_full_v5)
    result = v6.assess_state_forecast_v6(
        "selection-leak",
        conditional,
        marginal,
        covered,
        groups,
        blocks,
        region_size=np.ones(8),
        validation_row_ids=row_ids,
        selection_row_ids_by_stage={"candidate_ranking": ("dev-a", row_ids[0])},
        # Deliberately incomplete downstream scheme metadata: selection leakage
        # must short-circuit before any of it is interpreted.
        refit_schemes={"broken": ((0.1,),)},
        validation_gamma=1.0,
        bootstrap_draws=100,
        minimum_blocks_per_group=2,
        scheme_nested_draws=500,
        scheme_minimum_refits=2,
    )

    assert calls == []
    assert result.downstream_v5_assessment is None
    assert result.settings["downstream_v5_assessment_run"] is False
    assert result.selection_validation_provenance is not None
    assert result.selection_validation_provenance.separation_category == "selection_validation_leakage"
    assert result.v6_certification.certification_status == "unavailable"
    assert result.v6_certification.provenance_blocking_reasons == (
        "selection_validation_leakage",
    )
    assert result.v6_certification.training_validation_provenance_status == (
        "not_run_selection_validation_leakage"
    )
    assert result.v6_certification.heldout_row_provenance_status == (
        "not_run_selection_validation_leakage"
    )
