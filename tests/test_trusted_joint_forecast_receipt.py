from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip(
    "sklearn",
    reason="trusted joint forecast receipt replay requires the optional predict extra",
)

from odsp.trusted_joint_forecast_benchmark import run_trusted_joint_forecast_benchmark


ROOT = Path(__file__).resolve().parents[1]


def test_trusted_joint_forecast_receipt_replays_exact_benchmark():
    receipt = json.loads(
        (ROOT / "TRUSTED_JOINT_FORECAST_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    frozen = receipt["benchmark"]
    result = run_trusted_joint_forecast_benchmark(
        seed=frozen["seed"],
        training_rows=frozen["training_rows"],
        calibration_rows=frozen["calibration_rows"],
        test_rows=frozen["test_rows"],
    ).as_dict()
    assert result == frozen

    provenance = receipt["contract_correction_provenance"]
    assert provenance["generator_changed_after_diagnostic"] is False
    assert provenance["seed_changed_after_diagnostic"] is False
    assert provenance["split_sizes_changed_after_diagnostic"] is False
    assert provenance["model_tuned_to_reduce_valid_coverage"] is False
    assert receipt["first_green_workflow"]["conclusion"] == "success"
    assert receipt["claim_boundary"]["single_confidence_score_claimed"] is False
    assert receipt["frozen_v4_preservation"]["closed_empirical_endpoint_rerun"] is False
