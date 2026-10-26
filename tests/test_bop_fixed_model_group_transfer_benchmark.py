from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_bop_fixed_model_group_transfer_benchmark import (
    CONTRACT_PATH, load_contract, single_replicate,
)


def test_frozen_contract_is_expected_and_is_not_an_empirical_bop_retest():
    contract = load_contract()
    assert contract["freeze_date"] == "2026-10-26"
    assert contract["role"] == "prospective_known_truth_method_benchmark_only"
    assert contract["closed_endpoint_modification"] is False
    assert contract["acceptance"]["per_scenario_validation_group_count"] == 40960
    assert contract["design"]["per_stratum_groups"] == {
        "train": 20, "calibration": 39, "validation": 80
    }


def test_one_precommitted_world_passes_fixed_forecast_chronology_and_group_ids():
    contract = load_contract()
    row = single_replicate(contract, replicate_index=0)
    assert row["validation_groups"] == 320
    assert row["training_groups"] == 80
    assert row["calibration_groups"] == 156
    assert row["model_artifact_retrained_after_calibration"] is False
    assert row["calibration_touched_validation_labels"] is False
    assert len(row["plan_sha256"]) == 64
    assert len(row["calibration_sha256"]) == 64
    assert 0 <= row["same_covered"] <= 320
    assert 0 <= row["shift_covered"] <= 320


def test_first_contract_cannot_silently_change_generator(tmp_path: Path):
    modified = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    modified["design"]["seed"] += 1
    path = tmp_path / "modified.json"
    path.write_text(json.dumps(modified), encoding="utf-8")
    with pytest.raises(ValueError, match="generator"):
        load_contract(path)


def test_benchmark_and_original_terminal_are_separate():
    contract = load_contract()
    assert contract["frozen_empirical_bop_rodent_terminal"] == (
        "empirical_state_prediction_mixed"
    )
    assert contract["future_real_validation"].startswith(
        "requires new independent animals"
    )
    assert "BOP_RODENT_STATE_PREDICTION_TERMINAL_RECEIPT.json" not in (
        Path(__file__).read_text()
    )
