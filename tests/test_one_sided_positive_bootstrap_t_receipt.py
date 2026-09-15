from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_one_sided_null_calibration_receipt_is_complete_and_non_empirical():
    receipt = json.loads(
        (ROOT / "ONE_SIDED_POSITIVE_BOOTSTRAP_T_NULL_CALIBRATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["receipt_type"] == "odsp_one_sided_positive_bootstrap_t_null_calibration"
    assert receipt["empirical_endpoint"] is False
    assert receipt["frozen_endpoint_reclassified"] is False

    run = receipt["first_1000_simulation_run"]
    assert run["simulations_per_scenario"] == 1000
    assert run["bootstrap_draws_per_interval"] == 500
    assert run["group_count"] == 6
    assert run["contrast_correlation"] == 0.5
    assert run["familywise_lower_confidence_level"] == 0.95
    assert run["generator_version"] == "analytic_independent_group_equicorrelated_contrasts_one_sided_v1"

    rule = receipt["acceptance_rule"]
    assert rule["maximum_accepted_rate"] < 0.064
    scenarios = receipt["scenarios"]
    assert len(scenarios) == 5
    assert all(row["acceptance_pass"] is True for row in scenarios)
    assert max(row["one_sided_familywise_false_positive_rate"] for row in scenarios) == 0.047

    summary = receipt["summary"]
    assert summary["qualification_pass"] is True
    assert summary["pass_count"] == 5
    assert summary["fail_count"] == 0

    boundary = receipt["scientific_boundary"]
    assert boundary["directional_positive_transfer_claim_only"] is True
    assert boundary["two_sided_v2_replaced"] is False
    assert boundary["upstream_model_refit_uncertainty_included"] is False
    assert boundary["paired_or_arbitrary_dependence_validated"] is False
    assert boundary["no_empirical_endpoint_rerun"] is True
