from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_multicontrast_calibration_receipt_is_non_empirical_and_complete():
    receipt = json.loads(
        (ROOT / "MULTICONTRAST_BOOTSTRAP_T_V2_OPERATING_CHARACTERISTICS_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["receipt_type"] == "odsp_independent_multicontrast_bootstrap_t_v2_operating_characteristics"
    assert receipt["generator_version"] == "analytic_independent_group_equicorrelated_contrasts_v1"
    assert receipt["empirical_endpoint"] is False
    assert receipt["frozen_endpoint_reclassified"] is False
    run = receipt["first_1000_simulation_run"]
    assert run["simulations_per_scenario"] == 1000
    assert run["bootstrap_draws_per_interval"] == 500
    assert run["group_count"] == 6
    assert run["contrast_correlation"] == 0.5
    scenarios = receipt["scenarios"]
    assert len(scenarios) == 5
    assert {row["contrast_count"] for row in scenarios} == {2, 4}
    assert all(row["v2_acceptance_pass"] is True for row in scenarios)
    assert max(row["v2_two_sided_familywise_noncoverage_rate"] for row in scenarios) == 0.037
    assert receipt["summary"]["qualification_pass"] is True
    boundary = receipt["scientific_boundary"]
    assert boundary["simulation_result_not_biological_evidence"] is True
    assert boundary["validation_group_independence_assumed"] is True
    assert boundary["within_group_cross_contrast_covariance_preserved"] is True
    assert boundary["upstream_model_refit_uncertainty_included"] is False
