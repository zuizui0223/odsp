from __future__ import annotations

import json
from pathlib import Path

from odsp.continuous_circular_conformal_benchmark import (
    run_continuous_circular_conformal_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]


def test_conformal_validation_receipt_reproduces_frozen_benchmark():
    receipt = json.loads(
        (ROOT / "CONTINUOUS_CIRCULAR_CONFORMAL_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    frozen = receipt["benchmark"]
    result = run_continuous_circular_conformal_benchmark(
        seed=frozen["seed"],
        replicates=frozen["replicate_count"],
        calibration_rows=frozen["calibration_rows"],
        test_rows=frozen["test_rows"],
    ).as_dict()

    assert result["passed"] is True
    for key in (
        "seed",
        "replicate_count",
        "calibration_rows",
        "test_rows",
        "target_coverage",
        "mean_continuous_coverage",
        "mean_circular_coverage",
        "mean_joint_coverage",
        "mean_shifted_continuous_coverage",
        "mean_shifted_circular_coverage",
        "continuous_affine_quantile_error",
        "circular_phase_quantile_error",
        "circular_unit_relative_error",
        "passed",
    ):
        assert result[key] == frozen[key]

    assert receipt["first_green_workflow"]["conclusion"] == "success"
    assert receipt["claim_boundary"]["conditional_coverage_claimed"] is False
    assert receipt["claim_boundary"]["shift_robust_coverage_claimed"] is False
    assert receipt["claim_boundary"]["joint_region_called_highest_density_region"] is False
    assert receipt["frozen_v4_preservation"]["v4_manuscript_changed"] is False
    assert receipt["frozen_v4_preservation"]["closed_empirical_endpoint_rerun"] is False
