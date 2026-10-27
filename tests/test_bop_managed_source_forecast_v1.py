from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.run_bop_managed_source_to_forecast_v1 import (
    CONTRACT_PATH,
    load_contract,
    run_world,
)


def test_new_benchmark_contract_is_frozen_before_first_outcome_and_keeps_historic():
    c = load_contract()
    assert c["rng_seed"] == 20261027
    assert c["replicates"] == 64
    assert c["role"] == "prospective_known_truth_method_validation_not_real_BOP"
    assert c["primary_immutable_terminal"] == "empirical_state_prediction_mixed"
    assert c["independent_groups_per_stratum"] == {
        "training": 20, "calibration": 39, "validation": 40,
    }
    assert c["acceptance"]["n_expected_validation_groups_each_condition"] == 10240


def test_one_predeclared_world_produces_generated_forecasts_without_outcome_leakage():
    c = load_contract()
    out = run_world(c, 0)
    assert out["world_index"] == 0
    assert out["training_groups"] == 80
    assert out["calibration_groups"] == 156
    assert out["validation_groups"] == 160
    assert 0 <= out["same_covered"] <= 160
    assert 0 <= out["shift_covered"] <= 160
    assert out["trained_only_before_calibration"] is True
    assert out["generated_forecasts_directly_from_model_artifacts"] is True
    assert out["validation_labels_not_used_to_adjust_model_or_calibration"] is True
    assert len(out["training_source_sha256"]) == 64
    assert len(out["plan_sha256"]) == 64
    assert len(out["calibration_sha256"]) == 64


def test_unauthorized_seed_or_scientific_result_promotion_is_rejected(tmp_path: Path):
    c = load_contract()
    c["rng_seed"] = 31
    q = tmp_path / "tampered.json"
    q.write_text(json.dumps(c), encoding="utf-8")
    with pytest.raises(ValueError, match="contract changed"):
        load_contract(q)
    c = load_contract()
    c["primary_immutable_terminal"] = "empirical_state_prediction_generalizing"
    q.write_text(json.dumps(c), encoding="utf-8")
    with pytest.raises(ValueError, match="contract changed"):
        load_contract(q)
