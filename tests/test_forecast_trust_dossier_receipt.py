from __future__ import annotations

import json
from pathlib import Path

from odsp.forecast_trust_dossier_benchmark import run_forecast_trust_dossier_benchmark

ROOT = Path(__file__).resolve().parents[1]


def _close(a: float, b: float, tol: float = 1e-15) -> None:
    assert abs(a - b) <= tol


def test_forecast_trust_dossier_receipt_replays_frozen_benchmark():
    receipt = json.loads((ROOT / "FORECAST_TRUST_DOSSIER_VALIDATION_RECEIPT.json").read_text(encoding="utf-8"))
    cfg = receipt["benchmark_config"]
    result = run_forecast_trust_dossier_benchmark(
        seed=cfg["seed"],
        bootstrap_draws=cfg["bootstrap_draws"],
    )
    assert result["passed"] is True
    expected = receipt["canonical_results"]

    for name in (
        "robust_in_domain",
        "fragile_in_domain",
        "coverage_failed_in_domain",
        "robust_strict_extrapolation",
        "too_few_blocks",
    ):
        actual = result["dossiers"][name]
        exp = expected[name]
        assert actual["validation"]["robust_validation_status"] == exp["validation_status"]
        assert actual["validation"]["blocking_reasons"] == exp["blocking_reasons"]
        assert actual["deployment"]["status"] == exp["deployment_status"]
        assert actual["selection"]["status"] == exp["selection_status"]
        assert actual["aggregate_confidence_score_emitted"] is False
        if "mean_log_density_gain" in exp:
            _close(actual["validation"]["mean_log_density_gain"], exp["mean_log_density_gain"])
        if "minimum_group_lower_bound" in exp:
            _close(actual["validation"]["minimum_group_lower_bound"], exp["minimum_group_lower_bound"])
        if "worst_group_coverage_error" in exp:
            _close(actual["validation"]["worst_group_coverage_error"], exp["worst_group_coverage_error"])
        if "deployment_warnings" in exp:
            assert actual["deployment"]["warnings"] == exp["deployment_warnings"]
        if "strict_extrapolation_fraction" in exp:
            _close(actual["deployment"]["strict_extrapolation_fraction"], exp["strict_extrapolation_fraction"])
        if "maximum_novelty_ratio" in exp:
            _close(actual["deployment"]["maximum_novelty_ratio"], exp["maximum_novelty_ratio"])

    assert expected["aggregate_confidence_score_emitted"] is False
