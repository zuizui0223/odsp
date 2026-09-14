from __future__ import annotations

import json
import math
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "BOOTSTRAP_T_V2_OPERATING_CHARACTERISTICS_RECEIPT.json"


def _load() -> dict[str, object]:
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def test_receipt_freezes_first_1000_simulation_run_and_predeclared_panel():
    receipt = _load()
    run = receipt["first_1000_simulation_run"]
    assert run["github_actions_run_id"] == 34799364644
    assert run["github_actions_job_id"] == 103838722462
    assert run["head_sha"] == "bce9c069739409649c25c9c50ecffbc0149492a0"
    assert run["simulations_per_scenario"] == 1000
    assert run["bootstrap_draws_per_interval"] == 500
    assert run["independent_group_count"] == 6
    assert run["nominal_familywise_confidence_level"] == 0.95

    scenarios = receipt["scenarios"]
    assert [row["scenario_id"] for row in scenarios] == [
        "normal-b8",
        "normal-b20",
        "normal-b50",
        "t3-b20",
    ]


def test_v2_passes_predeclared_two_sigma_monte_carlo_acceptance_rule():
    receipt = _load()
    rule = receipt["acceptance_rule"]
    alpha = float(rule["nominal_alpha"])
    simulation_count = int(rule["simulation_count"])
    expected_threshold = alpha + 2.0 * math.sqrt(
        alpha * (1.0 - alpha) / simulation_count
    )
    assert float(rule["maximum_accepted_rate"]) == pytest.approx(
        expected_threshold,
        abs=1e-15,
    )
    assert rule["v1_used_for_acceptance"] is False

    rates = [
        float(row["v2_two_sided_familywise_noncoverage_rate"])
        for row in receipt["scenarios"]
    ]
    assert all(rate <= expected_threshold for rate in rates)
    assert all(row["v2_acceptance_pass"] is True for row in receipt["scenarios"])
    summary = receipt["summary"]
    assert summary["v2_pass_count"] == len(rates) == 4
    assert summary["v2_fail_count"] == 0
    assert summary["qualification_pass"] is True
    assert float(summary["largest_v2_two_sided_familywise_noncoverage_rate"]) == max(rates)


def test_receipt_records_exact_first_1000_run_v2_rates_without_using_v1_as_gate():
    receipt = _load()
    expected = {
        "normal-b8": 0.017,
        "normal-b20": 0.033,
        "normal-b50": 0.043,
        "t3-b20": 0.007,
    }
    observed = {
        row["scenario_id"]: row["v2_two_sided_familywise_noncoverage_rate"]
        for row in receipt["scenarios"]
    }
    assert observed == expected
    assert receipt["acceptance_rule"]["v1_role"] == "descriptive legacy comparator only"


def test_receipt_is_explicitly_non_empirical_and_non_reclassifying():
    receipt = _load()
    assert receipt["empirical_endpoint"] is False
    assert receipt["frozen_endpoint_reclassified"] is False
    boundary = receipt["scientific_boundary"]
    assert boundary["simulation_result_not_biological_evidence"] is True
    assert boundary["no_empirical_endpoint_rerun"] is True
    assert boundary["no_frozen_terminal_reclassification"] is True
    assert boundary["upstream_model_refit_uncertainty_included"] is False
