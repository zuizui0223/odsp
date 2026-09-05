from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("sklearn")

from odsp.prediction_trust_benchmark import run_prediction_trust_benchmark


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "PREDICTION_TRUST_LAYER_VALIDATION_RECEIPT.json"


def test_prediction_trust_receipt_matches_deterministic_benchmark():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    result = run_prediction_trust_benchmark(seed=receipt["benchmark"]["seed"])
    observed = result.as_dict()
    expected = receipt["benchmark"]

    assert result.passed is True
    assert len(result.checks) == expected["check_count"] == 6
    assert all(check.passed for check in result.checks)
    for key in (
        "conformal_target_coverage",
        "conformal_exchangeable_coverage",
        "conformal_shifted_coverage",
        "conformal_mean_set_size",
        "novelty_in_domain_median_ratio",
        "novelty_shifted_median_ratio",
        "novelty_shifted_strict_fraction",
        "novelty_affine_max_abs_ratio_error",
    ):
        assert np.isclose(observed[key], expected[key], rtol=0.0, atol=1e-12), key
    assert observed["individual_gain_category"] == expected["individual_gain_category"]
    assert observed["species_gain_category"] == expected["species_gain_category"]
    assert observed["fine_level_failure_preserved"] is expected["fine_level_failure_preserved"] is True


def test_prediction_trust_receipt_keeps_claim_ceiling_and_v4_freeze():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    boundary = receipt["claim_boundary"]
    assert not any(boundary.values())
    frozen = receipt["frozen_v4_preservation"]
    assert frozen["v4_submission_receipt_changed"] is False
    assert frozen["v4_empirical_endpoint_rerun"] is False
    assert frozen["v4_review_environment_package_version"] == "0.10.0"
    assert frozen["live_package_release_version_bumped_in_this_development"] is False
