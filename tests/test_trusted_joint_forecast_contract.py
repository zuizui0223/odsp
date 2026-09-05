from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_trusted_joint_forecast_contract_keeps_roles_and_claims_separate():
    contract = json.loads(
        (ROOT / "TRUSTED_JOINT_FORECAST_CONTRACT.json").read_text(encoding="utf-8")
    )
    assert contract["contract_id"] == "odsp-trusted-joint-forecast-v1"
    roles = contract["data_roles"]
    assert "joint density model" in roles["training"]
    assert "conformal" in roles["calibration"]
    assert "validation" in roles
    no_collapse = contract["no_collapse"]
    assert no_collapse["single_confidence_number_produced"] is False
    assert no_collapse["novelty_overrides_probability"] is False
    assert no_collapse["conformal_coverage_implies_transfer"] is False
    assert no_collapse["positive_transfer_overrides_extrapolation_warning"] is False
    truth = contract["known_truth_integration"]
    assert truth["seed"] == 20260905
    assert truth["training_rows"] == 1200
    assert truth["calibration_rows"] == 1200
    assert truth["test_rows"] == 3000
    boundary = contract["claim_boundary"]
    assert all(value is False for value in boundary.values())
    frozen = contract["frozen_v4_preservation"]
    assert all(value is False for value in frozen.values())
