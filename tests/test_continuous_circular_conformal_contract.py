from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_continuous_circular_conformal_contract_freezes_claim_boundaries():
    contract = json.loads(
        (ROOT / "CONTINUOUS_CIRCULAR_CONFORMAL_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["contract_id"] == "odsp-continuous-circular-conformal-trust-v1"
    assert contract["joint_bonferroni_target"]["total_miscoverage"] == 0.10
    assert contract["joint_bonferroni_target"]["component_target_coverage"] == 0.95
    benchmark = contract["known_truth_benchmark"]
    assert benchmark["seed"] == 20260905
    assert benchmark["replicates"] == 128
    assert benchmark["calibration_rows"] == 1000
    assert benchmark["test_rows"] == 2000
    boundary = contract["claim_boundary"]
    assert boundary["conditional_coverage_guaranteed"] is False
    assert boundary["distribution_shift_robust_coverage_guaranteed"] is False
    assert boundary["conformal_set_repairs_bad_base_predictor"] is False
    assert boundary["bonferroni_region_is_highest_density_joint_region"] is False
    assert boundary["coverage_implies_biological_validity"] is False
    frozen = contract["frozen_v4_preservation"]
    assert all(value is False for value in frozen.values())
