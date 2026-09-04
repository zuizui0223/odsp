from __future__ import annotations

import json
from pathlib import Path

import pytest

from odsp.state_prediction_benchmark import run_state_prediction_benchmark


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "STATE_RESOLVED_PREDICTION_VALIDATION_RECEIPT.json"


def _receipt():
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def _cell(result, family, sample_size):
    return next(
        cell
        for cell in result.cells
        if cell.family == family and cell.sample_size_per_base == sample_size
    )


def test_prediction_receipt_pins_main_release_and_workflows():
    receipt = _receipt()
    assert receipt["package"] == {
        "name": "odsp-niche-geometry",
        "version": "0.10.0",
        "main_sha": "7ac3b36ac93585713ca1dc8c4f86b5e466def81b",
    }
    validation = receipt["main_validation"]
    assert validation["regular_test_run_id"] == 33870772447
    assert validation["regular_test_conclusion"] == "success"
    assert validation["prediction_workflow_run_id"] == 33870772425
    assert validation["prediction_workflow_conclusion"] == "success"
    assert validation["benchmark_artifact_id"] == 9935781853
    assert validation["benchmark_artifact_digest"] == "sha256:c9abfd34979b53507cc558fdc3137ea4230e9294ec1d4a68ec81a756b35ae3c8"


def test_prediction_receipt_regenerates_known_truth_benchmark():
    receipt = _receipt()
    result = run_state_prediction_benchmark()
    recorded = {
        (cell["family"], cell["sample_size_per_base"]): cell
        for cell in receipt["finite_sample_benchmark"]["cells"]
    }

    assert result.seed == receipt["finite_sample_benchmark"]["seed"]
    assert result.alpha == receipt["finite_sample_benchmark"]["alpha"]
    assert result.replicates == receipt["finite_sample_benchmark"]["replicates_per_cell"]
    assert list(result.sample_sizes) == receipt["finite_sample_benchmark"]["sample_sizes_per_base"]

    for cell in result.cells:
        expected = recorded[(cell.family, cell.sample_size_per_base)]
        assert cell.mean_log_score_gain == pytest.approx(expected["mean_log_score_gain"], abs=1e-15)
        assert cell.positive_gain_fraction == pytest.approx(expected["positive_gain_fraction"], abs=1e-15)
        assert cell.negative_gain_fraction == pytest.approx(expected["negative_gain_fraction"], abs=1e-15)
        assert cell.mean_probability_rmse == pytest.approx(expected["mean_probability_rmse"], abs=1e-15)
        assert cell.mean_brier_improvement == pytest.approx(expected["mean_brier_improvement"], abs=1e-15)
        assert cell.mean_top1_accuracy == pytest.approx(expected["mean_top1_accuracy"], abs=1e-15)


def test_prediction_release_has_expected_scientific_ceiling():
    receipt = _receipt()
    boundary = receipt["scientific_boundary"]
    assert all(value is False for value in boundary.values())
    assert receipt["position"]["new_occurrence_sdm_algorithm"] is False
    assert receipt["position"]["prediction_targets"] == ["P(A|B)", "P(A|X)"]
    assert "new public dataset" in receipt["next_empirical_requirement"]
