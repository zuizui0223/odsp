from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_frozen_paired_bootstrap_t_calibration_receipt_is_non_empirical_and_complete():
    receipt = json.loads(
        (ROOT / "SHARED_BLOCK_BOOTSTRAP_T_V2_OPERATING_CHARACTERISTICS_RECEIPT.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["receipt_type"] == "odsp_shared_block_bootstrap_t_v2_operating_characteristics"
    assert receipt["empirical_endpoint"] is False
    assert receipt["frozen_endpoint_reclassified"] is False
    run = receipt["first_1000_simulation_run"]
    assert run["simulations_per_scenario"] == 1000
    assert run["group_count"] == 6
    assert run["contrast_count"] == 2
    assert run["group_correlation"] == 0.7
    assert run["contrast_correlation"] == 0.5
    rule = receipt["acceptance_rule"]
    assert rule["v1_used_for_acceptance"] is False
    assert rule["maximum_accepted_rate"] < 0.064
    scenarios = receipt["scenarios"]
    assert len(scenarios) == 4
    assert all(row["v2_acceptance_pass"] is True for row in scenarios)
    assert max(row["v2_two_sided_familywise_noncoverage_rate"] for row in scenarios) == 0.051
    assert max(row["v1_two_sided_familywise_noncoverage_rate"] for row in scenarios) == 0.279
    boundary = receipt["scientific_boundary"]
    assert boundary["simulation_result_not_biological_evidence"] is True
    assert boundary["no_empirical_endpoint_rerun"] is True
    assert boundary["upstream_model_refit_uncertainty_included"] is False
    assert boundary["arbitrary_dependence_structures_validated"] is False
