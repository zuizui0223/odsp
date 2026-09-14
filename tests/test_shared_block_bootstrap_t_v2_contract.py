from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_shared_block_bootstrap_t_v2_contract_freezes_paired_studentization():
    contract = json.loads(
        (ROOT / "ODSP_SHARED_BLOCK_BOOTSTRAP_T_V2_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["schema_version"] == 2
    assert contract["contract_id"] == "odsp-shared-block-bootstrap-t-v2"
    estimator = contract["estimator"]
    assert "reuse the identical sampled sequence" in estimator["bootstrap_draw"]
    assert "recompute" in estimator["replicate_standard_error"]
    dependence = contract["dependence"]
    assert dependence["validation_group_independence_assumed"] is False
    assert dependence["cross_group_covariance_preserved_by_shared_block_draw"] is True
    assert dependence["unbalanced_shared_block_support"] == "fail closed"
    boundary = contract["scientific_boundaries"]
    assert boundary["upstream_model_refit_uncertainty_included"] is False
    assert boundary["missing_shared_blocks_imputed"] is False
    assert boundary["frozen_endpoint_rerun"] is False
    calibration = contract["calibration"]
    assert calibration["predeclared_group_correlation"] == 0.7
    assert calibration["predeclared_contrast_correlation"] == 0.5
    assert len(calibration["predeclared_scenarios"]) == 4
