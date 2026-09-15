from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_directional_power_comparison_receipt_is_complete_and_non_empirical():
    receipt = json.loads(
        (ROOT / "DIRECTIONAL_TRANSFER_POWER_COMPARISON_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["receipt_type"] == "odsp_directional_transfer_power_comparison"
    assert receipt["empirical_endpoint"] is False
    assert receipt["frozen_endpoint_reclassified"] is False

    run = receipt["first_1000_simulation_run"]
    assert run["simulations_per_scenario"] == 1000
    assert run["bootstrap_draws_per_interval"] == 500
    assert run["same_world_per_method"] is True
    assert run["same_bootstrap_seed_per_method"] is True

    rule = receipt["predeclared_qualification"]
    assert rule["candidate_ceiling_regression_count_must_equal"] == 0
    assert rule["coarse_truth_overreach_maximum_rate"] == 0.06378404875209022
    assert rule["power_gain_used_for_qualification"] is False

    scenarios = {row["scenario_id"]: row for row in receipt["scenarios"]}
    assert len(scenarios) == 6
    assert scenarios["strong-full-normal-b20"]["one_sided_exact_ceiling_recovery_rate"] == 0.994
    assert scenarios["weak-full-normal-b20"]["one_sided_exact_ceiling_recovery_rate"] == 0.058
    assert scenarios["coarse-null-t3-b20"]["one_sided_exact_ceiling_recovery_rate"] == 0.729
    assert all(row["paired_dataset_ceiling_regression_count"] == 0 for row in scenarios.values())
    assert all(row["candidate_acceptance_pass"] is True for row in scenarios.values())
    assert max(row["one_sided_overreach_rate"] for row in scenarios.values()) == 0.0

    summary = receipt["summary"]
    assert summary["qualification_pass"] is True
    assert summary["two_sided_reference_reproduced_exactly"] is True
    assert summary["total_paired_dataset_ceiling_regressions"] == 0
    assert summary["total_paired_dataset_ceiling_advances"] == 196

    boundary = receipt["scientific_boundary"]
    assert boundary["directional_positive_transfer_primary_when_alternative_predeclared_greater"] is True
    assert boundary["two_sided_route_retained_for_bidirectional_inference"] is True
    assert boundary["upstream_model_refit_uncertainty_included"] is False
    assert boundary["historical_empirical_endpoint_rerun"] is False
