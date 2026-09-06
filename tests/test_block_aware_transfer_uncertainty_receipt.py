from __future__ import annotations

import json
from pathlib import Path

from odsp.block_aware_transfer_uncertainty_benchmark import (
    run_block_aware_transfer_uncertainty_benchmark,
)


ROOT = Path(__file__).resolve().parents[1]


def _assert_close(actual: float, expected: float, tol: float = 1e-15) -> None:
    assert abs(actual - expected) <= tol


def test_block_aware_transfer_receipt_replays_frozen_benchmark():
    receipt = json.loads(
        (ROOT / "BLOCK_AWARE_TRANSFER_UNCERTAINTY_VALIDATION_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    cfg = receipt["benchmark_config"]
    result = run_block_aware_transfer_uncertainty_benchmark(
        seed=cfg["seed"],
        bootstrap_draws=cfg["bootstrap_draws"],
        confidence_level=cfg["confidence_level"],
    )
    assert result["passed"] is True
    expected = receipt["canonical_results"]

    strong = result["strong_positive"]
    assert strong["point_transfer_category"] == expected["strong_positive"]["point_transfer_category"]
    assert strong["robust_transfer_category"] == expected["strong_positive"]["robust_transfer_category"]
    _assert_close(strong["mean_gain"], expected["strong_positive"]["mean_gain"])
    _assert_close(
        min(row["lower_bound"] for row in strong["groups"]),
        expected["strong_positive"]["minimum_lower_bound"],
    )

    weak = result["weak_positive"]
    assert weak["point_transfer_category"] == expected["weak_positive"]["point_transfer_category"]
    assert weak["robust_transfer_category"] == expected["weak_positive"]["robust_transfer_category"]
    _assert_close(weak["mean_gain"], expected["weak_positive"]["mean_gain"])
    _assert_close(
        min(row["lower_bound"] for row in weak["groups"]),
        expected["weak_positive"]["minimum_lower_bound"],
    )
    _assert_close(
        max(row["upper_bound"] for row in weak["groups"]),
        expected["weak_positive"]["maximum_upper_bound"],
    )

    negative = result["negative"]
    assert negative["robust_transfer_category"] == expected["negative"]["robust_transfer_category"]
    _assert_close(negative["mean_gain"], expected["negative"]["mean_gain"])
    _assert_close(
        max(row["upper_bound"] for row in negative["groups"]),
        expected["negative"]["maximum_upper_bound"],
    )

    row_mode = result["pseudoreplication_row_mode"]
    block_mode = result["pseudoreplication_block_mode"]
    pseudo = expected["pseudoreplication"]
    _assert_close(row_mode["groups"][0]["lower_bound"], pseudo["row_mode_lower_bound"])
    _assert_close(block_mode["groups"][0]["lower_bound"], pseudo["block_mode_lower_bound"])
    _assert_close(block_mode["groups"][0]["upper_bound"], pseudo["block_mode_upper_bound"])
    assert row_mode["robust_transfer_category"] == pseudo["row_mode_category"]
    assert block_mode["robust_transfer_category"] == pseudo["block_mode_category"]
    assert block_mode["groups"][0]["block_count"] == pseudo["block_count"]

    insufficient = result["too_few_blocks"]
    assert insufficient["robust_transfer_category"] == expected["too_few_blocks"]["robust_transfer_category"]
    assert insufficient["groups"][0]["block_count"] == expected["too_few_blocks"]["block_count"]
    assert result["positive_scaled_strong"]["robust_transfer_category"] == strong["robust_transfer_category"]
    assert result["group_reordered_strong"]["robust_transfer_category"] == strong["robust_transfer_category"]
    assert expected["aggregate_confidence_score_emitted"] is False
